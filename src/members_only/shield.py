"""Default-deny brokered requests for the Members Only sandbox seam."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import hmac
import json
from typing import Protocol
from .approvals import proposal_digest
from .models import Capability, Proposal


class ShieldChannel(str, Enum):
    """The controlled route a request wants to use."""

    INGRESS = "ingress"
    EGRESS = "egress"
    UPDATE = "update"
    TELEMETRY = "telemetry"
    MODEL = "model"
    LOG = "log"


@dataclass(frozen=True, slots=True)
class ShieldRequest:
    """Payload-free identity for one request crossing the shield."""

    proposal_id: str
    member_id: str
    agent_id: str
    action: str
    destination: str
    proposal_digest: str
    channel: ShieldChannel
    request_id: str = ""

    def __post_init__(self) -> None:
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("member_id", self.member_id),
            ("agent_id", self.agent_id),
            ("action", self.action),
            ("destination", self.destination),
            ("proposal_digest", self.proposal_digest),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.channel, ShieldChannel):
            raise TypeError("channel must be a ShieldChannel")
        if not self.request_id:
            object.__setattr__(self, "request_id", f"shield-{self.proposal_id}")

    @classmethod
    def from_proposal(
        cls,
        proposal: Proposal,
        *,
        channel: ShieldChannel = ShieldChannel.EGRESS,
    ) -> "ShieldRequest":
        """Create a stable request identity without copying the proposal payload."""

        return cls(
            proposal_id=proposal.proposal_id,
            member_id=proposal.member_id,
            agent_id=proposal.agent_id,
            action=proposal.action,
            destination=proposal.destination,
            proposal_digest=proposal_digest(proposal),
            channel=channel,
        )

    def canonical_bytes(self) -> bytes:
        """Return the signed, payload-free representation of the request."""

        return json.dumps(
            {
                "action": self.action,
                "agent_id": self.agent_id,
                "channel": self.channel.value,
                "destination": self.destination,
                "member_id": self.member_id,
                "proposal_digest": self.proposal_digest,
                "proposal_id": self.proposal_id,
                "request_id": self.request_id,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")


@dataclass(frozen=True, slots=True)
class MachineAttestation:
    """Evidence presented by the workload before a request is brokered."""

    workload_id: str
    hardware_id: str
    signature: str


@dataclass(frozen=True, slots=True)
class MachineVerification:
    """The verifier's result without including secrets or raw payloads."""

    verified: bool
    reasons: tuple[str, ...]


class MachineVerifier(Protocol):
    """Interface for static, TPM, enclave, or orchestrator-backed verification."""

    def verify(
        self,
        request: ShieldRequest,
        attestation: MachineAttestation,
    ) -> MachineVerification:
        """Verify workload identity, hardware identity, and request signature."""
        ...


class StaticMachineVerifier:
    """Deterministic verifier for the local MVP and security tests."""

    def __init__(
        self,
        *,
        trusted_workload_id: str,
        trusted_hardware_id: str,
        signing_secret: str,
    ) -> None:
        if not signing_secret:
            raise ValueError("signing_secret must be non-empty")
        self._trusted_workload_id = trusted_workload_id
        self._trusted_hardware_id = trusted_hardware_id
        self._signing_secret = signing_secret.encode("utf-8")

    def verify(
        self,
        request: ShieldRequest,
        attestation: MachineAttestation,
    ) -> MachineVerification:
        reasons: list[str] = []
        if attestation.workload_id != self._trusted_workload_id:
            reasons.append("untrusted_workload")
        if attestation.hardware_id != self._trusted_hardware_id:
            reasons.append("untrusted_hardware")
        expected = sign_request(
            request,
            workload_id=attestation.workload_id,
            hardware_id=attestation.hardware_id,
            signing_secret=self._signing_secret,
        )
        if not hmac.compare_digest(attestation.signature, expected):
            reasons.append("invalid_request_signature")
        return MachineVerification(verified=not reasons, reasons=tuple(reasons))


@dataclass(frozen=True, slots=True)
class ApprovedRule:
    """An exact, pre-approved route through the sealed environment."""

    rule_id: str
    channel: ShieldChannel
    action: str
    destination: str
    workload_id: str

    def __post_init__(self) -> None:
        for name, value in (
            ("rule_id", self.rule_id),
            ("action", self.action),
            ("destination", self.destination),
            ("workload_id", self.workload_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.channel, ShieldChannel):
            raise TypeError("channel must be a ShieldChannel")

    def matches(self, request: ShieldRequest, attestation: MachineAttestation) -> bool:
        return (
            request.channel == self.channel
            and request.action == self.action
            and request.destination == self.destination
            and attestation.workload_id == self.workload_id
        )


@dataclass(frozen=True, slots=True)
class BrokerReceipt:
    """Safe result from a broker; it never contains request payload data."""

    accepted: bool
    broker: str
    reason: str


class RequestBroker(Protocol):
    """Interface for local, network, update, telemetry, model, or log brokers."""

    def forward(self, request: ShieldRequest) -> BrokerReceipt:
        """Forward an already-authorized request or reject it."""
        ...


class DenyAllBroker:
    """Safe default when no concrete broker has been explicitly configured."""

    def forward(self, _request: ShieldRequest) -> BrokerReceipt:
        return BrokerReceipt(False, type(self).__name__, "no broker is configured")


class LocalBroker:
    """A no-network broker for synthetic local actions."""

    def forward(self, request: ShieldRequest) -> BrokerReceipt:
        if request.channel != ShieldChannel.EGRESS:
            return BrokerReceipt(False, type(self).__name__, "broker does not serve this channel")
        if not request.destination.startswith("local:"):
            return BrokerReceipt(False, type(self).__name__, "destination is not local")
        return BrokerReceipt(True, type(self).__name__, "local route accepted")


@dataclass(frozen=True, slots=True)
class ShieldReceipt:
    """Safe decision record for one request through the shield."""

    request_id: str
    proposal_id: str
    allowed: bool
    reason: str
    machine_verified: bool
    approval_source: str | None = None
    broker: str | None = None
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ShieldDenied(PermissionError):
    """Raised after the shield refuses a request."""

    def __init__(self, receipt: ShieldReceipt) -> None:
        super().__init__(receipt.reason)
        self.receipt = receipt


class SandboxShield:
    """Deep default-deny interface for all requests leaving the application."""

    def __init__(
        self,
        *,
        verifier: MachineVerifier,
        broker: RequestBroker | None = None,
        rules: tuple[ApprovedRule, ...] = (),
    ) -> None:
        self._verifier = verifier
        self._broker = broker or DenyAllBroker()
        self._rules = tuple(rules)

    def authorize(
        self,
        proposal: Proposal,
        capability: Capability | None,
        attestation: MachineAttestation,
        *,
        channel: ShieldChannel = ShieldChannel.EGRESS,
    ) -> ShieldReceipt:
        """Verify, require approval, and pass one request to the configured broker."""

        request = ShieldRequest.from_proposal(proposal, channel=channel)
        verification = self._verifier.verify(request, attestation)
        if not verification.verified:
            return self._receipt(
                request,
                allowed=False,
                reason="machine verification failed: " + ", ".join(verification.reasons),
                machine_verified=False,
            )

        approval_source = self._approval_source(request, capability, attestation)
        if approval_source is None:
            return self._receipt(
                request,
                allowed=False,
                reason="explicit approval is required for this exact request",
                machine_verified=True,
            )

        broker_receipt = self._broker.forward(request)
        if not broker_receipt.accepted:
            return self._receipt(
                request,
                allowed=False,
                reason=f"broker denied request: {broker_receipt.reason}",
                machine_verified=True,
                approval_source=approval_source,
                broker=broker_receipt.broker,
            )

        return self._receipt(
            request,
            allowed=True,
            reason=broker_receipt.reason,
            machine_verified=True,
            approval_source=approval_source,
            broker=broker_receipt.broker,
        )

    def _approval_source(
        self,
        request: ShieldRequest,
        capability: Capability | None,
        attestation: MachineAttestation,
    ) -> str | None:
        if capability is not None and (
            capability.proposal_id == request.proposal_id
            and capability.member_id == request.member_id
            and capability.action == request.action
            and capability.proposal_digest == request.proposal_digest
        ):
            return "member_capability"
        if any(rule.matches(request, attestation) for rule in self._rules):
            return "approved_rule"
        return None

    @staticmethod
    def _receipt(
        request: ShieldRequest,
        *,
        allowed: bool,
        reason: str,
        machine_verified: bool,
        approval_source: str | None = None,
        broker: str | None = None,
    ) -> ShieldReceipt:
        return ShieldReceipt(
            request_id=request.request_id,
            proposal_id=request.proposal_id,
            allowed=allowed,
            reason=reason,
            machine_verified=machine_verified,
            approval_source=approval_source,
            broker=broker,
        )


def sign_request(
    request: ShieldRequest,
    *,
    workload_id: str,
    hardware_id: str,
    signing_secret: str | bytes,
) -> str:
    """Create the deterministic signature used by the local verifier."""

    secret = signing_secret.encode("utf-8") if isinstance(signing_secret, str) else signing_secret
    message = b"|".join((workload_id.encode(), hardware_id.encode(), request.canonical_bytes()))
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def demo_attestation(
    proposal: Proposal,
    *,
    workload_id: str = "members-only-demo",
    hardware_id: str = "sandbox-hardware-demo",
    signing_secret: str = "local-demo-only",
) -> tuple[StaticMachineVerifier, MachineAttestation]:
    """Build the explicit software-verifier fixture used by the CLI demo."""

    request = ShieldRequest.from_proposal(proposal)
    verifier = StaticMachineVerifier(
        trusted_workload_id=workload_id,
        trusted_hardware_id=hardware_id,
        signing_secret=signing_secret,
    )
    attestation = MachineAttestation(
        workload_id=workload_id,
        hardware_id=hardware_id,
        signature=sign_request(
            request,
            workload_id=workload_id,
            hardware_id=hardware_id,
            signing_secret=signing_secret,
        ),
    )
    return verifier, attestation

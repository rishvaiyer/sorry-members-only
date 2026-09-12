"""Shared data types for the Members Only security pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return uuid4().hex


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


class SensitivityLevel(str, Enum):
    """How harmful it could be to expose the detected information."""

    NONE = "none"
    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


class Decision(str, Enum):
    """The policy engine's possible outcomes."""

    ALLOW = "allow"
    DENY = "deny"
    REQUIRES_APPROVAL = "requires_approval"


class ExecutionStatus(str, Enum):
    """The outcome recorded after an approved action is attempted."""

    SUCCEEDED = "succeeded"
    DENIED = "denied"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Proposal:
    """An action an agent wants to perform for a member."""

    member_id: str
    agent_id: str
    action: str
    destination: str
    payload: Mapping[str, Any]
    proposal_id: str = field(default_factory=_new_id)
    created_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        for name, value in (
            ("member_id", self.member_id),
            ("agent_id", self.agent_id),
            ("action", self.action),
            ("destination", self.destination),
            ("proposal_id", self.proposal_id),
        ):
            _require_text(name, value)
        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


@dataclass(frozen=True, slots=True)
class SensitivityFinding:
    """Evidence that a proposal contains information requiring protection."""

    category: str
    level: SensitivityLevel
    reason: str
    confidence: float
    field: str | None = None

    def __post_init__(self) -> None:
        _require_text("category", self.category)
        _require_text("reason", self.reason)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """The policy engine's decision and the evidence behind it."""

    proposal_id: str
    decision: Decision
    reasons: tuple[str, ...]
    findings: tuple[SensitivityFinding, ...] = ()
    decided_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _require_text("proposal_id", self.proposal_id)
        object.__setattr__(self, "reasons", tuple(self.reasons))
        object.__setattr__(self, "findings", tuple(self.findings))


@dataclass(frozen=True, slots=True)
class Approval:
    """A member's approval of one exact proposal."""

    proposal_id: str
    member_id: str
    proposal_digest: str
    approval_id: str = field(default_factory=_new_id)
    approved_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("member_id", self.member_id),
            ("proposal_digest", self.proposal_digest),
            ("approval_id", self.approval_id),
        ):
            _require_text(name, value)


@dataclass(frozen=True, slots=True)
class Capability:
    """A short-lived permission to execute one approved proposal once."""

    proposal_id: str
    member_id: str
    action: str
    proposal_digest: str
    expires_at: datetime
    capability_id: str = field(default_factory=_new_id)
    issued_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("member_id", self.member_id),
            ("action", self.action),
            ("proposal_digest", self.proposal_digest),
            ("capability_id", self.capability_id),
        ):
            _require_text(name, value)


@dataclass(frozen=True, slots=True)
class Receipt:
    """A compact record of the decision and execution outcome."""

    proposal_id: str
    decision: Decision
    status: ExecutionStatus
    summary: str
    receipt_id: str = field(default_factory=_new_id)
    recorded_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("summary", self.summary),
            ("receipt_id", self.receipt_id),
        ):
            _require_text(name, value)

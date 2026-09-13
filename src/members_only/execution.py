"""Final capability check before an action adapter runs."""

from __future__ import annotations

from .adapters.base import ActionAdapter, ActionResult
from .capabilities import CapabilityManager
from .models import Capability, Proposal
from .shield import MachineAttestation, SandboxShield, ShieldDenied, ShieldReceipt


class ExecutionGate:
    """Recheck and consume a capability before executing an action."""

    def __init__(
        self,
        capability_manager: CapabilityManager,
        adapter: ActionAdapter,
        *,
        shield: SandboxShield | None = None,
        attestation: MachineAttestation | None = None,
    ) -> None:
        self._capability_manager = capability_manager
        self._adapter = adapter
        self._shield = shield
        self._attestation = attestation
        self.last_shield_receipt: ShieldReceipt | None = None

    def execute(self, proposal: Proposal, capability: Capability) -> ActionResult:
        self.last_shield_receipt = None
        self._capability_manager.redeem(capability, proposal)
        if self._shield is not None:
            if self._attestation is None:
                raise ValueError("a machine attestation is required when the shield is enabled")
            receipt = self._shield.authorize(proposal, capability, self._attestation)
            self.last_shield_receipt = receipt
            if not receipt.allowed:
                raise ShieldDenied(receipt)
        return self._adapter.execute(proposal)

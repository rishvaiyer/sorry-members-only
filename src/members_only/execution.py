"""Final capability check before an action adapter runs."""

from __future__ import annotations

from .adapters.base import ActionAdapter, ActionResult
from .capabilities import CapabilityManager
from .models import Capability, Proposal


class ExecutionGate:
    """Recheck and consume a capability before executing an action."""

    def __init__(self, capability_manager: CapabilityManager, adapter: ActionAdapter) -> None:
        self._capability_manager = capability_manager
        self._adapter = adapter

    def execute(self, proposal: Proposal, capability: Capability) -> ActionResult:
        self._capability_manager.redeem(capability, proposal)
        return self._adapter.execute(proposal)

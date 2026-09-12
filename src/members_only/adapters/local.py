"""Synthetic local actions for development and security tests."""

from __future__ import annotations

from .base import ActionResult
from ..models import Proposal


class LocalActionAdapter:
    """Simulate supported actions without contacting an external service."""

    _SUPPORTED_ACTIONS = frozenset({"save_note", "send_message"})

    def __init__(self) -> None:
        self._executed_proposal_ids: list[str] = []

    @property
    def executed_proposal_ids(self) -> tuple[str, ...]:
        return tuple(self._executed_proposal_ids)

    def execute(self, proposal: Proposal) -> ActionResult:
        if not proposal.destination.startswith("local:"):
            raise ValueError("local adapter cannot execute an external destination")
        if proposal.action not in self._SUPPORTED_ACTIONS:
            raise ValueError(f"unsupported local action: {proposal.action}")

        self._executed_proposal_ids.append(proposal.proposal_id)
        return ActionResult(
            success=True,
            proposal_id=proposal.proposal_id,
            action=proposal.action,
            summary=f"Local {proposal.action} simulated; no external request was sent.",
        )

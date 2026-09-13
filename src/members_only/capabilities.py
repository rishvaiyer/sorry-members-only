"""Short-lived, one-use permissions for approved proposals."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .approvals import proposal_digest
from .models import Approval, Capability, Proposal


class CapabilityManager:
    """Issue and redeem in-memory capabilities for the current process."""

    def __init__(self) -> None:
        self._redeemed_ids: set[str] = set()

    def issue(
        self,
        proposal: Proposal,
        approval: Approval,
        *,
        ttl_seconds: int = 300,
    ) -> Capability:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero")
        if approval.proposal_id != proposal.proposal_id:
            raise ValueError("approval does not belong to this proposal")
        if approval.member_id != proposal.member_id:
            raise PermissionError("approval belongs to a different member")
        if approval.proposal_digest != proposal_digest(proposal):
            raise PermissionError("approval does not match the proposal contents")

        issued_at = datetime.now(timezone.utc)
        return Capability(
            proposal_id=proposal.proposal_id,
            member_id=proposal.member_id,
            action=proposal.action,
            proposal_digest=approval.proposal_digest,
            issued_at=issued_at,
            expires_at=issued_at + timedelta(seconds=ttl_seconds),
        )

    def redeem(self, capability: Capability, proposal: Proposal) -> None:
        """Consume a capability if it still matches and has not expired."""

        if capability.capability_id in self._redeemed_ids:
            raise PermissionError("capability has already been redeemed")
        if datetime.now(timezone.utc) >= capability.expires_at:
            raise PermissionError("capability has expired")
        if (
            capability.proposal_id != proposal.proposal_id
            or capability.member_id != proposal.member_id
            or capability.action != proposal.action
            or capability.proposal_digest != proposal_digest(proposal)
        ):
            raise PermissionError("capability does not match the proposal")

        self._redeemed_ids.add(capability.capability_id)

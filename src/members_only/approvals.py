"""Member approval and proposal binding helpers."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime
from enum import Enum
from typing import Any

from .models import Approval, Decision, PolicyDecision, Proposal


def _canonical_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonical_value(nested) for key, nested in value.items()}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def proposal_digest(proposal: Proposal) -> str:
    """Return a stable SHA-256 digest for the exact proposal contents."""

    canonical_proposal = {
        "proposal_id": proposal.proposal_id,
        "member_id": proposal.member_id,
        "agent_id": proposal.agent_id,
        "action": proposal.action,
        "destination": proposal.destination,
        "payload": proposal.payload,
        "created_at": proposal.created_at,
    }
    encoded = json.dumps(
        _canonical_value(canonical_proposal),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def approve_proposal(
    proposal: Proposal,
    policy_decision: PolicyDecision,
    *,
    member_id: str,
) -> Approval:
    """Create approval only for this member and this exact proposal."""

    if policy_decision.proposal_id != proposal.proposal_id:
        raise ValueError("policy decision does not belong to this proposal")
    if policy_decision.decision != Decision.REQUIRES_APPROVAL:
        raise ValueError("proposal is not waiting for approval")
    if member_id != proposal.member_id:
        raise PermissionError("only the proposal's member can approve it")

    return Approval(
        proposal_id=proposal.proposal_id,
        member_id=member_id,
        proposal_digest=proposal_digest(proposal),
    )

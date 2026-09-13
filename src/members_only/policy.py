"""Deterministic policy decisions for proposed agent actions."""

from __future__ import annotations

from collections.abc import Iterable

from .models import (
    Decision,
    PolicyDecision,
    Proposal,
    SensitivityFinding,
    SensitivityLevel,
)


def evaluate_proposal(
    proposal: Proposal,
    findings: Iterable[SensitivityFinding],
) -> PolicyDecision:
    """Return the policy outcome for one proposal and its findings."""

    findings_tuple = tuple(findings)
    if any(
        finding.category == "credential" or finding.level == SensitivityLevel.CRITICAL
        for finding in findings_tuple
    ):
        return PolicyDecision(
            proposal_id=proposal.proposal_id,
            decision=Decision.DENY,
            reasons=("Credential exposure is denied.",),
            findings=findings_tuple,
        )

    if not proposal.destination.startswith("local:"):
        return PolicyDecision(
            proposal_id=proposal.proposal_id,
            decision=Decision.REQUIRES_APPROVAL,
            reasons=("The destination leaves the local boundary and needs approval.",),
            findings=findings_tuple,
        )

    if findings_tuple:
        return PolicyDecision(
            proposal_id=proposal.proposal_id,
            decision=Decision.REQUIRES_APPROVAL,
            reasons=("Sensitive content requires member approval.",),
            findings=findings_tuple,
        )

    return PolicyDecision(
        proposal_id=proposal.proposal_id,
        decision=Decision.ALLOW,
        reasons=("No sensitive content was detected.",),
        findings=findings_tuple,
    )

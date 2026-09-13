"""End-to-end Members Only security workflow."""

from __future__ import annotations

from .adapters import ActionAdapter, LocalActionAdapter
from .approvals import approve_proposal
from .capabilities import CapabilityManager
from .execution import ExecutionGate
from .models import (
    Capability,
    Decision,
    ExecutionStatus,
    PolicyDecision,
    Proposal,
    Receipt,
)
from .policy import evaluate_proposal
from .receipts import TraceRecorder, create_receipt
from .sensitivity import inspect_proposal
from .storage import LocalStore


class MembersOnlyPipeline:
    """Connect proposal inspection, approval, execution, and receipts."""

    def __init__(
        self,
        *,
        adapter: ActionAdapter | None = None,
        store: LocalStore | None = None,
        capability_manager: CapabilityManager | None = None,
        trace: TraceRecorder | None = None,
    ) -> None:
        self.adapter = adapter or LocalActionAdapter()
        self.store = store or LocalStore()
        self.capability_manager = capability_manager or CapabilityManager()
        self.trace = trace or TraceRecorder()
        self.execution_gate = ExecutionGate(self.capability_manager, self.adapter)

    def evaluate(self, proposal: Proposal) -> PolicyDecision:
        """Inspect a proposal and record the resulting policy decision."""

        self.trace.record(
            "proposal_received",
            proposal.proposal_id,
            {
                "action": proposal.action,
                "destination_scope": (
                    "local" if proposal.destination.startswith("local:") else "external"
                ),
            },
        )
        findings = inspect_proposal(proposal)
        self.trace.record(
            "sensitivity_checked",
            proposal.proposal_id,
            {
                "finding_count": len(findings),
                "finding_categories": sorted({finding.category for finding in findings}),
            },
        )
        decision = evaluate_proposal(proposal, findings)
        self.trace.record(
            "policy_decided",
            proposal.proposal_id,
            {"decision": decision.decision.value},
        )
        return decision

    def approve(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecision,
        *,
        member_id: str,
        ttl_seconds: int = 300,
    ) -> Capability:
        """Record member approval and issue a one-use capability."""

        approval = approve_proposal(proposal, policy_decision, member_id=member_id)
        self.store.save_approval(approval)
        self.trace.record(
            "approval_recorded",
            proposal.proposal_id,
            {"approval_id": approval.approval_id, "member_id": member_id},
        )
        capability = self.capability_manager.issue(
            proposal,
            approval,
            ttl_seconds=ttl_seconds,
        )
        self.store.save_capability(capability)
        self.trace.record(
            "capability_issued",
            proposal.proposal_id,
            {"capability_id": capability.capability_id},
        )
        return capability

    def execute(
        self,
        proposal: Proposal,
        policy_decision: PolicyDecision,
        capability: Capability,
    ) -> Receipt:
        """Execute through the final gate and persist a safe receipt."""

        try:
            result = self.execution_gate.execute(proposal, capability)
        except PermissionError:
            self.trace.record(
                "execution_blocked",
                proposal.proposal_id,
                {"reason": "capability_check_failed"},
            )
            receipt = create_receipt(
                proposal,
                decision=Decision.DENY,
                status=ExecutionStatus.DENIED,
                summary="Execution blocked by capability checks.",
            )
        except ValueError:
            self.trace.record(
                "execution_failed",
                proposal.proposal_id,
                {"reason": "adapter_rejected_action"},
            )
            receipt = create_receipt(
                proposal,
                decision=policy_decision.decision,
                status=ExecutionStatus.FAILED,
                summary="The action adapter rejected the action.",
            )
        else:
            self.trace.record(
                "action_executed",
                proposal.proposal_id,
                {
                    "adapter": type(self.adapter).__name__,
                    "success": result.success,
                },
            )
            receipt = create_receipt(
                proposal,
                decision=policy_decision.decision,
                status=(
                    ExecutionStatus.SUCCEEDED
                    if result.success
                    else ExecutionStatus.FAILED
                ),
                summary=result.summary,
            )

        self.store.save_receipt(receipt)
        self.trace.record(
            "receipt_recorded",
            proposal.proposal_id,
            {"receipt_id": receipt.receipt_id, "status": receipt.status.value},
        )
        return receipt

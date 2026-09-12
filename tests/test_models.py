import unittest
from datetime import timezone

from members_only.models import (
    Approval,
    Capability,
    Decision,
    PolicyDecision,
    Proposal,
    SensitivityFinding,
    SensitivityLevel,
)


class ProposalTests(unittest.TestCase):
    def test_proposal_identifies_the_member_and_agent_action(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "hello"},
        )

        self.assertEqual(proposal.member_id, "member-1")
        self.assertEqual(proposal.action, "send_message")
        self.assertEqual(proposal.payload["body"], "hello")
        self.assertTrue(proposal.proposal_id)
        self.assertIsNotNone(proposal.created_at.tzinfo)
        self.assertEqual(proposal.created_at.tzinfo, timezone.utc)


class DecisionModelTests(unittest.TestCase):
    def test_policy_decision_keeps_findings_and_reasons(self):
        finding = SensitivityFinding(
            category="private_message",
            level=SensitivityLevel.HIGH,
            reason="The payload contains private content.",
            confidence=0.98,
        )
        decision = PolicyDecision(
            proposal_id="proposal-1",
            decision=Decision.REQUIRES_APPROVAL,
            reasons=("Sensitive content requires member approval.",),
            findings=(finding,),
        )

        self.assertEqual(decision.decision, Decision.REQUIRES_APPROVAL)
        self.assertEqual(decision.findings[0].category, "private_message")
        self.assertEqual(decision.reasons[0], "Sensitive content requires member approval.")


class PermissionModelTests(unittest.TestCase):
    def test_approval_and_capability_are_bound_to_the_same_proposal(self):
        approval = Approval(
            proposal_id="proposal-1",
            member_id="member-1",
            proposal_digest="digest-1",
        )
        capability = Capability(
            proposal_id=approval.proposal_id,
            member_id=approval.member_id,
            action="send_message",
            proposal_digest=approval.proposal_digest,
            expires_at=approval.approved_at,
        )

        self.assertEqual(capability.proposal_id, approval.proposal_id)
        self.assertEqual(capability.member_id, approval.member_id)
        self.assertEqual(capability.proposal_digest, approval.proposal_digest)
        self.assertTrue(capability.capability_id)


if __name__ == "__main__":
    unittest.main()

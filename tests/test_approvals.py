import unittest

from members_only import approve_proposal, proposal_digest
from members_only.models import Decision, PolicyDecision, Proposal


def approval_required_for(proposal: Proposal) -> PolicyDecision:
    return PolicyDecision(
        proposal_id=proposal.proposal_id,
        decision=Decision.REQUIRES_APPROVAL,
        reasons=("Sensitive content requires member approval.",),
    )


class ApprovalFlowTests(unittest.TestCase):
    def test_digest_is_stable_and_does_not_expose_payload_text(self):
        secret = "private-message-content"
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": secret},
        )

        first_digest = proposal_digest(proposal)
        second_digest = proposal_digest(proposal)

        self.assertEqual(first_digest, second_digest)
        self.assertEqual(len(first_digest), 64)
        self.assertNotIn(secret, first_digest)

    def test_member_approval_binds_to_the_exact_proposal_digest(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please review this."},
        )

        approval = approve_proposal(
            proposal,
            approval_required_for(proposal),
            member_id="member-1",
        )

        self.assertEqual(approval.proposal_id, proposal.proposal_id)
        self.assertEqual(approval.member_id, proposal.member_id)
        self.assertEqual(approval.proposal_digest, proposal_digest(proposal))

    def test_changed_payload_produces_a_different_digest(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please review this."},
        )
        changed_proposal = Proposal(
            member_id=proposal.member_id,
            agent_id=proposal.agent_id,
            action=proposal.action,
            destination=proposal.destination,
            payload={"body": "Please send this now."},
            proposal_id=proposal.proposal_id,
            created_at=proposal.created_at,
        )

        self.assertNotEqual(proposal_digest(proposal), proposal_digest(changed_proposal))

    def test_different_member_cannot_approve_the_proposal(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please review this."},
        )

        with self.assertRaises(PermissionError):
            approve_proposal(
                proposal,
                approval_required_for(proposal),
                member_id="member-2",
            )

    def test_approval_requires_a_policy_decision_for_this_proposal(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please review this."},
        )
        other_decision = PolicyDecision(
            proposal_id="different-proposal",
            decision=Decision.REQUIRES_APPROVAL,
            reasons=("Sensitive content requires member approval.",),
        )

        with self.assertRaises(ValueError):
            approve_proposal(proposal, other_decision, member_id="member-1")


if __name__ == "__main__":
    unittest.main()

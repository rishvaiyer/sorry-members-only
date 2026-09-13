import unittest

from members_only import evaluate_proposal, inspect_proposal
from members_only.models import Decision, Proposal


class PolicyEngineTests(unittest.TestCase):
    def test_allows_an_ordinary_local_note(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_note",
            destination="local:test-inbox",
            payload={"title": "status", "body": "The task is complete."},
        )

        decision = evaluate_proposal(proposal, inspect_proposal(proposal))

        self.assertEqual(decision.decision, Decision.ALLOW)
        self.assertEqual(decision.proposal_id, proposal.proposal_id)
        self.assertEqual(decision.findings, ())

    def test_requires_member_approval_for_private_message(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please keep this private."},
        )

        decision = evaluate_proposal(proposal, inspect_proposal(proposal))

        self.assertEqual(decision.decision, Decision.REQUIRES_APPROVAL)
        self.assertIn("member approval", decision.reasons[0].lower())

    def test_denies_credential_exposure(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "api_key=sk-live-1234567890abcdef"},
        )

        decision = evaluate_proposal(proposal, inspect_proposal(proposal))

        self.assertEqual(decision.decision, Decision.DENY)
        self.assertIn("credential", decision.reasons[0].lower())

    def test_requires_approval_before_leaving_local_boundary(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_note",
            destination="https://example.com/notes",
            payload={"body": "The task is complete."},
        )

        decision = evaluate_proposal(proposal, inspect_proposal(proposal))

        self.assertEqual(decision.decision, Decision.REQUIRES_APPROVAL)
        self.assertIn("destination", decision.reasons[0].lower())


if __name__ == "__main__":
    unittest.main()

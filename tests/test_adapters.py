import unittest

from members_only import LocalActionAdapter
from members_only.models import Proposal


def make_proposal(*, action: str = "send_message", destination: str = "local:test-inbox") -> Proposal:
    return Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action=action,
        destination=destination,
        payload={"body": "Hello from the local demo."},
    )


class LocalActionAdapterTests(unittest.TestCase):
    def test_executes_supported_local_action_without_network_access(self):
        adapter = LocalActionAdapter()
        proposal = make_proposal()

        result = adapter.execute(proposal)

        self.assertTrue(result.success)
        self.assertEqual(result.action, proposal.action)
        self.assertEqual(result.proposal_id, proposal.proposal_id)
        self.assertEqual(adapter.executed_proposal_ids, (proposal.proposal_id,))

    def test_rejects_external_destination(self):
        adapter = LocalActionAdapter()

        with self.assertRaises(ValueError):
            adapter.execute(make_proposal(destination="https://example.com"))

    def test_rejects_unsupported_action(self):
        adapter = LocalActionAdapter()

        with self.assertRaises(ValueError):
            adapter.execute(make_proposal(action="delete_account"))


if __name__ == "__main__":
    unittest.main()

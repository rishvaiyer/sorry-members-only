import unittest

from members_only import (
    CapabilityManager,
    ExecutionGate,
    LocalActionAdapter,
    approve_proposal,
    evaluate_proposal,
    inspect_proposal,
)
from members_only.models import Capability, Proposal


def make_approved_proposal() -> tuple[Proposal, CapabilityManager, Capability]:
    proposal = Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "Hello from the local demo."},
    )
    policy_decision = evaluate_proposal(proposal, inspect_proposal(proposal))
    approval = approve_proposal(proposal, policy_decision, member_id="member-1")
    manager = CapabilityManager()
    capability = manager.issue(proposal, approval, ttl_seconds=60)
    return proposal, manager, capability


class ExecutionGateTests(unittest.TestCase):
    def test_rechecks_and_consumes_capability_before_local_execution(self):
        proposal, manager, capability = make_approved_proposal()
        adapter = LocalActionAdapter()
        gate = ExecutionGate(manager, adapter)

        result = gate.execute(proposal, capability)

        self.assertTrue(result.success)
        self.assertEqual(adapter.executed_proposal_ids, (proposal.proposal_id,))

    def test_replay_does_not_execute_the_adapter_again(self):
        proposal, manager, capability = make_approved_proposal()
        adapter = LocalActionAdapter()
        gate = ExecutionGate(manager, adapter)
        gate.execute(proposal, capability)

        with self.assertRaises(PermissionError):
            gate.execute(proposal, capability)

        self.assertEqual(adapter.executed_proposal_ids, (proposal.proposal_id,))


if __name__ == "__main__":
    unittest.main()

import unittest

from members_only import (
    LocalActionAdapter,
    LocalStore,
    MembersOnlyPipeline,
    TraceRecorder,
)
from members_only.models import Decision, ExecutionStatus, Proposal


class MembersOnlyPipelineTests(unittest.TestCase):
    def test_pipeline_records_trace_and_persists_successful_receipt(self):
        secret = "Please keep this private."
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": secret},
        )
        trace = TraceRecorder()
        adapter = LocalActionAdapter()

        with LocalStore() as store:
            pipeline = MembersOnlyPipeline(adapter=adapter, store=store, trace=trace)
            decision = pipeline.evaluate(proposal)
            capability = pipeline.approve(proposal, decision, member_id="member-1")
            receipt = pipeline.execute(proposal, decision, capability)

            self.assertEqual(decision.decision, Decision.REQUIRES_APPROVAL)
            self.assertEqual(receipt.status, ExecutionStatus.SUCCEEDED)
            self.assertEqual(store.get_receipt(receipt.receipt_id), receipt)

        event_names = [event.event for event in trace.events]
        self.assertEqual(
            event_names,
            [
                "proposal_received",
                "sensitivity_checked",
                "policy_decided",
                "approval_recorded",
                "capability_issued",
                "action_executed",
                "receipt_recorded",
            ],
        )
        self.assertEqual(adapter.executed_proposal_ids, (proposal.proposal_id,))
        self.assertNotIn(secret, trace.to_jsonl())

    def test_pipeline_turns_capability_replay_into_denied_receipt(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": "Please keep this private."},
        )
        trace = TraceRecorder()
        adapter = LocalActionAdapter()

        with LocalStore() as store:
            pipeline = MembersOnlyPipeline(adapter=adapter, store=store, trace=trace)
            decision = pipeline.evaluate(proposal)
            capability = pipeline.approve(proposal, decision, member_id="member-1")
            first_receipt = pipeline.execute(proposal, decision, capability)
            replay_receipt = pipeline.execute(proposal, decision, capability)

        self.assertEqual(first_receipt.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(replay_receipt.status, ExecutionStatus.DENIED)
        self.assertEqual(adapter.executed_proposal_ids, (proposal.proposal_id,))
        self.assertIn("execution_blocked", [event.event for event in trace.events])


if __name__ == "__main__":
    unittest.main()

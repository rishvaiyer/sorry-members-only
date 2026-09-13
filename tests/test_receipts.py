import unittest

from members_only import TraceRecorder, create_receipt
from members_only.models import Decision, ExecutionStatus, Proposal


class ReceiptAndTraceTests(unittest.TestCase):
    def test_trace_contains_safe_metadata_without_payload_text(self):
        secret = "private-message-content"
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="send_message",
            destination="local:test-inbox",
            payload={"body": secret},
        )
        recorder = TraceRecorder()

        recorder.record(
            "policy_decided",
            proposal.proposal_id,
            {"decision": "requires_approval", "finding_categories": ["private_message"]},
        )

        self.assertEqual(len(recorder.events), 1)
        self.assertEqual(recorder.events[0].event, "policy_decided")
        self.assertNotIn(secret, recorder.to_jsonl())

    def test_trace_rejects_payload_like_detail_keys(self):
        recorder = TraceRecorder()

        with self.assertRaises(ValueError):
            recorder.record("unsafe", "proposal-1", {"payload": "do not log this"})

    def test_receipt_contains_decision_status_and_safe_summary(self):
        proposal = Proposal(
            member_id="member-1",
            agent_id="agent-1",
            action="save_note",
            destination="local:test-inbox",
            payload={"body": "done"},
        )

        receipt = create_receipt(
            proposal,
            decision=Decision.ALLOW,
            status=ExecutionStatus.SUCCEEDED,
            summary="Local note saved.",
        )

        self.assertEqual(receipt.proposal_id, proposal.proposal_id)
        self.assertEqual(receipt.status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(receipt.summary, "Local note saved.")


if __name__ == "__main__":
    unittest.main()

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from members_only import LocalStore
from members_only.models import Approval, Capability, Decision, ExecutionStatus, Receipt


class LocalStoreTests(unittest.TestCase):
    def test_approval_survives_reopening_the_database(self):
        approval = Approval(
            proposal_id="proposal-1",
            member_id="member-1",
            proposal_digest="digest-1",
        )

        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "members-only.sqlite3"
            first_store = LocalStore(database_path)
            first_store.save_approval(approval)
            first_store.close()

            second_store = LocalStore(database_path)
            restored = second_store.get_approval(approval.approval_id)
            second_store.close()

        self.assertEqual(restored, approval)

    def test_capability_persists_and_can_be_redeemed_only_once(self):
        issued_at = datetime.now(timezone.utc)
        capability = Capability(
            proposal_id="proposal-1",
            member_id="member-1",
            action="send_message",
            proposal_digest="digest-1",
            issued_at=issued_at,
            expires_at=issued_at + timedelta(minutes=5),
        )

        with LocalStore() as store:
            store.save_capability(capability)

            self.assertEqual(store.get_capability(capability.capability_id), capability)
            self.assertTrue(
                store.mark_capability_redeemed(
                    capability.capability_id,
                    datetime.now(timezone.utc),
                )
            )
            self.assertFalse(
                store.mark_capability_redeemed(
                    capability.capability_id,
                    datetime.now(timezone.utc),
                )
            )

    def test_receipt_persists_the_outcome_without_a_payload(self):
        receipt = Receipt(
            proposal_id="proposal-1",
            decision=Decision.ALLOW,
            status=ExecutionStatus.SUCCEEDED,
            summary="Local test action completed.",
        )

        with LocalStore() as store:
            store.save_receipt(receipt)
            restored = store.get_receipt(receipt.receipt_id)

        self.assertEqual(restored, receipt)


if __name__ == "__main__":
    unittest.main()

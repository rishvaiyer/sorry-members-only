import unittest
from datetime import datetime, timedelta, timezone

from members_only import (
    CapabilityManager,
    LocalStore,
    approve_proposal,
    evaluate_proposal,
    inspect_proposal,
    proposal_digest,
)
from members_only.models import Capability, Proposal


def build_approved_proposal() -> tuple[Proposal, object]:
    proposal = Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "Please review this."},
    )
    policy_decision = evaluate_proposal(proposal, inspect_proposal(proposal))
    approval = approve_proposal(proposal, policy_decision, member_id="member-1")
    return proposal, approval


class CapabilityManagerTests(unittest.TestCase):
    def test_issues_a_capability_bound_to_the_approved_action(self):
        proposal, approval = build_approved_proposal()
        manager = CapabilityManager()

        capability = manager.issue(proposal, approval, ttl_seconds=60)

        self.assertEqual(capability.proposal_id, proposal.proposal_id)
        self.assertEqual(capability.member_id, proposal.member_id)
        self.assertEqual(capability.action, proposal.action)
        self.assertGreater(capability.expires_at, capability.issued_at)

    def test_valid_capability_can_be_redeemed_only_once(self):
        proposal, approval = build_approved_proposal()
        manager = CapabilityManager()
        capability = manager.issue(proposal, approval, ttl_seconds=60)

        manager.redeem(capability, proposal)

        with self.assertRaises(PermissionError):
            manager.redeem(capability, proposal)

    def test_capability_rejects_a_changed_proposal(self):
        proposal, approval = build_approved_proposal()
        manager = CapabilityManager()
        capability = manager.issue(proposal, approval, ttl_seconds=60)
        changed_proposal = Proposal(
            member_id=proposal.member_id,
            agent_id=proposal.agent_id,
            action=proposal.action,
            destination=proposal.destination,
            payload={"body": "Send this different message."},
            proposal_id=proposal.proposal_id,
            created_at=proposal.created_at,
        )

        with self.assertRaises(PermissionError):
            manager.redeem(capability, changed_proposal)

    def test_expired_capability_cannot_be_redeemed(self):
        proposal, _approval = build_approved_proposal()
        manager = CapabilityManager()
        expired = Capability(
            proposal_id=proposal.proposal_id,
            member_id=proposal.member_id,
            action=proposal.action,
            proposal_digest=proposal_digest(proposal),
            issued_at=datetime.now(timezone.utc) - timedelta(minutes=2),
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )

        with self.assertRaises(PermissionError):
            manager.redeem(expired, proposal)

    def test_sqlite_redemption_state_blocks_replay_after_manager_restart(self):
        proposal, approval = build_approved_proposal()

        with LocalStore() as store:
            first_manager = CapabilityManager(store=store)
            capability = first_manager.issue(proposal, approval, ttl_seconds=60)
            store.save_capability(capability)
            first_manager.redeem(capability, proposal)

            restarted_manager = CapabilityManager(store=store)
            with self.assertRaises(PermissionError):
                restarted_manager.redeem(capability, proposal)


if __name__ == "__main__":
    unittest.main()

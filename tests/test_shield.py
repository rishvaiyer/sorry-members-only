import unittest

from members_only import (
    ApprovedRule,
    LocalActionAdapter,
    LocalBroker,
    LocalStore,
    MachineAttestation,
    MembersOnlyPipeline,
    SandboxShield,
    ShieldChannel,
    ShieldRequest,
    StaticMachineVerifier,
    demo_attestation,
    sign_request,
)
from members_only.models import Proposal
from members_only.shield import BrokerReceipt


class CountingBroker(LocalBroker):
    def __init__(self) -> None:
        self.requests: list[ShieldRequest] = []

    def forward(self, request: ShieldRequest) -> BrokerReceipt:
        self.requests.append(request)
        return super().forward(request)


def make_proposal() -> Proposal:
    return Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "private test content"},
    )


def approve(proposal: Proposal):
    with LocalStore() as store:
        pipeline = MembersOnlyPipeline(store=store)
        decision = pipeline.evaluate(proposal)
        return pipeline.approve(proposal, decision, member_id=proposal.member_id)


class SandboxShieldTests(unittest.TestCase):
    def test_default_deny_requires_explicit_approval(self):
        proposal = make_proposal()
        verifier, attestation = demo_attestation(proposal)
        broker = CountingBroker()
        shield = SandboxShield(verifier=verifier, broker=broker)

        receipt = shield.authorize(proposal, None, attestation)

        self.assertFalse(receipt.allowed)
        self.assertEqual(receipt.reason, "explicit approval is required for this exact request")
        self.assertEqual(broker.requests, [])

    def test_member_capability_passes_machine_and_broker_checks(self):
        proposal = make_proposal()
        verifier, attestation = demo_attestation(proposal)
        broker = CountingBroker()
        shield = SandboxShield(verifier=verifier, broker=broker)

        receipt = shield.authorize(proposal, approve(proposal), attestation)

        self.assertTrue(receipt.allowed)
        self.assertTrue(receipt.machine_verified)
        self.assertEqual(receipt.approval_source, "member_capability")
        self.assertEqual(receipt.broker, "CountingBroker")
        self.assertEqual(
            [request.proposal_id for request in broker.requests],
            [proposal.proposal_id],
        )

    def test_exact_approved_rule_can_allow_a_request_without_member_prompt(self):
        proposal = make_proposal()
        verifier, attestation = demo_attestation(proposal)
        shield = SandboxShield(
            verifier=verifier,
            broker=LocalBroker(),
            rules=(
                ApprovedRule(
                    rule_id="local-message-demo",
                    channel=ShieldChannel.EGRESS,
                    action=proposal.action,
                    destination=proposal.destination,
                    workload_id=attestation.workload_id,
                ),
            ),
        )

        receipt = shield.authorize(proposal, None, attestation)

        self.assertTrue(receipt.allowed)
        self.assertEqual(receipt.approval_source, "approved_rule")

    def test_untrusted_workload_is_denied_before_broker(self):
        proposal = make_proposal()
        verifier, _attestation = demo_attestation(proposal)
        broker = CountingBroker()
        shield = SandboxShield(verifier=verifier, broker=broker)
        secret = "local-demo-only"
        request = ShieldRequest.from_proposal(proposal)
        attestation = MachineAttestation(
            workload_id="untrusted-workload",
            hardware_id="sandbox-hardware-demo",
            signature=sign_request(
                request,
                workload_id="untrusted-workload",
                hardware_id="sandbox-hardware-demo",
                signing_secret=secret,
            ),
        )

        receipt = shield.authorize(proposal, approve(proposal), attestation)

        self.assertFalse(receipt.allowed)
        self.assertFalse(receipt.machine_verified)
        self.assertIn("untrusted_workload", receipt.reason)
        self.assertEqual(broker.requests, [])

    def test_pipeline_records_shield_block_and_does_not_run_adapter(self):
        proposal = make_proposal()
        verifier, _attestation = demo_attestation(proposal)
        adapter = LocalActionAdapter()
        trace = []
        with LocalStore() as store:
            pipeline = MembersOnlyPipeline(
                adapter=adapter,
                store=store,
                trace=None,
                shield=SandboxShield(verifier=verifier, broker=LocalBroker()),
                attestation=MachineAttestation(
                    workload_id="untrusted-workload",
                    hardware_id="sandbox-hardware-demo",
                    signature="invalid",
                ),
            )
            decision = pipeline.evaluate(proposal)
            capability = pipeline.approve(proposal, decision, member_id=proposal.member_id)
            receipt = pipeline.execute(proposal, decision, capability)
            trace = [event.event for event in pipeline.trace.events]

        self.assertEqual(receipt.status.value, "denied")
        self.assertIn("sandbox_blocked", trace)
        self.assertEqual(adapter.executed_proposal_ids, ())


if __name__ == "__main__":
    unittest.main()

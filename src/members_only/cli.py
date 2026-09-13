"""Command-line demonstrations for Members Only."""

from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import sys
from typing import Sequence, TextIO

from .adapters import LocalActionAdapter, SandboxCommandAdapter
from .models import Capability, PolicyDecision, Proposal
from .pipeline import MembersOnlyPipeline
from .receipts import TraceEvent, TraceRecorder
from .runtime import DockerSandbox
from .shield import (
    DenyAllBroker,
    LocalBroker,
    MachineAttestation,
    RequestBroker,
    SandboxShield,
    demo_attestation,
)
from .storage import LocalStore


def _print_trace_event(event: TraceEvent, output: TextIO) -> None:
    """Print a human-readable event using only safe trace metadata."""

    details = event.details
    messages = {
        "proposal_received": "Entering proposal intake check.",
        "policy_decided": (
            f"Policy check complete: decision={details.get('decision', 'unknown')}."
        ),
        "approval_recorded": "Member approval recorded for this exact proposal.",
        "capability_issued": "One-use capability issued for the approved action.",
        "sandbox_authorized": (
            "Sandbox shield passed: machine verification passed; "
            f"approval={details.get('approval_source', 'unknown')}; "
            f"broker={details.get('broker', 'unknown')}."
        ),
        "sandbox_blocked": (
            "Sandbox shield blocked the request: "
            f"{details.get('reason', 'request was denied')}."
        ),
        "sandbox_runtime_blocked": (
            "Hard sandbox runtime blocked the worker: "
            f"{details.get('reason', 'runtime denied the command')}."
        ),
        "action_executed": (
            "Entering local action execution: "
            f"adapter={details.get('adapter', 'unknown')}; "
            f"success={details.get('success', False)}."
        ),
        "execution_blocked": (
            "Replay or capability check blocked execution: "
            f"{details.get('reason', 'capability check failed')}."
        ),
        "execution_failed": "Action adapter rejected the request.",
        "receipt_recorded": (
            "Safe receipt recorded: "
            f"status={details.get('status', 'unknown')}."
        ),
    }

    if event.event == "sensitivity_checked":
        finding_count = details.get("finding_count", 0)
        categories = details.get("finding_categories", [])
        if finding_count:
            message = (
                "Sensitivity check completed: "
                f"{finding_count} protected finding(s) detected "
                f"({', '.join(categories)})."
            )
        else:
            message = "Sensitivity check passed: no protected findings detected."
    else:
        message = messages.get(event.event, "Trace event recorded.")

    print(f"[trace] {event.event} - {message}", file=output)


def _demo_proposal() -> Proposal:
    """Build the synthetic proposal used by the terminal demonstrations."""

    return Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "member-private-content"},
    )


def run_demo(output: TextIO) -> int:
    """Run a synthetic approval, execution, and replay-blocking demo."""

    proposal = _demo_proposal()
    print("Members Only synthetic local demo", file=output)
    print("Safe live progress (private payloads omitted):", file=output)
    print(file=output)

    trace = TraceRecorder(listener=lambda event: _print_trace_event(event, output))
    adapter = LocalActionAdapter()
    verifier, attestation = demo_attestation(proposal)
    shield = SandboxShield(verifier=verifier, broker=LocalBroker())

    with LocalStore() as store:
        pipeline = MembersOnlyPipeline(
            adapter=adapter,
            store=store,
            trace=trace,
            shield=shield,
            attestation=attestation,
        )
        decision = pipeline.evaluate(proposal)
        print("[demo] Entering member approval path.", file=output)
        capability = pipeline.approve(proposal, decision, member_id="member-1")
        print("[demo] Entering first execution path.", file=output)
        first_receipt = pipeline.execute(proposal, decision, capability)
        print("[demo] Entering replay test with the same one-use capability.", file=output)
        replay_receipt = pipeline.execute(proposal, decision, capability)

        print(file=output)
        print("Safe trace JSONL:", file=output)
        for event in trace.events:
            print(json.dumps(event.to_dict(), sort_keys=True), file=output)
        print(file=output)
        print(f"first_execution={first_receipt.status.value}", file=output)
        print(f"replay_attempt={replay_receipt.status.value}", file=output)

    return 0


def _prepare_attack_case(
    output: TextIO,
    *,
    proposal: Proposal | None = None,
    broker: RequestBroker | None = None,
    attestation: MachineAttestation | None = None,
) -> tuple[
    LocalStore,
    Proposal,
    MembersOnlyPipeline,
    PolicyDecision,
    Capability,
]:
    """Create one isolated, approved case for the attack demonstrations."""

    proposal = proposal or _demo_proposal()
    trace = TraceRecorder(listener=lambda event: _print_trace_event(event, output))
    verifier, valid_attestation = demo_attestation(proposal)
    case_attestation = attestation or valid_attestation
    store = LocalStore()
    pipeline = MembersOnlyPipeline(
        adapter=LocalActionAdapter(),
        store=store,
        trace=trace,
        shield=SandboxShield(verifier=verifier, broker=broker or LocalBroker()),
        attestation=case_attestation,
    )
    decision = pipeline.evaluate(proposal)
    capability = pipeline.approve(proposal, decision, member_id=proposal.member_id)
    return (
        store,
        proposal,
        pipeline,
        decision,
        capability,
    )


def _print_attack_result(output: TextIO, label: str, blocked: bool) -> bool:
    result = "BLOCKED as expected" if blocked else "UNEXPECTEDLY ALLOWED"
    print(f"[result] {label}: {result}", file=output)
    return blocked


def run_attack_demo(output: TextIO) -> int:
    """Run visible fail-closed demonstrations against the security controls."""

    print("Members Only security attack demo", file=output)
    print("Every scenario should fail closed; private payloads are omitted.", file=output)
    print(file=output)
    blocked_count = 0
    scenario_count = 5

    print("[attack 1/5] Tampered proposal", file=output)
    store, proposal, pipeline, decision, capability = _prepare_attack_case(output)
    try:
        changed_proposal = replace(
            proposal,
            payload={"body": "tampered-after-approval"},
        )
        print("[attack] Attempting execution after changing the approved content.", file=output)
        receipt = pipeline.execute(changed_proposal, decision, capability)
        blocked_count += int(
            _print_attack_result(
                output,
                "tampered proposal",
                receipt.status.value == "denied",
            )
        )
    finally:
        store.close()
    print(file=output)

    print("[attack 2/5] Invalid machine attestation", file=output)
    proposal = _demo_proposal()
    _, valid_attestation = demo_attestation(proposal)
    invalid_attestation = replace(valid_attestation, signature="invalid-signature")
    store, proposal, pipeline, decision, capability = _prepare_attack_case(
        output,
        proposal=proposal,
        attestation=invalid_attestation,
    )
    try:
        print("[attack] Attempting execution with an invalid machine signature.", file=output)
        receipt = pipeline.execute(proposal, decision, capability)
        blocked_count += int(
            _print_attack_result(
                output,
                "invalid attestation",
                receipt.status.value == "denied",
            )
        )
    finally:
        store.close()
    print(file=output)

    print("[attack 3/5] Broker denial", file=output)
    store, proposal, pipeline, decision, capability = _prepare_attack_case(
        output,
        broker=DenyAllBroker(),
    )
    try:
        print("[attack] Attempting execution through a deny-all broker.", file=output)
        receipt = pipeline.execute(proposal, decision, capability)
        blocked_count += int(
            _print_attack_result(
                output,
                "broker denial",
                receipt.status.value == "denied",
            )
        )
    finally:
        store.close()
    print(file=output)

    print("[attack 4/5] Expired capability", file=output)
    store, proposal, pipeline, decision, capability = _prepare_attack_case(output)
    try:
        expired_capability = replace(
            capability,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        print("[attack] Attempting execution with an expired capability.", file=output)
        receipt = pipeline.execute(proposal, decision, expired_capability)
        blocked_count += int(
            _print_attack_result(
                output,
                "expired capability",
                receipt.status.value == "denied",
            )
        )
    finally:
        store.close()
    print(file=output)

    print("[attack 5/5] One-use capability replay", file=output)
    store, proposal, pipeline, decision, capability = _prepare_attack_case(output)
    try:
        print("[attack] Executing once, then attempting the same capability again.", file=output)
        first_receipt = pipeline.execute(proposal, decision, capability)
        replay_receipt = pipeline.execute(proposal, decision, capability)
        blocked_count += int(
            _print_attack_result(
                output,
                "capability replay",
                first_receipt.status.value == "succeeded"
                and replay_receipt.status.value == "denied",
            )
        )
    finally:
        store.close()

    print(file=output)
    print(
        f"Attack demo summary: {blocked_count}/{scenario_count} scenarios blocked or contained.",
        file=output,
    )
    return 0 if blocked_count == scenario_count else 1


def run_sandbox_demo(output: TextIO) -> int:
    """Run an action through the optional Docker enforcement layer."""

    proposal = _demo_proposal()
    print("Members Only hard sandbox demo", file=output)
    print(
        "Configured: no network, read-only root, no host mounts, dropped capabilities, "
        "no-new-privileges, pull disabled.",
        file=output,
    )
    print("The image must already exist locally; a missing runtime fails closed.", file=output)
    print(file=output)

    trace = TraceRecorder(listener=lambda event: _print_trace_event(event, output))
    verifier, attestation = demo_attestation(proposal)
    adapter = SandboxCommandAdapter(
        runtime=DockerSandbox(image="python:3.12-alpine"),
        command=("python", "-c", "print('sandbox worker completed')"),
    )
    shield = SandboxShield(verifier=verifier, broker=LocalBroker())

    with LocalStore() as store:
        pipeline = MembersOnlyPipeline(
            adapter=adapter,
            store=store,
            trace=trace,
            shield=shield,
            attestation=attestation,
        )
        decision = pipeline.evaluate(proposal)
        capability = pipeline.approve(proposal, decision, member_id=proposal.member_id)
        receipt = pipeline.execute(proposal, decision, capability)

    print(file=output)
    print(f"sandbox_execution={receipt.status.value}", file=output)
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="members-only")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("demo", "attack-demo", "sandbox-demo"),
        default="demo",
    )
    args = parser.parse_args(argv)

    if args.command == "demo":
        return run_demo(sys.stdout)
    if args.command == "attack-demo":
        return run_attack_demo(sys.stdout)
    if args.command == "sandbox-demo":
        return run_sandbox_demo(sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

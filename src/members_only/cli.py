"""Command-line demonstrations for Members Only."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from .adapters import LocalActionAdapter
from .models import Proposal
from .pipeline import MembersOnlyPipeline
from .receipts import TraceEvent, TraceRecorder
from .shield import LocalBroker, SandboxShield, demo_attestation
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


def run_demo(output: TextIO) -> int:
    """Run a synthetic approval, execution, and replay-blocking demo."""

    proposal = Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "member-private-content"},
    )
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="members-only")
    parser.add_argument("command", nargs="?", choices=("demo",), default="demo")
    args = parser.parse_args(argv)

    if args.command == "demo":
        return run_demo(sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

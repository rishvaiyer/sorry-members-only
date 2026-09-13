"""Command-line demonstrations for Members Only."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Sequence, TextIO

from .adapters import LocalActionAdapter
from .models import Proposal
from .pipeline import MembersOnlyPipeline
from .receipts import TraceRecorder
from .storage import LocalStore


def run_demo(output: TextIO) -> int:
    """Run a synthetic approval, execution, and replay-blocking demo."""

    proposal = Proposal(
        member_id="member-1",
        agent_id="agent-1",
        action="send_message",
        destination="local:test-inbox",
        payload={"body": "member-private-content"},
    )
    trace = TraceRecorder()
    adapter = LocalActionAdapter()

    with LocalStore() as store:
        pipeline = MembersOnlyPipeline(adapter=adapter, store=store, trace=trace)
        decision = pipeline.evaluate(proposal)
        capability = pipeline.approve(proposal, decision, member_id="member-1")
        first_receipt = pipeline.execute(proposal, decision, capability)
        replay_receipt = pipeline.execute(proposal, decision, capability)

        print("Members Only synthetic local demo", file=output)
        print("Trace events:", file=output)
        for event in trace.events:
            print(json.dumps(event.to_dict(), sort_keys=True), file=output)
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

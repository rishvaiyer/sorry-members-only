# Members Only

Members Only is a small Python safety layer for individuals using AI agents.

The member is the person who owns the agent. The agent proposes an action, and Members Only:

1. Checks the proposal for sensitive content.
2. Allows safe local actions, denies credential exposure, and pauses risky actions for member approval.
3. Issues a short-lived, one-use capability.
4. Runs a synthetic local action or an approved read-only browser fetch.
5. Records a safe trace and receipt without printing the private payload.

## Documentation

[Open the architecture documentation](https://rishvaiyer.github.io/sorry-members-only/)

The documentation describes the current Python MVP, including the optional
Obscura browser adapter and its security boundary.

## Run the demo

From the repository root:

```bash
PYTHONPATH=src python3 -m members_only.cli demo
```

The demo shows approval, capability issuance, local execution, receipt creation, and replay blocking. It makes no network requests.

## Run the tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Current scope

This is a local Python MVP. The optional `ObscuraActionAdapter` adds one read-only
`browser_fetch` action through the Obscura CLI. It remains behind the normal
policy, approval, capability, and receipt pipeline; tests inject the command
runner and make no network requests. Browser MCP, browser writes, and automatic
external messages are not included.

Set `MEMBERS_ONLY_OBSCURA_BIN` when the `obscura` executable is not on `PATH`.

Example adapter setup:

```python
from members_only import MembersOnlyPipeline, Proposal
from members_only.adapters import ObscuraActionAdapter

pipeline = MembersOnlyPipeline(adapter=ObscuraActionAdapter())
proposal = Proposal(
    member_id="member-1",
    agent_id="agent-1",
    action="browser_fetch",
    destination="external:web",
    payload={"url": "https://example.com"},
)
decision = pipeline.evaluate(proposal)  # requires approval
```

The adapter currently supports fetching rendered text only. It does not submit
forms, send messages, make purchases, upload files, or expose page contents in
the receipt.

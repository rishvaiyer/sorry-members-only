# Members Only

Members Only is a small Python safety layer for individuals using AI agents.

The member is the person who owns the agent. The agent proposes an action, and Members Only:

1. Checks the proposal for sensitive content.
2. Allows safe local actions, denies credential exposure, and pauses risky actions for member approval.
3. Issues a short-lived, one-use capability.
4. Runs a synthetic local action.
5. Records a safe trace and receipt without printing the private payload.

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

This is a local Python MVP. Web MCP, real external integrations, and automatic external messages are not included.

# Members Only

Members Only is a Python reference implementation for approving risky AI-agent
actions before execution. It scans a proposed action, applies policy, issues a
short-lived one-use capability, and records a redacted receipt.

```text
proposal -> scan -> policy decision -> approval gate -> adapter -> receipt
```

Safe local actions can pass, credential exposure is denied, and risky actions
pause for approval.

## Run it

```bash
PYTHONPATH=src python3 -m members_only.cli demo
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

The adapter is simulated, and the demo makes no network requests. External
integrations and automatic external actions are not included.

[Read the architecture documentation](https://rishvaiyer.github.io/sorry-members-only/)

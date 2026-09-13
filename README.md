# Members Only

Members Only is a small Python safety layer for individuals using AI agents.

The member is the person who owns the agent. The agent proposes an action, and Members Only:

1. Checks the proposal for sensitive content.
2. Allows safe local actions, denies credential exposure, and pauses risky actions for member approval.
3. Issues a short-lived, one-use capability.
4. Runs a synthetic local action.
5. Records a safe trace and receipt without printing the private payload.

## Documentation

[Open the architecture documentation](https://rishvaiyer.github.io/sorry-members-only/)

## Run the demo

From the repository root:

```bash
PYTHONPATH=src python3 -m members_only.cli demo
```

The demo shows approval, capability issuance, sandbox verification, brokered local execution, receipt creation, and replay blocking. It makes no network requests.

## Run the tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Current scope

This is a local Python MVP. The sandbox security shield is a default-deny software control plane: requests need machine verification and either an exact member capability or an exact pre-approved rule before they reach a broker. The current demo has a local broker only.

The shield has replaceable seams for workload and hardware attestation plus separate brokers for ingress, egress, updates, telemetry, models, and logs. Real OS-level isolation, TPM or enclave attestation, network enforcement, and external brokers are not included yet.

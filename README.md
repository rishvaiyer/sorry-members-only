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

To run the fail-closed attack demonstrations:

```bash
PYTHONPATH=src python3 -m members_only.cli attack-demo
```

That demo shows tampered content, invalid machine attestation, broker denial, expired capability, and capability replay being blocked.

To exercise the optional hard runtime:

```bash
PYTHONPATH=src python3 -m members_only.cli sandbox-demo
```

This routes the worker through Docker with no network, a read-only root, no host mounts, dropped Linux capabilities, no-new-privileges, resource limits, and image pulling disabled. The image must already be available locally. If Docker or the image is unavailable, the action is denied rather than run outside the sandbox.

## Run the tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Current scope

This is a local Python MVP. The sandbox security shield is a default-deny software control plane: requests need machine verification and either an exact member capability or an exact pre-approved rule before they reach a broker. The current demo has a local broker only.

The shield has replaceable seams for workload and hardware attestation plus separate brokers for ingress, egress, updates, telemetry, models, and logs. The Docker runtime is an optional local enforcement adapter; TPM or enclave attestation, a production broker, and host-level enforcement outside Docker are not included yet.

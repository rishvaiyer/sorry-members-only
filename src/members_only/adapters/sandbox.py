"""Action adapter for commands executed inside a hard sandbox runtime."""

from __future__ import annotations

from collections.abc import Sequence

from .base import ActionResult
from ..models import Proposal
from ..runtime import SandboxRuntime, SandboxRuntimeDenied


class SandboxCommandAdapter:
    """Run a fixed worker command only inside the configured runtime.

    Proposal payload transport is intentionally not implicit. A future worker
    protocol must define how approved data enters the container without
    bypassing the Members Only trace and approval rules.
    """

    def __init__(
        self,
        *,
        runtime: SandboxRuntime,
        command: Sequence[str],
        timeout_seconds: float = 10.0,
    ) -> None:
        if not command or any(
            not isinstance(part, str) or not part for part in command
        ):
            raise ValueError("command must contain non-empty strings")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than zero")
        self._runtime = runtime
        self._command = tuple(command)
        self._timeout_seconds = timeout_seconds

    def execute(self, proposal: Proposal) -> ActionResult:
        """Execute the configured worker without passing the raw payload."""

        result = self._runtime.run(
            self._command,
            timeout_seconds=self._timeout_seconds,
        )
        if not result.completed:
            raise SandboxRuntimeDenied(result)
        return ActionResult(
            success=True,
            proposal_id=proposal.proposal_id,
            action=proposal.action,
            summary="The worker completed inside the isolated sandbox.",
        )

"""Obscura browser adapter behind the Members Only execution gate."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Sequence

from ..models import Proposal
from .base import ActionResult


Runner = Callable[[Sequence[str]], subprocess.CompletedProcess[str]]


class ObscuraActionAdapter:
    """Run one approved, read-only Obscura browser action.

    This adapter deliberately supports fetching page content only. Navigation,
    screenshots, and form submission can be added as separate action types with
    separate policy rules rather than silently broadening this capability.
    """

    def __init__(self, *, executable: str | None = None, runner: Runner | None = None) -> None:
        self.executable = executable or os.environ.get("MEMBERS_ONLY_OBSCURA_BIN", "obscura")
        self._runner = runner or self._run

    @staticmethod
    def _run(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.run(command, capture_output=True, text=True, check=False)

    def execute(self, proposal: Proposal) -> ActionResult:
        if proposal.action != "browser_fetch":
            raise ValueError(f"unsupported Obscura action: {proposal.action}")
        url = proposal.payload.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError("browser_fetch requires an http(s) payload url")

        completed = self._runner(
            (self.executable, "fetch", url, "--dump", "text", "--quiet")
        )
        if completed.returncode != 0:
            detail = (completed.stderr or "Obscura returned a non-zero exit code").strip()
            return ActionResult(False, proposal.proposal_id, proposal.action, detail)

        # Keep the page body out of the receipt and trace. The caller may use
        # the adapter directly when it needs the content; the pipeline only
        # receives this bounded summary.
        return ActionResult(
            True,
            proposal.proposal_id,
            proposal.action,
            json.dumps({"browser": "obscura", "url": url, "bytes": len(completed.stdout)}),
        )

"""Interfaces for actions Members Only may execute."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..models import Proposal


@dataclass(frozen=True, slots=True)
class ActionResult:
    """Safe summary returned by an action adapter."""

    success: bool
    proposal_id: str
    action: str
    summary: str


class ActionAdapter(Protocol):
    """The execution seam for a concrete action destination."""

    def execute(self, proposal: Proposal) -> ActionResult:
        """Execute a proposal that has already passed the security gate."""
        ...

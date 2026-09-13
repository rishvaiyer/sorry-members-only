"""Action adapter interfaces and safe local implementations."""

from .base import ActionAdapter, ActionResult
from .local import LocalActionAdapter
from .sandbox import SandboxCommandAdapter

__all__ = [
    "ActionAdapter",
    "ActionResult",
    "LocalActionAdapter",
    "SandboxCommandAdapter",
]

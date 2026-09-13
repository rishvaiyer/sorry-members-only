"""Action adapter interfaces and safe local implementations."""

from .base import ActionAdapter, ActionResult
from .local import LocalActionAdapter

__all__ = ["ActionAdapter", "ActionResult", "LocalActionAdapter"]

"""Human-gated security controls for individual AI agents."""

from .models import (
    Approval,
    Capability,
    Decision,
    ExecutionStatus,
    PolicyDecision,
    Proposal,
    Receipt,
    SensitivityFinding,
    SensitivityLevel,
)
from .policy import evaluate_proposal
from .sensitivity import inspect_proposal

__version__ = "0.1.0"

__all__ = [
    "Approval",
    "Capability",
    "Decision",
    "ExecutionStatus",
    "evaluate_proposal",
    "inspect_proposal",
    "PolicyDecision",
    "Proposal",
    "Receipt",
    "SensitivityFinding",
    "SensitivityLevel",
    "__version__",
]

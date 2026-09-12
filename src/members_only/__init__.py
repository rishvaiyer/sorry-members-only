"""Human-gated security controls for individual AI agents."""

from .approvals import approve_proposal, proposal_digest
from .adapters import ActionAdapter, ActionResult, LocalActionAdapter
from .capabilities import CapabilityManager
from .execution import ExecutionGate
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
from .storage import LocalStore

__version__ = "0.1.0"

__all__ = [
    "Approval",
    "ActionAdapter",
    "ActionResult",
    "approve_proposal",
    "Capability",
    "CapabilityManager",
    "Decision",
    "ExecutionStatus",
    "ExecutionGate",
    "evaluate_proposal",
    "inspect_proposal",
    "PolicyDecision",
    "Proposal",
    "LocalStore",
    "LocalActionAdapter",
    "proposal_digest",
    "Receipt",
    "SensitivityFinding",
    "SensitivityLevel",
    "__version__",
]

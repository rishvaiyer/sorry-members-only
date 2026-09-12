"""Human-gated security controls for individual AI agents."""

from .approvals import approve_proposal, proposal_digest
from .capabilities import CapabilityManager
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
    "approve_proposal",
    "Capability",
    "CapabilityManager",
    "Decision",
    "ExecutionStatus",
    "evaluate_proposal",
    "inspect_proposal",
    "PolicyDecision",
    "Proposal",
    "proposal_digest",
    "Receipt",
    "SensitivityFinding",
    "SensitivityLevel",
    "__version__",
]

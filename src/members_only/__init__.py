"""Human-gated security controls for individual AI agents."""

from .approvals import approve_proposal, proposal_digest
from .adapters import ActionAdapter, ActionResult, LocalActionAdapter, ObscuraActionAdapter
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
from .pipeline import MembersOnlyPipeline
from .receipts import TraceEvent, TraceRecorder, create_receipt
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
    "TraceEvent",
    "TraceRecorder",
    "create_receipt",
    "evaluate_proposal",
    "inspect_proposal",
    "PolicyDecision",
    "Proposal",
    "LocalStore",
    "LocalActionAdapter",
    "ObscuraActionAdapter",
    "MembersOnlyPipeline",
    "proposal_digest",
    "Receipt",
    "SensitivityFinding",
    "SensitivityLevel",
    "__version__",
]

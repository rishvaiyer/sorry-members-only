"""Human-gated security controls for individual AI agents."""

from .approvals import approve_proposal, proposal_digest
from .adapters import ActionAdapter, ActionResult, LocalActionAdapter, SandboxCommandAdapter
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
from .runtime import (
    DockerSandbox,
    SandboxResult,
    SandboxRuntime,
    SandboxRuntimeDenied,
)
from .sensitivity import inspect_proposal
from .shield import (
    ApprovedRule,
    BrokerReceipt,
    DenyAllBroker,
    LocalBroker,
    MachineAttestation,
    MachineVerification,
    SandboxShield,
    ShieldChannel,
    ShieldDenied,
    ShieldReceipt,
    ShieldRequest,
    StaticMachineVerifier,
    demo_attestation,
    sign_request,
)
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
    "SandboxCommandAdapter",
    "MembersOnlyPipeline",
    "proposal_digest",
    "Receipt",
    "SensitivityFinding",
    "SensitivityLevel",
    "ApprovedRule",
    "BrokerReceipt",
    "DenyAllBroker",
    "LocalBroker",
    "MachineAttestation",
    "MachineVerification",
    "SandboxShield",
    "ShieldChannel",
    "ShieldDenied",
    "ShieldReceipt",
    "ShieldRequest",
    "StaticMachineVerifier",
    "demo_attestation",
    "sign_request",
    "DockerSandbox",
    "SandboxResult",
    "SandboxRuntime",
    "SandboxRuntimeDenied",
    "__version__",
]

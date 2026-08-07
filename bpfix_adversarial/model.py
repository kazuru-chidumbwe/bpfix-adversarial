"""ProofSignal / ProofEvent model aligned with bpfix's evidence tiers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class ProofObligation(str, Enum):
    """Subset under adversarial scope + full bpfix enum for fidelity."""

    PACKET_BOUNDS = "PacketBounds"
    POINTER_PROVENANCE = "PointerProvenance"
    SCALAR_RANGE = "ScalarRange"
    NULLABLE_POINTER = "NullablePointer"
    # Additional bpfix families (extend, do not fork)
    STACK_INITIALIZED = "StackInitialized"
    REFERENCE_LIFECYCLE = "ReferenceLifecycle"
    ALIGNMENT = "Alignment"
    TYPE_CONTRACT = "TypeContract"
    HELPER_ARGUMENT = "HelperArgument"
    CONTEXT_ACCESS = "ContextAccess"
    VERIFIER_LIMIT = "VerifierLimit"
    ENVIRONMENT_CAPABILITY = "EnvironmentCapability"
    DYNPTR_SAFETY = "DynptrSafety"
    KFUNC_REFERENCE = "KfuncReference"
    ITERATOR_LIFECYCLE = "IteratorLifecycle"
    LOCK_STATE = "LockState"
    INSTRUCTION_SUPPORT = "InstructionSupport"
    LOOP_BOUND = "LoopBound"
    UNKNOWN = "Unknown"


# Adversarial v0 scope (sponsor lock)
ADVERSARIAL_SCOPE = (
    ProofObligation.POINTER_PROVENANCE,
    ProofObligation.SCALAR_RANGE,
    ProofObligation.NULLABLE_POINTER,
    ProofObligation.PACKET_BOUNDS,
)


class ProofEventEvidence(str, Enum):
    """Evidence tier — load-bearing shared design with adjacent eBPF work."""

    SOURCE_COMMENT = "SourceComment"
    VERIFIER_STATE = "VerifierState"


class ProofEventRole(str, Enum):
    PROOF_ESTABLISHED = "ProofEstablished"
    PROOF_LOST = "ProofLost"


@dataclass(frozen=True)
class SourceLocation:
    path: str
    line: int
    text: str


@dataclass(frozen=True)
class ProofEvent:
    role: ProofEventRole
    evidence: ProofEventEvidence
    obligation: ProofObligation
    detail: str
    pc: Optional[int] = None
    source: Optional[SourceLocation] = None
    register: Optional[int] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["role"] = self.role.value
        d["evidence"] = self.evidence.value
        d["obligation"] = self.obligation.value
        return d


@dataclass
class HeuristicHit:
    name: str
    matched: bool
    text: str
    notes: str = ""
    matched_patterns: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

# SPDX-License-Identifier: MIT
"""Upstream bpfix-bench indexing and subset selection utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import ProofObligation


# Error ID -> ProofObligation as declared by upstream crates/bpfix/src/classifier.rs
# at the pin (vendored in fixtures/upstream/bpfix-source-rs-pin/). E018 is omitted
# because upstream declares it for two obligations (LoopBound, VerifierLimit).
UPSTREAM_ERROR_OBLIGATION: dict[str, str] = {
    "E001": "PacketBounds",
    "E002": "NullablePointer",
    "E003": "StackInitialized",
    "E004": "ReferenceLifecycle",
    "E005": "ScalarRange",
    "E006": "PointerProvenance",
    "E007": "Alignment",
    "E008": "TypeContract",
    "E009": "EnvironmentCapability",
    "E010": "HelperArgument",
    "E011": "ContextAccess",
    "E012": "DynptrSafety",
    "E013": "KfuncReference",
    "E014": "IteratorLifecycle",
    "E015": "LockState",
    "E016": "InstructionSupport",
}


@dataclass(frozen=True)
class UpstreamCase:
    case_id: str
    obligation_guess: ProofObligation


def obligation_from_case_id(case_id: str) -> ProofObligation:
    """Case-name keyword label; PointerProvenance is the fallback bucket.

    Used only to stratify the depth-21 selection. It is not upstream's
    classification (see UPSTREAM_ERROR_OBLIGATION).
    """
    c = case_id.lower()
    if "null" in c or "ringbuf" in c:
        return ProofObligation.NULLABLE_POINTER
    if "packet" in c or "xdp" in c:
        return ProofObligation.PACKET_BOUNDS
    if "scalar" in c or "index" in c or "range" in c or "alu32" in c:
        return ProofObligation.SCALAR_RANGE
    return ProofObligation.POINTER_PROVENANCE


def classify_cases(case_ids: Iterable[str]) -> list[UpstreamCase]:
    return [
        UpstreamCase(case_id=c, obligation_guess=obligation_from_case_id(c))
        for c in sorted(case_ids)
    ]


def balanced_subset(cases: list[UpstreamCase], per_obligation: int = 6) -> list[UpstreamCase]:
    buckets: dict[ProofObligation, list[UpstreamCase]] = {
        ProofObligation.POINTER_PROVENANCE: [],
        ProofObligation.SCALAR_RANGE: [],
        ProofObligation.NULLABLE_POINTER: [],
        ProofObligation.PACKET_BOUNDS: [],
    }
    for c in cases:
        if c.obligation_guess in buckets:
            buckets[c.obligation_guess].append(c)

    out: list[UpstreamCase] = []
    for ob in (
        ProofObligation.POINTER_PROVENANCE,
        ProofObligation.SCALAR_RANGE,
        ProofObligation.NULLABLE_POINTER,
        ProofObligation.PACKET_BOUNDS,
    ):
        out.extend(buckets[ob][:per_obligation])
    return out

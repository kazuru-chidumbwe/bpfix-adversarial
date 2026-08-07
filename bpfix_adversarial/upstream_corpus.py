"""Upstream bpfix-bench indexing and subset selection utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .model import ProofObligation


@dataclass(frozen=True)
class UpstreamCase:
    case_id: str
    obligation_guess: ProofObligation


def obligation_from_case_id(case_id: str) -> ProofObligation:
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

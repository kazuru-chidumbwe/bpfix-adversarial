# SPDX-License-Identifier: MIT
"""Analyze source lines / files with bpfix SourceComment heuristics."""

from __future__ import annotations

from pathlib import Path

from .heuristics import classify_line
from .model import ProofEvent, ProofEventEvidence, ProofEventRole, ProofObligation, SourceLocation


def analyze_text_line(text: str, path: str = "<stdin>", line: int = 1) -> dict:
    hits = {k: v.to_dict() for k, v in classify_line(text).items()}
    events: list[ProofEvent] = []
    if hits["looks_like_null_check"]["matched"]:
        events.append(
            ProofEvent(
                role=ProofEventRole.PROOF_ESTABLISHED,
                evidence=ProofEventEvidence.SOURCE_COMMENT,
                obligation=ProofObligation.NULLABLE_POINTER,
                detail="non-null proof is established in this branch (bpfix SourceComment)",
                source=SourceLocation(path=path, line=line, text=text),
            )
        )
    if hits["looks_like_nullable_return"]["matched"]:
        events.append(
            ProofEvent(
                role=ProofEventRole.PROOF_LOST,
                evidence=ProofEventEvidence.SOURCE_COMMENT,
                obligation=ProofObligation.NULLABLE_POINTER,
                detail="nullable pointer returned here (helper-anchored)",
                source=SourceLocation(path=path, line=line, text=text),
            )
        )
    if hits["looks_like_packet_bounds_check"]["matched"]:
        events.append(
            ProofEvent(
                role=ProofEventRole.PROOF_ESTABLISHED,
                evidence=ProofEventEvidence.SOURCE_COMMENT,
                obligation=ProofObligation.PACKET_BOUNDS,
                detail="packet bounds proof via data_end check",
                source=SourceLocation(path=path, line=line, text=text),
            )
        )
    if hits["looks_like_scalar_guard"]["matched"]:
        events.append(
            ProofEvent(
                role=ProofEventRole.PROOF_ESTABLISHED,
                evidence=ProofEventEvidence.SOURCE_COMMENT,
                obligation=ProofObligation.SCALAR_RANGE,
                detail="scalar range guard visible",
                source=SourceLocation(path=path, line=line, text=text),
            )
        )
    return {
        "path": path,
        "line": line,
        "text": text,
        "heuristics": hits,
        "proof_events": [e.to_dict() for e in events],
    }


def analyze_file(path: Path) -> list[dict]:
    out: list[dict] = []
    for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = raw.strip()
        if not text:
            continue
        # Skip pure comments / preprocessor unless they look like checks
        if text.startswith("#") and "if" not in text:
            continue
        out.append(analyze_text_line(text, path=str(path), line=i))
    return out

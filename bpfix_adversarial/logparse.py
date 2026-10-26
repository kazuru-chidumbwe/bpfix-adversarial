# SPDX-License-Identifier: MIT
"""Parse minimal verifier-log source comments and score SourceComment honesty."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .heuristics import (
    looks_like_null_check,
    looks_like_nullable_return,
    looks_like_packet_bounds_check,
    looks_like_scalar_guard,
)
from .model import ProofEvent, ProofEventEvidence, ProofEventRole, ProofObligation, SourceLocation

# bpfix-style: `  ; source text @ path:line`
SOURCE_COMMENT_RE = re.compile(
    r";\s*(.*?)\s*@\s*([^:]+):(\d+)\s*$"
)


INSN_OR_STATE_RE = re.compile(r"^\s*\d+:")
# Verifier debug output that sits between the last instruction and the error
# message (precision backtracking, state-pruning notes); never the message.
NON_MESSAGE_RE = re.compile(r"^(mark_precise:|from \d+ to \d+:|propagating |frame\d+:|last_idx )")
TRAILER_RE = re.compile(r"^\s*(verification time \d+ usec|processed \d+ insns)")


def verifier_error_block(lines: list[str]) -> tuple[int, list[str]] | None:
    """Locate the verifier's terminal error message by log structure.

    The kernel prints the rejecting instruction, then one or more message lines,
    then ``verification time`` / ``processed N insns``. Walking back from the
    first trailer line over non-instruction, non-source-map lines yields that
    message, whatever its wording. Returns (index of the first message line,
    message lines) or None when there is no message (accepted programs, or a
    log without the trailer).
    """
    end = next((i for i, ln in enumerate(lines) if TRAILER_RE.match(ln)), None)
    if end is None:
        return None
    msg: list[int] = []
    for i in range(end - 1, -1, -1):
        s = lines[i].strip()
        if not s:
            continue
        if (
            INSN_OR_STATE_RE.match(lines[i])
            or s.startswith(";")
            or NON_MESSAGE_RE.match(s)
            or "BEGIN PROG LOAD LOG" in s
        ):
            break
        msg.append(i)
    if not msg:
        return None
    msg.reverse()
    return msg[0], [lines[i].strip() for i in msg]


@dataclass
class ParsedLog:
    terminal_error: str
    terminal_pc: Optional[int]
    source_locations: list[SourceLocation]


def parse_verifier_log(text: str) -> ParsedLog:
    locs: list[SourceLocation] = []
    terminal_error = ""
    terminal_pc: Optional[int] = None
    pc_re = re.compile(r"^\s*(\d+):\s*")
    all_lines = text.splitlines()
    block = verifier_error_block(all_lines)
    for line in all_lines:
        m = SOURCE_COMMENT_RE.search(line)
        if m:
            locs.append(
                SourceLocation(
                    path=m.group(2).strip(),
                    line=int(m.group(3)),
                    text=m.group(1).strip(),
                )
            )
        # Fallback for logs without a verification trailer (synthetic fixtures).
        if block is None and "R" in line and "invalid" in line.lower():
            terminal_error = line.strip()
        pm = pc_re.match(line)
        if pm:
            terminal_pc = int(pm.group(1))
    if block is not None:
        terminal_error = "; ".join(block[1])
    # last numbered insn before end often is reject pc
    return ParsedLog(
        terminal_error=terminal_error or "rejected",
        terminal_pc=terminal_pc,
        source_locations=locs,
    )


def sourcecomment_events(log: ParsedLog) -> list[ProofEvent]:
    """Approximate bpfix SourceComment event emission for scoped obligations."""
    events: list[ProofEvent] = []
    for loc in log.source_locations:
        t = loc.text
        if looks_like_null_check(t):
            events.append(
                ProofEvent(
                    role=ProofEventRole.PROOF_ESTABLISHED,
                    evidence=ProofEventEvidence.SOURCE_COMMENT,
                    obligation=ProofObligation.NULLABLE_POINTER,
                    detail="non-null proof established (looks_like_null_check)",
                    source=loc,
                )
            )
        if looks_like_nullable_return(t):
            events.append(
                ProofEvent(
                    role=ProofEventRole.PROOF_LOST,
                    evidence=ProofEventEvidence.SOURCE_COMMENT,
                    obligation=ProofObligation.NULLABLE_POINTER,
                    detail="nullable return without visible non-null proof",
                    source=loc,
                )
            )
        if looks_like_packet_bounds_check(t):
            events.append(
                ProofEvent(
                    role=ProofEventRole.PROOF_ESTABLISHED,
                    evidence=ProofEventEvidence.SOURCE_COMMENT,
                    obligation=ProofObligation.PACKET_BOUNDS,
                    detail="packet bounds via data_end",
                    source=loc,
                )
            )
        if looks_like_scalar_guard(t) and "data_end" not in t:
            events.append(
                ProofEvent(
                    role=ProofEventRole.PROOF_ESTABLISHED,
                    evidence=ProofEventEvidence.SOURCE_COMMENT,
                    obligation=ProofObligation.SCALAR_RANGE,
                    detail="scalar guard visible",
                    source=loc,
                )
            )
    return events


def reported_loss_from_events(
    events: list[ProofEvent],
    *,
    prefer_role: ProofEventRole = ProofEventRole.PROOF_LOST,
) -> Optional[int]:
    """Return source line of preferred event as a stand-in loss report."""
    preferred = [e for e in events if e.role == prefer_role and e.source]
    if preferred:
        return preferred[-1].source.line  # type: ignore[union-attr]
    established = [e for e in events if e.role == ProofEventRole.PROOF_ESTABLISHED and e.source]
    if established:
        return established[-1].source.line  # type: ignore[union-attr]
    return None

# SPDX-License-Identifier: MIT
"""Verifier-state oracle: the first-loss point read from the verifier's own log.

Rules: docs/STATE-ORACLE.md. Reads only the program-load log (log level 2):
never the fix, the source text or a reporter's output.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .logparse import verifier_error_block

SRC_RE = re.compile(r";\s*(.*?)\s*@\s*([^:\s]+):(\d+)\s*$")
INSN_RE = re.compile(r"^(\d+): \(([0-9a-f]{2})\) (.*?)(?:\s+; (.*))?$")
FROM_RE = re.compile(r"^from (\d+) to (\d+): ?(.*)$")
NULLABLE_RE = re.compile(r"\bR(\d+)(?:_w)?=[a-z_]*_or_null\(id=(\d+)")
REG_RE = re.compile(r"\bR(\d+)\b")


@dataclass(frozen=True)
class Step:
    idx: int  # instruction index
    insn: str  # instruction text
    state: str  # register state after the instruction ("" when not printed)
    src: tuple[str, int] | None  # (file base name, line)


@dataclass
class StateOracle:
    kind: str | None  # "NullablePointer" | "PacketBounds" | None (not covered)
    message: str
    path_len: int = 0
    first_loss: Step | None = None
    stop_line: tuple[str, int] | None = None  # the rejected instruction's line, never a site
    sites: list[tuple[str, int]] = field(default_factory=list)
    note: str = ""


def _segments(lines: list[str]) -> list[tuple[int | None, list[Step]]]:
    """Log split at `from A to B` markers: (A or None, steps)."""
    segs: list[tuple[int | None, list[Step]]] = [(None, [])]
    src: tuple[str, int] | None = None
    for ln in lines:
        s = ln.strip()
        m = FROM_RE.match(s)
        if m:
            segs.append((int(m.group(1)), []))
            continue
        m = SRC_RE.match(s)
        if m and s.startswith(";"):
            src = (Path(m.group(2)).name, int(m.group(3)))
            continue
        m = INSN_RE.match(s)
        if m:
            segs[-1][1].append(Step(int(m.group(1)), m.group(3), m.group(4) or "", src))
    return segs


def failing_path(lines: list[str]) -> list[Step]:
    """Rule 2: the last segment, preceded by the path to its fork point, recursively."""
    segs = _segments(lines)
    memo: dict[int, list[Step]] = {}

    def path_to(i: int) -> list[Step]:
        if i in memo:
            return memo[i]
        fork, steps = segs[i]
        out = list(steps)  # no marker, or fork point never printed: the segment alone
        if fork is not None:
            for j in range(i - 1, -1, -1):
                hits = [k for k, st in enumerate(segs[j][1]) if st.idx == fork]
                if hits:
                    pj = path_to(j)
                    out = pj[: len(pj) - len(segs[j][1]) + hits[-1] + 1] + list(steps)
                    break
        memo[i] = out
        return out

    for i in range(len(segs)):  # bottom-up, so deep logs never recurse far
        path_to(i)
    return memo[len(segs) - 1]


def compute(text: str) -> StateOracle:
    lines = text.splitlines()
    block = verifier_error_block(lines)
    if block is None:
        return StateOracle(None, "", note="no verifier error message")
    start, msg_lines = block
    msg = " ".join(msg_lines)
    if "_or_null" in msg:
        kind = "NullablePointer"
    elif "invalid access to packet" in msg:
        kind = "PacketBounds"
    else:
        return StateOracle(None, msg, note="not covered (rule 3)")
    path = failing_path(lines[:start])
    out = StateOracle(kind, msg, path_len=len(path))
    if not path:
        out.note = "no instruction steps before the error"
        return out
    first = None
    if kind == "NullablePointer":
        m = REG_RE.search(msg)
        reg = m.group(1) if m else None
        k = None
        for st in reversed(path):
            for r, i in NULLABLE_RE.findall(st.state):
                if r == reg:
                    k = i
                    break
            if k:
                break
        if k is None:
            out.note = f"R{reg} never shown as *_or_null on the failing path"
            return out
        first = next((n for n, st in enumerate(path) if any(i == k for _r, i in NULLABLE_RE.findall(st.state))), None)
    else:
        bounds = [n for n, st in enumerate(path) if st.insn.startswith("if ") and "pkt_end" in st.state]
        if bounds:
            first = bounds[-1]
        else:
            first = next((n for n, st in enumerate(path) if "pkt(" in st.state), None)
            out.note = "no bound against pkt_end on the path: first packet pointer"
    if first is None:
        out.note = "first-loss step not found"
        return out
    out.first_loss = path[first]
    out.stop_line = path[-1].src
    seen: list[tuple[str, int]] = []
    for st in path[first:]:
        if st.src and st.src not in seen and st.src != out.stop_line:  # rule 5: the stop line is not a site
            seen.append(st.src)
    out.sites = sorted(seen)
    if not out.sites:
        out.note = "first-loss point on the stop line: no sites"
    return out

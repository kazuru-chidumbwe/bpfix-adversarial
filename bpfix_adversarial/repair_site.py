# SPDX-License-Identifier: MIT
"""Repair-site oracle: lines that upstream's own buggy -> fixed edit touches.

The oracle is independent of this harness (written upstream, not here) and of
bpfix's output (bpfix never reads fixed.bpf.c). It is still an approximation of
"where the fault is": a fix may touch more lines than the fault, or repair at a
different site than the root cause. Results built on it report hunk-level
agreement, never a claim of exact root-cause localization.

Hunk sites are expressed in *buggy* line numbers:

* replace / delete of buggy lines i..j  -> sites i..j
* pure insertion after buggy line i     -> sites i and i+1 (the gap's neighbours)

A hunk is *non-semantic* when every changed line on both sides is blank, a
comment, or a preprocessor line (``oracle.code_line_mask``); those are dropped.
"""

from __future__ import annotations

import difflib
import math
from dataclasses import asdict, dataclass

from .oracle import code_line_mask


@dataclass(frozen=True)
class Hunk:
    tag: str  # replace | delete | insert
    buggy_start: int  # 1-based, inclusive
    buggy_end: int  # 1-based, inclusive (== start-1 for an insertion gap)
    fixed_start: int
    fixed_end: int
    sites: tuple[int, ...]
    semantic: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _norm(lines: list[str]) -> list[str]:
    return [ln.rstrip() for ln in lines]


def diff_hunks(buggy: str, fixed: str) -> list[Hunk]:
    b = _norm(buggy.replace("\r\n", "\n").splitlines())
    f = _norm(fixed.replace("\r\n", "\n").splitlines())
    bmask = code_line_mask(b)
    fmask = code_line_mask(f)
    out: list[Hunk] = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=b, b=f, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "insert":
            sites = tuple(x for x in (i1, i1 + 1) if 1 <= x <= len(b))
        else:
            sites = tuple(range(i1 + 1, i2 + 1))
        semantic = any(bmask[i1:i2]) or any(fmask[j1:j2])
        out.append(Hunk(tag, i1 + 1, i2, j1 + 1, j2, sites, semantic))
    return out


def repair_sites(hunks: list[Hunk]) -> list[int]:
    return sorted({s for h in hunks if h.semantic for s in h.sites})


def min_distance(line: int | None, sites: list[int]) -> int | None:
    if line is None or not sites:
        return None
    return min(abs(line - s) for s in sites)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float] | None:
    """Wilson score interval for k successes in n trials (95% by default)."""
    if n == 0:
        return None
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (round(max(0.0, centre - half), 4), round(min(1.0, centre + half), 4))


def mcnemar_exact(b: int, c: int) -> float | None:
    """Two-sided exact McNemar p-value from discordant counts b and c."""
    n = b + c
    if n == 0:
        return None
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2**n
    return round(min(1.0, 2 * tail), 6)

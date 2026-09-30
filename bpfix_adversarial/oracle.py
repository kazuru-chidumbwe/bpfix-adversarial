# SPDX-License-Identifier: MIT
"""Construction-time injection markers (ORACLE_* comments).

Historical names ORACLE_LOSS_LINE / ORACLE_REJECT_LINE are retained for fixture
compatibility. This harness measures injection-site agreement against these markers,
not a verified verifier-state transition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def code_line_mask(lines: list[str]) -> list[bool]:
    """Per-line executable flag, tracking ``/* … */`` state across lines.

    A line is code when anything other than whitespace remains after removing
    comments, and it is not a ``#`` preprocessor line. A leading ``*`` counts as
    a comment continuation only inside an open block comment, so a pointer store
    such as ``*p = 0;`` is code. String and char literals are not lexed; the
    templates contain no comment delimiters inside literals.
    """
    mask: list[bool] = []
    in_block = False
    for raw in lines:
        rest: list[str] = []
        i, n = 0, len(raw)
        while i < n:
            if in_block:
                end = raw.find("*/", i)
                if end < 0:
                    i = n
                else:
                    in_block = False
                    i = end + 2
            elif raw.startswith("/*", i):
                in_block = True
                i += 2
            elif raw.startswith("//", i):
                i = n
            else:
                rest.append(raw[i])
                i += 1
        t = "".join(rest).strip()
        mask.append(bool(t) and not t.startswith("#"))
    return mask


def is_code_line(raw: str) -> bool:
    """Single-line form of :func:`code_line_mask` (assumes no open block comment)."""
    return code_line_mask([raw])[0]


def oracle_sites(src: Path | str) -> dict[str, Any]:
    """Extract injection/reject marker lines and the executable injection span.

    Effective injection span = executable source lines strictly between the
    ORACLE_LOSS_LINE and ORACLE_REJECT_LINE markers, excluding blank/comment/
    preprocessor lines and distance pads (`__pad` / \"distance pad\").

    Scoring default: **top1_line** compares against ``oracle_loss_code`` (first span
    line when non-empty; else the last **executable** line *before* the LOSS marker
    for omitted-check seeds; **one-based**, pre-preprocessor).
    **top1_span** is set-membership against ``oracle_loss_span`` (separate metric).
    ``#`` lines are preprocessor directives and are skipped for the executable span.
    """
    path = Path(src)
    lines = path.read_text(encoding="utf-8").splitlines()
    code = code_line_mask(lines)
    loss_marker = reject_marker = None
    for i, raw in enumerate(lines, 1):
        if "ORACLE_LOSS_LINE" in raw and loss_marker is None:
            loss_marker = i
        if "ORACLE_REJECT_LINE" in raw and reject_marker is None:
            reject_marker = i

    span: list[int] = []
    if loss_marker is not None:
        end = reject_marker if reject_marker is not None else len(lines) + 1
        for i in range(loss_marker + 1, end):
            raw = lines[i - 1]
            if not code[i - 1]:
                continue
            if "__pad" in raw or "distance pad" in raw:
                continue
            span.append(i)

    loss_code = span[0] if span else None
    if loss_code is None and loss_marker is not None:
        # Empty injection span (e.g. omitted-check seeds): prior executable line,
        # not the comment immediately after the LOSS marker.
        for i in range(loss_marker - 1, 0, -1):
            if code[i - 1]:
                loss_code = i
                break
        if loss_code is None:
            loss_code = loss_marker + 1
    reject_code = None
    if reject_marker is not None:
        for i in range(reject_marker + 1, len(lines) + 1):
            if code[i - 1]:
                reject_code = i
                break

    return {
        "oracle_loss_marker": loss_marker,
        "oracle_reject_marker": reject_marker,
        "oracle_loss_span": span,
        "oracle_loss_code": loss_code,
        "oracle_reject_code": reject_code,
        # Published aliases
        "injection_marker": loss_marker,
        "injection_code": loss_code,
        "injection_span": span,
        "use_or_terminal_marker": reject_marker,
        "use_or_terminal_code": reject_code,
    }

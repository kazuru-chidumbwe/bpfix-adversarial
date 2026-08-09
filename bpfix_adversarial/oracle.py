# SPDX-License-Identifier: MIT
"""Construction-time injection markers (ORACLE_* comments).

Historical names ORACLE_LOSS_LINE / ORACLE_REJECT_LINE are retained for fixture
compatibility. SoftwareX measures injection-site agreement against these markers,
not a verified verifier-state transition.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def is_code_line(raw: str) -> bool:
    t = raw.strip()
    if not t:
        return False
    if t.startswith("/*") or t.startswith("*") or t.startswith("//"):
        return False
    if t.startswith("#"):
        return False
    return True


def oracle_sites(src: Path | str) -> dict[str, Any]:
    """Extract injection/reject marker lines and the executable injection span.

    Effective injection span = executable source lines strictly between the
    ORACLE_LOSS_LINE and ORACLE_REJECT_LINE markers, excluding blank/comment/
    preprocessor lines and distance pads (`__pad` / \"distance pad\").

    Scoring default: **top1_line** compares against ``oracle_loss_code`` (first span
    line, else the line after the loss marker; **one-based**, pre-preprocessor).
    **top1_span** is set-membership against ``oracle_loss_span`` (separate metric).
    ``#`` lines are preprocessor directives and are skipped for the executable span.
    """
    path = Path(src)
    lines = path.read_text(encoding="utf-8").splitlines()
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
            if not is_code_line(raw):
                continue
            if "__pad" in raw or "distance pad" in raw:
                continue
            span.append(i)

    loss_code = span[0] if span else (loss_marker + 1 if loss_marker else None)
    reject_code = None
    if reject_marker is not None:
        for i in range(reject_marker + 1, len(lines) + 1):
            if is_code_line(lines[i - 1]):
                reject_code = i
                break

    return {
        "oracle_loss_marker": loss_marker,
        "oracle_reject_marker": reject_marker,
        "oracle_loss_span": span,
        "oracle_loss_code": loss_code,
        "oracle_reject_code": reject_code,
        # SoftwareX aliases
        "injection_marker": loss_marker,
        "injection_code": loss_code,
        "injection_span": span,
        "use_or_terminal_marker": reject_marker,
        "use_or_terminal_code": reject_code,
    }

# SPDX-License-Identifier: MIT
"""Marker isolation helpers — strip ORACLE_* comments without shifting code lines."""

from __future__ import annotations

import re
from pathlib import Path

ORACLE_COMMENT_RE = re.compile(
    r"/\*\s*ORACLE_(?:LOSS|REJECT)_LINE\b.*?\*/",
    re.DOTALL,
)
ORACLE_LINE_RE = re.compile(r"ORACLE_(?:LOSS|REJECT)_LINE")


def strip_oracle_markers(text: str, *, preserve_lines: bool = True) -> str:
    """Return marker-neutral source.

    When ``preserve_lines`` is True (default), each ORACLE comment line is
    replaced with an inert ``/* */`` so subsequent code keeps the same line
    numbers — required for fair SC/VS line comparisons.
    """
    out_lines: list[str] = []
    for raw in text.splitlines():
        if ORACLE_LINE_RE.search(raw):
            if preserve_lines:
                # Keep indentation; neutralize token so reporters cannot see ORACLE_*.
                indent = raw[: len(raw) - len(raw.lstrip(" \t"))]
                out_lines.append(f"{indent}/* */")
            continue
        out_lines.append(raw)
    return "\n".join(out_lines) + ("\n" if text.endswith("\n") else "")


def strip_oracle_markers_path(src: Path, dest: Path, *, preserve_lines: bool = True) -> None:
    text = src.read_text(encoding="utf-8")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(strip_oracle_markers(text, preserve_lines=preserve_lines), encoding="utf-8")


def oracle_tokens_in_text(text: str) -> list[str]:
    return [ln for ln in text.splitlines() if "ORACLE_" in ln]

# SPDX-License-Identifier: MIT
"""Injection-site agreement scoring: construction markers vs reported line."""

from __future__ import annotations

from typing import Any, Optional


def score_honesty(
    *,
    oracle_loss_line: int,
    oracle_reject_line: int,
    reported_loss_line: Optional[int],
    reported_reject_line: Optional[int] = None,
) -> dict[str, Any]:
    """Score a reported primary line against the injection primary line.

    Distance (SoftwareX / Gates v1.1.11):
      ``distance_error = |predicted − oracle_loss_code|``
    This is absolute localization error on source lines — not a signed cancel
    of ``(reject−pred)−(reject−oracle)``. The algebraically equivalent signed
    form is exposed as ``signed_offset = predicted − oracle_loss_code``.

    ``distance_true`` / ``distance_reported`` remain pad-span diagnostics
    (reject−loss and reject−predicted) and are **not** the primary error metric.

    ``top1_loss_match`` is **top1_line** only (``predicted == oracle_loss_code``).
    Span membership is a separate caller-side metric (``top1_span``).
    """
    d_true = oracle_reject_line - oracle_loss_line
    if reported_loss_line is None:
        return {
            "top1_loss_match": False,
            "top1_line": False,
            "distance_true": d_true,
            "distance_reported": None,
            "distance_error": None,
            "signed_offset": None,
            "oracle_loss_line": oracle_loss_line,
            "oracle_reject_line": oracle_reject_line,
            "reported_loss_line": None,
            "reported_reject_line": reported_reject_line,
        }
    reject = reported_reject_line if reported_reject_line is not None else oracle_reject_line
    d_rep = reject - reported_loss_line
    signed = reported_loss_line - oracle_loss_line
    return {
        "top1_loss_match": reported_loss_line == oracle_loss_line,
        "top1_line": reported_loss_line == oracle_loss_line,
        "distance_true": d_true,
        "distance_reported": d_rep,
        "distance_error": abs(signed),
        "signed_offset": signed,
        "oracle_loss_line": oracle_loss_line,
        "oracle_reject_line": oracle_reject_line,
        "reported_loss_line": reported_loss_line,
        "reported_reject_line": reported_reject_line,
    }

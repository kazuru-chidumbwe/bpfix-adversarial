#!/usr/bin/env python3
"""RQ1 distance sweep using synthetic oracle + SourceComment diagnostic model.

For each pad length, oracle distance grows; a diagnostic that always reports
reject_line - 1 (near-reject bias) accumulates distance_error — illustrating
the honesty metric. A second model reports oracle_loss (honest).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.score import score_honesty  # noqa: E402


def sweep(pads: list[int] | None = None) -> dict:
    pads = pads or [0, 4, 8, 16, 32, 64]
    loss_line = 10
    rows_biased = []
    rows_honest = []
    for pad in pads:
        reject_line = loss_line + 2 + pad  # check, pad block, use
        biased = score_honesty(
            oracle_loss_line=loss_line,
            oracle_reject_line=reject_line,
            reported_loss_line=reject_line - 1,  # near-reject bias
        )
        honest = score_honesty(
            oracle_loss_line=loss_line,
            oracle_reject_line=reject_line,
            reported_loss_line=loss_line,
        )
        rows_biased.append({"pad": pad, **biased})
        rows_honest.append({"pad": pad, **honest})
    return {
        "metric": "accuracy / distance_error vs pad",
        "near_reject_bias_model": rows_biased,
        "oracle_honest_model": rows_honest,
        "top1_accuracy_biased": sum(1 for r in rows_biased if r["top1_loss_match"])
        / len(rows_biased),
        "top1_accuracy_honest": sum(1 for r in rows_honest if r["top1_loss_match"])
        / len(rows_honest),
        "note": (
            "Replace near_reject_bias_model with real bpfix loss PCs once lab "
            "captures are pinned; metric definitions stay fixed."
        ),
    }


def markdown(payload: dict) -> str:
    lines = [
        "# RQ1 — distance vs honesty (synthetic models)",
        "",
        "| pad | d_true | d_err (near-reject bias) | top1 bias | d_err (honest) | top1 honest |",
        "| ---: | ---: | ---: | --- | ---: | --- |",
    ]
    for b, h in zip(payload["near_reject_bias_model"], payload["oracle_honest_model"]):
        lines.append(
            f"| {b['pad']} | {b['distance_true']} | {b['distance_error']} | "
            f"{'yes' if b['top1_loss_match'] else 'no'} | {h['distance_error']} | "
            f"{'yes' if h['top1_loss_match'] else 'no'} |"
        )
    lines.append("")
    lines.append(
        f"Biased top-1 accuracy: **{payload['top1_accuracy_biased']:.0%}**; "
        f"honest model: **{payload['top1_accuracy_honest']:.0%}**."
    )
    return "\n".join(lines)


def main() -> None:
    payload = sweep()
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "distance_sweep.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    md = markdown(payload)
    (out_dir / "distance_sweep.md").write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"Wrote {out_dir / 'distance_sweep.json'}")


if __name__ == "__main__":
    main()

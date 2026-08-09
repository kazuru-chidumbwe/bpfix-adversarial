#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Cheap SoftwareX baseline battery over already-captured rejecting logs.

Baselines (no new lab work):
  - terminal_site: VerifierState stop-site map (last BTF line before reject)
  - random_line: uniform draw in [1, reject_code] with seed 42
  - oracle_upper: reports oracle_loss_code (perfect injection-site tip)

Compares top-1 vs injection code on the same SoftwareX-stamp rejecting cases
used in results/sc_vs_honesty.json.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.score import score_honesty  # noqa: E402

STAMP = "20260801T181331Z"
SEED = 42
OUT_JSON = ROOT / "results" / "baseline_battery.json"
OUT_MD = ROOT / "results" / "baseline_battery.md"


def in_loss_span(reported: int | None, loss: int | None, span: list[int] | None) -> bool:
    if reported is None or loss is None:
        return False
    if reported == loss:
        return True
    return reported in (span or [])


def main() -> None:
    sc = json.loads((ROOT / "results" / "sc_vs_honesty.json").read_text(encoding="utf-8"))
    rows_in = [r for r in sc["rows"] if r.get("lab_rejected") and STAMP in (r.get("log") or "")]
    rng = random.Random(SEED)
    rows = []
    for r in rows_in:
        loss = r["oracle_loss_code"]
        reject = r.get("oracle_reject_code") or r.get("oracle_reject_marker") or loss
        span = r.get("oracle_loss_span") or []
        terminal = r.get("vs_reported_line")
        rand_line = rng.randint(1, int(reject)) if reject else None
        upper = loss

        def pack(
            name: str,
            reported: int | None,
            *,
            loss: int | None = loss,
            reject: int | None = reject,
            span: list = span,
        ) -> dict:
            if loss is None or reported is None:
                return {
                    "baseline": name,
                    "reported_line": reported,
                    "top1_vs_loss": False,
                    "distance_error": None,
                }
            hit = in_loss_span(int(reported), int(loss), span)
            h = score_honesty(
                oracle_loss_line=int(loss),
                oracle_reject_line=int(reject),
                reported_loss_line=int(loss) if hit else int(reported),
            )
            return {
                "baseline": name,
                "reported_line": reported,
                "top1_vs_loss": bool(hit),
                "distance_error": 0 if hit else h["distance_error"],
            }

        rows.append(
            {
                "case_id": r["case_id"],
                "obligation": r["obligation"],
                "oracle_loss_code": loss,
                "oracle_reject_code": reject,
                "baselines": [
                    pack("terminal_site", terminal),
                    pack("random_line", rand_line),
                    pack("oracle_upper", upper),
                ],
            }
        )

    def rate(name: str) -> tuple[int, int, float]:
        hits = 0
        n = 0
        for row in rows:
            for b in row["baselines"]:
                if b["baseline"] != name:
                    continue
                n += 1
                if b["top1_vs_loss"]:
                    hits += 1
        return hits, n, (hits / n if n else 0.0)

    summary = {
        name: {
            "hits": rate(name)[0],
            "n": rate(name)[1],
            "top1_rate": round(rate(name)[2], 4),
        }
        for name in ("terminal_site", "random_line", "oracle_upper")
    }

    payload = {
        "stamp_filter": STAMP,
        "seed": SEED,
        "n_rejecting_cases": len(rows),
        "summary": summary,
        "rows": rows,
        "note": (
            "Offline scoring only. terminal_site = VS stop-site from sc_vs_honesty; "
            "random_line = Uniform{1..reject_code} seed 42; oracle_upper = injection code."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Baseline battery (rejecting SoftwareX-stamp cases)",
        "",
        f"Stamp filter `{STAMP}` · n={len(rows)} rejecting cases · random seed `{SEED}`.",
        "",
        "| Baseline | Top-1 hits | n | Rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ("terminal_site", "random_line", "oracle_upper"):
        s = summary[name]
        lines.append(f"| `{name}` | {s['hits']} | {s['n']} | {s['top1_rate']:.0%} |")
    lines += [
        "",
        "Per-case rows: `baseline_battery.json`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

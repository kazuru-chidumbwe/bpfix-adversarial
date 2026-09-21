#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Cheap baseline battery over already-captured rejecting logs.

Baselines (no new lab work):
  - terminal_site: VerifierState stop-site map (last BTF line before reject)
  - random_line: uniform draw in [1, reject_code] with seed 42
  - oracle_upper: reports oracle_loss_code (perfect injection-site tip)

Compares top1_span membership (reported line in oracle_loss_span) on the same
primary-stamp rejecting cases used in results/sc_vs_honesty.json. Distance is
always abs(reported - oracle_loss_code); never zeroed on a span-only hit.
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
                oracle_loss_code=int(loss),
                oracle_reject_line=int(reject),
                reported_loss_line=int(reported),
            )
            return {
                "baseline": name,
                "reported_line": reported,
                "top1_vs_loss": bool(hit),
                # Table 4: d = abs(predicted - oracle_loss_code); never zero a span-only hit.
                "distance_error": h["distance_error"],
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
            "top1_span_fraction": round(rate(name)[2], 4),
        }
        for name in ("terminal_site", "random_line", "oracle_upper")
    }

    # A single draw per row has a standard deviation close to its own mean, so
    # the drawn tally carries almost no information. The expectation over the
    # same rows is the stable quantity, and it costs nothing to state.
    per_row_p = []
    for r in rows_in:
        loss = r["oracle_loss_code"]
        reject = r.get("oracle_reject_code") or r.get("oracle_reject_marker") or loss
        span = r.get("oracle_loss_span") or [loss]
        if not reject:
            continue
        per_row_p.append(min(1.0, len(span) / int(reject)))
    expected = sum(per_row_p)
    variance = sum(p * (1.0 - p) for p in per_row_p)
    summary["random_line"]["expected_top1_span_hits"] = round(expected, 3)
    summary["random_line"]["expected_top1_span_sd"] = round(variance ** 0.5, 3)
    summary["random_line"]["expectation_note"] = (
        "Analytic expectation of span membership for a uniform draw over "
        "{1..reject_code}, summed across these rows. The drawn tally above is a "
        "single realisation and should not be read as a rate."
    )

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
        "# Baseline battery (rejecting primary-stamp cases)",
        "",
        f"Stamp filter `{STAMP}` · n={len(rows)} rejecting cases · random seed `{SEED}`.",
        "",
        "| Baseline | top1_span hits | n | Row tally |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name in ("terminal_site", "random_line", "oracle_upper"):
        s = summary[name]
        lines.append(f"| `{name}` | {s['hits']} | {s['n']} | {s['hits']}/{s['n']} |")
    lines += [
        "",
        f"The `random_line` row is one draw per case (seed {SEED}). Its expected "
        f"top1_span hit count over these rows is "
        f"{summary['random_line']['expected_top1_span_hits']} "
        f"(SD {summary['random_line']['expected_top1_span_sd']}), which is the "
        "stable comparison; the drawn tally is a single realisation.",
        "",
        "Per-case rows: `baseline_battery.json`. "
        "`top1_vs_loss` is the legacy name for top1_span (span membership, not "
        "exact-line top1_line); tallies are pad-repeat rows, not a rate. `distance_error` is "
        "`abs(reported - oracle_loss_code)` (never zeroed on a span-only hit).",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

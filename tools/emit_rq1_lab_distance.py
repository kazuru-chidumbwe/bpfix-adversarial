#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RQ1 lab distance table from sc_vs_honesty (pad 0/8/32 reject-oracles).

Uses loss-anchored scoring on lab-captured templates. This is SC-port + VerifierState
stop-site distance. Full upstream bpfix CLI localizations: `tools/emit_rq1_bpfix_cli.py`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / "results" / "sc_vs_honesty.json"
OUT_MD = ROOT / "results" / "rq1_lab_distance.md"
OUT_JSON = ROOT / "results" / "rq1_lab_distance.json"


def pad_of(case_id: str) -> int | None:
    m = re.search(r"pad(\d+)", case_id)
    return int(m.group(1)) if m else None


def dist_err(reported: int | None, loss: int | None) -> int | None:
    """Absolute localization error: |predicted − oracle_loss_code|."""
    if reported is None or loss is None:
        return None
    return abs(reported - loss)


def main() -> None:
    rows_in = json.loads(IN.read_text(encoding="utf-8"))["rows"]
    out_rows = []
    for r in rows_in:
        if not r.get("lab_rejected"):
            continue
        pad = pad_of(r["case_id"])
        if pad is None and "nocheck" in r["case_id"]:
            continue  # RQ4 seed — not a distance-pad arm
        loss = r.get("oracle_loss_code")
        reject = r.get("oracle_reject_code")
        sc = r.get("sc_reported_line")
        vs = r.get("vs_reported_line")
        d_true = (reject - loss) if loss is not None and reject is not None else None
        sc_err = dist_err(sc, loss)
        vs_err = dist_err(vs, loss)
        out_rows.append(
            {
                "obligation": r["obligation"],
                "case_id": r["case_id"],
                "pad": pad,
                "oracle_loss_code": loss,
                "oracle_reject_code": reject,
                "d_true_src": d_true,
                "sc_reported": sc,
                "sc_top1_line": r.get("sc_top1_line"),
                "sc_top1_span": r.get("sc_top1_span", r.get("sc_top1_vs_loss")),
                "sc_top1": r.get("sc_top1_span", r.get("sc_top1_vs_loss")),  # legacy
                "sc_distance_error": sc_err,
                "vs_reported": vs,
                "vs_top1_line": r.get("vs_top1_line"),
                "vs_top1_span": r.get("vs_top1_span", r.get("vs_top1_vs_loss")),
                "vs_top1": r.get("vs_top1_span", r.get("vs_top1_vs_loss")),  # legacy
                "vs_distance_error": vs_err,
                "log": r.get("log"),
            }
        )

    OUT_JSON.write_text(json.dumps({"n": len(out_rows), "rows": out_rows}, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# RQ1 — Lab distance vs construction oracle (template pads)",
        "",
        "Source: `results/sc_vs_honesty.json` · stamp family `20260801T181331Z`.",
        "Distance error: `d = |predicted − oracle_loss_code|` (absolute source-line error).",
        "Do **not** zero distance on `top1_span` hits; span membership is a separate metric.",
        "SC = bpfix SourceComment heuristic port; VS = verifier stop-site source map from log.",
        "Companion: full upstream bpfix CLI on the same logs → `rq1_bpfix_cli.*`.",
        "",
        "| Obligation | case_id | pad | loss | reject | SC | top1_line | top1_span | d_err | VS | top1_line | top1_span | d_err |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | ---: |",
    ]

    def yn(v: bool | None) -> str:
        if v is True:
            return "yes"
        if v is False:
            return "no"
        return "n/a"

    for r in sorted(out_rows, key=lambda x: (x["obligation"], x["pad"] or -1, x["case_id"])):
        lines.append(
            f"| {r['obligation']} | `{r['case_id']}` | {r['pad']} | {r['oracle_loss_code']} | "
            f"{r['oracle_reject_code']} | {r['sc_reported'] if r['sc_reported'] is not None else '—'} | "
            f"{yn(r['sc_top1_line'])} | {yn(r['sc_top1_span'])} | "
            f"{r['sc_distance_error'] if r['sc_distance_error'] is not None else '—'} | "
            f"{r['vs_reported'] if r['vs_reported'] is not None else '—'} | "
            f"{yn(r['vs_top1_line'])} | {yn(r['vs_top1_span'])} | "
            f"{r['vs_distance_error'] if r['vs_distance_error'] is not None else '—'} |"
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"rows={len(out_rows)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Minimal offline oracle-independence controls .

Uses already-captured stamped rows in results/sc_vs_honesty.json,
no new lab work.

Controls
--------
1. negative_control
   Templates built to be well-formed (NullablePointer with the null check in
   its injection span) carry the same markers. Selected by construction, so a
   marker-bearing template that rejected would count as a failure rather than
   drop out. Shows markers alone do not induce the claimed reject/loss.
   verdict_matches_construction extends the same test to all templates.

2. positive_control
   Rejecting PacketBounds templates where VerifierState stop-site is *outside*
   the injection span (terminal/use differs from construction-time injection).
   Shows scoring still anchors on injection while the stop can diverge.

3. compiler_preservation
   For rejecting stamped logs, assert at least one injection-span line
   (else reject/use code line) appears in verifier ``; … @ path:LINE`` maps.
   Links authored source lines to emitted debug maps without claiming a
   full semantic proof-loss oracle.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.logparse import parse_verifier_log  # noqa: E402

STAMP = "20260801T181331Z"
OUT_JSON = ROOT / "results" / "oracle_controls.json"
OUT_MD = ROOT / "results" / "oracle_controls.md"


def in_span(line: int | None, span: list[int] | None, primary: int | None) -> bool:
    if line is None:
        return False
    if primary is not None and line == primary:
        return True
    return line in (span or [])


def expected_verdict(r: dict) -> str:
    """Verdict each template is built to produce, fixed before any lab load.

    gen_nullable places `if (!var) return 0;` between the NullablePointer markers,
    so those programs are well-formed; every other template omits or breaks the
    proof its family needs (NP-idiomatic-nocheck has an empty injection span).
    """
    if r["obligation"] == "NullablePointer" and r.get("oracle_loss_span"):
        return "ACCEPT"
    return "REJECT"


def main() -> None:
    sc = json.loads((ROOT / "results" / "sc_vs_honesty.json").read_text(encoding="utf-8"))
    stamp_rows = [r for r in sc["rows"] if STAMP in (r.get("log") or "")]

    negatives = []
    for r in stamp_rows:
        if expected_verdict(r) != "ACCEPT" or r.get("oracle_loss_marker") is None:
            continue
        accepted = r.get("lab_rejected") is False
        negatives.append(
            {
                "case_id": r["case_id"],
                "obligation": r["obligation"],
                "oracle_loss_code": r.get("oracle_loss_code"),
                "expected_verdict": "ACCEPT",
                "lab_rejected": r.get("lab_rejected"),
                "pass": accepted,
                "note": (
                    "markers present; lab ACCEPT, injection did not induce reject"
                    if accepted
                    else "markers present on a well-formed template but lab REJECT"
                ),
            }
        )

    verdicts = []
    for r in stamp_rows:
        observed = "REJECT" if r.get("lab_rejected") else "ACCEPT"
        verdicts.append(
            {
                "case_id": r["case_id"],
                "expected_verdict": expected_verdict(r),
                "observed_verdict": observed,
                "pass": observed == expected_verdict(r),
            }
        )

    positives = []
    for r in stamp_rows:
        if not r.get("lab_rejected"):
            continue
        if r.get("obligation") != "PacketBounds":
            continue
        vs = r.get("vs_reported_line")
        loss = r.get("oracle_loss_code")
        span = r.get("oracle_loss_span") or []
        diverge = vs is not None and not in_span(vs, span, loss)
        positives.append(
            {
                "case_id": r["case_id"],
                "obligation": r["obligation"],
                "oracle_loss_code": loss,
                "oracle_loss_span": span,
                "vs_reported_line": vs,
                "sc_top1_vs_loss": r.get("sc_top1_vs_loss"),
                "vs_top1_vs_loss": r.get("vs_top1_vs_loss"),
                "stop_diverges_from_injection": bool(diverge),
                "pass": bool(diverge),
                "note": (
                    "VS stop outside injection span; SC may still hit injection "
                    "(threshold / tier disagreement)"
                ),
            }
        )

    preservations = []
    for r in stamp_rows:
        if not r.get("lab_rejected"):
            continue
        log_rel = r.get("log")
        if not log_rel:
            continue
        text = (ROOT / log_rel).read_text(encoding="utf-8", errors="replace")
        mapped = sorted({loc.line for loc in parse_verifier_log(text).source_locations})
        span = list(r.get("oracle_loss_span") or [])
        primary = r.get("oracle_loss_code")
        reject = r.get("oracle_reject_code")
        targets = set(span)
        if primary is not None:
            targets.add(int(primary))
        hit_injection = bool(targets & set(mapped))
        hit_reject = reject is not None and int(reject) in mapped
        # Prefer injection-span preservation; fall back to reject/use line in map.
        ok = hit_injection or hit_reject
        preservations.append(
            {
                "case_id": r["case_id"],
                "obligation": r["obligation"],
                "oracle_loss_code": primary,
                "oracle_loss_span": span,
                "oracle_reject_code": reject,
                "mapped_source_lines": mapped,
                "injection_span_in_map": hit_injection,
                "reject_line_in_map": hit_reject,
                "pass": ok,
                "note": (
                    "verifier ; @path:LINE map covers injection span"
                    if hit_injection
                    else (
                        "injection span absent from map; reject/use line present "
                        "(pad DCE / wash may collapse)"
                        if hit_reject
                        else "neither injection span nor reject line in map"
                    )
                ),
            }
        )

    def rate(rows: list[dict]) -> dict:
        n = len(rows)
        hits = sum(1 for x in rows if x.get("pass"))
        return {"hits": hits, "n": n, "pass_rate": round(hits / n, 4) if n else 0.0}

    summary = {
        "negative_control": rate(negatives),
        "positive_control_pb_stop_vs_injection": rate(positives),
        "compiler_preservation_source_map": rate(preservations),
        "verdict_matches_construction": rate(verdicts),
    }

    payload = {
        "stamp_filter": STAMP,
        "generator": "tools/emit_oracle_controls.py",
        "summary": summary,
        "negative_control": negatives,
        "positive_control_pb_stop_vs_injection": positives,
        "compiler_preservation_source_map": preservations,
        "verdict_matches_construction": verdicts,
        "note": (
            "Minimal offline controls over stamped captures. "
            "Not a verified semantic proof-loss oracle; not negative controls "
            "that mutate away the reject while keeping the same marker text."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# Oracle-independence controls (offline, stamped lab family)",
        "",
        f"Stamp filter `{STAMP}`. Offline only, no new lab captures.",
        "",
        "| Control | Pass | n | Row tally |",
        "| --- | ---: | ---: | ---: |",
    ]
    labels = [
        ("negative_control", "negative (markers + ACCEPT)"),
        ("positive_control_pb_stop_vs_injection", "positive (PB stop ≠ injection)"),
        ("compiler_preservation_source_map", "compiler-preservation (source map)"),
        ("verdict_matches_construction", "verdict = construction (all templates)"),
    ]
    for key, label in labels:
        s = summary[key]
        lines.append(f"| {label} | {s['hits']} | {s['n']} | {s['hits']}/{s['n']} |")
    lines += [
        "",
        "## Negative control",
        "",
        "Templates built to be well-formed (selected by construction, not by the "
        "observed verdict); markers present; lab load **ACCEPT**s.",
        "",
        "| case_id | obligation | loss_code |",
        "| --- | --- | ---: |",
    ]
    for r in negatives:
        lines.append(f"| `{r['case_id']}` | {r['obligation']} | {r['oracle_loss_code']} |")
    lines += [
        "",
        "## Positive control (PacketBounds)",
        "",
        "VerifierState stop-site outside injection span.",
        "",
        "| case_id | loss | VS | SC top1_span | VS top1_span | diverge |",
        "| --- | ---: | ---: | --- | --- | --- |",
    ]
    for r in positives:
        lines.append(
            f"| `{r['case_id']}` | {r['oracle_loss_code']} | {r['vs_reported_line']} | "
            f"{'yes' if r['sc_top1_vs_loss'] else 'no'} | "
            f"{'yes' if r['vs_top1_vs_loss'] else 'no'} | "
            f"{'yes' if r['stop_diverges_from_injection'] else 'no'} |"
        )
    lines += [
        "",
        "## Compiler-preservation (verifier source map)",
        "",
        "| case_id | injection span in map | reject line in map | pass |",
        "| --- | --- | --- | --- |",
    ]
    for r in preservations:
        lines.append(
            f"| `{r['case_id']}` | {'yes' if r['injection_span_in_map'] else 'no'} | "
            f"{'yes' if r['reject_line_in_map'] else 'no'} | "
            f"{'yes' if r['pass'] else 'no'} |"
        )
    lines += ["", "JSON: `oracle_controls.json`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

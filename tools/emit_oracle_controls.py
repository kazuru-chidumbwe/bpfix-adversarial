#!/usr/bin/env python3
"""Minimal offline oracle-independence controls (SoftwareX punch-list).

Uses already-captured SoftwareX-stamp rows in results/sc_vs_honesty.json —
no new lab work.

Controls
--------
1. negative_control
   Injection markers present on programs that ACCEPT under the lab pin.
   Shows markers alone do not induce the claimed reject/loss.

2. positive_control
   Rejecting PacketBounds templates where VerifierState stop-site is *outside*
   the injection span (terminal/use differs from construction-time injection).
   Shows scoring still anchors on injection while the stop can diverge.

3. compiler_preservation
   For rejecting SoftwareX-stamp logs, assert at least one injection-span line
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


def main() -> None:
    sc = json.loads((ROOT / "results" / "sc_vs_honesty.json").read_text(encoding="utf-8"))
    stamp_rows = [r for r in sc["rows"] if STAMP in (r.get("log") or "")]

    negatives = []
    for r in stamp_rows:
        if r.get("lab_rejected") is not False:
            continue
        if r.get("oracle_loss_marker") is None:
            continue
        negatives.append(
            {
                "case_id": r["case_id"],
                "obligation": r["obligation"],
                "oracle_loss_code": r.get("oracle_loss_code"),
                "lab_rejected": False,
                "pass": True,
                "note": "markers present; lab ACCEPT — injection did not induce reject",
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
                "injection_line_in_map": hit_injection,
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
    }

    payload = {
        "stamp_filter": STAMP,
        "generator": "tools/emit_oracle_controls.py",
        "summary": summary,
        "negative_control": negatives,
        "positive_control_pb_stop_vs_injection": positives,
        "compiler_preservation_source_map": preservations,
        "note": (
            "Minimal offline controls over SoftwareX-stamp captures. "
            "Not a verified semantic proof-loss oracle; not negative controls "
            "that mutate away the reject while keeping the same marker text."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Oracle-independence controls (minimal, SoftwareX-stamp)",
        "",
        f"Stamp filter `{STAMP}`. Offline only — no new lab captures.",
        "",
        "| Control | Pass | n | Rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    labels = [
        ("negative_control", "negative (markers + ACCEPT)"),
        ("positive_control_pb_stop_vs_injection", "positive (PB stop ≠ injection)"),
        ("compiler_preservation_source_map", "compiler-preservation (source map)"),
    ]
    for key, label in labels:
        s = summary[key]
        lines.append(f"| {label} | {s['hits']} | {s['n']} | {s['pass_rate']:.0%} |")
    lines += [
        "",
        "## Negative control",
        "",
        "Injection markers present; lab load **ACCEPT**s.",
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
        "| case_id | loss | VS | SC top-1 | VS top-1 | diverge |",
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
        "| case_id | injection in map | reject in map | pass |",
        "| --- | --- | --- | --- |",
    ]
    for r in preservations:
        lines.append(
            f"| `{r['case_id']}` | {'yes' if r['injection_line_in_map'] else 'no'} | "
            f"{'yes' if r['reject_line_in_map'] else 'no'} | "
            f"{'yes' if r['pass'] else 'no'} |"
        )
    lines += ["", "JSON: `oracle_controls.json`.", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

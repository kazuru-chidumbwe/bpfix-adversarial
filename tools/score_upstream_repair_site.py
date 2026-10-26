#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score upstream's own committed bpfix diagnostics against upstream's own fixes.

For every vendored bpfix-bench case (fixtures/upstream/bpfix-bench-cases/<id>/)
the oracle is the set of buggy-file lines touched by the semantic hunks of the
buggy.bpf.c -> fixed.bpf.c diff (bpfix_adversarial.repair_site). The reporter is
upstream's committed diagnostic.txt (bpfix @ the pin, upstream's own capture).
No lab host and no bpfix binary are needed.

Metrics per case:
  primary_in_repair   the `-->` line is a repair site            (headline)
  any_label_in_repair some snippet line (primary or secondary) is a repair site
  primary_within_3    `-->` line within 3 lines of a repair site
  primary_distance    min |primary - site|
A `-->` line of 0 counts as no primary (recorded as primary_zero).

This is hunk-level agreement with a fix, not root-cause ground truth: a fix can
touch more lines than the fault, or repair elsewhere.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.bpfix_output import parse_bpfix  # noqa: E402
from bpfix_adversarial.oracle import code_line_mask  # noqa: E402
from bpfix_adversarial.repair_site import diff_hunks, min_distance, repair_sites, wilson  # noqa: E402
from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION  # noqa: E402

CASES = ROOT / "fixtures" / "upstream" / "bpfix-bench-cases"
OUT_JSON = ROOT / "results" / "upstream_repair_site.json"
OUT_MD = ROOT / "results" / "upstream_repair_site.md"
NEAR = 3


def case_kind(case_id: str) -> str:
    return "real-project seed" if case_id.startswith("rs_") else "canary"


def score_case(case_dir: Path) -> dict:
    buggy = (case_dir / "buggy.bpf.c").read_text(encoding="utf-8")
    fixed = (case_dir / "fixed.bpf.c").read_text(encoding="utf-8")
    diag = parse_bpfix((case_dir / "diagnostic.txt").read_text(encoding="utf-8"))
    hunks = diff_hunks(buggy, fixed)
    sites = repair_sites(hunks)
    blines = buggy.replace("\r\n", "\n").splitlines()
    # Snippet text must equal the buggy source at that line, or the line numbers
    # do not refer to this file and the row is not scorable.
    mismatched = [
        lab.line
        for lab in diag.labels
        if not (1 <= lab.line <= len(blines)) or blines[lab.line - 1].strip() != lab.source
    ]
    primary = diag.primary
    dist = min_distance(primary, sites)
    # Chance baseline: probability that a uniformly drawn executable line of
    # buggy.bpf.c is a repair site.
    code = [i for i, c in enumerate(code_line_mask(blines), 1) if c]
    p_chance = (sum(1 for i in code if i in sites) / len(code)) if code else None
    return {
        "case_id": case_dir.name,
        "error_id": diag.error_id,
        "upstream_obligation": UPSTREAM_ERROR_OBLIGATION.get(diag.error_id or ""),
        "primary": primary,
        "primary_zero": diag.primary_raw == 0,
        "label_lines": diag.label_lines,
        "snippet_lines_not_matching_buggy": mismatched,
        "n_hunks": len(hunks),
        "n_semantic_hunks": sum(1 for h in hunks if h.semantic),
        "repair_sites": sites,
        "primary_in_repair": primary is not None and primary in sites,
        "any_label_in_repair": any(ln in sites for ln in diag.label_lines),
        "primary_within_3": dist is not None and dist <= NEAR,
        "primary_distance": dist,
        "n_code_lines": len(code),
        "chance_line_in_repair": round(p_chance, 4) if p_chance is not None else None,
        "hunks": [h.to_dict() for h in hunks],
    }


def tally(rows: list[dict], key: str) -> dict:
    k = sum(1 for r in rows if r[key])
    n = len(rows)
    return {"hits": k, "n": n, "wilson95": wilson(k, n)}


def main() -> None:
    rows = [score_case(d) for d in sorted(p for p in CASES.iterdir() if p.is_dir())]
    scorable = [r for r in rows if not r["snippet_lines_not_matching_buggy"] and r["repair_sites"]]
    metrics = ("primary_in_repair", "any_label_in_repair", "primary_within_3")
    summary = {m: tally(scorable, m) for m in metrics}
    summary["n_cases"] = len(rows)
    summary["n_scorable"] = len(scorable)
    summary["n_primary_zero"] = sum(1 for r in rows if r["primary_zero"])
    summary["chance_expected_primary_hits"] = round(
        sum(r["chance_line_in_repair"] or 0 for r in scorable), 3
    )
    by_ob: dict[str, list[dict]] = defaultdict(list)
    for r in scorable:
        by_ob[r["upstream_obligation"] or "unmapped"].append(r)
    per_ob = {ob: {m: tally(rs, m) for m in metrics} for ob, rs in sorted(by_ob.items())}
    # Upstream names its real-project seeds rs_<project>_...; the rest are canary cases.
    by_kind: dict[str, list[dict]] = defaultdict(list)
    for r in scorable:
        by_kind[case_kind(r["case_id"])].append(r)
    per_kind = {k: {m: tally(rs, m) for m in metrics} for k, rs in sorted(by_kind.items())}
    selection = (
        "the full main75 split" if summary["n_cases"] == 75
        else "the keyword-stratified depth-21 selection, not a random sample of main75"
    )

    payload = {
        "generator": "tools/score_upstream_repair_site.py",
        "oracle": "semantic buggy->fixed diff hunks (buggy line numbers); insertions mark both neighbours",
        "reporter": "upstream committed diagnostic.txt (bpfix @ 81d97e4a528456e0082a77f4fb6edd13fa092b7b)",
        "near_threshold": NEAR,
        "summary": summary,
        "by_upstream_obligation": per_ob,
        "by_case_kind": per_kind,
        "rows": rows,
        "caveat": (
            "Hunk-level agreement with upstream's fix, not root-cause ground truth. "
            f"Cases are {selection}."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    def frac(t: dict) -> str:
        ci = t["wilson95"]
        ci_s = f" (95% CI {ci[0]:.2f}–{ci[1]:.2f})" if ci else ""
        return f"{t['hits']}/{t['n']}{ci_s}"

    yn = {True: "yes", False: "no"}
    lines = [
        "# Upstream diagnostics vs upstream fixes (repair-site oracle)",
        "",
        "Reporter: upstream's committed `diagnostic.txt` (bpfix @ `81d97e4a5284`). "
        "Oracle: lines touched by the semantic hunks of upstream's `buggy.bpf.c` → `fixed.bpf.c` diff, "
        "in buggy line numbers (an insertion marks the lines on both sides of the gap). "
        "Neither input is authored by this harness.",
        "",
        f"Cases: {summary['n_cases']} vendored ({selection.split(',')[0]}); scorable: {summary['n_scorable']}. "
        f"`-->` line 0 (no primary): {summary['n_primary_zero']}.",
        "",
        "| Metric | Hits |",
        "| --- | ---: |",
        f"| primary `-->` on a repair site | {frac(summary['primary_in_repair'])} |",
        f"| any snippet label on a repair site | {frac(summary['any_label_in_repair'])} |",
        f"| primary within {NEAR} lines of a repair site | {frac(summary['primary_within_3'])} |",
        f"| chance: expected primary hits for a uniformly random executable line | "
        f"{summary['chance_expected_primary_hits']:.1f}/{summary['n_scorable']} |",
        "",
        "## By upstream obligation",
        "",
        "| Upstream obligation | primary on site | any label on site | n |",
        "| --- | ---: | ---: | ---: |",
    ]
    for ob, t in per_ob.items():
        lines.append(
            f"| {ob} | {t['primary_in_repair']['hits']} | {t['any_label_in_repair']['hits']} | "
            f"{t['primary_in_repair']['n']} |"
        )
    lines += [
        "",
        "## By case kind",
        "",
        "| Case kind | primary on site | any label on site | n |",
        "| --- | ---: | ---: | ---: |",
    ]
    for kind, t in per_kind.items():
        lines.append(
            f"| {kind} | {frac(t['primary_in_repair'])} | {frac(t['any_label_in_repair'])} | "
            f"{t['primary_in_repair']['n']} |"
        )
    lines += [
        "",
        "## Per case",
        "",
        "| case | error | primary | repair sites | primary on site | label on site | distance |",
        "| --- | --- | ---: | --- | --- | --- | ---: |",
    ]
    for r in rows:
        sites = ",".join(str(s) for s in r["repair_sites"]) or "none"
        prim = "0 (none)" if r["primary_zero"] else str(r["primary"])
        dist = "n/a" if r["primary_distance"] is None else str(r["primary_distance"])
        lines.append(
            f"| `{r['case_id']}` | {r['error_id']} | {prim} | {sites} | "
            f"{yn[r['primary_in_repair']]} | {yn[r['any_label_in_repair']]} | {dist} |"
        )
    lines += [
        "",
        "Hunk-level agreement with upstream's fix, not root-cause ground truth: a fix can touch more "
        f"lines than the fault or repair elsewhere. Cases are {selection}; "
        "intervals are Wilson 95% over cases.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

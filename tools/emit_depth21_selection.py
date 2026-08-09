#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Emit depth-21 selection + join table (campaign label 20260728)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "fixtures" / "upstream" / "depth21_manifest.json"
OUT_MD = ROOT / "results" / "depth21_selection.md"
OUT_JSON = ROOT / "results" / "depth21_selection.json"

# Template-arm evidence already locked for the same obligation families.
TEMPLATE_EVIDENCE = {
    "PointerProvenance": {
        "template_cases": ["PP-pad0", "PP-pad8", "PP-pad32"],
        "lab_reject": "3/3",
        "sc_top1": "0/3",
        "vs_top1": "3/3",
        "note": "pkt⊕prandom wash; VS hits loss span",
    },
    "ScalarRange": {
        "template_cases": ["SR-pad0", "SR-pad8", "SR-pad32"],
        "lab_reject": "3/3",
        "sc_top1": "0/3",
        "vs_top1": "0/3",
        "note": "stack[prandom]; both miss loss (VS near-reject)",
    },
    "NullablePointer": {
        "template_cases": [
            "NP-brittle-pad0",
            "NP-brittle-pad8",
            "NP-brittle-pad32",
            "NP-idiomatic-pad0",
            "NP-idiomatic-pad8",
            "NP-idiomatic-pad32",
            "NP-idiomatic-nocheck",
        ],
        "lab_reject": "1/7 (nocheck); 6/7 accept controls",
        "sc_top1": "rename matrix 32/32 breaks + brittle hits",
        "vs_top1": "n/a on accepts; nocheck miss vs loss-span",
        "note": "RQ2 lead + RQ4 seed",
    },
    "PacketBounds": {
        "template_cases": ["PB-pad0", "PB-pad8", "PB-pad32"],
        "lab_reject": "3/3",
        "sc_top1": "3/3",
        "vs_top1": "0/3",
        "note": "SC/VS tier disagree",
    },
}


def main() -> None:
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    cases = man["cases"]
    counts = Counter(c["upstream_proof_obligation"] for c in cases)

    rows = []
    for i, c in enumerate(cases, 1):
        buggy = ROOT / c["local_path"] / "buggy.bpf.c"
        rows.append(
            {
                "depth_index": i,
                "upstream_case_id": c["upstream_case_id"],
                "obligation": c["upstream_proof_obligation"],
                "upstream_commit": c["upstream_commit"],
                "has_buggy": buggy.is_file(),
                "buggy_bytes": buggy.stat().st_size if buggy.is_file() else 0,
                "local_path": c["local_path"],
                "template_family_evidence": TEMPLATE_EVIDENCE.get(
                    c["upstream_proof_obligation"], {}
                ),
            }
        )

    OUT_JSON.write_text(
        json.dumps(
            {
                "campaign_label": man.get("campaign_label", "20260728"),
                "selection_method": "balanced obligation guess (per=6; SR pool=3)",
                "upstream_commit": man["upstream_commit"],
                "n": len(rows),
                "counts": dict(counts),
                "rows": rows,
                "status": "IDs_locked_sources_fetched_template_evidence_joined",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Depth-21 stratified selection (campaign `20260728`)",
        "",
        f"Upstream pin: `eunomia-bpf/bpfix` @ `{man['upstream_commit']}`",
        "Selection: balanced obligation guess · target ≤6/obligation · **n=21** (SR pool only 3).",
        "Sources: sparse-fetched under `fixtures/upstream/bpfix-bench-cases/<id>/` (no full vendor tree).",
        "",
        "## Counts",
        "",
        "| Obligation | n |",
        "| --- | ---: |",
    ]
    for ob in (
        "PointerProvenance",
        "ScalarRange",
        "NullablePointer",
        "PacketBounds",
    ):
        lines.append(f"| {ob} | {counts.get(ob, 0)} |")
    lines += ["", f"**Total** | **{len(rows)}** |", ""]

    lines += [
        "## Selection table",
        "",
        "| # | upstream_case_id | Obligation | buggy.bpf.c | Template-family evidence |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for r in rows:
        te = r["template_family_evidence"]
        ev = (
            f"reject {te.get('lab_reject', '?')}; SC {te.get('sc_top1', '?')}; "
            f"VS {te.get('vs_top1', '?')}"
            if te
            else "—"
        )
        lines.append(
            f"| {r['depth_index']} | `{r['upstream_case_id']}` | {r['obligation']} | "
            f"{'yes' if r['has_buggy'] else 'no'} ({r['buggy_bytes']} B) | {ev} |"
        )

    lines += [
        "",
        "## Status",
        "",
        "- **Corpus selection & sourcing: done** — 21 `upstream_case_id`s + local buggy/fixed/diagnostic/verifier.log",
        "- **Per-case lab validation: not started** — family-level template SC/VS scores in the table are "
        "**inherited**, not independently measured on these upstream programs",
        "- **SoftwareX scope:** curated real-world validation *target* only — not RQ1/RQ3 evidence",
        "- **SR pool:** n=3 vs target 6 — corpus-availability limitation",
        "- **Next (EuroSys / future):** per-case pad/rename mutants + individual lab / bpfix re-captures",
        "",
        f"Manifest: `fixtures/upstream/depth21_manifest.json`",
        f"Artifacts: `{OUT_MD.relative_to(ROOT).as_posix()}` · `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_MD} n={len(rows)} counts={dict(counts)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Emit depth-21 selection + join table (campaign label 20260728).

The 21 upstream cases were selected by stratifying on case-name keyword labels
(bpfix_adversarial.upstream_corpus.obligation_from_case_id). Each row also shows
upstream's own obligation for the case. These cases are not scored.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION  # noqa: E402

MANIFEST = ROOT / "fixtures" / "upstream" / "depth21_manifest.json"
DIAG = ROOT / "fixtures" / "upstream" / "main75_upstream_diagnostics.json"
OUT_MD = ROOT / "results" / "depth21_selection.md"
OUT_JSON = ROOT / "results" / "depth21_selection.json"

# Template results for each family, as reported in the paper (Section 3.2).
# Shown per family only; they are not measurements on the upstream cases.
TEMPLATE_EVIDENCE = {
    "PointerProvenance": {
        "template_cases": ["PP-pad0", "PP-pad8", "PP-pad32"],
        "lab_reject": "3/3",
        "sourcecomment": "N/A (no upstream PointerProvenance predicate)",
        "verifierstate": "top1_span 3/3, top1_line 0/3",
    },
    "ScalarRange": {
        "template_cases": ["SR-pad0", "SR-pad8", "SR-pad32"],
        "lab_reject": "3/3",
        "sourcecomment": "top1_line 0/3 (no scalar-guard line to match)",
        "verifierstate": "top1_line 0/3",
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
        "lab_reject": "1/7 (nocheck); 6 ACCEPT controls",
        "sourcecomment": (
            "nocheck top1_line hit (construction-determined); rename boundary is an "
            "exhaustive 4x8 enumeration, not a rate"
        ),
        "verifierstate": "nocheck top1_line miss; n/a on ACCEPT controls",
    },
    "PacketBounds": {
        "template_cases": ["PB-pad0", "PB-pad8", "PB-pad32"],
        "lab_reject": "3/3",
        "sourcecomment": "top1_line 3/3 (construction-determined)",
        "verifierstate": "top1_line 0/3",
    },
}
FAMILIES = ("PointerProvenance", "ScalarRange", "NullablePointer", "PacketBounds")


def check_template_evidence() -> None:
    """Fail if the per-family literals above drift from results/sc_vs_honesty.json.

    The literals are prose for the paper; the freshness guard alone cannot see
    them go stale because the emitter and the committed file share them.
    """
    rows = json.loads((ROOT / "results" / "sc_vs_honesty.json").read_text(encoding="utf-8"))["rows"]

    def fam(ob: str) -> list[dict]:
        return [r for r in rows if r["obligation"] == ob]

    def rej(ob: str) -> list[dict]:
        return [r for r in fam(ob) if r["lab_rejected"]]

    def tally(rs: list[dict], key: str) -> str:
        return f"{sum(1 for r in rs if r[key] is True)}/{len(rs)}"

    nocheck = [r for r in rej("NullablePointer") if "nocheck" in r["case_id"]]
    hit = lambda key: "hit" if nocheck and nocheck[0][key] is True else "miss"  # noqa: E731
    expect = {
        "PointerProvenance": {
            "lab_reject": f"{len(rej('PointerProvenance'))}/{len(fam('PointerProvenance'))}",
            "verifierstate": (
                f"top1_span {tally(rej('PointerProvenance'), 'vs_top1_span')}, "
                f"top1_line {tally(rej('PointerProvenance'), 'vs_top1_line')}"
            ),
        },
        "ScalarRange": {
            "lab_reject": f"{len(rej('ScalarRange'))}/{len(fam('ScalarRange'))}",
            "sourcecomment": f"top1_line {tally(rej('ScalarRange'), 'sc_top1_line')}",
            "verifierstate": f"top1_line {tally(rej('ScalarRange'), 'vs_top1_line')}",
        },
        "NullablePointer": {
            "lab_reject": (
                f"{len(rej('NullablePointer'))}/{len(fam('NullablePointer'))} (nocheck); "
                f"{len(fam('NullablePointer')) - len(rej('NullablePointer'))} ACCEPT"
            ),
            "sourcecomment": f"nocheck top1_line {hit('sc_top1_line')}",
            "verifierstate": f"nocheck top1_line {hit('vs_top1_line')}",
        },
        "PacketBounds": {
            "lab_reject": f"{len(rej('PacketBounds'))}/{len(fam('PacketBounds'))}",
            "sourcecomment": f"top1_line {tally(rej('PacketBounds'), 'sc_top1_line')}",
            "verifierstate": f"top1_line {tally(rej('PacketBounds'), 'vs_top1_line')}",
        },
    }
    for ob, fields in expect.items():
        te = TEMPLATE_EVIDENCE[ob]
        if sorted(te["template_cases"]) != sorted(r["case_id"] for r in fam(ob)):
            raise SystemExit(f"TEMPLATE_EVIDENCE[{ob}] case list differs from sc_vs_honesty.json")
        for key, want in fields.items():
            if want not in te[key]:
                raise SystemExit(
                    f"TEMPLATE_EVIDENCE[{ob}][{key}] = {te[key]!r} no longer states {want!r}"
                )


def main() -> None:
    check_template_evidence()
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    diag = {
        c["upstream_case_id"]: c
        for c in json.loads(DIAG.read_text(encoding="utf-8"))["cases"]
    }
    cases = man["cases"]
    counts = Counter(c["keyword_label"] for c in cases)

    rows = []
    for i, c in enumerate(cases, 1):
        cid = c["upstream_case_id"]
        buggy = ROOT / c["local_path"] / "buggy.bpf.c"
        err = diag[cid]["error_id"]
        rows.append(
            {
                "depth_index": i,
                "upstream_case_id": cid,
                "keyword_label": c["keyword_label"],
                "upstream_error_id": err,
                "upstream_obligation": UPSTREAM_ERROR_OBLIGATION[err],
                "upstream_commit": c["upstream_commit"],
                "has_buggy": buggy.is_file(),
                "buggy_bytes": buggy.stat().st_size if buggy.is_file() else 0,
                "local_path": c["local_path"],
            }
        )
    agree = sum(1 for r in rows if r["keyword_label"] == r["upstream_obligation"])

    OUT_JSON.write_text(
        json.dumps(
            {
                "campaign_label": man.get("campaign_label", "20260728"),
                "selection_method": (
                    "stratified on case-name keyword labels (per=6; ScalarRange pool=3)"
                ),
                "upstream_commit": man["upstream_commit"],
                "n": len(rows),
                "keyword_label_counts": dict(counts),
                "keyword_label_agreement_with_upstream": agree,
                "scored": False,
                "template_evidence_by_family": TEMPLATE_EVIDENCE,
                "rows": rows,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# Depth-21 stratified selection (campaign `20260728`)",
        "",
        f"Upstream pin: `eunomia-bpf/bpfix` @ `{man['upstream_commit']}`",
        "Selection: stratified on case-name keyword labels (target 6 per label; "
        "ScalarRange pool only 3), **n=21**.",
        "Sources: sparse-fetched under `fixtures/upstream/bpfix-bench-cases/<id>/`.",
        "",
        "**These cases are not scored.** They are a curated target for later per-case work.",
        "",
        "## Keyword-label counts",
        "",
        "| Keyword label | n |",
        "| --- | ---: |",
    ]
    for ob in FAMILIES:
        lines.append(f"| {ob} | {counts.get(ob, 0)} |")
    lines += [
        f"| **Total** | **{len(rows)}** |",
        "",
        f"Keyword labels agree with upstream's own obligation on **{agree}/{len(rows)}** "
        "of these cases (see `upstream_obligations.md` for all 75).",
        "",
        "## Selection table",
        "",
        "| # | upstream_case_id | Keyword label | Upstream obligation (error ID) | buggy.bpf.c |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['depth_index']} | `{r['upstream_case_id']}` | {r['keyword_label']} | "
            f"{r['upstream_obligation']} ({r['upstream_error_id']}) | "
            f"{'yes' if r['has_buggy'] else 'no'} ({r['buggy_bytes']} B) |"
        )
    lines += [
        "",
        "## Template evidence by family",
        "",
        "Results on the hand-authored templates (paper Section 3.2), listed per family for "
        "orientation. They are not measurements on the upstream cases above.",
        "",
        "| Family | Lab reject | SourceComment | VerifierState |",
        "| --- | --- | --- | --- |",
    ]
    for ob in FAMILIES:
        te = TEMPLATE_EVIDENCE[ob]
        lines.append(
            f"| {ob} | {te['lab_reject']} | {te['sourcecomment']} | {te['verifierstate']} |"
        )
    lines += [
        "",
        "Manifest: `fixtures/upstream/depth21_manifest.json`",
        f"Artifacts: `{OUT_MD.relative_to(ROOT).as_posix()}` · `{OUT_JSON.relative_to(ROOT).as_posix()}`",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_MD.relative_to(ROOT)} n={len(rows)} agreement={agree}/{len(rows)}")


if __name__ == "__main__":
    main()

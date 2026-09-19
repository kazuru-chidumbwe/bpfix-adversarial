#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Emit upstream's own obligation classification of the main75 split.

Each main75 case ships upstream bpfix's diagnostic.txt; its error ID maps to
the ProofObligation that upstream classifier.rs declares for that ID
(bpfix_adversarial.upstream_corpus.UPSTREAM_ERROR_OBLIGATION). Reports how
many cases fall in the four families the harness templates, and how the
case-name keyword labels used to stratify depth-21 compare.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION  # noqa: E402

DIAG = ROOT / "fixtures" / "upstream" / "main75_upstream_diagnostics.json"
INDEX = ROOT / "fixtures" / "upstream" / "main75_case_index.json"
OUT_JSON = ROOT / "results" / "upstream_obligations.json"
OUT_MD = ROOT / "results" / "upstream_obligations.md"
TEMPLATED = ("NullablePointer", "PacketBounds", "PointerProvenance", "ScalarRange")


def main() -> None:
    diag = json.loads(DIAG.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    keyword = {c["upstream_case_id"]: c["keyword_label"] for c in index["cases"]}

    rows = []
    for c in diag["cases"]:
        cid = c["upstream_case_id"]
        rows.append(
            {
                "upstream_case_id": cid,
                "error_id": c["error_id"],
                "upstream_obligation": UPSTREAM_ERROR_OBLIGATION[c["error_id"]],
                "keyword_label": keyword[cid],
            }
        )
    if {r["upstream_case_id"] for r in rows} != set(keyword):
        raise SystemExit("main75 case sets differ between diagnostics and index")

    n = len(rows)
    by_ob = Counter(r["upstream_obligation"] for r in rows)
    templated = sum(by_ob[o] for o in TEMPLATED)
    agree = sum(1 for r in rows if r["upstream_obligation"] == r["keyword_label"])
    confusion = Counter((r["keyword_label"], r["upstream_obligation"]) for r in rows)

    payload = {
        "upstream_commit": diag["upstream_commit"],
        "method": (
            "error ID from each case's upstream diagnostic.txt, mapped to the "
            "ProofObligation upstream classifier.rs declares for that ID"
        ),
        "n": n,
        "by_upstream_obligation": dict(sorted(by_ob.items(), key=lambda kv: (-kv[1], kv[0]))),
        "templated_families": list(TEMPLATED),
        "templated_family_cases": templated,
        "keyword_label_agreement": agree,
        "keyword_vs_upstream": [
            {"keyword_label": k, "upstream_obligation": u, "n": v}
            for (k, u), v in sorted(confusion.items())
        ],
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# Upstream obligation classification of main75",
        "",
        f"Upstream bpfix `{diag['upstream_commit'][:12]}`: error ID in each case's "
        "committed `diagnostic.txt`, mapped to the ProofObligation that upstream "
        "`classifier.rs` declares for it.",
        "",
        "| Upstream obligation | Cases | Templated here |",
        "| --- | ---: | --- |",
    ]
    for ob, k in payload["by_upstream_obligation"].items():
        lines.append(f"| {ob} | {k} | {'yes' if ob in TEMPLATED else 'no'} |")
    lines += [
        f"| **Total** | **{n}** | |",
        "",
        f"The four templated families account for **{templated}/{n}** cases. "
        "This is label coverage, not a behavioral sample; the main75 programs are not scored.",
        "",
        f"Case-name keyword labels (`keyword_label`, used only to stratify the depth-21 "
        f"selection) agree with upstream on **{agree}/{n}** cases.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(f"templated={templated}/{n} keyword_agreement={agree}/{n}")


if __name__ == "__main__":
    main()

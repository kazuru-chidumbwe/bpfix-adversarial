#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus batch 3: the single phrase `verifier` over the batch-1 and batch-2 sources.

Implements the 27 Oct 2026 "Batch 3" entry of "Changes after the freeze" in
docs/WILD-CORPUS-PROTOCOL.md. Everything after the search (pass 1, review dump,
build) is batch 2's code with batch-3 files under fixtures/wild/batch3/.

Usage: python3 tools/wild_batch3.py {collect,files,review,build} [--max-candidates N]
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import wild_batch2 as b2  # noqa: E402
from tools import wild_collect_candidates as wc  # noqa: E402

B3 = ROOT / "fixtures" / "wild" / "batch3"
PHRASE = "verifier"
SEED = 20261028
RANK_BASE = 2000

b2.CANDS, b2.FILES, b2.REVIEW, b2.OUT = B3 / "candidates.json", B3 / "screen_files.jsonl", B3 / "review", B3 / "build.jsonl"
b2.BATCH = 3
b2.PRIOR_BUILDS = [ROOT / "fixtures" / "wild" / "batch2" / "build.jsonl"]


def sources() -> list[str]:
    return list(wc.REPOS) + b2.repos()


def screened_before() -> set[str]:
    seen = set()
    for f in (ROOT / "fixtures/wild/candidates.json", ROOT / "fixtures/wild/batch2/candidates.json"):
        seen |= {c["commit"] for c in json.loads(f.read_text(encoding="utf-8"))["candidates"]}
    return seen


def collect() -> int:
    before = screened_before()
    by_commit: dict[str, dict] = {}
    dropped = 0
    srcs = sources()
    for repo in srcs:
        for it in b2.search(repo, PHRASE):
            if it["sha"] in before:
                dropped += 1
                continue
            by_commit.setdefault(it["sha"], {
                "repo": repo, "commit": it["sha"], "parents": [p["sha"] for p in it.get("parents", [])],
                "title": it["commit"]["message"].split("\n", 1)[0],
                "committer_date": it["commit"]["committer"]["date"], "html_url": it["html_url"], "matched": [PHRASE]})
        print(f"{repo:50s} total={len(by_commit)}", flush=True)
    rows = sorted(by_commit.values(), key=lambda r: (r["repo"], r["commit"]))
    order = [r["commit"] for r in rows]
    random.Random(SEED).shuffle(order)
    rank = {c: RANK_BASE + i for i, c in enumerate(order)}
    for r in rows:
        r["screen_rank"] = rank[r["commit"]]
    rows.sort(key=lambda r: r["screen_rank"])
    B3.mkdir(parents=True, exist_ok=True)
    b2.CANDS.write_text(json.dumps({"protocol": "docs/WILD-CORPUS-PROTOCOL.md (batch 3)", "window": b2.WINDOW, "seed": SEED,
                                    "rank_base": RANK_BASE, "repos": srcs, "phrases": [PHRASE],
                                    "dropped_already_screened": dropped, "n": len(rows), "candidates": rows},
                                   indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {b2.CANDS} n={len(rows)} dropped_already_screened={dropped}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("collect", "files", "review", "build"):
        print(__doc__)
        return 2
    if argv[0] == "collect":
        return collect()
    return b2.main(argv)


if __name__ == "__main__":
    sys.exit(main())

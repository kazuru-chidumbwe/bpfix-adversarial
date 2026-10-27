#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus batch 1, rebuilt with the final build step (pass 5).

Implements the 27 Oct 2026 "Pass 5" entry of "Changes after the freeze" in
docs/WILD-CORPUS-PROTOCOL.md: every pass-2 survivor of batch 1, built, loaded and
decided by exactly the driver batches 2 and 3 use (pass 4 plus batch-2 items 8 to
10), with batch 1's project-build recipe for cilium and tetragon. Rows go to
fixtures/wild/pass5.jsonl and replace the pass-3 and pass-4 rows.

Usage: python3 tools/wild_batch1_rebuild.py build [--ranks 111]
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import wild_batch2 as b2  # noqa: E402
from tools import wild_pass3 as p3  # noqa: E402

WILD = ROOT / "fixtures" / "wild"


def pass2_survivors() -> set[int]:
    return {int(r["rank"]) for r in csv.DictReader((WILD / "pass2_decisions.tsv").open(encoding="utf-8"), delimiter="\t")
            if r["decision"] == "pass"}


b2.CANDS, b2.FILES, b2.OUT = WILD / "candidates.json", WILD / "screen_files.jsonl", WILD / "pass5.jsonl"
b2.BATCH = 1
b2.MAKE_BPF = set(p3.MAKE_BPF)
b2.STOP_RULE = False
b2.TODO = pass2_survivors

if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv or argv[0] != "build":
        print(__doc__)
        sys.exit(2)
    sys.exit(b2.build(argv[1:]))

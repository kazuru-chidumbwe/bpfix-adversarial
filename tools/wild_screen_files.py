#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus, screening pass 1 (docs/WILD-CORPUS-PROTOCOL.md, inclusion 1 / E2).

For each candidate in fixtures/wild/candidates.json, in screening order, fetch
the commit's changed files (``gh api``) and record whether it changes BPF C:
a ``*.bpf.c``/``*.bpf.h`` file, or a ``.c``/``.h`` file under a path segment
named ``bpf``, ``ebpf``, ``bpf_prog``, ``kern`` or ``probe(s)``, or a file
whose name ends in ``_kern.c``. Commits that change none are E2. This pass
only reads file lists; no candidate is built or scored.

Writes fixtures/wild/screen_files.jsonl (one row per candidate).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDS = ROOT / "fixtures" / "wild" / "candidates.json"
OUT = ROOT / "fixtures" / "wild" / "screen_files.jsonl"
BPF_DIR = re.compile(r"(^|/)(bpf|ebpf|bpf_prog|kern|probe|probes)(/|$)", re.I)


def is_bpf_c(path: str) -> bool:
    p = path.lower()
    if p.endswith((".bpf.c", ".bpf.h", "_kern.c")):
        return True
    return p.endswith((".c", ".h")) and bool(BPF_DIR.search(p.rsplit("/", 1)[0] if "/" in p else ""))


def files_of(repo: str, sha: str) -> list[dict]:
    for attempt in range(5):
        p = subprocess.run(["gh", "api", f"repos/{repo}/commits/{sha}", "--jq",
                            "[.files[] | {filename, status, additions, deletions}]"],
                           capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0:
            return json.loads(p.stdout or "[]")
        if "rate limit" in (p.stdout + p.stderr).lower():
            time.sleep(60)
            continue
        raise RuntimeError(f"{repo}@{sha}: {p.stderr.strip()}")
    raise RuntimeError(f"{repo}@{sha}: rate limit not cleared")


def main() -> int:
    cands = json.loads(CANDS.read_text(encoding="utf-8"))["candidates"]
    done = set()
    if OUT.is_file():
        done = {json.loads(ln)["commit"] for ln in OUT.read_text(encoding="utf-8").splitlines() if ln.strip()}
    with OUT.open("a", encoding="utf-8", newline="\n") as f:
        for c in cands:
            if c["commit"] in done:
                continue
            files = files_of(c["repo"], c["commit"])
            bpf = [x["filename"] for x in files if is_bpf_c(x["filename"])]
            row = {"screen_rank": c["screen_rank"], "repo": c["repo"], "commit": c["commit"],
                   "n_files": len(files), "bpf_c_files": bpf,
                   "pass1": "bpf-c" if bpf else "E2-no-bpf-c"}
            f.write(json.dumps(row) + "\n")
            f.flush()
            time.sleep(0.3)
    rows = [json.loads(ln) for ln in OUT.read_text(encoding="utf-8").splitlines() if ln.strip()]
    print(f"screened {len(rows)}; bpf-c {sum(r['pass1'] == 'bpf-c' for r in rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

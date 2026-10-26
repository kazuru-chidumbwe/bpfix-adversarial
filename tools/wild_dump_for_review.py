#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus, screening pass 2 input: commit message and BPF C diff per candidate.

For candidates that passed pass 1 (fixtures/wild/screen_files.jsonl), in
screening order, writes one text file per candidate under
``fixtures/wild/review/<rank>-<repo>-<sha8>.txt`` holding the full commit
message and the patch of its BPF C files only. Pass 2 (E1 and inclusion 4 of
docs/WILD-CORPUS-PROTOCOL.md) is decided from these files.

Usage: python tools/wild_dump_for_review.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PASS1 = ROOT / "fixtures" / "wild" / "screen_files.jsonl"
OUT = ROOT / "fixtures" / "wild" / "review"
MAX_PATCH = 12000


def gh(path: str, jq: str) -> str:
    for _ in range(5):
        p = subprocess.run(["gh", "api", path, "--jq", jq], capture_output=True, text=True, encoding="utf-8")
        if p.returncode == 0:
            return p.stdout
        if "rate limit" in (p.stdout + p.stderr).lower():
            time.sleep(60)
            continue
        raise RuntimeError(p.stderr.strip())
    raise RuntimeError("rate limit not cleared")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args(argv)
    rows = [json.loads(ln) for ln in PASS1.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows = sorted((r for r in rows if r["pass1"] == "bpf-c"), key=lambda r: r["screen_rank"])
    if args.limit:
        rows = rows[: args.limit]
    OUT.mkdir(parents=True, exist_ok=True)
    for r in rows:
        name = f"{r['screen_rank']:03d}-{r['repo'].replace('/', '_')}-{r['commit'][:8]}.txt"
        dest = OUT / name
        if dest.exists():
            continue
        msg = gh(f"repos/{r['repo']}/commits/{r['commit']}", ".commit.message")
        files = json.loads(gh(f"repos/{r['repo']}/commits/{r['commit']}", "[.files[] | {filename, patch}]"))
        parts = [f"repo: {r['repo']}", f"commit: {r['commit']}", f"rank: {r['screen_rank']}", "", msg.strip(), ""]
        for f in files:
            if f["filename"] in r["bpf_c_files"]:
                patch = f.get("patch") or "(no patch: binary or too large)"
                parts += [f"--- {f['filename']}", patch[:MAX_PATCH] + ("\n[truncated]" if len(patch) > MAX_PATCH else ""), ""]
        dest.write_text("\n".join(parts) + "\n", encoding="utf-8", newline="\n")
        time.sleep(0.3)
    print(f"wrote {len(list(OUT.glob('*.txt')))} review files")
    return 0


if __name__ == "__main__":
    sys.exit(main())

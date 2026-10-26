#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Collect wild-corpus candidates by the frozen search in docs/WILD-CORPUS-PROTOCOL.md.

Runs GitHub commit search (via the ``gh`` CLI, so the caller's auth and rate
limit apply) for every repository x phrase pair, de-duplicates by commit, and
writes ``fixtures/wild/candidates.json`` with the seeded screening order.

Usage: python tools/wild_collect_candidates.py [--out fixtures/wild/candidates.json]
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "fixtures" / "wild" / "candidates.json"
CUTOFF = "2026-10-26"
SEED = 20261026

REPOS = (
    "iovisor/bcc", "cilium/cilium", "cilium/tetragon", "cilium/pwru",
    "cilium/ebpf", "falcosecurity/libs", "aquasecurity/tracee",
    "inspektor-gadget/inspektor-gadget", "facebookincubator/katran",
    "parca-dev/parca-agent", "open-telemetry/opentelemetry-ebpf-profiler",
    "netobserv/netobserv-ebpf-agent", "elastic/ebpf", "kubearmor/KubeArmor",
    "libbpf/libbpf-bootstrap", "DataDog/datadog-agent",
)

PHRASES = (
    "verifier error", "verifier reject", "verifier fail", "fix verifier",
    "make verifier happy", "please the verifier", "satisfy the verifier",
    "invalid mem access", "invalid access to packet", "unbounded memory access",
    "min value is negative", "math between", "!read_ok", "unreleased reference",
    "R1 type=", "R2 type=", "expected=map_ptr", "fails to load",
)


def search(repo: str, phrase: str) -> list[dict]:
    q = f'"{phrase}" repo:{repo} committer-date:<{CUTOFF}'
    items: list[dict] = []
    for page in range(1, 11):  # search API caps at 1000 results
        cmd = ["gh", "api", "-X", "GET", "search/commits", "-f", f"q={q}",
               "-f", "per_page=100", "-f", f"page={page}"]
        for attempt in range(5):
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if res.returncode == 0:
                break
            if "rate limit" in (res.stdout + res.stderr).lower():
                time.sleep(65)
                continue
            raise RuntimeError(f"gh failed for {q!r}: {res.stderr.strip()}")
        else:
            raise RuntimeError(f"rate limit not cleared for {q!r}")
        data = json.loads(res.stdout)
        batch = data.get("items", [])
        items.extend(batch)
        time.sleep(2.1)  # stay under 30 search requests per minute
        if len(batch) < 100:
            break
    return items


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args(argv)

    by_commit: dict[str, dict] = {}
    for repo in REPOS:
        for phrase in PHRASES:
            for it in search(repo, phrase):
                sha = it["sha"]
                row = by_commit.setdefault(sha, {
                    "repo": repo,
                    "commit": sha,
                    "parents": [p["sha"] for p in it.get("parents", [])],
                    "title": it["commit"]["message"].split("\n", 1)[0],
                    "committer_date": it["commit"]["committer"]["date"],
                    "html_url": it["html_url"],
                    "matched": [],
                })
                if phrase not in row["matched"]:
                    row["matched"].append(phrase)
            print(f"{repo:45s} {phrase!r:28s} total={len(by_commit)}", flush=True)

    rows = sorted(by_commit.values(), key=lambda r: (r["repo"], r["commit"]))
    order = [r["commit"] for r in rows]
    random.Random(SEED).shuffle(order)
    rank = {c: i for i, c in enumerate(order)}
    for r in rows:
        r["screen_rank"] = rank[r["commit"]]
    rows.sort(key=lambda r: r["screen_rank"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "protocol": "docs/WILD-CORPUS-PROTOCOL.md",
        "cutoff": CUTOFF,
        "seed": SEED,
        "repos": list(REPOS),
        "phrases": list(PHRASES),
        "n": len(rows),
        "candidates": rows,
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {args.out} n={len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

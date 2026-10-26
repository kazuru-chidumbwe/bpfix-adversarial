#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Replay every captured verifier log in a capture directory through upstream bpfix.

Reads the newest ``manifest.<stamp>.jsonl`` in ``--captured`` (written by
tools/capture_local.py), runs ``bpfix <log>`` for each REJECT row and writes
``<case>.<stamp>.bpfix.txt`` next to the log. Provenance goes to
``bpfix.<stamp>.json``: ``bpfix --version``, the git commit of the source tree
the binary was built from (``--bpfix-src``), whether that equals the pin, and
the binary's SHA-256. A version string alone (``bpfix 0.1.9``) does not
identify a commit.

bpfix reads log text only, so this can run on any Linux host.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial import UPSTREAM_BPFIX  # noqa: E402


def newest_manifest(captured: Path) -> Path:
    ms = sorted(captured.glob("manifest.*.jsonl"))
    if not ms:
        raise SystemExit(f"no manifest.*.jsonl in {captured}")
    return ms[-1]


def git_head(src: Path | None) -> str | None:
    if src is None:
        return None
    p = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    return p.stdout.strip() or None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--captured", type=Path, required=True)
    ap.add_argument("--bpfix", type=Path, required=True, help="path to the bpfix binary")
    ap.add_argument("--bpfix-src", type=Path, default=None, help="bpfix source checkout the binary was built from")
    ap.add_argument("--allow-unpinned", action="store_true", help="do not fail when the source commit differs from the pin")
    args = ap.parse_args(argv)

    captured = args.captured if args.captured.is_absolute() else ROOT / args.captured
    manifest = newest_manifest(captured)
    stamp = manifest.name.split(".")[1]
    rows = [json.loads(ln) for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]

    version = subprocess.run([str(args.bpfix), "--version"], capture_output=True, text=True, check=False).stdout.strip()
    commit = git_head(args.bpfix_src)
    pinned = commit == UPSTREAM_BPFIX["commit"]
    if commit is not None and not pinned and not args.allow_unpinned:
        raise SystemExit(f"bpfix source is at {commit}, pin is {UPSTREAM_BPFIX['commit']} (use --allow-unpinned)")
    prov = {
        "bpfix_version": version,
        "bpfix_source_commit": commit,
        "bpfix_pin": UPSTREAM_BPFIX["commit"],
        "source_commit_matches_pin": pinned if commit else None,
        "bpfix_binary_sha256": hashlib.sha256(args.bpfix.read_bytes()).hexdigest(),
        "manifest": manifest.name,
    }
    n = 0
    for r in rows:
        if r.get("verdict") != "REJECT":
            continue
        log = ROOT / r["log"] if not Path(r["log"]).is_absolute() else Path(r["log"])
        if not log.is_file():
            log = captured / Path(r["log"]).name
        out = captured / f"{r['case_id']}.{stamp}.bpfix.txt"
        p = subprocess.run([str(args.bpfix), str(log)], capture_output=True, text=True, check=False)
        out.write_text(p.stdout, encoding="utf-8", newline="\n")
        if p.stderr.strip():
            (captured / f"{r['case_id']}.{stamp}.bpfix.err").write_text(p.stderr, encoding="utf-8", newline="\n")
        n += 1
    prov["n_replayed"] = n
    (captured / f"bpfix.{stamp}.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(prov, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

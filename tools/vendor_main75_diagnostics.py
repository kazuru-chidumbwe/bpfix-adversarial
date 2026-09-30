#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Vendor upstream's own diagnostic header for every main75 case at the pin.

Reads a local checkout of eunomia-bpf/bpfix at the pinned commit and writes
fixtures/upstream/main75_upstream_diagnostics.json (error ID and headline from
each case's committed bpfix-bench/cases/<id>/diagnostic.txt, plus a SHA-256 of
that file) and copies crates/bpfix/src/classifier.rs into the source pin.
Needs the upstream checkout, so it is not run in CI; the emitter that consumes
the vendored file is.

Usage: python tools/vendor_main75_diagnostics.py --upstream /path/to/bpfix
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PIN = "81d97e4a528456e0082a77f4fb6edd13fa092b7b"
OUT = ROOT / "fixtures" / "upstream" / "main75_upstream_diagnostics.json"
CLASSIFIER_DEST = ROOT / "fixtures" / "upstream" / "bpfix-source-rs-pin" / "classifier.rs"
HEADER_RE = re.compile(r"^error\[BPFIX-(E\d+)\]:\s*(.*)$")


def sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--upstream", type=Path, required=True)
    args = ap.parse_args()
    up = args.upstream.resolve()

    head = subprocess.run(
        ["git", "-C", str(up), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    if head != PIN:
        raise SystemExit(f"upstream checkout is at {head}, expected pin {PIN}")

    split = up / "bpfix-bench" / "splits" / "main.txt"
    case_ids = [ln.strip() for ln in split.read_text(encoding="utf-8").splitlines() if ln.strip()]
    rows = []
    for cid in case_ids:
        diag = up / "bpfix-bench" / "cases" / cid / "diagnostic.txt"
        first = diag.read_text(encoding="utf-8").splitlines()[0]
        m = HEADER_RE.match(first)
        if not m:
            raise SystemExit(f"{cid}: unexpected diagnostic header {first!r}")
        rows.append(
            {
                "upstream_case_id": cid,
                "error_id": m.group(1),
                "headline": m.group(2),
                "diagnostic_sha256": sha256_lf(diag),
            }
        )

    payload = {
        "upstream_repo": "https://github.com/eunomia-bpf/bpfix",
        "upstream_commit": PIN,
        "split": "bpfix-bench/splits/main.txt",
        "source": "bpfix-bench/cases/<case>/diagnostic.txt (first line: error ID and headline)",
        "n_cases": len(rows),
        "cases": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    shutil.copyfile(up / "crates" / "bpfix" / "src" / "classifier.rs", CLASSIFIER_DEST)
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(rows)} cases)")
    print(f"Copied classifier.rs (sha256 {sha256_lf(CLASSIFIER_DEST)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

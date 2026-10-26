#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Sparse-fetch bpfix-bench depth-21 subset @ pinned commit (no full vendor tree)."""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMIT = "81d97e4a528456e0082a77f4fb6edd13fa092b7b"
SUBSET = ROOT / "fixtures" / "upstream" / "subset_seed.json"
OUT_DIR = ROOT / "fixtures" / "upstream" / "bpfix-bench-cases"
RAW = f"https://raw.githubusercontent.com/eunomia-bpf/bpfix/{COMMIT}/bpfix-bench/cases"
API = f"https://api.github.com/repos/eunomia-bpf/bpfix/contents/bpfix-bench/cases"

FILES = ("buggy.bpf.c", "fixed.bpf.c", "README.md", "diagnostic.txt", "verifier.log")


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "bpfix-adversarial-depth21"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--subset", type=Path, default=SUBSET,
                    help="case list (default: depth-21 seed; fixtures/upstream/main75_case_index.json for all 75)")
    ap.add_argument("--manifest", type=Path, default=ROOT / "fixtures" / "upstream" / "depth21_manifest.json")
    ap.add_argument("--label", default="20260728", help="campaign label written into case_meta.json")
    ap.add_argument("--keep-existing", action="store_true",
                    help="leave cases that already have a case_meta.json untouched")
    args = ap.parse_args()
    subset = json.loads(args.subset.read_text(encoding="utf-8"))
    cases = subset["cases"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cases:
        cid = c["upstream_case_id"]
        ob = c["keyword_label"]
        dest = OUT_DIR / cid
        if args.keep_existing and (dest / "case_meta.json").is_file():
            rows.append(json.loads((dest / "case_meta.json").read_text(encoding="utf-8")))
            print(f"KEEP {cid}")
            continue
        dest.mkdir(parents=True, exist_ok=True)
        got = []
        for name in FILES:
            url = f"{RAW}/{cid}/{name}"
            try:
                data = fetch(url)
            except Exception as e:  # noqa: BLE001
                print(f"MISS {cid}/{name}: {e}")
                continue
            (dest / name).write_bytes(data)
            got.append(name)
        meta = {
            "upstream_case_id": cid,
            "keyword_label": ob,
            "upstream_commit": COMMIT,
            "campaign_label": args.label,
            "selection_method": subset.get("selection_method") or f"full {subset.get('split', 'list')}",
            "files": got,
            "local_path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        }
        (dest / "case_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
        rows.append(meta)
        print(f"OK {cid} ({len(got)} files)")

    manifest = {
        "upstream_commit": COMMIT,
        "campaign_label": args.label,
        "n": len(rows),
        "cases": rows,
    }
    out_m = args.manifest
    out_m.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {out_m} n={len(rows)}")


if __name__ == "__main__":
    main()

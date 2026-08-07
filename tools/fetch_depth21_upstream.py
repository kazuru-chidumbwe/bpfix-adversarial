#!/usr/bin/env python3
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
    subset = json.loads(SUBSET.read_text(encoding="utf-8"))
    cases = subset["cases"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cases:
        cid = c["upstream_case_id"]
        ob = c["upstream_proof_obligation"]
        dest = OUT_DIR / cid
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
            "upstream_proof_obligation": ob,
            "upstream_commit": COMMIT,
            "campaign_label": "20260728",
            "selection_method": subset.get("selection_method"),
            "files": got,
            "local_path": str(dest.relative_to(ROOT)).replace("\\", "/"),
        }
        (dest / "case_meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
        rows.append(meta)
        print(f"OK {cid} ({len(got)} files)")

    manifest = {
        "upstream_commit": COMMIT,
        "campaign_label": "20260728",
        "n": len(rows),
        "cases": rows,
    }
    out_m = ROOT / "fixtures" / "upstream" / "depth21_manifest.json"
    out_m.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_m} n={len(rows)}")


if __name__ == "__main__":
    main()

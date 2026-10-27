#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Replay every included wild case through each registered external reporter.

For each fixtures/wild/cases/<rank>/ this calls the adapter's ``replay(ctx, obj)``
on the stored ``buggy.o`` (the object the kernel rejected, built by pass 3 or 4,
not rebuilt here) and writes the text to ``buggy<suffix>`` next to ``buggy.log``.
Provenance goes to ``fixtures/wild/replay.<reporter>.json``. With ``--bpfix``, the
pinned bpfix binary is also run on ``buggy.log`` (it reads the log only), writing
``buggy.bpfix.txt`` and ``fixtures/wild/replay.bpfix.json``. Runs on the lab host,
where the reporters are installed; the scorers then read the outputs offline.

Usage: python3 tools/wild_replay.py [--reporter PREVAIL] [--bpfix BIN --bpfix-src DIR]
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
from bpfix_adversarial.reporters import CaseContext, registry  # noqa: E402

CASES = ROOT / "fixtures" / "wild" / "cases"


def case_source(d: Path, meta: dict) -> Path:
    """The parent version of the changed file the failing object was compiled from."""
    src_name = meta["object"].split("::")[0]
    for rel in meta["changed_files"]:
        if Path(rel).name == src_name and (d / "parent" / rel).is_file():
            return d / "parent" / rel
    return d / "parent" / meta["changed_files"][0]


def replay_bpfix(binary: Path, src: Path | None) -> None:
    commit = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], capture_output=True, text=True,
                            check=False).stdout.strip() if src else None
    if commit != UPSTREAM_BPFIX["commit"]:
        raise SystemExit(f"bpfix source is at {commit}, pin is {UPSTREAM_BPFIX['commit']}")
    done = []
    for d in sorted(p for p in CASES.iterdir() if (p / "buggy.log").is_file()):
        out = subprocess.run([str(binary), str(d / "buggy.log")], capture_output=True, text=True, check=False)
        (d / "buggy.bpfix.txt").write_text(out.stdout, encoding="utf-8", newline="\n")
        done.append(d.name)
    prov = {"reporter": "bpfix",
            "bpfix_version": subprocess.run([str(binary), "--version"], capture_output=True, text=True,
                                            check=False).stdout.strip(),
            "bpfix_source_commit": commit, "bpfix_binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
            "cases": done}
    (CASES.parent / "replay.bpfix.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(prov))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reporter", action="append", default=None)
    ap.add_argument("--bpfix", type=Path, default=None, help="pinned bpfix binary")
    ap.add_argument("--bpfix-src", type=Path, default=None, help="source checkout it was built from")
    args = ap.parse_args(argv)
    if args.bpfix:
        replay_bpfix(args.bpfix, args.bpfix_src)
    reps = registry()
    names = args.reporter or sorted(n for n, r in reps.items() if r.needs_artifact and hasattr(r, "replay"))
    for name in names:
        rep = reps[name]
        done, missing = [], []
        for d in sorted(p for p in CASES.iterdir() if (p / "meta.json").is_file()):
            meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
            obj = d / "buggy.o"
            if not obj.is_file():
                missing.append(d.name)
                continue
            text = rep.replay(CaseContext(d.name, case_source(d, meta), d / "buggy.log"), obj)
            (d / f"buggy{rep.needs_artifact}").write_text(text, encoding="utf-8", newline="\n")
            done.append(d.name)
        prov = {"reporter": rep.name, **rep.provenance(), "cases": done, "missing_object": missing}
        (CASES.parent / f"replay.{rep.name}.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8",
                                                              newline="\n")
        print(json.dumps(prov))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

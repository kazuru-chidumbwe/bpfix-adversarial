#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Replay a capture directory through a registered external reporter.

For every REJECT row of the newest ``manifest.<stamp>.jsonl`` in ``--captured``
(written by tools/capture_local.py), this recompiles the case's object with the
capture's own flags (``capture_local.compile_argv``; same clang, same profile),
calls the adapter's ``replay(ctx, obj)`` and writes the returned text to
``<case>.<stamp><suffix>`` next to the log, where ``<suffix>`` is the
adapter's ``needs_artifact``. Provenance (the adapter's ``provenance()``, the
clang version and the manifest) goes to ``<reporter>.<stamp>.json``.

The scorers then read those files through the registry, offline.

Usage:
  python tools/replay_reporter.py --reporter PrettyVerifier --captured <dir> \
      [--vmlinux-dir .cache/vmlinux-<kernel>]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.reporters import CaseContext, registry  # noqa: E402
from tools.capture_local import compile_argv  # noqa: E402


def newest_manifest(captured: Path) -> Path:
    ms = sorted(captured.glob("manifest.*.jsonl"))
    if not ms:
        raise SystemExit(f"no manifest.*.jsonl in {captured}")
    return ms[-1]


def resolve(p: str, captured: Path) -> Path:
    q = Path(p)
    if q.is_absolute():
        return q
    if (ROOT / q).exists():
        return ROOT / q
    return captured / q.name


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reporter", required=True)
    ap.add_argument("--captured", type=Path, required=True)
    ap.add_argument("--vmlinux-dir", default=None, help="vmlinux.h directory (upstream profile)")
    ap.add_argument("--clang", default="clang")
    args = ap.parse_args(argv)

    rep = registry().get(args.reporter)
    if rep is None or not rep.needs_artifact or not hasattr(rep, "replay"):
        raise SystemExit(f"{args.reporter!r} is not a registered external reporter with replay()")
    captured = args.captured if args.captured.is_absolute() else ROOT / args.captured
    manifest = newest_manifest(captured)
    stamp = manifest.name.split(".")[1]
    rows = [json.loads(ln) for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]

    clang_v = subprocess.run([args.clang, "--version"], capture_output=True, text=True, check=False)
    n = failed = 0
    with tempfile.TemporaryDirectory(prefix="bpfix-replay-") as td:
        for r in rows:
            if r.get("verdict") != "REJECT":
                continue
            src, log = resolve(r["src"], captured), resolve(r["log"], captured)
            obj = Path(td) / f"{r['case_id']}.o"
            cp = subprocess.run(compile_argv(r.get("profile", "template"), src, obj, [args.clang], args.vmlinux_dir),
                                capture_output=True, text=True, check=False)
            out = captured / f"{r['case_id']}.{stamp}{rep.needs_artifact}"
            if cp.returncode != 0:
                out.write_text(f"REPLAY_COMPILE_FAIL\n{cp.stderr}", encoding="utf-8", newline="\n")
                failed += 1
                continue
            text = rep.replay(CaseContext(r["case_id"], src, log), obj)
            out.write_text(text, encoding="utf-8", newline="\n")
            n += 1
    prov = {
        "reporter": rep.name,
        **rep.provenance(),
        "clang": clang_v.stdout.splitlines()[0] if clang_v.stdout else None,
        "manifest": manifest.name,
        "n_replayed": n,
        "n_compile_failed": failed,
    }
    (captured / f"{rep.name}.{stamp}.json").write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(prov, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

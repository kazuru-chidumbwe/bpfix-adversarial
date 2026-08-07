#!/usr/bin/env python3
"""Fail if committed results/*.json drift from a fresh offline emitter run.

Lab / network / Ollama-backed artifacts are listed as SKIP with a reason so every
results/*.json is accounted for (closes the “forgot to recommit” hole).
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Offline emitters: (committed relative path, argv relative to ROOT).
# Order: independent first; dependents of sc_vs_honesty after it.
OFFLINE_EMITTERS: list[tuple[str, list[str]]] = [
    ("results/distance_sweep.json", ["tools/emit_distance_sweep.py"]),
    ("results/np_pair_score.json", ["tools/score_np_pair.py"]),
    ("results/rename_honesty.json", ["tools/emit_rename_table.py"]),
    ("results/tier_disagreement.json", ["tools/emit_tier_table.py"]),
    ("results/four_obligation_matrix.json", ["tools/emit_four_obligation_matrix.py"]),
    ("results/depth21_selection.json", ["tools/emit_depth21_selection.py"]),
    ("results/sc_vs_honesty.json", ["tools/score_sc_vs_honesty.py"]),
    ("results/rq1_lab_distance.json", ["tools/emit_rq1_lab_distance.py"]),
    ("results/baseline_battery.json", ["tools/emit_baseline_battery.py"]),
    ("results/oracle_controls.json", ["tools/emit_oracle_controls.py"]),
    ("results/marker_isolation.json", ["tools/emit_marker_isolation.py"]),
    ("results/rq1_bpfix_cli.json", ["tools/emit_rq1_bpfix_cli.py"]),
]

# Must exist under results/; not re-run in CI (lab / Ollama / capture-only).
SKIP_RESULTS: dict[str, str] = {
    "results/marker_isolation_lab.json": (
        "Ubuntu lab A/B capture (tools/lab_marker_isolation_ab.py); requires SSH host"
    ),
    "results/honesty_utility_rq4.json": (
        "Pinned Ollama separation demonstration (tools/rq4_llm_repair.py); not offline"
    ),
}


def _load(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_canonical(obj: object) -> str:
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


def check_one(rel: str, script_argv: list[str]) -> None:
    path = ROOT / rel
    if not path.is_file():
        raise SystemExit(f"missing committed artifact: {rel}")
    committed = _load(path)
    # Run emitter in a copy of the tree's CWD so it writes the real path, then restore.
    backup = path.read_bytes()
    try:
        cmd = [sys.executable, *script_argv]
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise SystemExit(
                f"emitter failed for {rel}: {' '.join(cmd)}\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )
        fresh = _load(path)
    finally:
        path.write_bytes(backup)

    if committed != fresh:
        # Write a temp diff aid for humans
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "committed.json"
            b = Path(td) / "fresh.json"
            a.write_text(_dump_canonical(committed), encoding="utf-8")
            b.write_text(_dump_canonical(fresh), encoding="utf-8")
        raise SystemExit(
            f"STALE: {rel} does not match fresh run of {' '.join(script_argv)}\n"
            f"Re-run: python {' '.join(script_argv)} && git add {rel}"
        )


def main() -> int:
    covered = {rel for rel, _ in OFFLINE_EMITTERS} | set(SKIP_RESULTS)
    on_disk = {
        f"results/{p.name}"
        for p in (ROOT / "results").glob("*.json")
    }
    missing_registry = sorted(on_disk - covered)
    extra_registry = sorted(covered - on_disk)
    if missing_registry:
        raise SystemExit(
            "results/*.json not in OFFLINE_EMITTERS or SKIP_RESULTS:\n  "
            + "\n  ".join(missing_registry)
        )
    if extra_registry:
        raise SystemExit(
            "registry entries missing on disk:\n  " + "\n  ".join(extra_registry)
        )

    for rel, argv in OFFLINE_EMITTERS:
        check_one(rel, argv)
        print(f"OK fresh: {rel}")

    for rel, reason in sorted(SKIP_RESULTS.items()):
        print(f"SKIP {rel}: {reason}")

    print("All offline results/*.json match their emitters.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

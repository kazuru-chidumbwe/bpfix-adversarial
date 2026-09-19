#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Measure statement+branch coverage across bpfix_adversarial/ and tools/.

Single-command reproduction of the coverage figures quoted in the paper and
cover letter. Requires `pip install coverage` (not a runtime dependency of
the package itself, which stays stdlib-only; `pip install -e ".[dev]"` pulls
it in).

Why this script exists rather than a one-line `coverage run` instruction:
tests/test_results_emitter_fresh.py invokes every emitter via
subprocess.run, and coverage.py does not trace child processes unless the
interpreter is instrumented at startup (see
https://coverage.readthedocs.io/en/latest/subprocess.html). A plain
`coverage run -m unittest discover` under-reports tools/ at 0% and the
total at roughly 14%. coverage.py installs its own startup hook
(a1_coverage.pth) that traces any child process when COVERAGE_PROCESS_START
is set, so this script writes a temporary rcfile and data files at the
repository root, sets that variable for the run, combines the parallel data
files, prints the report, and removes the rcfile and data files on exit.

Usage: python tools/measure_coverage.py
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RCFILE = ROOT / ".coveragerc.measure"
DATA_PREFIX = ".coverage.measure"


def main() -> int:
    try:
        import coverage  # noqa: F401
    except ImportError:
        print(
            "coverage is not installed. Run: pip install coverage "
            '(or: pip install -e ".[dev]")',
            file=sys.stderr,
        )
        return 1

    RCFILE.write_text(
        "[run]\n"
        "parallel = True\n"
        "branch = True\n"
        "source = bpfix_adversarial,tools\n"
        "omit = tools/measure_coverage.py\n"
        f"data_file = {DATA_PREFIX}\n"
        "[report]\n"
        "show_missing = False\n",
        encoding="utf-8",
    )
    def cleanup() -> None:
        RCFILE.unlink(missing_ok=True)
        for f in ROOT.glob(f"{DATA_PREFIX}*"):
            f.unlink(missing_ok=True)

    atexit.register(cleanup)

    for f in ROOT.glob(f"{DATA_PREFIX}*"):
        f.unlink(missing_ok=True)

    env = dict(os.environ)
    env["COVERAGE_PROCESS_START"] = str(RCFILE)

    run = subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "run",
            f"--rcfile={RCFILE}",
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-q",
        ],
        cwd=ROOT,
        env=env,
    )
    subprocess.run(
        [sys.executable, "-m", "coverage", "combine", f"--rcfile={RCFILE}"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    subprocess.run(
        [sys.executable, "-m", "coverage", "report", f"--rcfile={RCFILE}"],
        cwd=ROOT,
        env=env,
        check=True,
    )
    print("\nPackage only (bpfix_adversarial/):", flush=True)
    subprocess.run(
        [
            sys.executable,
            "-m",
            "coverage",
            "report",
            f"--rcfile={RCFILE}",
            "--include=bpfix_adversarial/*",
        ],
        cwd=ROOT,
        env=env,
        check=True,
    )
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())

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
total at roughly 14%. This script wires up the subprocess hook for the
duration of the run only: it writes a `.pth` file into the current
interpreter's site-packages that calls `coverage.process_startup()`, points
`COVERAGE_PROCESS_START` at a throwaway rcfile, runs the suite, combines the
parallel data files, prints the report, and removes both the `.pth` and the
rcfile again on exit. It does not touch this repository's own files.

Usage: python tools/measure_coverage.py
"""

from __future__ import annotations

import atexit
import os
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PTH_NAME = "bpfix_adversarial_coverage_subprocess.pth"
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

    site_dir = Path(sysconfig.get_path("purelib"))
    pth = site_dir / PTH_NAME

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
    pth.write_text(
        "import coverage; coverage.process_startup()\n", encoding="utf-8"
    )

    def cleanup() -> None:
        pth.unlink(missing_ok=True)
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
    return run.returncode


if __name__ == "__main__":
    raise SystemExit(main())

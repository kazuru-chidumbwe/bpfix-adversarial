"""Committed results/*.json must match a fresh offline emitter run.

Extends the narrow src_sha256 guards: every results/*.json is either
re-emitted and compared, or explicitly listed as lab/Ollama SKIP in
tools/check_results_fresh.py (so drift cannot recur unnoticed).
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestResultsEmitterFresh(unittest.TestCase):
    def test_all_offline_results_match_emitters(self) -> None:
        proc = subprocess.run(
            [sys.executable, "tools/check_results_fresh.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            self.fail(
                "results/*.json drifted from emitters (or registry incomplete).\n"
                f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
            )


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
"""Offline unit coverage for bpfix_adversarial.cli entry points."""

from __future__ import annotations

import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from bpfix_adversarial.cli import main

ROOT = Path(__file__).resolve().parents[1]
SYN_LOG = ROOT / "fixtures" / "logs" / "synthetic" / "NP-brittle-pad8.log"


class TestCli(unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, dict]:
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(argv)
        payload = json.loads(buf.getvalue())
        return code, payload

    def test_version(self) -> None:
        code, payload = self._run(["version"])
        self.assertEqual(code, 0)
        self.assertEqual(payload["bpfix_adversarial"], "1.0.1")
        self.assertIn("commit", payload["upstream"])

    def test_heuristics(self) -> None:
        code, payload = self._run(["heuristics", "--text", "if (!tmp)"])
        self.assertEqual(code, 0)
        self.assertEqual(payload["text"], "if (!tmp)")
        self.assertIn("heuristics", payload)

    def test_rename_demo_limit(self) -> None:
        code, payload = self._run(["rename-demo", "--limit", "2"])
        self.assertEqual(code, 0)
        self.assertEqual(len(payload["cases"]), 2)
        self.assertIn("summary", payload)

    def test_analyze_text(self) -> None:
        code, payload = self._run(["analyze", "--text", "if (!ptr)"])
        self.assertEqual(code, 0)
        self.assertIn("heuristics", payload)

    def test_score_log(self) -> None:
        self.assertTrue(SYN_LOG.is_file(), msg=f"missing fixture {SYN_LOG}")
        code, payload = self._run(
            [
                "score-log",
                str(SYN_LOG),
                "--oracle-loss",
                "1",
                "--oracle-reject",
                "1",
            ]
        )
        self.assertEqual(code, 0)
        self.assertIn("reported_loss_line", payload)
        self.assertIn("scores", payload)


if __name__ == "__main__":
    unittest.main()

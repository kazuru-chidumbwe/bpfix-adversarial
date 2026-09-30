# SPDX-License-Identifier: MIT
"""Parsing of rendered upstream bpfix CLI output (tools/emit_rq1_bpfix_cli.py)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "results" / "rq1_bpfix_cli_raw"


def _load():
    spec = importlib.util.spec_from_file_location(
        "emit_rq1_bpfix_cli", ROOT / "tools" / "emit_rq1_bpfix_cli.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class TestCliReplayParse(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load()

    def test_primary_line_with_and_without_column(self) -> None:
        for arrow in ("  --> PB-pad8.c:26", "  --> PB-pad8.c:26:5", "  --> /tmp/x/PB-pad8.c:26:12"):
            with self.subTest(arrow=arrow):
                self.assertEqual(self.mod.parse_raw(arrow + "\n")["primary_src"], 26)

    def test_committed_raw_outputs_parse(self) -> None:
        raws = sorted(RAW.glob("*.txt"))
        raws = [p for p in raws if p.name != "bpfix-version.txt"]
        self.assertEqual(len(raws), 9)
        for p in raws:
            with self.subTest(raw=p.name):
                parsed = self.mod.parse_raw(p.read_text(encoding="utf-8"))
                self.assertIsNotNone(parsed["primary_src"])
                self.assertIsNotNone(parsed["error_id"])


if __name__ == "__main__":
    unittest.main()

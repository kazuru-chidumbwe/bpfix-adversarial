# SPDX-License-Identifier: MIT
"""Pads and renames must not change what the verifier processes on the pin."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPadRenameInvariance(unittest.TestCase):
    def test_committed_inset_is_invariant(self):
        data = json.loads(
            (ROOT / "results" / "pad_rename_invariance.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(data["pad_invariance"]), 3)
        self.assertEqual(len(data["rename_invariance"]), 3)
        for group in data["pad_invariance"] + data["rename_invariance"]:
            self.assertTrue(group["identical"], group)


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
"""The generators reproduce every generated mutant under mutants/ byte-for-byte."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from bpfix_adversarial.gen_nullable import write_nullable_pair
from bpfix_adversarial.gen_obligations import write_obligation_templates

ROOT = Path(__file__).resolve().parents[1]
MUTANTS = ROOT / "mutants"
PADS = (0, 8, 32)


def _lf(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


class TestGenerateMutants(unittest.TestCase):
    def test_generators_reproduce_committed_mutants(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generated: list[Path] = []
            for pad in PADS:
                generated += write_nullable_pair(out / "NullablePointer", pad=pad)
            generated += write_obligation_templates(out, pads=list(PADS))

            self.assertEqual(len(generated), 15)
            for path in generated:
                rel = path.relative_to(out)
                committed = MUTANTS / rel
                self.assertTrue(committed.is_file(), f"no committed mutant for {rel}")
                self.assertEqual(_lf(path), _lf(committed), f"{rel} differs from generator")


if __name__ == "__main__":
    unittest.main()

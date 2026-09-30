#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Captured verifier source maps must agree with the committed mutant sources.

tests/test_capture_provenance.py checks the capture-manifest hashes themselves.
This test checks the property the scores depend on: every `path:LINE` the
verifier printed still names the same source text in the committed mutant.
It covers NP-idiomatic-nocheck, whose capture-time copy was never committed
and so has no matching manifest hash.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURED = ROOT / "fixtures" / "logs" / "captured"
MUTANTS = ROOT / "mutants"
STAMP = "20260801T181331Z"

# "; <source text> @ <file>:<line>"
MAP_RE = re.compile(r"^;\s*(?P<text>.*?)\s+@\s+(?P<file>[\w./-]+\.c):(?P<line>\d+)\s*$")


def mutant_path(name: str) -> Path | None:
    hits = sorted(MUTANTS.rglob(name))
    return hits[0] if hits else None


class TestLogSourceMapMatchesMutant(unittest.TestCase):
    def test_every_source_map_entry_matches_committed_source(self) -> None:
        logs = sorted(CAPTURED.glob(f"*.{STAMP}.log"))
        self.assertTrue(logs, f"no captured logs for stamp {STAMP}")

        checked = 0
        mismatches: list[str] = []
        for log in logs:
            for raw in log.read_text(encoding="utf-8", errors="replace").splitlines():
                m = MAP_RE.match(raw)
                if not m:
                    continue
                src = mutant_path(Path(m.group("file")).name)
                if src is None:
                    mismatches.append(f"{log.name}: no committed mutant {m.group('file')}")
                    continue
                lines = src.read_text(encoding="utf-8").splitlines()
                n = int(m.group("line"))
                if not 1 <= n <= len(lines):
                    mismatches.append(
                        f"{log.name}: {m.group('file')}:{n} out of range "
                        f"(file has {len(lines)} lines)"
                    )
                    continue
                if lines[n - 1].strip() != m.group("text").strip():
                    mismatches.append(
                        f"{log.name}: {m.group('file')}:{n}\n"
                        f"      log:    {m.group('text').strip()!r}\n"
                        f"      source: {lines[n - 1].strip()!r}"
                    )
                    continue
                checked += 1

        self.assertEqual(mismatches, [], "\n".join(mismatches))
        # Guard against the regex silently matching nothing.
        self.assertGreaterEqual(checked, 16, f"only {checked} source-map entries checked")


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
"""The committed mutants must be the bytes the committed logs were captured from.

The 2026-08-01 lab capture compiled a copy of the tree taken from a Windows
checkout, so its manifest hashes the CRLF form of each source. The committed
files are LF (.gitattributes), so the check converts LF -> CRLF before hashing.

NP-idiomatic-nocheck is a hand-written seed whose capture-time copy was never
committed; its manifest hash has never matched any committed revision. It is
listed here so that any other drift fails the test.

The Ubuntu marker A/B (marker_isolation_lab.json) hashed the LF text of the
same files, so every bearing-variant hash there must match directly.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "results" / "env_pins" / "capture-manifest.20260801T181331Z.jsonl"
LAB_AB = ROOT / "results" / "marker_isolation_lab.json"
KNOWN_UNMATCHED = {"NP-idiomatic-nocheck"}


def _lf(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


class TestCaptureProvenance(unittest.TestCase):
    def test_manifest_hashes_match_committed_mutants(self) -> None:
        rows = [json.loads(ln) for ln in MANIFEST.read_text(encoding="utf-8").splitlines() if ln.strip()]
        self.assertEqual(len(rows), 16)
        unmatched = set()
        for row in rows:
            crlf = _lf(ROOT / row["src"]).replace(b"\n", b"\r\n")
            if hashlib.sha256(crlf).hexdigest() != row["src_sha256"]:
                unmatched.add(row["case_id"])
        self.assertEqual(unmatched, KNOWN_UNMATCHED)

    def test_marker_ab_hashes_match_committed_mutants(self) -> None:
        lab = json.loads(LAB_AB.read_text(encoding="utf-8"))
        self.assertEqual(len(lab["pairs"]), 16)
        for pair in lab["pairs"]:
            with self.subTest(case=pair["case_id"]):
                live = hashlib.sha256(_lf(ROOT / pair["src"])).hexdigest()
                self.assertEqual(live, pair["bearing"]["src_sha256"])


if __name__ == "__main__":
    unittest.main()

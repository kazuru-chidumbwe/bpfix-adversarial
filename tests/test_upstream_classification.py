# SPDX-License-Identifier: MIT
"""The error-ID -> obligation map must match the vendored upstream classifier."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path

from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION

ROOT = Path(__file__).resolve().parents[1]
PIN = ROOT / "fixtures" / "upstream" / "bpfix-source-rs-pin"
CLASSIFIER = PIN / "classifier.rs"
CLASSIFIER_SHA256 = "340462545a300d95af4d6b53c1ae8d354e7c0965acf7acbd3a2078df4e0ecb37"


class TestUpstreamClassification(unittest.TestCase):
    def test_vendored_classifier_is_the_pin(self):
        data = CLASSIFIER.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(data).hexdigest(), CLASSIFIER_SHA256)

    def test_map_matches_classifier_declarations(self):
        src = CLASSIFIER.read_text(encoding="utf-8")
        for code, obligation in UPSTREAM_ERROR_OBLIGATION.items():
            pattern = rf'"BPFIX-{code}",\s*ProofObligation::{obligation}\b'
            self.assertRegex(src, pattern, f"{code} -> {obligation} not declared upstream")

    def test_every_main75_case_maps(self):
        diag = json.loads(
            (ROOT / "fixtures" / "upstream" / "main75_upstream_diagnostics.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(diag["n_cases"], 75)
        for c in diag["cases"]:
            self.assertIn(c["error_id"], UPSTREAM_ERROR_OBLIGATION, c["upstream_case_id"])
            self.assertTrue(re.fullmatch(r"[0-9a-f]{64}", c["diagnostic_sha256"]))


if __name__ == "__main__":
    unittest.main()

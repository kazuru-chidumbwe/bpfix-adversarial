# SPDX-License-Identifier: MIT
"""Unit tests: marker extraction, logparse, score, distance."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from bpfix_adversarial.logparse import (
    parse_verifier_log,
    reported_loss_from_events,
    sourcecomment_events,
)
from bpfix_adversarial.oracle import oracle_sites
from bpfix_adversarial.score import score_honesty

ROOT = Path(__file__).resolve().parents[1]


class OracleMarkerTests(unittest.TestCase):
    def test_extracts_markers_and_skips_pads(self) -> None:
        text = "\n".join(
            [
                "int x = 0;",
                "/* ORACLE_LOSS_LINE */",
                "x = 1;",
                "/* distance pad */",
                "__pad0;",
                "/* ORACLE_REJECT_LINE */",
                "return x;",
            ]
        )
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "m.c"
            p.write_text(text + "\n", encoding="utf-8")
            sites = oracle_sites(p)
        self.assertEqual(sites["oracle_loss_marker"], 2)
        self.assertEqual(sites["oracle_reject_marker"], 6)
        self.assertEqual(sites["oracle_loss_code"], 3)
        self.assertEqual(sites["oracle_loss_span"], [3])
        self.assertEqual(sites["oracle_reject_code"], 7)
        self.assertEqual(sites["injection_code"], 3)

    def test_real_mutant_has_markers(self) -> None:
        src = ROOT / "mutants" / "NullablePointer" / "NP-idiomatic-nocheck.c"
        if not src.is_file():
            self.skipTest("mutant fixture missing")
        sites = oracle_sites(src)
        self.assertIsNotNone(sites["oracle_loss_marker"])
        self.assertIsNotNone(sites["oracle_reject_marker"])
        self.assertIsNotNone(sites["oracle_loss_code"])
        self.assertLess(sites["oracle_loss_marker"], sites["oracle_reject_marker"])


class LogParseTests(unittest.TestCase):
    def test_parses_source_at_comments(self) -> None:
        text = "\n".join(
            [
                "0: (bf) r1 = r0",
                "  ; if (!tmp) @ mutants/x.c:12",
                "1: (15) if r1 == 0x0 goto pc+1",
                "R1 invalid mem access",
            ]
        )
        log = parse_verifier_log(text)
        self.assertEqual(len(log.source_locations), 1)
        self.assertEqual(log.source_locations[0].line, 12)
        self.assertIn("invalid", log.terminal_error.lower())

    def test_fixture_log_parses(self) -> None:
        log_path = ROOT / "fixtures" / "logs" / "synthetic" / "NP-brittle-pad8.log"
        if not log_path.is_file():
            self.skipTest("synthetic log missing")
        log = parse_verifier_log(log_path.read_text(encoding="utf-8"))
        self.assertTrue(log.source_locations)
        events = sourcecomment_events(log)
        reported = reported_loss_from_events(events)
        self.assertIsNotNone(reported)


class ScoreDistanceTests(unittest.TestCase):
    def test_top1_hit_zero_distance_error(self) -> None:
        s = score_honesty(
            oracle_loss_code=10, oracle_reject_line=40, reported_loss_line=10
        )
        self.assertTrue(s["top1_loss_match"])
        self.assertEqual(s["distance_true"], 30)
        self.assertEqual(s["distance_error"], 0)

    def test_near_reject_bias_distance_error(self) -> None:
        s = score_honesty(
            oracle_loss_code=10, oracle_reject_line=40, reported_loss_line=39
        )
        self.assertFalse(s["top1_loss_match"])
        self.assertEqual(s["distance_true"], 30)
        self.assertEqual(s["distance_reported"], 1)
        self.assertEqual(s["distance_error"], 29)
        self.assertEqual(s["signed_offset"], 29)

    def test_missing_report(self) -> None:
        s = score_honesty(
            oracle_loss_code=5, oracle_reject_line=15, reported_loss_line=None
        )
        self.assertFalse(s["top1_loss_match"])
        self.assertIsNone(s["distance_error"])


class OracleControlsInsetTests(unittest.TestCase):
    """Minimal Gates construct-validity controls over SoftwareX-stamp captures."""

    @classmethod
    def setUpClass(cls) -> None:
        path = ROOT / "results" / "oracle_controls.json"
        if not path.is_file():
            raise unittest.SkipTest("oracle_controls.json missing — run emit_oracle_controls.py")
        cls.payload = json.loads(path.read_text(encoding="utf-8"))

    def test_negative_control_all_accept_with_markers(self) -> None:
        rows = self.payload["negative_control"]
        self.assertGreaterEqual(len(rows), 6)
        self.assertEqual(self.payload["summary"]["negative_control"]["pass_rate"], 1.0)
        for r in rows:
            self.assertFalse(r["lab_rejected"])
            self.assertIsNotNone(r["oracle_loss_code"])

    def test_positive_control_pb_stop_diverges(self) -> None:
        rows = self.payload["positive_control_pb_stop_vs_injection"]
        self.assertEqual(len(rows), 3)
        self.assertEqual(
            self.payload["summary"]["positive_control_pb_stop_vs_injection"]["pass_rate"],
            1.0,
        )
        for r in rows:
            self.assertTrue(r["stop_diverges_from_injection"])

    def test_compiler_preservation_maps_source_lines(self) -> None:
        rows = self.payload["compiler_preservation_source_map"]
        self.assertEqual(len(rows), 10)
        self.assertEqual(
            self.payload["summary"]["compiler_preservation_source_map"]["pass_rate"],
            1.0,
        )
        for r in rows:
            self.assertTrue(r["pass"])
            self.assertTrue(r["mapped_source_lines"])


class MarkerIsolationTests(unittest.TestCase):
    def test_strip_preserves_line_count_and_removes_tokens(self) -> None:
        from bpfix_adversarial.marker_isolation import strip_oracle_markers

        src = "\n".join(
            [
                "int x;",
                "/* ORACLE_LOSS_LINE */",
                "x = 1;",
                "/* ORACLE_REJECT_LINE */",
                "return x;",
            ]
        )
        neut = strip_oracle_markers(src, preserve_lines=True)
        self.assertNotIn("ORACLE_", neut)
        self.assertEqual(src.count("\n"), neut.count("\n"))
        self.assertIn("x = 1;", neut)

    def test_marker_isolation_inset_lab_ab_passes(self) -> None:
        path = ROOT / "results" / "marker_isolation.json"
        if not path.is_file():
            self.skipTest("marker_isolation.json missing")
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(payload["summary"]["log_input_no_oracle_tokens"]["pass_rate"], 1.0)
        self.assertEqual(
            payload["summary"]["sc_bearing_vs_neutral_identical"]["pass_rate"], 1.0
        )
        lab = payload["summary"]["lab_bearing_vs_neutral_load"]
        self.assertEqual(lab.get("pass_rate"), 1.0)
        self.assertEqual(lab.get("n"), 16)


if __name__ == "__main__":
    unittest.main()

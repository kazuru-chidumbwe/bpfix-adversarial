# SPDX-License-Identifier: MIT
"""Unit tests — stdlib unittest (no pytest required)."""

from __future__ import annotations

import unittest

from bpfix_adversarial.heuristics import (
    looks_like_null_check,
    looks_like_nullable_return,
    looks_like_packet_bounds_check,
)
from bpfix_adversarial.logparse import parse_verifier_log, sourcecomment_events
from bpfix_adversarial.model import ProofEventRole
from bpfix_adversarial.rename_attack import generate_rename_cases, summary
from bpfix_adversarial.score import score_honesty


class HeuristicTests(unittest.TestCase):
    def test_null_check_brittle_names_match(self):
        for name in ("tmp", "val", "ptr", "value"):
            self.assertTrue(looks_like_null_check(f"if (!{name})"))

    def test_null_check_idiomatic_rename_misses(self):
        for name in ("entry", "rec", "slot", "item", "elem"):
            self.assertFalse(looks_like_null_check(f"if (!{name})"))

    def test_structural_null_still_matches(self):
        self.assertTrue(looks_like_null_check("if (entry == NULL)"))
        self.assertTrue(looks_like_null_check("if (entry != 0)"))

    def test_helper_anchored_rename_insensitive(self):
        self.assertTrue(looks_like_nullable_return("x = bpf_map_lookup_elem(&m, &k);"))
        self.assertTrue(looks_like_nullable_return("entry = bpf_map_lookup_elem(&m, &k);"))

    def test_packet_bounds(self):
        self.assertTrue(looks_like_packet_bounds_check("if (data + 14 > data_end)"))
        self.assertFalse(looks_like_packet_bounds_check("if (data + 14 > end)"))

    def test_rename_demo_finds_honesty_breaks(self):
        cases = generate_rename_cases()
        breaks = [c for c in cases if c.honesty_break]
        self.assertEqual(len(breaks), 32)
        self.assertEqual(summary(cases)["break_rate"], 1.0)

    def test_score_honesty(self):
        s = score_honesty(
            oracle_loss_code=10, oracle_reject_line=40, reported_loss_line=10
        )
        self.assertTrue(s["top1_loss_match"])
        self.assertEqual(s["distance_true"], 30)
        self.assertEqual(s["distance_error"], 0)

    def test_fixture_brittle_recognizes_null_check(self):
        from pathlib import Path

        log = parse_verifier_log(
            (Path(__file__).resolve().parents[1] / "fixtures/logs/synthetic/NP-brittle-pad8.log").read_text(
                encoding="utf-8"
            )
        )
        events = sourcecomment_events(log)
        est = [e for e in events if e.role == ProofEventRole.PROOF_ESTABLISHED]
        self.assertTrue(any(e.source and looks_like_null_check(e.source.text) for e in est))

    def test_fixture_idiomatic_misses_null_check(self):
        from pathlib import Path

        log = parse_verifier_log(
            (
                Path(__file__).resolve().parents[1] / "fixtures/logs/synthetic/NP-idiomatic-pad8.log"
            ).read_text(encoding="utf-8")
        )
        for loc in log.source_locations:
            if "if (!entry)" in loc.text:
                self.assertFalse(looks_like_null_check(loc.text))


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
"""Pass-2 exclusions in the wild scorer (docs/WILD-CORPUS-PROTOCOL.md, 29 Oct 2026 entry)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tools import score_wild as sw

HEADER = "rank\tdecision\tcode\tnote\n"


def decisions(text: str) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "pass2_decisions.tsv"
        p.write_text(HEADER + text, encoding="utf-8", newline="\n")
        return sw.pass2_exclusions((p, Path(tmp) / "absent.tsv"))


class Pass2File(unittest.TestCase):
    def test_only_exclude_rows(self):
        p2 = decisions("10\tpass\t\tfine\n11\texclude\tE3\tlater duplicate of 10\n")
        self.assertEqual(p2, {11: {"code": "E3", "note": "later duplicate of 10"}})


class YieldCode(unittest.TestCase):
    p2 = {11: {"code": "E3", "note": "dup"}}

    def test_included_case_excluded_at_pass_2_moves_to_its_code(self):
        self.assertEqual(sw.final_code({"screen_rank": 11, "outcome": "included"}, self.p2), "E3")

    def test_other_cases_keep_the_build_outcome(self):
        self.assertEqual(sw.final_code({"screen_rank": 10, "outcome": "included"}, self.p2), "included")
        self.assertEqual(sw.final_code({"screen_rank": 11, "outcome": "E4"}, self.p2), "E4")

    def test_every_exclusion_code_has_a_yield_column(self):
        self.assertIn("E3", sw.CODES)


class Consistency(unittest.TestCase):
    def test_agreeing_hand_check_and_pass_2(self):
        hand = {10: {"verdict": "ok"}, 11: {"verdict": "E3"}, 12: {"verdict": "artefact"}}
        self.assertEqual(sw.consistency(hand, {11: {"code": "E3", "note": ""}}), [])

    def test_disagreements_are_reported(self):
        self.assertTrue(sw.consistency({11: {"verdict": "E3"}}, {}))
        self.assertTrue(sw.consistency({11: {"verdict": "ok"}}, {11: {"code": "E3", "note": ""}}))
        self.assertTrue(sw.consistency({11: {"verdict": "maybe"}}, {}))


class CommittedCorpus(unittest.TestCase):
    def test_rank_4259_is_e3_and_the_rest_are_scored(self):
        p2 = sw.pass2_exclusions()
        self.assertEqual(p2[4259]["code"], "E3")
        self.assertEqual(sw.consistency(sw.hand_checks(), p2), [])
        y = sw.yields(p2)
        self.assertEqual(y["batch 3"]["outcomes"]["included"], 4)
        self.assertEqual(y["batch 3"]["outcomes"]["E3"], 1)
        self.assertEqual(y["pooled"]["outcomes"]["included"], 5)


if __name__ == "__main__":
    unittest.main()

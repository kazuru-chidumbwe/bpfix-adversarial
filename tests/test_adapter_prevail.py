# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path

from bpfix_adversarial.adapters.prevail import Prevail
from bpfix_adversarial.reporters import CaseContext, registry

FAIL = """PREVAIL exit=1
FAIL: xdp/ringbuf_missing_null

; /lab/cases/x/buggy.bpf.c:35
;     rec->mark = 7;

17: Possible null access (valid_access(r7.offset, width=4) for write)
"""


class TestPrevailAdapter(unittest.TestCase):
    def test_registered(self):
        self.assertIn("PREVAIL", registry())

    def _predict(self, text: str, src_name: str = "buggy.bpf.c"):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "x__buggy.S.log"
            log.write_text("", encoding="utf-8")
            (Path(td) / "x__buggy.S.prevail.txt").write_text(text, encoding="utf-8")
            return Prevail().predict(CaseContext("x", Path(td) / src_name, log))

    def test_parses_failure_location(self):
        p = self._predict(FAIL)
        self.assertEqual(p.primary, 35)
        self.assertEqual(p.note, "PREVAIL FAIL")

    def test_source_text_line_is_not_a_location(self):
        self.assertEqual(self._predict(FAIL).labels, [])

    def test_location_in_other_file_is_ignored(self):
        self.assertIsNone(self._predict(FAIL, "other.bpf.c").primary)

    def test_pass_is_a_miss(self):
        p = self._predict("PREVAIL exit=0\nPASS: xdp/prog\n")
        self.assertIsNone(p.primary)
        self.assertTrue(p.note.startswith("PREVAIL PASS"))


if __name__ == "__main__":
    unittest.main()

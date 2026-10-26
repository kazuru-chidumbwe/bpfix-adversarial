# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path

from bpfix_adversarial.adapters.pretty_verifier import PrettyVerifier, plain_log
from bpfix_adversarial.reporters import CaseContext, registry

CAPTURE = """libbpf: prog 'p': BPF program load failed: Permission denied
libbpf: prog 'p': -- BEGIN PROG LOAD LOG --
35: (62) *(u32 *)(r7 +0) = 7
R7 invalid mem access 'ringbuf_mem_or_null'
verification time 101 usec
stack depth 0
processed 16 insns (limit 1000000) max_states_per_insn 0 total_states 1 peak_states 1 mark_read 1
-- END PROG LOAD LOG --
libbpf: prog 'p': failed to load: -13
"""

OUTPUT = """Prettier Verifier ##
#######################

error: Cannot write into ring buffer pointer to memory not null-checked
   35 | rec->mark = 7; @ buggy.bpf.c:35
      | in file /lab/cases/x/buggy.bpf.c
"""


class TestPrettyVerifierAdapter(unittest.TestCase):
    def test_registered(self):
        self.assertIn("PrettyVerifier", registry())

    def test_plain_log_drops_only_the_two_stats_lines(self):
        out = plain_log(CAPTURE).splitlines()
        self.assertEqual(out[-2], "R7 invalid mem access 'ringbuf_mem_or_null'")
        self.assertTrue(out[-1].startswith("processed 16 insns"))
        self.assertFalse(any(ln.startswith(("verification time", "stack depth", "libbpf")) for ln in out))

    def _predict(self, text: str, src_name: str = "buggy.bpf.c"):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "x__buggy.S.log"
            log.write_text(CAPTURE, encoding="utf-8")
            (Path(td) / "x__buggy.S.prettyverifier.txt").write_text(text, encoding="utf-8")
            return PrettyVerifier().predict(CaseContext("x", Path(td) / src_name, log))

    def test_parses_source_location(self):
        p = self._predict(OUTPUT)
        self.assertEqual((p.primary, p.labels), (35, [35]))

    def test_location_in_other_file_is_ignored(self):
        self.assertIsNone(self._predict(OUTPUT, "other.bpf.c").primary)

    def test_not_managed_is_a_miss(self):
        p = self._predict("Prettier Verifier ##\nerror: Error not managed -> stack depth 0\n")
        self.assertIsNone(p.primary)
        self.assertEqual(p.note, "error not managed")


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
import tempfile
import unittest
from pathlib import Path

from bpfix_adversarial.reporters import BUILTIN, CaseContext, registry


class TestReporterRegistry(unittest.TestCase):
    def test_builtins_registered_once(self):
        reg = registry()
        for rep in BUILTIN:
            self.assertIs(reg[rep.name], rep)
        self.assertEqual(len(reg), len(set(reg)))

    def test_every_reporter_has_the_interface(self):
        for name, rep in registry().items():
            self.assertEqual(rep.name, name)
            self.assertTrue(callable(rep.predict))
            self.assertTrue(rep.needs_artifact is None or rep.needs_artifact.startswith("."))

    def test_artifact_lookup_beside_log(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "case__buggy.20260101T000000Z.log"
            log.write_text("", encoding="utf-8")
            ctx = CaseContext("case", Path(td) / "buggy.bpf.c", log)
            self.assertIsNone(ctx.artifact(".bpfix.txt"))
            out = Path(td) / "case__buggy.20260101T000000Z.bpfix.txt"
            out.write_text("x", encoding="utf-8")
            self.assertEqual(ctx.artifact(".bpfix.txt"), out)

    def test_missing_artifact_is_a_miss_not_an_error(self):
        with tempfile.TemporaryDirectory() as td:
            log = Path(td) / "c.log"
            log.write_text("", encoding="utf-8")
            pred = registry()["bpfix"].predict(CaseContext("c", Path(td) / "c.bpf.c", log))
            self.assertIsNone(pred.primary)


if __name__ == "__main__":
    unittest.main()

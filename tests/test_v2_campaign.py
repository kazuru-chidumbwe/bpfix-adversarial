# SPDX-License-Identifier: MIT
"""Campaign v2: generators, bpfix-output parser, repair-site oracle, log structure."""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from bpfix_adversarial.bpfix_output import parse_bpfix, structure_key
from bpfix_adversarial.gen_v2 import rename_reject_cases, write_v2_mutants
from bpfix_adversarial.logparse import parse_verifier_log, verifier_error_block
from bpfix_adversarial.oracle import oracle_sites
from bpfix_adversarial.repair_site import diff_hunks, mcnemar_exact, repair_sites, wilson

ROOT = Path(__file__).resolve().parents[1]
V2 = ROOT / "campaigns" / "v2"
CAP = ROOT / "fixtures" / "logs" / "captured"
STAMP = "20260801T181331Z"


def _load_tool(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "tools" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _lf(p: Path) -> bytes:
    return p.read_bytes().replace(b"\r\n", b"\n")


class TestV2Generators(unittest.TestCase):
    def test_v2_mutants_match_generator(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            paths = write_v2_mutants(Path(td))
            self.assertEqual(len(paths), 29)
            for p in paths:
                rel = p.relative_to(td)
                committed = V2 / "mutants" / rel
                self.assertTrue(committed.is_file(), rel)
                self.assertEqual(_lf(p), _lf(committed), rel)

    def test_rename_pairs_differ_only_in_identifier(self) -> None:
        pairs: dict[str, list[tuple[str, str]]] = {}
        for case_id, _construct, name, pair in rename_reject_cases():
            pairs.setdefault(pair, []).append((case_id, name))
        for pair, ((a_id, a_name), (b_id, b_name)) in pairs.items():
            with self.subTest(pair=pair):
                a = (V2 / "mutants" / "RenameReject" / f"{a_id}.c").read_text(encoding="utf-8")
                b = (V2 / "mutants" / "RenameReject" / f"{b_id}.c").read_text(encoding="utf-8")
                code = lambda t: [ln for ln in t.splitlines() if not ln.startswith("/* case_id=")]  # noqa: E731
                word = lambda t, n: [re.sub(rf"\b{n}\b", "@", ln) for ln in code(t)]  # noqa: E731
                self.assertEqual(word(a, a_name), word(b, b_name))

    def test_v2_oracle_markers_resolve(self) -> None:
        for src in sorted((V2 / "mutants").rglob("*.c")):
            with self.subTest(src=src.name):
                s = oracle_sites(src)
                self.assertIsNotNone(s["oracle_loss_code"])
                self.assertIsNotNone(s["oracle_reject_code"])
                self.assertLess(s["oracle_loss_code"], s["oracle_reject_code"])

    def test_upstream_variants_match_generator(self) -> None:
        mod = _load_tool("gen_upstream_metamorphic")
        with tempfile.TemporaryDirectory() as td:
            import contextlib
            import io

            with contextlib.redirect_stdout(io.StringIO()):
                mod.main(Path(td))
            gen = sorted(p.relative_to(td) for p in Path(td).rglob("*") if p.is_file())
            committed = sorted(p.relative_to(V2 / "upstream") for p in (V2 / "upstream").rglob("*") if p.is_file())
            self.assertEqual(gen, committed)
            for rel in gen:
                self.assertEqual(_lf(Path(td) / rel), _lf(V2 / "upstream" / rel), rel)

    def test_pad_variants_shift_repair_sites(self) -> None:
        for tf in sorted((V2 / "upstream").glob("*/transform.json")):
            meta = json.loads(tf.read_text(encoding="utf-8"))
            orig = (tf.parent / "orig.bpf.c").read_text(encoding="utf-8").splitlines()
            for v, info in meta["variants"].items():
                if not v.startswith("pad"):
                    continue
                with self.subTest(case=tf.parent.name, variant=v):
                    lines = (tf.parent / f"{v}.bpf.c").read_text(encoding="utf-8").splitlines()
                    k, a = info["shift"], info["shift_from"]
                    self.assertEqual(len(lines), len(orig) + k)
                    self.assertEqual(lines[a - 1 + k], orig[a - 1])  # anchor moved by k
                    for s_orig, s_new in zip(meta["variants"]["orig"]["repair_sites"], info["repair_sites"]):
                        self.assertEqual(orig[s_orig - 1], lines[s_new - 1])

    @unittest.skipUnless(shutil.which("clang") and Path("/usr/include/bpf/bpf_helpers.h").is_file(),
                         "clang with libbpf headers not available")
    def test_v2_mutants_compile(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for src in sorted((V2 / "mutants").rglob("*.c")):
                p = subprocess.run(
                    ["clang", "-O2", "-g", "-target", "bpf", "-idirafter", "/usr/include",
                     f"-I/usr/include/{subprocess.run(['gcc', '-dumpmachine'], capture_output=True, text=True).stdout.strip() or 'x86_64-linux-gnu'}",
                     "-c", str(src), "-o", str(Path(td) / "o.o")],
                    capture_output=True, text=True,
                )
                self.assertEqual(p.returncode, 0, f"{src.name}: {p.stderr}")


class TestBpfixOutput(unittest.TestCase):
    def test_parses_committed_cli_output(self) -> None:
        d = parse_bpfix((ROOT / "results" / "rq1_bpfix_cli_raw" / "PB-pad8.txt").read_text(encoding="utf-8"))
        self.assertEqual(d.error_id, "E001")
        self.assertEqual(d.primary, 26)
        self.assertEqual([(lab.line, lab.kind) for lab in d.labels], [(12, "secondary"), (26, "primary")])
        self.assertEqual(d.next_action, "bounds")

    def test_primary_zero_is_none(self) -> None:
        d = parse_bpfix(
            (ROOT / "fixtures" / "upstream" / "bpfix-bench-cases" / "packet_ihl_udp_undercheck_001" / "diagnostic.txt")
            .read_text(encoding="utf-8")
        )
        self.assertEqual(d.primary_raw, 0)
        self.assertIsNone(d.primary)
        self.assertEqual(d.label_lines, [66])

    def test_log_location_is_not_a_source_line(self) -> None:
        # Kernel 6.8 logs have no "@ file:line", so bpfix points into the log.
        p = next((ROOT / "campaigns" / "main75" / "lab" / "testbed-b-20261029T204226Z" / "buggy")
                 .glob("alu32_pointer_cookie_001__buggy.*.bpfix.txt"))
        d = parse_bpfix(p.read_text(encoding="utf-8"))
        self.assertEqual((d.path, d.primary_raw), ("<verifier-log>", 26))
        self.assertIsNone(d.primary)
        self.assertEqual(d.labels, [])

    def test_structure_key_ignores_source_text(self) -> None:
        a = "error[BPFIX-E002]: x\n  --> a.c:9\n   |\n 5 | if (!ptr)\n   | --- ctx\n"
        b = "error[BPFIX-E002]: x\n  --> b.c:9\n   |\n 5 | if (!entry)\n   | ----- ctx\n"
        self.assertEqual(structure_key(parse_bpfix(a)), structure_key(parse_bpfix(b)))


class TestRepairSite(unittest.TestCase):
    def test_hunks_and_semantic_filter(self) -> None:
        buggy = "int f() {\n  int x = 1;\n  return x;\n}\n"
        fixed = "// header comment\nint f() {\n  int x = 2;\n  if (x) x++;\n  return x;\n}\n"
        hunks = diff_hunks(buggy, fixed)
        self.assertFalse(hunks[0].semantic)  # inserted comment only
        self.assertEqual(repair_sites(hunks), [2])  # `int x = 1;` replaced (+ insertion folded in)

    def test_pure_insertion_marks_both_neighbours(self) -> None:
        hunks = diff_hunks("a;\nb;\nc;\n", "a;\nb;\nif (p) return;\nc;\n")
        self.assertEqual(repair_sites(hunks), [2, 3])

    def test_stats(self) -> None:
        lo, hi = wilson(16, 21)
        self.assertTrue(0.54 < lo < 0.56 and 0.89 < hi < 0.90)
        self.assertIsNone(mcnemar_exact(0, 0))
        self.assertAlmostEqual(mcnemar_exact(0, 6), 0.03125)


class TestVerifierErrorBlock(unittest.TestCase):
    def test_finds_message_by_structure(self) -> None:
        expect = {
            "PB-pad8": "invalid access to packet, off=0 size=8, R1(id=0,off=0,r=1); R1 offset is outside of the packet",
            "SR-pad8": "R1 unbounded memory access, make sure to bounds check any such access",
            "PP-pad8": "math between pkt pointer and register with unbounded min value is not allowed",
            "NP-idiomatic-nocheck": "R0 invalid mem access 'map_value_or_null'",
        }
        for case, msg in expect.items():
            with self.subTest(case=case):
                text = (CAP / f"{case}.{STAMP}.log").read_text(encoding="utf-8")
                self.assertEqual(parse_verifier_log(text).terminal_error, msg)

    def test_accepted_log_has_no_message(self) -> None:
        text = (CAP / f"NP-brittle-pad8.{STAMP}.log").read_text(encoding="utf-8")
        self.assertIsNone(verifier_error_block(text.splitlines()))

    def test_unfamiliar_wording_is_found(self) -> None:
        log = "0: (b7) r0 = 0\n1: (95) exit\nUnreleased reference id=2 alloc_insn=11\nverification time 5 usec\n"
        self.assertEqual(verifier_error_block(log.splitlines()), (2, ["Unreleased reference id=2 alloc_insn=11"]))


class TestCampaignScoresReproduce(unittest.TestCase):
    """The committed campaign v2 scores on the pin must equal a fresh scoring of the committed captures."""

    def test_rescore_pin_run(self) -> None:
        run = V2 / "lab" / "testbed-a-20261026T041232Z"
        committed = json.loads((run / "results" / "v2_scores.json").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as td:
            p = subprocess.run(
                [sys.executable, "tools/score_v2_campaign.py", "--captured", str(run / "templates"),
                 "--upstream-captured", str(run / "upstream"), "--out", td],
                cwd=ROOT, capture_output=True, text=True,
            )
            self.assertEqual(p.returncode, 0, p.stderr)
            fresh = json.loads((Path(td) / "v2_scores.json").read_text(encoding="utf-8"))
        self.assertEqual(fresh, committed)


if __name__ == "__main__":
    unittest.main()

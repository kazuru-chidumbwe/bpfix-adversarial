# SPDX-License-Identifier: MIT
"""Pass 4 retry set and missing-header resolution (docs/WILD-CORPUS-PROTOCOL.md, 27 Oct entry)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import wild_pass4 as p4

ROOT = Path(__file__).resolve().parents[1]


class RetrySet(unittest.TestCase):
    def test_every_e5_and_e4(self):
        rows = [json.loads(ln) for ln in (ROOT / "fixtures/wild/pass3.jsonl").read_text(encoding="utf-8").splitlines()
                if ln.strip()]
        want = {r["screen_rank"] for r in rows if r["outcome"] in ("E5", "E4")}
        self.assertEqual(set(p4.retry_set()), want)
        self.assertEqual(len(want), 71)


class LlcSteps(unittest.TestCase):
    def test_ir_followed_to_object(self):
        log = ("clang -O2 -target bpf -emit-llvm -c bpf_lxc.c -o bpf_lxc.ll\n"
               "llc -march=bpf -mcpu=v2 -filetype=obj -o bpf_lxc.o bpf_lxc.ll\n")
        self.assertEqual(p4.llc_steps(log)["bpf_lxc.ll"][1], "bpf_lxc.o")


class HeaderResolution(unittest.TestCase):
    index = ["pkg/ebpf/c/bpf_tracing.h", "pkg/network/ebpf/c/x/bpf_tracing.h", "kconfig.h", "a/b/c.h"]

    def test_shortest_path_wins(self):
        self.assertEqual(p4.repo_dir_for(Path("/w"), "bpf_tracing.h", self.index), str(Path("/w/pkg/ebpf/c")))

    def test_root_level_header(self):
        self.assertEqual(p4.repo_dir_for(Path("/w"), "kconfig.h", self.index), str(Path("/w")))

    def test_path_with_directory(self):
        self.assertEqual(p4.repo_dir_for(Path("/w"), "b/c.h", self.index), str(Path("/w/a")))

    def test_not_in_repository(self):
        self.assertIsNone(p4.repo_dir_for(Path("/w"), "linux/nsproxy.h", self.index))

    def test_unit_markers(self):
        for text in ('SEC("kprobe/x")', "__section(\"kprobe/x\")", "__bpf_section(\"x\")", "__attribute__((section(\"x\")))"):
            self.assertTrue(p4.UNIT_MARK.search(text), text)
        self.assertIsNone(p4.UNIT_MARK.search("static int helper(void)"))


class TemplatedConstant(unittest.TestCase):
    def test_unsubstituted_load_time_constant_is_environment(self):
        import tempfile
        log = ("libbpf: prog 'x': -- BEGIN PROG LOAD LOG --\n"
               "21: (18) r4 = 0xffffd1bb0017c048      ; R4_w=map_value(map=bpf_lxc.data,ks=4,vs=88,off=72)\n"
               "25: (67) r4 <<= 32\n"
               "R4 pointer arithmetic with <<= operator prohibited\n"
               "processed 22 insns (limit 1000000) max_states_per_insn 0 total_states 0 peak_states 0 mark_read 0\n"
               "-- END PROG LOAD LOG --\n")
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8") as f:
            f.write(log)
        self.assertEqual(p4.P3_REJECT_KIND(f.name), "safety")
        self.assertEqual(p4.reject_kind(f.name), "environment")


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
"""Pass 4 retry set and missing-header resolution (docs/WILD-CORPUS-PROTOCOL.md, 27 Oct entry)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from tools import wild_pass4 as p4

ROOT = Path(__file__).resolve().parents[1]


class RetrySet(unittest.TestCase):
    def test_every_e5_and_objectless_e4(self):
        rows = [json.loads(ln) for ln in (ROOT / "fixtures/wild/pass3.jsonl").read_text(encoding="utf-8").splitlines()
                if ln.strip()]
        e5 = {r["screen_rank"] for r in rows if r["outcome"] == "E5"}
        todo = set(p4.retry_set())
        self.assertTrue(e5 <= todo)
        self.assertEqual(todo - e5, {243, 245})
        self.assertEqual(len(todo), 43)


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
        for text in ('SEC("kprobe/x")', "__section(\"kprobe/x\")", "__attribute__((section(\"x\")))"):
            self.assertTrue(p4.UNIT_MARK.search(text), text)
        self.assertIsNone(p4.UNIT_MARK.search("static int helper(void)"))


if __name__ == "__main__":
    unittest.main()

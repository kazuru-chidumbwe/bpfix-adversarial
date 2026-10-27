# SPDX-License-Identifier: MIT
"""Batch-2 pass-1 path rule (docs/WILD-CORPUS-PROTOCOL.md, batch 2 item 4)."""

from __future__ import annotations

import unittest

from tools import wild_batch2 as b2


class PathRule(unittest.TestCase):
    def test_batch1_paths_still_match(self):
        for p in ("libbpf-tools/biosnoop.bpf.c", "bpf/bpf_lxc.c", "scheds/c/scx_simple.bpf.c"):
            self.assertTrue(b2.is_bpf_c(p), p)

    def test_batch2_directories(self):
        for p in ("felix/bpf-gpl/tc.c", "pkg/plugin/dropreason/_cprog/drop_reason.c", "kernel/process_kern.c",
                  "agent/src/ebpf/kernel/include/socket_trace.h"):
            self.assertTrue(b2.is_bpf_c(p), p)

    def test_userspace_does_not_match(self):
        for p in ("cmd/main.go", "src/loader.c", "user/kernelinfo.go", "kernelversion.c"):
            self.assertFalse(b2.is_bpf_c(p), p)


if __name__ == "__main__":
    unittest.main()

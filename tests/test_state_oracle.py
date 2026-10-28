# SPDX-License-Identifier: MIT
"""Verifier-state oracle (docs/STATE-ORACLE.md)."""

from __future__ import annotations

import unittest

from bpfix_adversarial.state_oracle import compute, failing_path

NP = """func#0 @0
0: R1=ctx() R10=fp0
; eth = bpf_dynptr_slice(&ptr, 0, 0, sizeof(*eth)); @ buggy.bpf.c:32
13: (85) call bpf_dynptr_slice#57560          ; R0=rdonly_mem_or_null(id=2,sz=14)
; if (bpf_ntohs(eth->h_proto) != ETH_P_IP) @ buggy.bpf.c:33
14: (69) r1 = *(u16 *)(r0 +12)
R0 invalid mem access 'rdonly_mem_or_null'
verification time 115 usec
processed 15 insns (limit 1000000) max_states_per_insn 0 total_states 1 peak_states 1 mark_read 0
"""

PB_BRANCH = """func#0 @0
; void *data = (void *)(long)ctx->data; @ p.c:10
1: (61) r2 = *(u32 *)(r1 +4)          ; R2_w=pkt_end()
2: (61) r1 = *(u32 *)(r1 +0)          ; R1_w=pkt(r=0)
; if (data + 14 > data_end) @ p.c:12
3: (2d) if r3 > r2 goto pc+4          ; R2_w=pkt_end() R3_w=pkt(off=14,r=14)
; return 1; @ p.c:13
4: (b7) r0 = 1                        ; R0_w=1
5: (95) exit
from 3 to 8: R1=pkt(r=0) R2=pkt_end()
; x = *(u32 *)(data + 20); @ p.c:16
8: (61) r0 = *(u32 *)(r1 +20)
invalid access to packet, off=20 size=4, R1(id=0,off=20,r=0)
R1 offset is outside of the packet
verification time 52 usec
processed 7 insns (limit 1000000) max_states_per_insn 0 total_states 0 peak_states 0 mark_read 0
"""


class StateOracle(unittest.TestCase):
    def test_nullable_creation_is_the_site_and_stop_line_is_not(self):
        o = compute(NP)
        self.assertEqual(o.kind, "NullablePointer")
        self.assertEqual(o.first_loss.idx, 13)
        self.assertEqual(o.sites, [("buggy.bpf.c", 32)])
        self.assertEqual(o.stop_line, ("buggy.bpf.c", 33))

    def test_branch_path_runs_through_the_fork_point(self):
        path = failing_path(PB_BRANCH.splitlines())
        self.assertEqual([s.idx for s in path], [1, 2, 3, 8])  # 4 and 5 are on the other branch
        o = compute(PB_BRANCH)
        self.assertEqual(o.kind, "PacketBounds")
        self.assertEqual(o.first_loss.idx, 3)
        self.assertEqual(o.sites, [("p.c", 12)])

    def test_other_messages_are_not_covered(self):
        o = compute(NP.replace("R0 invalid mem access 'rdonly_mem_or_null'", "R2 invalid mem access 'scalar'"))
        self.assertIsNone(o.kind)


if __name__ == "__main__":
    unittest.main()

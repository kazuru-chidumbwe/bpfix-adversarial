# SPDX-License-Identifier: MIT
import json
import unittest
from pathlib import Path

from tools.gen_main75_rewrites import PAD, counterpart, inline, macro, reorder, split, vpad

ROOT = Path(__file__).resolve().parents[1]

PROG = """#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int prog(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    __u32 a = 1;
    __u32 b = 2;
    if (data + 14 > data_end && a)
        return XDP_PASS;
    a = b + 1;
    return *(__u8 *)data;
}
""".split("\n")
ANCHOR = PROG.index("    return *(__u8 *)data;")


class TestRewrites(unittest.TestCase):
    def test_vpad_inserts_eight_lines_before_anchor(self):
        out, why = vpad(PROG, ANCHOR)
        self.assertIsNone(why)
        self.assertEqual([ln.strip() for ln in out[ANCHOR:ANCHOR + 8]], [PAD] * 8)
        self.assertEqual(out[ANCHOR + 8], PROG[ANCHOR])

    def test_macro_refuses_return_and_wraps_a_statement(self):
        self.assertIsNone(macro(PROG, ANCHOR)[0])
        out, why = macro(PROG, ANCHOR - 1)
        self.assertIsNone(why)
        self.assertIn("    ADV_STMT(a = b + 1);", out)
        self.assertIn("#define ADV_STMT(...) \\", out)

    def test_inline_moves_the_nearest_if_into_a_helper(self):
        out, why = inline(PROG, ANCHOR)
        self.assertIsNone(why)
        helper = [ln for ln in out if ln.startswith("static __always_inline int __adv_guard(")]
        self.assertEqual(len(helper), 1)
        self.assertIn("void *data", helper[0])
        self.assertIn("__u32 a", helper[0])
        self.assertTrue(any("if (__adv_guard(" in ln for ln in out))

    def test_reorder_refuses_dependent_statements(self):
        out, why = reorder(PROG, ANCHOR - 1)  # a = b + 1 after an if line: not a ';' statement
        self.assertIsNone(out)
        lines = ["    __u32 x = 1;", "    __u32 y = 2;"]
        swapped, why = reorder(lines, 1)
        self.assertEqual(swapped, ["    __u32 y = 2;", "    __u32 x = 1;"])
        self.assertIsNone(reorder(["    __u32 x = 1;", "    __u32 y = x;"], 1)[0])

    def test_split_on_top_level_and(self):
        out, why = split(PROG, ANCHOR)
        self.assertIsNone(why)
        self.assertIn("    if (data + 14 > data_end) if (a)", out)

    def test_counterpart_follows_the_diff(self):
        fixed = PROG[:ANCHOR] + ["    if (data + 1 > data_end) return 0;"] + PROG[ANCHOR:]
        self.assertEqual(counterpart(PROG, fixed, ANCHOR), ANCHOR + 1)

    def test_committed_rewrites_regenerate(self):
        meta = json.loads((ROOT / "campaigns" / "n3" / "rewrites.json").read_text(encoding="utf-8"))
        self.assertEqual(meta["applied"]["VPAD"], sum(1 for r in meta["cases"].values() if r["VPAD"]["applied"]))


if __name__ == "__main__":
    unittest.main()

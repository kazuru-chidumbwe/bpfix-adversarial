# SPDX-License-Identifier: MIT
"""Pretty Verifier line-lookup sensitivity (tools/score_pv_lookup.py)."""

from __future__ import annotations

import unittest

from tools import score_pv_lookup as pl

OUT = """Prettier Verifier ##
#######################

error: Invalid access to map value
   519 | if (proc_info->mappings[mid].begin <= pc) { @ native.bpf.c:491
       | in file /home/test/wild/tmp/4049/parent/bpf/unwinders/native.bpf.c
Access is 4456 bytes past the end of the map value (capacity: 16032 bytes).
"""


class Locations(unittest.TestCase):
    def test_printed_and_log_lines(self):
        self.assertEqual(pl.locations(OUT), {"printed": ["native.bpf.c", 519], "log": ["native.bpf.c", 491]})

    def test_header_location_keeps_its_file(self):
        out = OUT.replace("519 | if", "63 | if").replace("native.bpf.c:491", "buffer.h:368").replace(
            "bpf/unwinders/native.bpf.c", "common/context.h")
        self.assertEqual(pl.locations(out), {"printed": ["context.h", 63], "log": ["buffer.h", 368]})

    def test_no_location(self):
        self.assertIsNone(pl.locations("Prettier Verifier ##\n\nerror: Error not managed -> stack depth 144\n"))


class Tally(unittest.TestCase):
    def test_rows_without_the_key_count_as_released(self):
        hit = {"primary_on_site": True, "label_on_site": True, "primary_within_3": True}
        miss = {"primary_on_site": False, "label_on_site": False, "primary_within_3": False}
        rows = [{"released": {r: miss for r in pl.RULES}, "log_line": {r: hit for r in pl.RULES}},
                {"released": {r: hit for r in pl.RULES}}]
        self.assertEqual(pl.tally(rows, "released")["R0"]["primary_on_site"], 1)
        self.assertEqual(pl.tally(rows, "log_line")["R0"]["primary_on_site"], 2)


if __name__ == "__main__":
    unittest.main()

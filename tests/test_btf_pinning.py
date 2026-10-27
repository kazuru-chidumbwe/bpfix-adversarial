# SPDX-License-Identifier: MIT
"""Clearing unknown pinning values in BTF (docs/WILD-CORPUS-PROTOCOL.md, batch 2 item 9)."""

from __future__ import annotations

import struct
import unittest

from tools.btf_pinning import patch_btf


def btf(members: list[tuple[str, int]], nelems: int = 100) -> bytearray:
    """int (1), int[nelems] (2), int (*)[nelems] (3), struct { members } (4)."""
    strs = b"\0int\0" + b"".join(n.encode() + b"\0" for n, _ in members)
    offs, o = {}, 5
    for n, _ in members:
        offs[n] = o
        o += len(n) + 1
    t = struct.pack("<IIII", 1, (1 << 24), 4, 32)  # INT, size 4, 32 bits
    t += struct.pack("<III", 0, 3 << 24, 0) + struct.pack("<III", 1, 1, nelems)  # ARRAY
    t += struct.pack("<III", 0, 2 << 24, 2)  # PTR -> ARRAY
    t += struct.pack("<III", 0, (4 << 24) | len(members), 8 * len(members))
    for i, (n, ty) in enumerate(members):
        t += struct.pack("<III", offs[n], ty, i * 64)
    hdr = struct.pack("<HBBIIIII", 0xEB9F, 1, 0, 24, 0, len(t), len(t), len(strs))
    return bytearray(hdr + t + strs)


def nelems(b: bytearray) -> int:
    return struct.unpack_from("<I", b, 24 + 16 + 20)[0]


class PinningPatch(unittest.TestCase):
    def test_unknown_pinning_is_cleared(self):
        b = btf([("pinning", 3)])
        self.assertEqual(patch_btf(b), [100])
        self.assertEqual(nelems(b), 0)

    def test_pin_by_name_is_kept(self):
        b = btf([("pinning", 3)], nelems=1)
        self.assertEqual(patch_btf(b), [])
        self.assertEqual(nelems(b), 1)

    def test_array_shared_with_max_entries_is_left_alone(self):
        b = btf([("pinning", 3), ("max_entries", 3)])
        self.assertEqual(patch_btf(b), [])
        self.assertEqual(nelems(b), 100)


if __name__ == "__main__":
    unittest.main()

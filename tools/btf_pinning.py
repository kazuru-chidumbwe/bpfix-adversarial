# SPDX-License-Identifier: MIT
"""Clear map pinning values that libbpf does not know, in a copy of a BPF object.

Some projects mark maps with their own pinning values, which only their loader
understands (opentelemetry-ebpf-instrumentation: 100). libbpf refuses the
object at open ("invalid pinning value"). Pinning only decides where a map
lives in bpffs; it plays no part in verification. This rewrites, in the BTF of
a copy, the array length that encodes ``__uint(pinning, N)`` to 0 (no pinning)
when N is neither 0 nor 1 (LIBBPF_PIN_BY_NAME), and only when that array type
and the pointer to it are used by ``pinning`` members alone, so no other
attribute (``max_entries`` and the like) can change. Protocol: batch 2 item 9.
"""

from __future__ import annotations

import shutil
import struct
from pathlib import Path

BTF_MAGIC = 0xEB9F
KIND_PTR, KIND_ARRAY, KIND_STRUCT, KIND_UNION = 2, 3, 4, 5
# extra bytes after the 12-byte btf_type, per kind (vlen-scaled where noted)
_FIXED = {1: 4, 3: 12, 14: 4, 17: 4}
_PER_V = {4: 12, 5: 12, 6: 8, 13: 8, 15: 12, 19: 12}


def _btf_section(data: bytes) -> tuple[int, int] | None:
    """(offset, size) of the .BTF section of a little-endian ELF64 object."""
    if data[:4] != b"\x7fELF" or data[4] != 2 or data[5] != 1:
        return None
    shoff, = struct.unpack_from("<Q", data, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from("<HHH", data, 0x3A)
    sh = [struct.unpack_from("<IIQQQQ", data, shoff + i * shentsize) for i in range(shnum)]
    stroff = sh[shstrndx][4]
    for name, _t, _f, _a, off, size in sh:
        end = data.index(b"\0", stroff + name)
        if data[stroff + name:end] == b".BTF":
            return off, size
    return None


def patch_btf(btf: bytearray) -> list[int]:
    """Patch in place; returns the old pinning values that were cleared."""
    magic, _ver, _flags, hdr_len, type_off, type_len, str_off, _str_len = struct.unpack_from("<HBBIIIII", btf, 0)
    if magic != BTF_MAGIC:
        return []
    t0, s0 = hdr_len + type_off, hdr_len + str_off

    def name(off: int) -> bytes:
        return bytes(btf[s0 + off: btf.index(b"\0", s0 + off)])

    types: dict[int, tuple[int, int, int, int]] = {}  # id -> (kind, vlen, ref, record offset)
    members: list[tuple[bytes, int]] = []  # (member name, member type)
    refs: dict[int, int] = {}  # type id -> number of references
    pos, tid = t0, 1
    while pos < t0 + type_len:
        _name_off, info, size_or_type = struct.unpack_from("<III", btf, pos)
        kind, vlen = (info >> 24) & 0x1F, info & 0xFFFF
        types[tid] = (kind, vlen, size_or_type, pos)
        extra = _FIXED.get(kind, 0) + _PER_V.get(kind, 0) * vlen
        if kind == KIND_ARRAY:
            elem, = struct.unpack_from("<I", btf, pos + 12)
            refs[elem] = refs.get(elem, 0) + 1
        elif kind in (KIND_STRUCT, KIND_UNION):
            for i in range(vlen):
                m_name, m_type, _m_off = struct.unpack_from("<III", btf, pos + 12 + 12 * i)
                members.append((name(m_name), m_type))
                refs[m_type] = refs.get(m_type, 0) + 1
        elif kind == 13:  # FUNC_PROTO: return type and each parameter
            refs[size_or_type] = refs.get(size_or_type, 0) + 1
            for i in range(vlen):
                p_type, = struct.unpack_from("<I", btf, pos + 12 + 8 * i + 4)
                refs[p_type] = refs.get(p_type, 0) + 1
        elif kind in (2, 8, 9, 10, 11, 12, 14, 17, 18):
            refs[size_or_type] = refs.get(size_or_type, 0) + 1
        pos += 12 + extra
        tid += 1

    cleared = []
    pin_ptrs = {t for n, t in members if n == b"pinning"}
    for ptr in sorted(pin_ptrs):
        kind, _v, arr, _p = types.get(ptr, (0, 0, 0, 0))
        if kind != KIND_PTR or types.get(arr, (0,))[0] != KIND_ARRAY:
            continue
        uses = sum(1 for n, t in members if t == ptr)
        if refs.get(ptr, 0) != uses or any(n != b"pinning" for n, t in members if t == ptr) or refs.get(arr, 0) != 1:
            continue  # shared with another attribute: leave it, the object stays unopenable
        apos = types[arr][3]
        nelems, = struct.unpack_from("<I", btf, apos + 20)
        if nelems not in (0, 1):
            struct.pack_into("<I", btf, apos + 20, 0)
            cleared.append(nelems)
    return cleared


def clear_unknown_pinning(src: Path, dst: Path) -> list[int]:
    """Copy src to dst with unknown pinning values cleared; returns the cleared values ([] = dst unchanged)."""
    data = bytearray(src.read_bytes())
    sec = _btf_section(bytes(data))
    if sec is None:
        return []
    off, size = sec
    btf = bytearray(data[off:off + size])
    cleared = patch_btf(btf)
    if cleared:
        data[off:off + size] = btf
        dst.write_bytes(bytes(data))
    elif src != dst:
        shutil.copy2(src, dst)
    return cleared

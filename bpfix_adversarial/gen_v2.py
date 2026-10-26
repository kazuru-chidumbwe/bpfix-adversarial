# SPDX-License-Identifier: MIT
"""Campaign v2 mutant generators (see campaigns/v2/README.md).

Three families, written under ``campaigns/v2/mutants/`` so the cited v1.0.2
tree in ``mutants/`` (whose bytes the committed logs were captured from) is
never touched:

* ``RenameReject``: *rejecting* NullablePointer programs that contain a
  null-check-shaped line before the reject site which the verifier does not
  credit. Upstream bpfix only consults ``looks_like_null_check`` on rejected
  programs, via ``latest_source_before`` (proof_events.rs, nullable_pointer_events),
  so these are the programs where a rename can change bpfix's output at all.
  Each construct is emitted once with a name on upstream's name list and once
  with an idiomatic name; the pair differs only in that identifier.
* ``VolatilePad``: PacketBounds / ScalarRange / nocheck templates whose padding
  is ``volatile`` and therefore survives ``clang -O2`` (one stack load/add/store
  per pad line, each with its own BTF line record). The v1 pads compile away.
  ``PBS`` spills and refills the packet pointer through a volatile stack slot on
  every pad line, so the pointer state itself crosses the padding.
* ``ProvenanceMap``: PointerProvenance candidate in which a packet pointer is
  round-tripped through a map value (allowed for privileged loads) and
  dereferenced later, so the verifier is expected to stop at the dereference
  rather than at the washing operation. The verdict and bpfix's error ID are
  unverified until captured (a candidate, not a result).
"""

from __future__ import annotations

from pathlib import Path

from .templates import COMMON_INCLUDES, MAP_LOOKUP_DECL

PADS = (0, 8, 32)

# (upstream-list name, idiomatic name). Upstream's name-shaped literals are
# !tmp, !val, !ptr, !value (source.rs looks_like_null_check).
POINTER_NAME_PAIRS = (("ptr", "entry"), ("tmp", "slot"))
# A non-pointer flag whose name happens to contain "!val" once negated.
FLAG_NAME_PAIR = ("valid", "ok")


def _footer(case_id: str, family: str, extra: str = "") -> str:
    tail = f" {extra}" if extra else ""
    return (
        '\nchar _license[] SEC("license") = "GPL";\n'
        f"/* case_id={case_id} family={family}{tail} */\n"
    )


def volatile_pad_c(n: int, indent: str = "\t") -> str:
    """Pad lines that survive -O2: one volatile load/add/store per line."""
    if n <= 0:
        return ""
    lines = [f"{indent}/* distance pad (volatile): {n} ops */", f"{indent}volatile __u64 __pad = 0;"]
    lines += [f"{indent}__pad += {i + 1};" for i in range(n)]
    return "\n".join(lines) + "\n"


def spill_pad_c(n: int, ptr: str = "data", indent: str = "\t") -> str:
    """Pad lines that move the packet pointer through a volatile stack slot."""
    if n <= 0:
        return ""
    lines = [f"{indent}/* distance pad (pointer spill): {n} round trips */", f"{indent}void * volatile __pad_slot;"]
    lines += [f"{indent}__pad_slot = {ptr}; {ptr} = __pad_slot;" for _ in range(n)]
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------
# RenameReject


def rename_reject_src(construct: str, name: str, case_id: str) -> str:
    """One rejecting program; ``name`` is the identifier on the check line."""
    # Same function name for both members of a pair: the pair must differ only
    # in the renamed identifier.
    head = f'{COMMON_INCLUDES}\n{MAP_LOOKUP_DECL}\nSEC("socket")\nint rr_{construct}(void *ctx)\n{{\n'
    if construct == "wrongptr":
        body = (
            "\t__u32 key = 0;\n"
            f"\t__u64 *{name} = bpf_map_lookup_elem(&m, &key);\n"
            "\t__u64 *other = bpf_map_lookup_elem(&m, &key);\n"
            "\t/* ORACLE_LOSS_LINE: check guards the wrong pointer */\n"
            f"\tif (!{name})\n"
            "\t\treturn 0;\n"
            "\t/* ORACLE_REJECT_LINE: unchecked pointer dereferenced */\n"
            "\treturn *other;\n"
        )
    elif construct == "branch":
        body = (
            "\t__u32 key = 0;\n"
            f"\t__u64 *{name} = bpf_map_lookup_elem(&m, &key);\n"
            "\t__u32 flag = bpf_get_prandom_u32() & 1;\n"
            "\t/* ORACLE_LOSS_LINE: check only on one branch */\n"
            "\tif (flag) {\n"
            f"\t\tif (!{name})\n"
            "\t\t\treturn 0;\n"
            "\t}\n"
            "\t/* ORACLE_REJECT_LINE: other branch reaches the use unchecked */\n"
            f"\treturn *{name};\n"
        )
    elif construct == "reassign":
        body = (
            "\t__u32 key = 0;\n"
            f"\t__u64 *{name} = bpf_map_lookup_elem(&m, &key);\n"
            f"\tif (!{name})\n"
            "\t\treturn 0;\n"
            "\t/* ORACLE_LOSS_LINE: pointer reassigned after its check */\n"
            f"\t{name} = bpf_map_lookup_elem(&m, &key);\n"
            "\t/* ORACLE_REJECT_LINE: reassigned pointer dereferenced */\n"
            f"\treturn *{name};\n"
        )
    elif construct == "flag":
        body = (
            "\t__u32 key = 0;\n"
            "\t__u64 *entry = bpf_map_lookup_elem(&m, &key);\n"
            "\t/* ORACLE_LOSS_LINE: null check on entry omitted; flag check is not one */\n"
            f"\t__u32 {name} = bpf_get_prandom_u32() & 1;\n"
            f"\tif (!{name})\n"
            "\t\treturn 0;\n"
            "\t/* ORACLE_REJECT_LINE: unchecked map value dereferenced */\n"
            "\treturn *entry;\n"
        )
    else:
        raise ValueError(construct)
    return head + body + "}\n" + _footer(case_id, "RenameReject", f"construct={construct} name={name}")


def rename_reject_cases() -> list[tuple[str, str, str, str]]:
    """(case_id, construct, name, pair_id) for every RenameReject program."""
    out: list[tuple[str, str, str, str]] = []
    for construct in ("wrongptr", "branch", "reassign"):
        for brittle, idiomatic in POINTER_NAME_PAIRS:
            pair = f"RR-{construct}-{brittle}-{idiomatic}"
            out.append((f"RR-{construct}-{brittle}", construct, brittle, pair))
            out.append((f"RR-{construct}-{idiomatic}", construct, idiomatic, pair))
    brittle, idiomatic = FLAG_NAME_PAIR
    pair = f"RR-flag-{brittle}-{idiomatic}"
    out.append((f"RR-flag-{brittle}", "flag", brittle, pair))
    out.append((f"RR-flag-{idiomatic}", "flag", idiomatic, pair))
    return out


# --------------------------------------------------------------------------
# VolatilePad


def pbv_src(pad: int, case_id: str) -> str:
    return (
        f'{COMMON_INCLUDES}\nSEC("xdp")\nint {case_id.replace("-", "_").lower()}(struct xdp_md *ctx)\n{{\n'
        "\tvoid *data = (void *)(long)ctx->data;\n"
        "\tvoid *data_end = (void *)(long)ctx->data_end;\n"
        "\t/* ORACLE_LOSS_LINE: under-check, only 1 byte proven */\n"
        "\tif (data + 1 > data_end)\n"
        "\t\treturn XDP_DROP;\n"
        f"{volatile_pad_c(pad)}"
        "\t/* ORACLE_REJECT_LINE: 8-byte load needs a larger packet range */\n"
        "\treturn *(__u64 *)data;\n}\n" + _footer(case_id, "VolatilePad", f"base=PacketBounds pad={pad}")
    )


def pbs_src(pad: int, case_id: str) -> str:
    return (
        f'{COMMON_INCLUDES}\nSEC("xdp")\nint {case_id.replace("-", "_").lower()}(struct xdp_md *ctx)\n{{\n'
        "\tvoid *data = (void *)(long)ctx->data;\n"
        "\tvoid *data_end = (void *)(long)ctx->data_end;\n"
        "\t/* ORACLE_LOSS_LINE: under-check, only 1 byte proven */\n"
        "\tif (data + 1 > data_end)\n"
        "\t\treturn XDP_DROP;\n"
        f"{spill_pad_c(pad)}"
        "\t/* ORACLE_REJECT_LINE: 8-byte load needs a larger packet range */\n"
        "\treturn *(__u64 *)data;\n}\n" + _footer(case_id, "VolatilePad", f"base=PacketBounds-spill pad={pad}")
    )


def srv_src(pad: int, case_id: str) -> str:
    return (
        f'{COMMON_INCLUDES}\nSEC("socket")\nint {case_id.replace("-", "_").lower()}(void *ctx)\n{{\n'
        "\t__u64 table[4] = {0, 1, 2, 3};\n"
        "\t/* ORACLE_LOSS_LINE: missing scalar range guard on idx */\n"
        "\t__u32 idx = bpf_get_prandom_u32();\n"
        f"{volatile_pad_c(pad)}"
        "\t/* ORACLE_REJECT_LINE: load with unbounded index */\n"
        "\treturn table[idx];\n}\n" + _footer(case_id, "VolatilePad", f"base=ScalarRange pad={pad}")
    )


def npv_src(pad: int, case_id: str) -> str:
    return (
        f'{COMMON_INCLUDES}\n{MAP_LOOKUP_DECL}\nSEC("socket")\nint {case_id.replace("-", "_").lower()}(void *ctx)\n{{\n'
        "\t__u32 key = 0;\n"
        "\t__u64 *entry = bpf_map_lookup_elem(&m, &key);\n"
        "\t/* ORACLE_LOSS_LINE: null check on entry omitted */\n"
        f"{volatile_pad_c(pad)}"
        "\t/* ORACLE_REJECT_LINE: possibly-null map value dereferenced */\n"
        "\treturn *entry;\n}\n" + _footer(case_id, "VolatilePad", f"base=NullablePointer-nocheck pad={pad}")
    )


# --------------------------------------------------------------------------
# ProvenanceMap (candidate)

SLOT_MAP_DECL = """\
struct {
\t__uint(type, BPF_MAP_TYPE_ARRAY);
\t__uint(max_entries, 1);
\t__type(key, __u32);
\t__type(value, __u64);
} slot SEC(".maps");
"""


def ppm_src(pad: int, case_id: str) -> str:
    return (
        f'{COMMON_INCLUDES}\n{SLOT_MAP_DECL}\nSEC("xdp")\nint {case_id.replace("-", "_").lower()}(struct xdp_md *ctx)\n{{\n'
        "\tvoid *data = (void *)(long)ctx->data;\n"
        "\tvoid *data_end = (void *)(long)ctx->data_end;\n"
        "\t__u32 key = 0;\n"
        "\tif (data + 8 > data_end)\n"
        "\t\treturn XDP_DROP;\n"
        "\t__u64 *cell = bpf_map_lookup_elem(&slot, &key);\n"
        "\tif (!cell)\n"
        "\t\treturn XDP_DROP;\n"
        "\t/* ORACLE_LOSS_LINE: packet pointer round-tripped through a map value */\n"
        "\t*(volatile __u64 *)cell = (__u64)(long)data;\n"
        "\tvoid *back = (void *)(long)*(volatile __u64 *)cell;\n"
        f"{volatile_pad_c(pad)}"
        "\t/* ORACLE_REJECT_LINE: scalar dereferenced as a packet pointer */\n"
        "\treturn *(__u8 *)back;\n}\n" + _footer(case_id, "ProvenanceMap", f"base=PointerProvenance pad={pad}")
    )


FAMILY_WRITERS = (
    ("VolatilePad", "PBV", pbv_src),
    ("VolatilePad", "PBS", pbs_src),
    ("VolatilePad", "SRV", srv_src),
    ("VolatilePad", "NPV", npv_src),
    ("ProvenanceMap", "PPM", ppm_src),
)


def write_v2_mutants(out_dir: Path, pads: tuple[int, ...] = PADS) -> list[Path]:
    paths: list[Path] = []
    rr = out_dir / "RenameReject"
    rr.mkdir(parents=True, exist_ok=True)
    for case_id, construct, name, _pair in rename_reject_cases():
        p = rr / f"{case_id}.c"
        p.write_text(rename_reject_src(construct, name, case_id), encoding="utf-8", newline="\n")
        paths.append(p)
    for family, prefix, fn in FAMILY_WRITERS:
        sub = out_dir / family
        sub.mkdir(parents=True, exist_ok=True)
        for pad in pads:
            case_id = f"{prefix}-pad{pad}"
            p = sub / f"{case_id}.c"
            p.write_text(fn(pad, case_id), encoding="utf-8", newline="\n")
            paths.append(p)
    return paths

# SPDX-License-Identifier: MIT
"""Oracle templates for PointerProvenance, ScalarRange, PacketBounds."""

from __future__ import annotations

from pathlib import Path

from .templates import COMMON_INCLUDES, pad_nops_c


def pointer_provenance_src(*, pad: int = 0, case_id: str) -> str:
    """PTR_TO_PACKET XOR bpf_get_prandom_u32(), then a dereference.

    Plain (__u64)data casts are optimized away; the verifier keeps pkt type.
    The XOR was meant to wash provenance so the later dereference rejects. On
    the cite pin (6.12.86) the verifier instead rejects the XOR itself ("math
    between pkt pointer and register with unbounded min value is not allowed"),
    which sits inside the injection span; the dereference after the
    ORACLE_REJECT_LINE marker is never reached, and upstream bpfix labels the
    capture BPFIX-E005 (ScalarRange). The bounds check comes first so the
    failure is not a PacketBounds under-check. Marker text is left as captured
    (see tests/test_capture_provenance.py).
    """
    pad_block = pad_nops_c(pad)
    return f"""{COMMON_INCLUDES}
SEC("xdp")
int pp_pad{pad}(struct xdp_md *ctx)
{{
\tvoid *data = (void *)(long)ctx->data;
\tvoid *data_end = (void *)(long)ctx->data_end;
\tif (data + 8 > data_end)
\t\treturn XDP_DROP;
\t/* ORACLE_LOSS_LINE: provenance washed — pkt pointer XOR prandom → scalar */
\t__u64 cookie = (__u64)data;
\tcookie ^= bpf_get_prandom_u32();
{pad_block}\t/* ORACLE_REJECT_LINE: dereference unbound scalar as pointer */
\treturn *(__u64 *)(void *)cookie;
}}

char _license[] SEC("license") = "MIT";
/* case_id={case_id} obligation=PointerProvenance pad={pad} */
"""


def scalar_range_src(*, pad: int = 0, case_id: str) -> str:
    """Unbounded index into a small constant array, a genuine scalar-range violation.

    Prior template used ARRAY bpf_map_lookup_elem(prandom); the helper returns
    NULL for OOB keys, so the program never rejected. Retune: index a fixed
    four-element array with an unbound prandom index. clang -O2 places the
    constant array in .rodata, so the verifier sees a map-value access with an
    unbounded offset ("R1 unbounded memory access"), not a stack load.
    """
    pad_block = pad_nops_c(pad)
    return f"""{COMMON_INCLUDES}
SEC("socket")
int sr_pad{pad}(void *ctx)
{{
\t__u64 stack[4] = {{0, 1, 2, 3}};
\t/* ORACLE_LOSS_LINE: missing scalar range guard on idx */
\t__u32 idx = bpf_get_prandom_u32();
{pad_block}\t/* ORACLE_REJECT_LINE: stack load with unbound index */
\treturn stack[idx];
}}

char _license[] SEC("license") = "MIT";
/* case_id={case_id} obligation=ScalarRange pad={pad} */
"""


def packet_bounds_src(*, pad: int = 0, case_id: str) -> str:
    """Insufficient data_end check then wider load."""
    pad_block = pad_nops_c(pad)
    return f"""{COMMON_INCLUDES}
SEC("xdp")
int pb_pad{pad}(struct xdp_md *ctx)
{{
\tvoid *data = (void *)(long)ctx->data;
\tvoid *data_end = (void *)(long)ctx->data_end;
\t/* ORACLE_LOSS_LINE: under-check — only 1 byte proven */
\tif (data + 1 > data_end)
\t\treturn XDP_DROP;
{pad_block}\t/* ORACLE_REJECT_LINE: 8-byte load needs larger packet range */
\treturn *(__u64 *)data;
}}

char _license[] SEC("license") = "MIT";
/* case_id={case_id} obligation=PacketBounds pad={pad} */
"""


def write_obligation_templates(out_dir: Path, pads: list[int] | None = None) -> list[Path]:
    pads = pads or [0, 8, 32]
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    writers = (
        ("PointerProvenance", "PP", pointer_provenance_src),
        ("ScalarRange", "SR", scalar_range_src),
        ("PacketBounds", "PB", packet_bounds_src),
    )
    for obligation, prefix, fn in writers:
        sub = out_dir / obligation
        sub.mkdir(parents=True, exist_ok=True)
        for pad in pads:
            case_id = f"{prefix}-pad{pad}"
            p = sub / f"{case_id}.c"
            p.write_text(fn(pad=pad, case_id=case_id), encoding="utf-8", newline="\n")
            paths.append(p)
    return paths

"""Oracle templates for PointerProvenance, ScalarRange, PacketBounds."""

from __future__ import annotations

from pathlib import Path

from .templates import COMMON_INCLUDES, pad_nops_c


def pointer_provenance_src(*, pad: int = 0, case_id: str) -> str:
    """PTR_TO_PACKET → scalar wash → deref (no recovering packet bounds check).

    Plain (__u64)data casts are optimized away; the verifier keeps pkt type.
    Retune: XOR with bpf_get_prandom_u32() so the address becomes an unbound
    scalar — expect reject (invalid mem access / scalar). Bounds-check first
    so failure is provenance wash, not PacketBounds under-check.
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
    """Unbounded stack index — genuine scalar-range violation.

    Prior template used ARRAY bpf_map_lookup_elem(prandom); the helper returns
    NULL for OOB keys, so the program never rejected. Retune: index a fixed
    stack slot array with an unbound prandom index (classic SR reject).
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
            p.write_text(fn(pad=pad, case_id=case_id), encoding="utf-8")
            paths.append(p)
    return paths

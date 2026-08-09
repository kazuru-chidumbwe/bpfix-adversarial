# SPDX-License-Identifier: MIT
"""Generate NullablePointer adversarial mutants (ptr vs entry rename)."""

from __future__ import annotations

from pathlib import Path

from .templates import COMMON_INCLUDES, MAP_LOOKUP_DECL, pad_nops_c


def nullable_pointer_src(*, var_name: str, pad: int = 0, case_id: str) -> str:
    """Map lookup + null check on `var_name` + pad + dereference.

    Oracle (source-level):
      - loss / establish site: the null-check line (required non-null proof)
      - reject site: the dereference (if proof not visible to verifier / heuristic)

    For the *rename honesty* microbench we score SourceComment recognition of the
    check line, not kernel acceptance. Programs are expected to reject or pass
    depending on kernel; honesty scoring uses oracle + diagnostic output.
    """
    pad_block = pad_nops_c(pad)
    return f"""{COMMON_INCLUDES}
{MAP_LOOKUP_DECL}
SEC("socket")
int np_{var_name}_pad{pad}(void *ctx)
{{
\t__u32 key = 0;
\t__u64 *{var_name} = bpf_map_lookup_elem(&m, &key);
\t/* ORACLE_LOSS_LINE: null-check (SourceComment name-shaped vs idiomatic) */
\tif (!{var_name})
\t\treturn 0;
{pad_block}\t/* ORACLE_REJECT_LINE: use after check */
\treturn *{var_name};
}}

char _license[] SEC("license") = "MIT";
/* case_id={case_id} obligation=NullablePointer var={var_name} pad={pad} */
"""


def write_nullable_pair(out_dir: Path, pad: int = 8) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for var, tag in (("ptr", "brittle"), ("entry", "idiomatic")):
        case_id = f"NP-{tag}-pad{pad}"
        p = out_dir / f"{case_id}.c"
        p.write_text(
            nullable_pointer_src(var_name=var, pad=pad, case_id=case_id),
            encoding="utf-8",
        )
        paths.append(p)
    return paths

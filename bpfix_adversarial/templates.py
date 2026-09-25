"""Shared BPF program header for adversarial mutants (lab / Linux)."""

COMMON_INCLUDES = """\
// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>
"""

MAP_LOOKUP_DECL = """\
struct {
\t__uint(type, BPF_MAP_TYPE_HASH);
\t__uint(max_entries, 1);
\t__type(key, __u32);
\t__type(value, __u64);
} m SEC(".maps");
"""


def pad_nops_c(n: int, indent: str = "\t") -> str:
    """Emit verifier-visible but semantically inert scalar ops as distance padding."""
    if n <= 0:
        return ""
    lines = [f"{indent}/* distance pad: {n} scalar ops */", f"{indent}__u64 __pad = 0;"]
    for i in range(n):
        lines.append(f"{indent}__pad += {i + 1};")
    lines.append(f"{indent}(void)__pad;")
    return "\n".join(lines) + "\n"

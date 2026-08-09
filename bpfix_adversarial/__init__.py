# SPDX-License-Identifier: MIT
"""Check whether eBPF reject diagnostics still name the injection line after pad and rename stress."""

__version__ = "1.0.1"

# Upstream pin: eunomia-bpf/bpfix @ 81d97e4a528456e0082a77f4fb6edd13fa092b7b (2026-07-11)
UPSTREAM_BPFIX = {
    "repo": "https://github.com/eunomia-bpf/bpfix",
    "commit": "81d97e4a528456e0082a77f4fb6edd13fa092b7b",
    "source_rs": "crates/bpfix/src/source.rs",
}

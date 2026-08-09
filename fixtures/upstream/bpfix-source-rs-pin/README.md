# Vendored snapshot of upstream bpfix SourceComment predicates

**Upstream:** https://github.com/eunomia-bpf/bpfix  
**Commit:** `81d97e4a528456e0082a77f4fb6edd13fa092b7b`  
**Path:** `crates/bpfix/src/source.rs`  
**SHA-256:** `f86f884583491f7c0606772ba4ec56e4468437f6d986e26412931820cbf73e52`

This directory holds a **predicates-only** snapshot for SoftwareX port-fidelity tests
(`tests/test_port_fidelity.py`). It does **not** vendor the full bpfix crate.

The Python helpers in `bpfix_adversarial/heuristics.py` match the seven
`looks_like_*` predicates' string literals. The harness **reporter**
pipeline (raw mutant C + first top-down match) is intentionally not identical
to upstream (`latest_source_before` over log-emitted source comments).

Note: Rust uses `to_ascii_lowercase` while Python uses `str.lower()`; for ASCII
C source comments these agree.

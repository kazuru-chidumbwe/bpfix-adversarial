# Vendored snapshot of upstream bpfix SourceComment predicates

**Upstream:** https://github.com/eunomia-bpf/bpfix  
**Commit:** `81d97e4a528456e0082a77f4fb6edd13fa092b7b`  
**Path:** `crates/bpfix/src/source.rs`

This directory holds a **predicates-only** snapshot for SoftwarX port-fidelity tests
(`tests/test_port_fidelity.py`). It does **not** vendor the full bpfix crate.

The Python helpers in `bpfix_adversarial/heuristics.py` match the seven
`looks_like_*` predicates character-for-character. The harness **reporter**
pipeline (raw mutant C + first top-down match) is intentionally not identical
to upstream (`latest_source_before` over log-emitted source comments).

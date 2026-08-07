# Upstream pin — eunomia-bpf/bpfix

**Repo:** https://github.com/eunomia-bpf/bpfix  
**Commit:** `81d97e4a528456e0082a77f4fb6edd13fa092b7b` (2026-07-11)  
**Paper:** Zheng et al., [arXiv:2607.02748](https://arxiv.org/abs/2607.02748)

## `looks_like_null_check` (source.rs)

Recognizes `if …` lines containing any of:

| Class | Patterns |
| --- | --- |
| Structural | `null`, `== 0`, `!= 0`, `== null`, `!= null` |
| Name-shaped | `!tmp`, `!val`, `!ptr`, `!value` |

Idiomatic renames such as `if (!entry)` / `if (!slot)` **miss** the name-shaped class unless a structural pattern is also present.

## Contrast (rename-insensitive)

`looks_like_nullable_return` keys off helper names (`bpf_map_lookup_elem`, `bpf_ringbuf_reserve`, …).

Pointer-provenance / packet-bounds SourceComment helpers similarly avoid bang-variable name lists.

## Evidence tiers

`ProofEventEvidence::SourceComment` vs `VerifierState` — extend this ontology in adjacent work; do not fork.

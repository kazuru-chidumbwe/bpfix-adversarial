# Upstream pin — eunomia-bpf/bpfix

**Repo:** https://github.com/eunomia-bpf/bpfix  
**Commit:** `81d97e4a528456e0082a77f4fb6edd13fa092b7b` (2026-07-11)  
**Paper:** Zheng et al., [arXiv:2607.02748](https://arxiv.org/abs/2607.02748)

## Obligation classification of main75

**Upstream's own classification** (SoftwareX Table 2): each main75 case ships
upstream's `diagnostic.txt`; its error ID is mapped to the `ProofObligation` that
upstream `crates/bpfix/src/classifier.rs` declares for that ID. Vendored inputs:
`fixtures/upstream/main75_upstream_diagnostics.json` (error ID, headline and SHA-256
of each `diagnostic.txt`, written by `tools/vendor_main75_diagnostics.py`) and
`fixtures/upstream/bpfix-source-rs-pin/classifier.rs`. The map lives in
`bpfix_adversarial.upstream_corpus.UPSTREAM_ERROR_OBLIGATION`; a unit test checks
each entry against the vendored classifier. Output: `results/upstream_obligations.*`.
The four templated families cover 47 of 75 cases.

**Keyword labels** (`keyword_label` in `main75_case_index.json`, `depth21_manifest.json`
and each `case_meta.json`) come from a case-name keyword heuristic,
`bpfix_adversarial.upstream_corpus.obligation_from_case_id`: `null`/`ringbuf` →
NullablePointer, `packet`/`xdp` → PacketBounds, `scalar`/`index`/`range`/`alu32` →
ScalarRange, anything else → PointerProvenance. They were used only to stratify the
depth-21 selection. They are not upstream's classification and agree with it on
16 of 75 cases.

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

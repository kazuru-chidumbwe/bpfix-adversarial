# RQ1 — Full bpfix CLI localizations (lab pad reject-oracles)

Upstream bpfix **0.1.9** @ `81d97e4a5284…` · stamp `20260801T181331Z` · WSL (offline log replay; not lab-server).
Primary report = rustc-style `--> file:LINE`. Top-1 / distance error use the locked **loss-anchored** rule (`docs/METRICS.md`).
Pad note: scalar __pad chains DCE under clang — nearest_bpf_pc stable across pads for these templates.

| Obligation | case_id | pad | d_true | primary | PC | top-1 | d_err | loss in snippet |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | --- |
| PacketBounds | `PB-pad0` | 0 | 3 | 15 | 6 | no | 3 | yes |
| PacketBounds | `PB-pad32` | 32 | 38 | 50 | 6 | no | 38 | yes |
| PacketBounds | `PB-pad8` | 8 | 14 | 26 | 6 | no | 14 | yes |
| PointerProvenance | `PP-pad0` | 0 | 3 | 15 | 7 | yes | 0 | yes |
| PointerProvenance | `PP-pad32` | 32 | 38 | 15 | 7 | yes | 0 | yes |
| PointerProvenance | `PP-pad8` | 8 | 14 | 15 | 7 | yes | 0 | yes |
| ScalarRange | `SR-pad0` | 0 | 2 | 13 | 7 | no | 2 | no |
| ScalarRange | `SR-pad32` | 32 | 37 | 48 | 7 | no | 37 | no |
| ScalarRange | `SR-pad8` | 8 | 13 | 24 | 7 | no | 13 | no |

## Reading (SoftwareX)

- **PacketBounds:** primary `-->` tracks the wide load (reject). Under loss-anchored **primary-arrow** scoring this is a top-1 miss; `d_err` tracks pad (3, 38, 14). The E001 snippet still *mentions* the narrow `data_end` check (loss) as related context — `loss in snippet = yes`. This is **not** a contradiction with `rq1_lab_distance.*` (SC port: PB honest): SC keys on contextual loss pickup; CLI primary is the headline location. Both are correct measurements of different things (headline vs full message).
- **PointerProvenance:** primary lands on the pkt⊕prandom wash (loss span) across pads (yes top-1); nearest PC stable (DCE) — validates the lab VS pattern.
- **ScalarRange:** primary stays on the unbound stack load (reject); loss (`prandom` idx) not in snippet — miss (no top-1), matching lab SC/VS.
- Offline WSL replay of stamped lab logs (not lab-server): bpfix diagnoses log text and does not re-verify, so the offline host is not a kernel-version confound.
- Complements `rq1_lab_distance.*` (SC-port / VS stop-site) with native upstream CLI output on the same logs.

Raw CLI dumps: `results/rq1_bpfix_cli_raw/`. Artifacts: `results/rq1_bpfix_cli.md` · `results/rq1_bpfix_cli.json`.


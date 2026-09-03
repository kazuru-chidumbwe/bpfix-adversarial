# RQ1 — Full bpfix CLI localizations (lab pad reject-oracles)

Upstream bpfix **0.1.9** @ `81d97e4a5284…` · stamp `20260801T181331Z` · WSL (offline log replay; not lab-server).
Primary report = rustc-style `--> file:LINE`. **top1_line** = exact `oracle_loss_code`; **top1_span** = span membership (`docs/METRICS.md`).
Pad note: scalar __pad chains DCE under clang — nearest_bpf_pc stable across pads for these templates.

| Obligation | case_id | pad | d_true | primary | PC | top1_line | top1_span | d_err | set_recall |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |
| PacketBounds | `PB-pad0` | 0 | 3 | 15 | 6 | no | no | 3 | yes |
| PacketBounds | `PB-pad32` | 32 | 38 | 50 | 6 | no | no | 38 | yes |
| PacketBounds | `PB-pad8` | 8 | 14 | 26 | 6 | no | no | 14 | yes |
| PointerProvenance | `PP-pad0` | 0 | 3 | 15 | 7 | no | yes | 1 | no |
| PointerProvenance | `PP-pad32` | 32 | 38 | 15 | 7 | no | yes | 1 | no |
| PointerProvenance | `PP-pad8` | 8 | 14 | 15 | 7 | no | yes | 1 | no |
| ScalarRange | `SR-pad0` | 0 | 2 | 13 | 7 | no | no | 2 | no |
| ScalarRange | `SR-pad32` | 32 | 37 | 48 | 7 | no | no | 37 | no |
| ScalarRange | `SR-pad8` | 8 | 13 | 24 | 7 | no | no | 13 | no |

## Reading (SoftwareX)

- **PacketBounds:** primary `-->` tracks the wide load (reject). Under **top1_line** this is a miss; `d_err` tracks pad (3, 38, 14). The E001 snippet still *mentions* the narrow `data_end` check (loss) as related context — `set_recall_message = yes`. This is **not** a contradiction with `rq1_lab_distance.*` (SC port: PB honest): SC keys on contextual loss pickup; CLI primary is the headline location. Both are correct measurements of different things (headline vs full message).
- **PointerProvenance:** primary lands on a later XOR-wash line in the loss **span** (top1_line=no; top1_span=yes); nearest PC stable (DCE) — span hit without exact first-line hit.
- **ScalarRange:** primary stays on the unbound stack load (reject); loss (`prandom` idx) not in snippet — miss (top1_line=no), matching lab SC/VS.
- Offline WSL replay of stamped lab logs (not lab-server): bpfix diagnoses log text and does not re-verify, so the offline host is not a kernel-version confound.
- Complements `rq1_lab_distance.*` (SC-port / VS stop-site) with native upstream CLI output on the same logs.

Raw CLI dumps: `results/rq1_bpfix_cli_raw/`. Artifacts: `results/rq1_bpfix_cli.md` · `results/rq1_bpfix_cli.json`.


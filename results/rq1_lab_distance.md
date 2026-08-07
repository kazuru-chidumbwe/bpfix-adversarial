# RQ1 — Lab distance vs construction oracle (template pads)

Source: `results/sc_vs_honesty.json` · stamp family `20260801T181331Z`.
Distance error: `d = |predicted − oracle_loss_code|` (absolute source-line error).
Do **not** zero distance on `top1_span` hits; span membership is a separate metric.
SC = bpfix SourceComment heuristic port; VS = verifier stop-site source map from log.
Companion: full upstream bpfix CLI on the same logs → `rq1_bpfix_cli.*`.

| Obligation | case_id | pad | loss | reject | SC | top1_line | top1_span | d_err | VS | top1_line | top1_span | d_err |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | ---: | --- | --- | ---: |
| PacketBounds | `PB-pad0` | 0 | 12 | 15 | 12 | yes | yes | 0 | 15 | no | no | 3 |
| PacketBounds | `PB-pad8` | 8 | 12 | 26 | 12 | yes | yes | 0 | 26 | no | no | 14 |
| PacketBounds | `PB-pad32` | 32 | 12 | 50 | 12 | yes | yes | 0 | 50 | no | no | 38 |
| PointerProvenance | `PP-pad0` | 0 | 14 | 17 | — | no | no | — | 15 | no | yes | 1 |
| PointerProvenance | `PP-pad8` | 8 | 14 | 28 | — | no | no | — | 15 | no | yes | 1 |
| PointerProvenance | `PP-pad32` | 32 | 14 | 52 | — | no | no | — | 15 | no | yes | 1 |
| ScalarRange | `SR-pad0` | 0 | 11 | 13 | — | no | no | — | 13 | no | no | 2 |
| ScalarRange | `SR-pad8` | 8 | 11 | 24 | — | no | no | — | 24 | no | no | 13 |
| ScalarRange | `SR-pad32` | 32 | 11 | 48 | — | no | no | — | 48 | no | no | 37 |

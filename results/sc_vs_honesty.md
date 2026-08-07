# SC vs VS injection-site agreement — lab stamp family `20260801T181331Z`

Scoring: **top1_line** (`predicted == oracle_loss_code`); **top1_span**
(membership in injection span); **distance_error** `|predicted − oracle_loss_code|`.
Legacy column `top1_vs_loss` aliases **top1_span**. Never score vs marked reject/use alone.

SC = bpfix SourceComment heuristic port on mutant source. VS = last source-mapped line in the **captured verifier log** (does not load object BTF; consumes log text only).

| Obligation | case_id | loss_span | SC line | SC top1_line | SC top1_span | VS line | VS top1_line | VS top1_span | lab reject | disagree (span) |
| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- |
| NullablePointer | `NP-brittle-pad0` | 19,20 | 19 | yes | yes | 23 | n/a | n/a | no | n/a |
| NullablePointer | `NP-brittle-pad32` | 19,20 | 19 | yes | yes | 58 | n/a | n/a | no | n/a |
| NullablePointer | `NP-brittle-pad8` | 19,20 | 19 | yes | yes | 34 | n/a | n/a | no | n/a |
| NullablePointer | `NP-idiomatic-nocheck-repaired-llm` | — | 21 | no | no | — | n/a | n/a | n/a | n/a |
| NullablePointer | `NP-idiomatic-nocheck-repaired-ollama` | — | 21 | n/a | n/a | — | n/a | n/a | no | n/a |
| NullablePointer | `NP-idiomatic-nocheck-repaired` | — | 21 | no | no | — | n/a | n/a | n/a | n/a |
| NullablePointer | `NP-idiomatic-nocheck` | — | 21 | no | no | 36 | no | no | yes | no |
| NullablePointer | `NP-idiomatic-pad0` | 19,20 | 17 | no | no | 23 | n/a | n/a | no | n/a |
| NullablePointer | `NP-idiomatic-pad32` | 19,20 | 17 | no | no | 58 | n/a | n/a | no | n/a |
| NullablePointer | `NP-idiomatic-pad8` | 19,20 | 17 | no | no | 34 | n/a | n/a | no | n/a |
| PacketBounds | `PB-pad0` | 12,13 | 12 | yes | yes | 15 | no | no | yes | yes |
| PacketBounds | `PB-pad32` | 12,13 | 12 | yes | yes | 50 | no | no | yes | yes |
| PacketBounds | `PB-pad8` | 12,13 | 12 | yes | yes | 26 | no | no | yes | yes |
| PointerProvenance | `PP-pad0` | 14,15 | — | no | no | 15 | no | yes | yes | yes |
| PointerProvenance | `PP-pad32` | 14,15 | — | no | no | 15 | no | yes | yes | yes |
| PointerProvenance | `PP-pad8` | 14,15 | — | no | no | 15 | no | yes | yes | yes |
| ScalarRange | `SR-pad0` | 11 | — | no | no | 13 | no | no | yes | no |
| ScalarRange | `SR-pad32` | 11 | — | no | no | 48 | no | no | yes | no |
| ScalarRange | `SR-pad8` | 11 | — | no | no | 24 | no | no | yes | no |

## PointerProvenance + ScalarRange

| case_id | SC line/span | VS line/span | note |
| --- | --- | --- | --- |
| `PP-pad0` | no/no | no/yes | Terminal verifier report maps to XOR wash (coincides with author injection span), not the later marked use — not a semantic proof-loss claim |
| `PP-pad32` | no/no | no/yes | Terminal verifier report maps to XOR wash (coincides with author injection span), not the later marked use — not a semantic proof-loss claim |
| `PP-pad8` | no/no | no/yes | Terminal verifier report maps to XOR wash (coincides with author injection span), not the later marked use — not a semantic proof-loss claim |
| `SR-pad0` | no/no | no/no | VS near-reject (stack load); SC has no scalar-guard → both miss loss |
| `SR-pad32` | no/no | no/no | VS near-reject (stack load); SC has no scalar-guard → both miss loss |
| `SR-pad8` | no/no | no/no | VS near-reject (stack load); SC has no scalar-guard → both miss loss |

## Summary by obligation (rejecting cases only)

| Obligation | n_reject | SC top1_line | SC top1_span | VS top1_line | VS top1_span | span disagree |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| NullablePointer | 1 | 0/1 | 0/1 | 0/1 | 0/1 | 0/1 |
| PacketBounds | 3 | 3/3 | 3/3 | 0/3 | 0/3 | 3/3 |
| PointerProvenance | 3 | 0/3 | 0/3 | 0/3 | 3/3 | 3/3 |
| ScalarRange | 3 | 0/3 | 0/3 | 0/3 | 0/3 | 0/3 |

## Takeaways

- **PP:** SC has no provenance heuristic (systematic miss). VS **top1_span** hits the XOR wash (coincides with author injection span; **top1_line** may miss if the map is not the first executable line) — not a semantic proof-loss claim.
- **SR:** SC finds no scalar guard on unbound-index templates (miss). VS reports the stack load (reject/use), not the unbound `idx` assignment (loss).
- **PB:** SC **top1_line** hits the under-check; VS hits the wide load (reject).
- **NP-nocheck:** SC reports lookup (before injection); VS reports reject deref — both miss line and span; still the RQ4 separation seed.
- Accepting NP-with-check rows: VS score n/a (no reject); SC rename story unchanged.

Artifacts: `results/sc_vs_honesty.json` · `results/sc_vs_honesty.md`


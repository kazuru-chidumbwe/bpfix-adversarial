# Baseline battery (rejecting cases in the stamped lab family)

Stamp filter `20260801T181331Z` · n=10 rejecting cases · random seed `42`.

| Baseline | top1_span hits | n | Row tally |
| --- | ---: | ---: | ---: |
| `terminal_site` | 3 | 10 | 3/10 |
| `random_line` | 1 | 10 | 1/10 |
| `oracle_upper` | 10 | 10 | 10/10 |

`terminal_site` hits by family: PointerProvenance 3. PointerProvenance templates are rejected at the pointer XOR inside the injection span, so those hits are construction-determined.

The `random_line` row is one draw per case (seed 42). Its expected top1_span hit count over these rows is 0.645 (SD 0.768), which is the stable comparison; the drawn tally is a single realisation.

Per-case rows: `baseline_battery.json`. `top1_vs_loss` is the legacy name for top1_span (span membership, not exact-line top1_line); tallies are pad-repeat rows, not a rate. `distance_error` is `abs(reported - oracle_loss_code)` (never zeroed on a span-only hit).

# Baseline battery (rejecting SoftwareX-stamp cases)

Stamp filter `20260801T181331Z` · n=10 rejecting cases · random seed `42`.

| Baseline | Top-1 hits | n | Rate |
| --- | ---: | ---: | ---: |
| `terminal_site` | 3 | 10 | 30% |
| `random_line` | 1 | 10 | 10% |
| `oracle_upper` | 10 | 10 | 100% |

Per-case rows: `baseline_battery.json`. `top1_vs_loss` is span membership; `distance_error` is `abs(reported - oracle_loss_code)` (never zeroed on a span-only hit).

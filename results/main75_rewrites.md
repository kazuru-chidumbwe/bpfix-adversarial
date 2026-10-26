# Verifier-visible rewrites of main75 on the cite pin

Run `campaigns/n3/lab/testbed-a-20261026T060709Z` · rules `docs/MAIN75-PIN-PROTOCOL.md Section 7`. A rewritten pair is valid when the rewritten buggy REJECTS and the rewritten fixed ACCEPTS. Repair sites are recomputed from the rewritten pair (R0).

| rewrite | applied | valid | invalid |
| --- | ---: | ---: | ---: |
| VPAD | 46 | 45 | 0 |
| VPADC | 68 | 67 | 0 |
| MACRO | 32 | 31 | 0 |
| INLINE | 48 | 43 | 4 |
| REORDER | 0 | 0 | 0 |
| SPLIT | 3 | 3 | 0 |

Primary location: on-site count before and after the rewrite, paired McNemar. Any label: the same for the primary or any labelled line. `orig` is the reporter's count on the applicable cases before the rewrite.

| rewrite | reporter | pairs | primary orig → rewrite | lost / gained | p | any label orig → rewrite | lost / gained | p | primary moved |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VPAD | bpfix | 45 | 11 → 3 | 9 / 1 | 0.0215 | 26 → 19 | 8 / 1 | 0.0391 | 6/45 (0.06–0.26) |
| VPAD | VerifierState | 45 | 11 → 3 | 9 / 1 | 0.0215 | 11 → 3 | 9 / 1 | 0.0215 | 6/45 (0.06–0.26) |
| VPAD | SourceComment | 45 | 7 → 7 | 0 / 0 | n/a | 7 → 7 | 0 / 0 | n/a | 0/45 (0.00–0.08) |
| VPAD | PrettyVerifier | 45 | 10 → 3 | 8 / 1 | 0.0391 | 10 → 3 | 8 / 1 | 0.0391 | 6/45 (0.06–0.26) |
| VPAD | PREVAIL | 45 | 8 → 2 | 6 / 0 | 0.0312 | 8 → 2 | 6 / 0 | 0.0312 | 5/45 (0.05–0.23) |
| VPAD | StaleLine (control) | 45 | 11 → 10 | 1 / 0 | 1.0000 | 11 → 10 | 1 / 0 | 1.0000 | 45/45 (0.92–1.00) |
| VPADC | bpfix | 67 | 29 → 21 | 9 / 1 | 0.0215 | 45 → 38 | 8 / 1 | 0.0391 | 6/67 (0.04–0.18) |
| VPADC | VerifierState | 67 | 29 → 21 | 9 / 1 | 0.0215 | 29 → 21 | 9 / 1 | 0.0215 | 6/67 (0.04–0.18) |
| VPADC | SourceComment | 67 | 9 → 9 | 0 / 0 | n/a | 9 → 9 | 0 / 0 | n/a | 0/67 (0.00–0.05) |
| VPADC | PrettyVerifier | 67 | 22 → 15 | 8 / 1 | 0.0391 | 22 → 15 | 8 / 1 | 0.0391 | 6/67 (0.04–0.18) |
| VPADC | PREVAIL | 67 | 22 → 16 | 6 / 0 | 0.0312 | 22 → 16 | 6 / 0 | 0.0312 | 5/67 (0.03–0.16) |
| VPADC | StaleLine (control) | 67 | 29 → 10 | 19 / 0 | 0.0000 | 29 → 10 | 19 / 0 | 0.0000 | 67/67 (0.95–1.00) |
| MACRO | bpfix | 31 | 16 → 16 | 0 / 0 | n/a | 22 → 22 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | VerifierState | 31 | 16 → 16 | 0 / 0 | n/a | 16 → 16 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | SourceComment | 31 | 7 → 7 | 0 / 0 | n/a | 7 → 7 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | PrettyVerifier | 31 | 12 → 12 | 0 / 0 | n/a | 12 → 12 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | PREVAIL | 31 | 11 → 11 | 0 / 0 | n/a | 11 → 11 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | StaleLine (control) | 31 | 16 → 6 | 15 / 5 | 0.0414 | 16 → 6 | 15 / 5 | 0.0414 | 31/31 (0.89–1.00) |
| INLINE | bpfix | 43 | 18 → 18 | 0 / 0 | n/a | 29 → 29 | 0 / 0 | n/a | 0/43 (0.00–0.08) |
| INLINE | VerifierState | 43 | 18 → 18 | 0 / 0 | n/a | 18 → 18 | 0 / 0 | n/a | 0/43 (0.00–0.08) |
| INLINE | SourceComment | 43 | 8 → 7 | 1 / 0 | 1.0000 | 8 → 7 | 1 / 0 | 1.0000 | 0/43 (0.00–0.08) |
| INLINE | PrettyVerifier | 43 | 16 → 16 | 0 / 0 | n/a | 16 → 16 | 0 / 0 | n/a | 0/43 (0.00–0.08) |
| INLINE | PREVAIL | 43 | 16 → 16 | 0 / 0 | n/a | 16 → 16 | 0 / 0 | n/a | 1/43 (0.00–0.12) |
| INLINE | StaleLine (control) | 43 | 18 → 6 | 17 / 5 | 0.0169 | 18 → 6 | 17 / 5 | 0.0169 | 43/43 (0.92–1.00) |
| SPLIT | bpfix | 3 | 0 → 0 | 0 / 0 | n/a | 1 → 1 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | VerifierState | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | SourceComment | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | PrettyVerifier | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | PREVAIL | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | StaleLine (control) | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |

Lost primary hits by mechanism: *unmoved* = the reporter's line is the same statement as before and the rewrite moved the repair site away from it; *moved* = the reporter's line changed.

| rewrite | reporter | lost | unmoved | moved |
| --- | --- | ---: | ---: | ---: |
| VPAD | bpfix | 9 | 9 | 0 |
| VPAD | VerifierState | 9 | 9 | 0 |
| VPAD | PrettyVerifier | 8 | 8 | 0 |
| VPAD | PREVAIL | 6 | 6 | 0 |
| VPAD | StaleLine (control) | 1 | 0 | 1 |
| VPADC | bpfix | 9 | 9 | 0 |
| VPADC | VerifierState | 9 | 9 | 0 |
| VPADC | PrettyVerifier | 8 | 8 | 0 |
| VPADC | PREVAIL | 6 | 6 | 0 |
| VPADC | StaleLine (control) | 19 | 0 | 19 |
| MACRO | StaleLine (control) | 15 | 0 | 15 |
| INLINE | SourceComment | 1 | 1 | 0 |
| INLINE | StaleLine (control) | 17 | 0 | 17 |

Invalid pairs: INLINE `map_value_branch_merge_001` (buggy COMPILE_FAIL, fixed COMPILE_FAIL); INLINE `map_value_inline_cookie_001` (buggy REJECT, fixed COMPILE_FAIL); INLINE `map_value_pointer_cookie_001` (buggy REJECT, fixed COMPILE_FAIL); INLINE `rs_agentsight_fs_overflow_counter_merge_001` (buggy REJECT, fixed COMPILE_FAIL)

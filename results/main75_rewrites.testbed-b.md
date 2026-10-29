# Verifier-visible rewrites of main75 on testbed-b

Run `campaigns/n3/lab/testbed-b-20261029T205135Z` · rules `docs/MAIN75-PIN-PROTOCOL.md Section 7`. A rewritten pair is valid when the rewritten buggy REJECTS and the rewritten fixed ACCEPTS. Repair sites are recomputed from the rewritten pair (R0).

| rewrite | applied | not scored in main75 | valid | invalid |
| --- | ---: | ---: | ---: | ---: |
| VPAD | 46 | 2 | 44 | 0 |
| VPADC | 68 | 2 | 66 | 0 |
| MACRO | 32 | 1 | 31 | 0 |
| INLINE | 48 | 2 | 42 | 4 |
| REORDER | 0 | 0 | 0 | 0 |
| SPLIT | 3 | 0 | 3 | 0 |

Not scored in main75 (no semantic hunk), so not scored here either: `rs_bpftime_sslsniff_perf_copy_len_001`, `rs_eunomia_wq_container_map_001`.

Primary location: on-site count before and after the rewrite, paired McNemar. Any label: the same for the primary or any labelled line. `orig` is the reporter's count on the applicable cases before the rewrite.

| rewrite | reporter | pairs | primary orig → rewrite | lost / gained | p | any label orig → rewrite | lost / gained | p | primary moved |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| VPAD | bpfix | 44 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/44 (0.00–0.08) |
| VPAD | VerifierState | 44 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/44 (0.00–0.08) |
| VPAD | SourceComment | 44 | 7 → 7 | 0 / 0 | n/a | 7 → 7 | 0 / 0 | n/a | 0/44 (0.00–0.08) |
| VPAD | PrettyVerifier | 44 | 10 → 3 | 8 / 1 | 0.0391 | 10 → 3 | 8 / 1 | 0.0391 | 6/44 (0.06–0.27) |
| VPAD | PREVAIL | 44 | 8 → 2 | 7 / 1 | 0.0703 | 8 → 2 | 7 / 1 | 0.0703 | 6/44 (0.06–0.27) |
| VPAD | StaleLine (control) | 44 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/44 (0.00–0.08) |
| VPADC | bpfix | 66 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/66 (0.00–0.06) |
| VPADC | VerifierState | 66 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/66 (0.00–0.06) |
| VPADC | SourceComment | 66 | 9 → 9 | 0 / 0 | n/a | 9 → 9 | 0 / 0 | n/a | 0/66 (0.00–0.06) |
| VPADC | PrettyVerifier | 66 | 22 → 15 | 8 / 1 | 0.0391 | 22 → 15 | 8 / 1 | 0.0391 | 6/66 (0.04–0.18) |
| VPADC | PREVAIL | 66 | 23 → 17 | 7 / 1 | 0.0703 | 23 → 17 | 7 / 1 | 0.0703 | 6/66 (0.04–0.18) |
| VPADC | StaleLine (control) | 66 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/66 (0.00–0.06) |
| MACRO | bpfix | 31 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | VerifierState | 31 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | SourceComment | 31 | 7 → 7 | 0 / 0 | n/a | 7 → 7 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | PrettyVerifier | 31 | 12 → 12 | 0 / 0 | n/a | 12 → 12 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | PREVAIL | 31 | 12 → 12 | 0 / 0 | n/a | 12 → 12 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| MACRO | StaleLine (control) | 31 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/31 (0.00–0.11) |
| INLINE | bpfix | 42 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/42 (0.00–0.08) |
| INLINE | VerifierState | 42 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/42 (0.00–0.08) |
| INLINE | SourceComment | 42 | 8 → 7 | 1 / 0 | 1.0000 | 8 → 7 | 1 / 0 | 1.0000 | 0/42 (0.00–0.08) |
| INLINE | PrettyVerifier | 42 | 16 → 16 | 0 / 0 | n/a | 16 → 16 | 0 / 0 | n/a | 0/42 (0.00–0.08) |
| INLINE | PREVAIL | 42 | 16 → 16 | 0 / 0 | n/a | 16 → 16 | 0 / 0 | n/a | 1/42 (0.00–0.12) |
| INLINE | StaleLine (control) | 42 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/42 (0.00–0.08) |
| SPLIT | bpfix | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | VerifierState | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | SourceComment | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | PrettyVerifier | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | PREVAIL | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |
| SPLIT | StaleLine (control) | 3 | 0 → 0 | 0 / 0 | n/a | 0 → 0 | 0 / 0 | n/a | 0/3 (0.00–0.56) |

Lost primary hits by mechanism: *unmoved* = the reporter's line is the same statement as before and the rewrite moved the repair site away from it; *moved* = the reporter's line changed.

| rewrite | reporter | lost | unmoved | moved |
| --- | --- | ---: | ---: | ---: |
| VPAD | PrettyVerifier | 8 | 8 | 0 |
| VPAD | PREVAIL | 7 | 7 | 0 |
| VPADC | PrettyVerifier | 8 | 8 | 0 |
| VPADC | PREVAIL | 7 | 7 | 0 |
| INLINE | SourceComment | 1 | 1 | 0 |

Primary location under the alternative repair-site rules, same valid pairs: before → after, lost / gained, exact McNemar p.

| rewrite | reporter | R1 | R2 |
| --- | --- | --- | --- |
| VPAD | bpfix | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| VPAD | VerifierState | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| VPAD | SourceComment | 8 → 7 (1 / 0, 1.0000) | 8 → 7 (1 / 0, 1.0000) |
| VPAD | PrettyVerifier | 18 → 6 (14 / 2, 0.0042) | 14 → 4 (11 / 1, 0.0063) |
| VPAD | PREVAIL | 14 → 5 (11 / 2, 0.0225) | 9 → 3 (7 / 1, 0.0703) |
| VPAD | StaleLine (control) | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| VPADC | bpfix | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| VPADC | VerifierState | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| VPADC | SourceComment | 11 → 10 (1 / 0, 1.0000) | 10 → 9 (1 / 0, 1.0000) |
| VPADC | PrettyVerifier | 30 → 18 (14 / 2, 0.0042) | 26 → 16 (11 / 1, 0.0063) |
| VPADC | PREVAIL | 29 → 20 (11 / 2, 0.0225) | 24 → 18 (7 / 1, 0.0703) |
| VPADC | StaleLine (control) | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| MACRO | bpfix | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| MACRO | VerifierState | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| MACRO | SourceComment | 7 → 7 (0 / 0, n/a) | 7 → 7 (0 / 0, n/a) |
| MACRO | PrettyVerifier | 17 → 17 (0 / 0, n/a) | 13 → 13 (0 / 0, n/a) |
| MACRO | PREVAIL | 15 → 15 (0 / 0, n/a) | 12 → 12 (0 / 0, n/a) |
| MACRO | StaleLine (control) | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| INLINE | bpfix | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| INLINE | VerifierState | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| INLINE | SourceComment | 9 → 8 (1 / 0, 1.0000) | 9 → 8 (1 / 0, 1.0000) |
| INLINE | PrettyVerifier | 23 → 22 (1 / 0, 1.0000) | 19 → 19 (0 / 0, n/a) |
| INLINE | PREVAIL | 22 → 20 (2 / 0, 0.5000) | 16 → 16 (0 / 0, n/a) |
| INLINE | StaleLine (control) | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| REORDER | bpfix | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| REORDER | VerifierState | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| REORDER | SourceComment | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| REORDER | PrettyVerifier | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| REORDER | PREVAIL | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| REORDER | StaleLine (control) | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| SPLIT | bpfix | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| SPLIT | VerifierState | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| SPLIT | SourceComment | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| SPLIT | PrettyVerifier | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| SPLIT | PREVAIL | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |
| SPLIT | StaleLine (control) | 0 → 0 (0 / 0, n/a) | 0 → 0 (0 / 0, n/a) |

Invalid pairs: INLINE `map_value_branch_merge_001` (buggy COMPILE_FAIL, fixed COMPILE_FAIL); INLINE `map_value_inline_cookie_001` (buggy REJECT, fixed COMPILE_FAIL); INLINE `map_value_pointer_cookie_001` (buggy REJECT, fixed COMPILE_FAIL); INLINE `rs_agentsight_fs_overflow_counter_merge_001` (buggy REJECT, fixed COMPILE_FAIL)

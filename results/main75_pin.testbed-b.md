# main75 on testbed-b

Run `campaigns/main75/lab/testbed-b-20261029T204226Z` · harness `0e54f95` · rules `docs/MAIN75-PIN-PROTOCOL.md`.
Cases 75; scored 73; informative (R0 chance < 0.25) 68.
Oracle: lines of upstream's own buggy → fixed edit. Intervals: Wilson 95% over distinct cases.

Excluded: `rs_bpftime_sslsniff_perf_copy_len_001` (no-semantic-hunk), `rs_eunomia_wq_container_map_001` (buggy-compile-fail)

## Primary location on a repair site (all cases)

| reporter | R0 | R1 | R2 |
| --- | ---: | ---: | ---: |
| bpfix | 0/73 (0.00–0.05) | 0/73 (0.00–0.05) | 0/73 (0.00–0.05) |
| VerifierState | 0/73 (0.00–0.05) | 0/73 (0.00–0.05) | 0/73 (0.00–0.05) |
| SourceComment | 9/73 (0.07–0.22) | 11/73 (0.09–0.25) | 10/73 (0.08–0.23) |
| PrettyVerifier | 27/73 (0.27–0.48) | 35/73 (0.37–0.59) | 31/73 (0.32–0.54) |
| PREVAIL | 28/73 (0.28–0.50) | 34/73 (0.36–0.58) | 29/73 (0.29–0.51) |
| uniform random (expected hits) | 7.0 | 14.6 | 10.2 |

bpfix, any label on a repair site (all): R0 0/73 (0.00–0.05), R1 0/73 (0.00–0.05), R2 0/73 (0.00–0.05); primary within 3 lines: R0 0/73 (0.00–0.05), R1 0/73 (0.00–0.05), R2 0/73 (0.00–0.05)

## Primary location on a repair site (informative cases)

| reporter | R0 | R1 | R2 |
| --- | ---: | ---: | ---: |
| bpfix | 0/68 (0.00–0.05) | 0/68 (0.00–0.05) | 0/68 (0.00–0.05) |
| VerifierState | 0/68 (0.00–0.05) | 0/68 (0.00–0.05) | 0/68 (0.00–0.05) |
| SourceComment | 8/68 (0.06–0.22) | 10/68 (0.08–0.25) | 9/68 (0.07–0.23) |
| PrettyVerifier | 25/68 (0.26–0.49) | 32/68 (0.36–0.59) | 29/68 (0.32–0.54) |
| PREVAIL | 27/68 (0.29–0.52) | 33/68 (0.37–0.60) | 28/68 (0.30–0.53) |
| uniform random (expected hits) | 5.3 | 11.4 | 7.4 |

bpfix, any label on a repair site (informative): R0 0/68 (0.00–0.05), R1 0/68 (0.00–0.05), R2 0/68 (0.00–0.05); primary within 3 lines: R0 0/68 (0.00–0.05), R1 0/68 (0.00–0.05), R2 0/68 (0.00–0.05)

## By case kind (R0, all cases)

| case kind | bpfix primary | bpfix any label | VerifierState | SourceComment | PrettyVerifier | PREVAIL | uniform random (expected hits) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| canary | 0/40 (0.00–0.09) | 0/40 (0.00–0.09) | 0/40 (0.00–0.09) | 5/40 (0.05–0.26) | 19/40 (0.33–0.62) | 18/40 (0.31–0.60) | 5.15 |
| real-project seed | 0/33 (0.00–0.10) | 0/33 (0.00–0.10) | 0/33 (0.00–0.10) | 4/33 (0.05–0.27) | 8/33 (0.13–0.41) | 10/33 (0.17–0.47) | 1.82 |

## By upstream obligation (R0, all cases)

| upstream obligation | bpfix primary | bpfix any label | VerifierState | SourceComment | PrettyVerifier | PREVAIL | uniform random (expected hits) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| ContextAccess | 0/6 (0.00–0.39) | 0/6 (0.00–0.39) | 0/6 (0.00–0.39) | 0/6 (0.00–0.39) | 2/6 (0.10–0.70) | 2/6 (0.10–0.70) | 0.29 |
| DynptrSafety | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0.64 |
| EnvironmentCapability | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0.26 |
| HelperArgument | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 1/2 (0.09–0.91) | 0/2 (0.00–0.66) | 0.47 |
| NullablePointer | 0/20 (0.00–0.16) | 0/20 (0.00–0.16) | 0/20 (0.00–0.16) | 5/20 (0.11–0.47) | 6/20 (0.15–0.52) | 5/20 (0.11–0.47) | 1.75 |
| PacketBounds | 0/11 (0.00–0.26) | 0/11 (0.00–0.26) | 0/11 (0.00–0.26) | 3/11 (0.10–0.57) | 4/11 (0.15–0.65) | 4/11 (0.15–0.65) | 0.85 |
| PointerProvenance | 0/9 (0.00–0.30) | 0/9 (0.00–0.30) | 0/9 (0.00–0.30) | 0/9 (0.00–0.30) | 9/9 (0.70–1.00) | 8/9 (0.56–0.98) | 0.83 |
| ReferenceLifecycle | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0.36 |
| ScalarRange | 0/6 (0.00–0.39) | 0/6 (0.00–0.39) | 0/6 (0.00–0.39) | 1/6 (0.03–0.56) | 2/6 (0.10–0.70) | 3/6 (0.19–0.81) | 0.68 |
| TypeContract | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 3/4 (0.30–0.95) | 3/4 (0.30–0.95) | 0.53 |
| unmapped | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 3/4 (0.30–0.95) | 0.32 |

## Exact McNemar, primary on a repair site

| pair | rule | only first | only second | p |
| --- | --- | ---: | ---: | ---: |
| bpfix vs VerifierState | R0 | 0 | 0 | n/a |
| bpfix vs VerifierState | R1 | 0 | 0 | n/a |
| bpfix vs VerifierState | R2 | 0 | 0 | n/a |
| bpfix vs SourceComment | R0 | 0 | 9 | 0.0039 |
| bpfix vs SourceComment | R1 | 0 | 11 | 0.0010 |
| bpfix vs SourceComment | R2 | 0 | 10 | 0.0020 |
| bpfix vs PrettyVerifier | R0 | 0 | 27 | 0.0000 |
| bpfix vs PrettyVerifier | R1 | 0 | 35 | 0.0000 |
| bpfix vs PrettyVerifier | R2 | 0 | 31 | 0.0000 |
| bpfix vs PREVAIL | R0 | 0 | 28 | 0.0000 |
| bpfix vs PREVAIL | R1 | 0 | 34 | 0.0000 |
| bpfix vs PREVAIL | R2 | 0 | 29 | 0.0000 |
| VerifierState vs SourceComment | R0 | 0 | 9 | 0.0039 |
| VerifierState vs SourceComment | R1 | 0 | 11 | 0.0010 |
| VerifierState vs SourceComment | R2 | 0 | 10 | 0.0020 |
| VerifierState vs PrettyVerifier | R0 | 0 | 27 | 0.0000 |
| VerifierState vs PrettyVerifier | R1 | 0 | 35 | 0.0000 |
| VerifierState vs PrettyVerifier | R2 | 0 | 31 | 0.0000 |
| VerifierState vs PREVAIL | R0 | 0 | 28 | 0.0000 |
| VerifierState vs PREVAIL | R1 | 0 | 34 | 0.0000 |
| VerifierState vs PREVAIL | R2 | 0 | 29 | 0.0000 |
| SourceComment vs PrettyVerifier | R0 | 5 | 23 | 0.0009 |
| SourceComment vs PrettyVerifier | R1 | 7 | 31 | 0.0001 |
| SourceComment vs PrettyVerifier | R2 | 5 | 26 | 0.0002 |
| SourceComment vs PREVAIL | R0 | 5 | 24 | 0.0005 |
| SourceComment vs PREVAIL | R1 | 6 | 29 | 0.0001 |
| SourceComment vs PREVAIL | R2 | 6 | 25 | 0.0009 |
| PrettyVerifier vs PREVAIL | R0 | 3 | 4 | 1.0000 |
| PrettyVerifier vs PREVAIL | R1 | 6 | 5 | 1.0000 |
| PrettyVerifier vs PREVAIL | R2 | 6 | 4 | 0.7539 |

## Exact McNemar by case kind, bpfix against each reporter (R0)

| case kind | reporter | only bpfix | only reporter | p |
| --- | --- | ---: | ---: | ---: |
| canary | VerifierState | 0 | 0 | n/a |
| canary | SourceComment | 0 | 5 | 0.0625 |
| canary | PrettyVerifier | 0 | 19 | 0.0000 |
| canary | PREVAIL | 0 | 18 | 0.0000 |
| real-project seed | VerifierState | 0 | 0 | n/a |
| real-project seed | SourceComment | 0 | 4 | 0.1250 |
| real-project seed | PrettyVerifier | 0 | 8 | 0.0078 |
| real-project seed | PREVAIL | 0 | 10 | 0.0020 |

## Metamorphic pairs (R0 sites mapped into each variant)

| variant | reporter | pairs | orig on site | variant on site | lost | gained | McNemar p | primary moved |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pad8 | bpfix | 64 | 0 | 0 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad8 | VerifierState | 64 | 0 | 0 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad8 | SourceComment | 64 | 9 | 9 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad8 | PrettyVerifier | 64 | 26 | 26 | 0 | 0 | n/a | 4/64 (0.02–0.15) |
| pad8 | PREVAIL | 64 | 27 | 27 | 0 | 0 | n/a | 4/64 (0.02–0.15) |
| pad8 | StaleLine (control) | 64 | 0 | 0 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad32 | bpfix | 64 | 0 | 0 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad32 | VerifierState | 64 | 0 | 0 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad32 | SourceComment | 64 | 9 | 9 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| pad32 | PrettyVerifier | 64 | 26 | 26 | 0 | 0 | n/a | 4/64 (0.02–0.15) |
| pad32 | PREVAIL | 64 | 27 | 27 | 0 | 0 | n/a | 4/64 (0.02–0.15) |
| pad32 | StaleLine (control) | 64 | 0 | 0 | 0 | 0 | n/a | 0/64 (0.00–0.06) |
| rename | bpfix | 34 | 0 | 0 | 0 | 0 | n/a | 0/34 (0.00–0.10) |
| rename | VerifierState | 34 | 0 | 0 | 0 | 0 | n/a | 0/34 (0.00–0.10) |
| rename | SourceComment | 34 | 5 | 1 | 4 | 0 | 0.1250 | 14/34 (0.26–0.58) |
| rename | PrettyVerifier | 34 | 11 | 11 | 0 | 0 | n/a | 0/34 (0.00–0.10) |
| rename | PREVAIL | 34 | 11 | 11 | 0 | 0 | n/a | 0/34 (0.00–0.10) |
| rename | StaleLine (control) | 34 | 0 | 0 | 0 | 0 | n/a | 0/34 (0.00–0.10) |

Metamorphic pairs excluded: `rs_actplane_mmap_pending_merge_001` rename (orig REJECT / rename COMPILE_FAIL)

pad8: the verifier's processed-instruction count differs from the unpadded capture in 63 of 66 padded programs; unchanged: `map_value_spill_cookie_001`, `rs_bpftime_opensnoop_stack_wrong_prog_type_001`, `rs_eunomia_wq_container_map_001`.

pad32: the verifier's processed-instruction count differs from the unpadded capture in 63 of 66 padded programs; unchanged: `map_value_spill_cookie_001`, `rs_bpftime_opensnoop_stack_wrong_prog_type_001`, `rs_eunomia_wq_container_map_001`.

# main75 on the cite pin

Run `campaigns/main75/lab/testbed-a-20261026T044355Z` · harness `b4d24f9` · rules `docs/MAIN75-PIN-PROTOCOL.md`.
Cases 75; scored 74; informative (R0 chance < 0.25) 69.
Oracle: lines of upstream's own buggy → fixed edit. Intervals: Wilson 95% over distinct cases.

Excluded: `rs_bpftime_sslsniff_perf_copy_len_001` (no-semantic-hunk)

## Primary location on a repair site (all cases)

| reporter | R0 | R1 | R2 |
| --- | ---: | ---: | ---: |
| bpfix | 34/74 (0.35–0.57) | 44/74 (0.48–0.70) | 38/74 (0.40–0.62) |
| VerifierState | 34/74 (0.35–0.57) | 44/74 (0.48–0.70) | 38/74 (0.40–0.62) |
| SourceComment | 9/74 (0.07–0.22) | 11/74 (0.09–0.25) | 10/74 (0.08–0.23) |
| PrettyVerifier | 27/74 (0.26–0.48) | 35/74 (0.36–0.59) | 31/74 (0.31–0.53) |
| PREVAIL | 0/74 (0.00–0.05) | 0/74 (0.00–0.05) | 0/74 (0.00–0.05) |
| uniform random (expected hits) | 7.0 | 14.7 | 10.2 |

bpfix, any label on a repair site (all): R0 50/74 (0.56–0.77), R1 64/74 (0.77–0.92), R2 54/74 (0.62–0.82); primary within 3 lines: R0 55/74 (0.63–0.83), R1 59/74 (0.69–0.87), R2 55/74 (0.63–0.83)

## Primary location on a repair site (informative cases)

| reporter | R0 | R1 | R2 |
| --- | ---: | ---: | ---: |
| bpfix | 30/69 (0.32–0.55) | 39/69 (0.45–0.68) | 34/69 (0.38–0.61) |
| VerifierState | 30/69 (0.32–0.55) | 39/69 (0.45–0.68) | 34/69 (0.38–0.61) |
| SourceComment | 8/69 (0.06–0.21) | 10/69 (0.08–0.25) | 9/69 (0.07–0.23) |
| PrettyVerifier | 25/69 (0.26–0.48) | 32/69 (0.35–0.58) | 29/69 (0.31–0.54) |
| PREVAIL | 0/69 (0.00–0.05) | 0/69 (0.00–0.05) | 0/69 (0.00–0.05) |
| uniform random (expected hits) | 5.3 | 11.5 | 7.5 |

bpfix, any label on a repair site (informative): R0 46/69 (0.55–0.77), R1 59/69 (0.75–0.92), R2 50/69 (0.61–0.82); primary within 3 lines: R0 50/69 (0.61–0.82), R1 54/69 (0.67–0.86), R2 50/69 (0.61–0.82)

## By case kind (R0, all cases)

| case kind | bpfix primary | bpfix any label | VerifierState | SourceComment | PrettyVerifier | PREVAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| canary | 23/40 (0.42–0.71) | 29/40 (0.57–0.84) | 23/40 (0.42–0.71) | 5/40 (0.05–0.26) | 19/40 (0.33–0.62) | 0/40 (0.00–0.09) |
| real-project seed | 11/34 (0.19–0.49) | 21/34 (0.45–0.76) | 11/34 (0.19–0.49) | 4/34 (0.05–0.27) | 8/34 (0.12–0.40) | 0/34 (0.00–0.10) |

## By upstream obligation (R0, all cases)

| upstream obligation | bpfix primary | bpfix any label | VerifierState | SourceComment | PrettyVerifier | PREVAIL |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ContextAccess | 2/6 (0.10–0.70) | 2/6 (0.10–0.70) | 2/6 (0.10–0.70) | 0/6 (0.00–0.39) | 2/6 (0.10–0.70) | 0/6 (0.00–0.39) |
| DynptrSafety | 1/2 (0.09–0.91) | 1/2 (0.09–0.91) | 1/2 (0.09–0.91) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) | 0/2 (0.00–0.66) |
| EnvironmentCapability | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) |
| HelperArgument | 2/3 (0.21–0.94) | 2/3 (0.21–0.94) | 2/3 (0.21–0.94) | 0/3 (0.00–0.56) | 1/3 (0.06–0.79) | 0/3 (0.00–0.56) |
| NullablePointer | 6/20 (0.15–0.52) | 16/20 (0.58–0.92) | 6/20 (0.15–0.52) | 5/20 (0.11–0.47) | 6/20 (0.15–0.52) | 0/20 (0.00–0.16) |
| PacketBounds | 4/11 (0.15–0.65) | 7/11 (0.35–0.85) | 4/11 (0.15–0.65) | 3/11 (0.10–0.57) | 4/11 (0.15–0.65) | 0/11 (0.00–0.26) |
| PointerProvenance | 9/9 (0.70–1.00) | 9/9 (0.70–1.00) | 9/9 (0.70–1.00) | 0/9 (0.00–0.30) | 9/9 (0.70–1.00) | 0/9 (0.00–0.30) |
| ReferenceLifecycle | 0/5 (0.00–0.43) | 2/5 (0.12–0.77) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) |
| ScalarRange | 4/6 (0.30–0.90) | 5/6 (0.44–0.97) | 4/6 (0.30–0.90) | 1/6 (0.03–0.56) | 2/6 (0.10–0.70) | 0/6 (0.00–0.39) |
| TypeContract | 3/4 (0.30–0.95) | 3/4 (0.30–0.95) | 3/4 (0.30–0.95) | 0/4 (0.00–0.49) | 3/4 (0.30–0.95) | 0/4 (0.00–0.49) |
| unmapped | 3/4 (0.30–0.95) | 3/4 (0.30–0.95) | 3/4 (0.30–0.95) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) |

## Exact McNemar, primary on a repair site

| pair | rule | only first | only second | p |
| --- | --- | ---: | ---: | ---: |
| bpfix vs VerifierState | R0 | 0 | 0 | n/a |
| bpfix vs VerifierState | R1 | 0 | 0 | n/a |
| bpfix vs VerifierState | R2 | 0 | 0 | n/a |
| bpfix vs SourceComment | R0 | 30 | 5 | 0.0000 |
| bpfix vs SourceComment | R1 | 38 | 5 | 0.0000 |
| bpfix vs SourceComment | R2 | 33 | 5 | 0.0000 |
| bpfix vs PrettyVerifier | R0 | 7 | 0 | 0.0156 |
| bpfix vs PrettyVerifier | R1 | 9 | 0 | 0.0039 |
| bpfix vs PrettyVerifier | R2 | 7 | 0 | 0.0156 |
| bpfix vs PREVAIL | R0 | 34 | 0 | 0.0000 |
| bpfix vs PREVAIL | R1 | 44 | 0 | 0.0000 |
| bpfix vs PREVAIL | R2 | 38 | 0 | 0.0000 |
| VerifierState vs SourceComment | R0 | 30 | 5 | 0.0000 |
| VerifierState vs SourceComment | R1 | 38 | 5 | 0.0000 |
| VerifierState vs SourceComment | R2 | 33 | 5 | 0.0000 |
| VerifierState vs PrettyVerifier | R0 | 7 | 0 | 0.0156 |
| VerifierState vs PrettyVerifier | R1 | 9 | 0 | 0.0039 |
| VerifierState vs PrettyVerifier | R2 | 7 | 0 | 0.0156 |
| VerifierState vs PREVAIL | R0 | 34 | 0 | 0.0000 |
| VerifierState vs PREVAIL | R1 | 44 | 0 | 0.0000 |
| VerifierState vs PREVAIL | R2 | 38 | 0 | 0.0000 |
| SourceComment vs PrettyVerifier | R0 | 5 | 23 | 0.0009 |
| SourceComment vs PrettyVerifier | R1 | 7 | 31 | 0.0001 |
| SourceComment vs PrettyVerifier | R2 | 5 | 26 | 0.0002 |
| SourceComment vs PREVAIL | R0 | 9 | 0 | 0.0039 |
| SourceComment vs PREVAIL | R1 | 11 | 0 | 0.0010 |
| SourceComment vs PREVAIL | R2 | 10 | 0 | 0.0020 |
| PrettyVerifier vs PREVAIL | R0 | 27 | 0 | 0.0000 |
| PrettyVerifier vs PREVAIL | R1 | 35 | 0 | 0.0000 |
| PrettyVerifier vs PREVAIL | R2 | 31 | 0 | 0.0000 |

## Metamorphic pairs (R0 sites mapped into each variant)

| variant | reporter | pairs | orig on site | variant on site | lost | gained | McNemar p | primary moved |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| pad8 | bpfix | 65 | 33 | 33 | 0 | 0 | n/a | 4/65 (0.02–0.15) |
| pad8 | VerifierState | 65 | 33 | 33 | 0 | 0 | n/a | 4/65 (0.02–0.15) |
| pad8 | SourceComment | 65 | 9 | 9 | 0 | 0 | n/a | 0/65 (0.00–0.06) |
| pad8 | PrettyVerifier | 65 | 26 | 26 | 0 | 0 | n/a | 4/65 (0.02–0.15) |
| pad8 | PREVAIL | 65 | 0 | 0 | 0 | 0 | n/a | 0/65 (0.00–0.06) |
| pad8 | StaleLine (control) | 65 | 33 | 0 | 33 | 0 | 0.0000 | 65/65 (0.94–1.00) |
| pad32 | bpfix | 65 | 33 | 33 | 0 | 0 | n/a | 4/65 (0.02–0.15) |
| pad32 | VerifierState | 65 | 33 | 33 | 0 | 0 | n/a | 4/65 (0.02–0.15) |
| pad32 | SourceComment | 65 | 9 | 9 | 0 | 0 | n/a | 0/65 (0.00–0.06) |
| pad32 | PrettyVerifier | 65 | 26 | 26 | 0 | 0 | n/a | 4/65 (0.02–0.15) |
| pad32 | PREVAIL | 65 | 0 | 0 | 0 | 0 | n/a | 0/65 (0.00–0.06) |
| pad32 | StaleLine (control) | 65 | 33 | 0 | 33 | 0 | 0.0000 | 65/65 (0.94–1.00) |
| rename | bpfix | 35 | 12 | 12 | 0 | 0 | n/a | 0/35 (0.00–0.10) |
| rename | VerifierState | 35 | 12 | 12 | 0 | 0 | n/a | 0/35 (0.00–0.10) |
| rename | SourceComment | 35 | 5 | 1 | 4 | 0 | 0.1250 | 14/35 (0.26–0.56) |
| rename | PrettyVerifier | 35 | 11 | 11 | 0 | 0 | n/a | 0/35 (0.00–0.10) |
| rename | PREVAIL | 35 | 0 | 0 | 0 | 0 | n/a | 0/35 (0.00–0.10) |
| rename | StaleLine (control) | 35 | 12 | 12 | 0 | 0 | n/a | 0/35 (0.00–0.10) |

Metamorphic pairs excluded: `rs_actplane_mmap_pending_merge_001` rename (orig REJECT / rename COMPILE_FAIL)

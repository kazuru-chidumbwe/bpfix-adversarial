# Wild cases on the cite pin

Rules `docs/WILD-CORPUS-PROTOCOL.md (scoring rules for the wild cases)`. Included cases 2; scored 1.
Oracle: lines of the developer's own parent → fix edit, per file. Intervals: Wilson 95% over distinct cases.

## Yield per batch

| batch | candidates | pass 1 | screened | included | I3 | I4 | C | E4 | E5 | included / screened |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| batch 1 | 280 | 143 | 81 | 1 | 5 | 7 | 0 | 22 | 46 | 0.012 (0.002–0.067) |
| batch 2 | 141 | 41 | 41 | 0 | 2 | 7 | 0 | 21 | 11 | 0.000 (0.000–0.086) |
| batch 3 | 4606 | 355 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | n/a |
| pooled | 5027 | 539 | 122 | 1 | 7 | 14 | 0 | 43 | 57 | 0.008 (0.001–0.045) |

Not scored: rank 2043 (pending reporter outputs: PREVAIL, PrettyVerifier, bpfix)

## Primary location on a repair site, pooled (1 cases, 1 informative)

| reporter | R0 | R1 | R2 | any label R0 | within 3 R0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| bpfix | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| VerifierState | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| SourceComment | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) |
| PrettyVerifier | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| PREVAIL | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| uniform random (expected hits) | 0.02 | 0.03 | 0.02 | | |

## Primary location on a repair site, batch 1 (1 cases, 1 informative)

| reporter | R0 | R1 | R2 | any label R0 | within 3 R0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| bpfix | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| VerifierState | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| SourceComment | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) |
| PrettyVerifier | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| PREVAIL | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| uniform random (expected hits) | 0.02 | 0.03 | 0.02 | | |

## Per case (R0)

| rank | repo | program | bpfix | VerifierState | SourceComment | PrettyVerifier | PREVAIL |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 111 | iovisor/bcc | `block_rq_complete` | **hit** biosnoop.bpf.c:182 | **hit** biosnoop.bpf.c:182 | none | **hit** biosnoop.bpf.c:182 | **hit** biosnoop.bpf.c:182 |

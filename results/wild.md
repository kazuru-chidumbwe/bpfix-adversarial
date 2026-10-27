# Wild cases on the cite pin

Rules `docs/WILD-CORPUS-PROTOCOL.md (scoring rules for the wild cases)`. Included cases 1; scored 1.
Oracle: lines of the developer's own parent → fix edit, per file. Intervals: Wilson 95% over distinct cases.

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

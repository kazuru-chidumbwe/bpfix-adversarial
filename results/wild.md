# Wild cases on the cite pin

Rules `docs/WILD-CORPUS-PROTOCOL.md (scoring rules for the wild cases)`. Case directories 6; scored 5.
Oracle: lines of the developer's own parent → fix edit, per file. Intervals: Wilson 95% over distinct cases.

## Yield per batch

| batch | candidates | pass 1 | screened | included | I3 | I4 | C | E1 | E3 | N0 | E4 | E5 | included / screened |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| batch 1 | 280 | 143 | 81 | 1 | 5 | 7 | 0 | 0 | 0 | 0 | 22 | 46 | 0.012 (0.002–0.067) |
| batch 2 | 141 | 41 | 41 | 0 | 2 | 7 | 0 | 0 | 0 | 0 | 21 | 11 | 0.000 (0.000–0.086) |
| batch 3 | 4606 | 355 | 355 | 4 | 23 | 22 | 1 | 0 | 1 | 0 | 115 | 189 | 0.011 (0.004–0.029) |
| pooled | 5027 | 539 | 477 | 5 | 30 | 36 | 1 | 0 | 1 | 0 | 158 | 246 | 0.010 (0.004–0.024) |

Not scored: rank 4259 (pass 2: E3 (same bug as rank 4049 fixed on the PR #2667 branch that 4049 merges; 4049 ranks earlier))

## Primary location on a repair site, pooled (5 cases, 5 informative)

| reporter | R0 | R1 | R2 | any label R0 | within 3 R0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| bpfix | 2/5 (0.12–0.77) | 3/5 (0.23–0.88) | 2/5 (0.12–0.77) | 4/5 (0.38–0.96) | 3/5 (0.23–0.88) |
| VerifierState | 2/5 (0.12–0.77) | 3/5 (0.23–0.88) | 2/5 (0.12–0.77) | 2/5 (0.12–0.77) | 3/5 (0.23–0.88) |
| SourceComment | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) | 0/5 (0.00–0.43) |
| PrettyVerifier | 2/5 (0.12–0.77) | 2/5 (0.12–0.77) | 2/5 (0.12–0.77) | 2/5 (0.12–0.77) | 3/5 (0.23–0.88) |
| PREVAIL | 1/5 (0.04–0.62) | 1/5 (0.04–0.62) | 1/5 (0.04–0.62) | 1/5 (0.04–0.62) | 1/5 (0.04–0.62) |
| uniform random (expected hits) | 0.19 | 0.36 | 0.37 | | |

## Primary location on a repair site, batch 1 (1 cases, 1 informative)

| reporter | R0 | R1 | R2 | any label R0 | within 3 R0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| bpfix | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| VerifierState | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| SourceComment | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) | 0/1 (0.00–0.79) |
| PrettyVerifier | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| PREVAIL | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) | 1/1 (0.21–1.00) |
| uniform random (expected hits) | 0.02 | 0.03 | 0.02 | | |

## Primary location on a repair site, batch 3 (4 cases, 4 informative)

| reporter | R0 | R1 | R2 | any label R0 | within 3 R0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| bpfix | 1/4 (0.05–0.70) | 2/4 (0.15–0.85) | 1/4 (0.05–0.70) | 3/4 (0.30–0.95) | 2/4 (0.15–0.85) |
| VerifierState | 1/4 (0.05–0.70) | 2/4 (0.15–0.85) | 1/4 (0.05–0.70) | 1/4 (0.05–0.70) | 2/4 (0.15–0.85) |
| SourceComment | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) |
| PrettyVerifier | 1/4 (0.05–0.70) | 1/4 (0.05–0.70) | 1/4 (0.05–0.70) | 1/4 (0.05–0.70) | 2/4 (0.15–0.85) |
| PREVAIL | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) | 0/4 (0.00–0.49) |
| uniform random (expected hits) | 0.17 | 0.33 | 0.35 | | |

## Per case (R0)

| rank | repo | program | bpfix | VerifierState | SourceComment | PrettyVerifier | PREVAIL |
| ---: | --- | --- | --- | --- | --- | --- | --- |
| 111 | iovisor/bcc | `block_rq_complete` | **hit** biosnoop.bpf.c:182 | **hit** biosnoop.bpf.c:182 | none | **hit** biosnoop.bpf.c:182 | **hit** biosnoop.bpf.c:182 |
| 2043 | aquasecurity/tracee | `syscall__execve_enter` | buffer.h:368 | buffer.h:368 | tracee.bpf.c:53 | none | none |
| 3285 | ThisSeanZhang/landscape | `xdp_lan_root` | **hit** xdp_meta.h:41 | **hit** xdp_meta.h:41 | none | **hit** xdp_meta.h:41 | none |
| 4049 | parca-dev/parca-agent | `entrypoint` | native.bpf.c:491 | native.bpf.c:491 | native.bpf.c:322 | native.bpf.c:519 | native.bpf.c:491 |
| 6257 | inspektor-gadget/inspektor-gadget | `ig_seccomp_e` | program.bpf.c:157 | program.bpf.c:157 | program.bpf.c:110 | program.bpf.c:157 | none |

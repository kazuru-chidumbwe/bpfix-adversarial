# RQ3 — SourceComment vs VerifierState

| case | SC null-check? | SC line | VS line | SC ok | VS ok | Disagree |
| --- | --- | ---: | ---: | --- | --- | --- |
| NP-idiomatic-pad8 | no | 12 | 14 | no | yes | yes |
| NP-brittle-pad8 | yes | 14 | 14 | yes | yes | no |
| PB-pad0 | no | 10 | 10 | yes | yes | no |

Lead example: **NP-idiomatic-pad8** — VerifierState remains oracle-correct; SourceComment misses `if (!entry)` establish.

# SourceComment vs VerifierState

| case | SC null-check? | SC line | VS line (asserted) | SC matches oracle |
| --- | --- | ---: | ---: | --- |
| NP-idiomatic-pad8 | no | 12 | 14 | no |
| NP-brittle-pad8 | yes | 14 | 14 | yes |
| PB-pad0 | no | 10 | 10 | yes |

Lead example: **NP-idiomatic-pad8**. SourceComment misses the `if (!entry)` establish under rename.

Illustration of the tier contract on synthetic fixture logs, not an empirical finding. The VS line is carried by each fixture's annotation rather than measured from the log, so it is reported for context and is not scored against the oracle. Lab-derived SourceComment and VerifierState outcomes are in `sc_vs_honesty.*`.

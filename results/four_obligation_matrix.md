# Four-obligation stratified mutant matrix

Construction-time oracle markers scanned from mutant sources. The marker columns give the line of the ORACLE_* comment; the code columns give the line scoring uses: the first executable line of the injection span (`oracle_loss_code`), or for an empty span the last executable line before the marker (`NP-idiomatic-nocheck`). Score against the code columns, never the marker columns.
Log tier: `captured` = lab bpftool; `synthetic` = fixture; `missing` = no log yet.

## NullablePointer (n=7)

| case_id | pad | loss marker | loss code | reject marker | reject code | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `NP-brittle-pad0` | 0 | 18 | 19 | 21 | 22 | captured | `6ef5414b7cec…` | SC name-list hit expected (!ptr) |
| `NP-brittle-pad32` | 32 | 18 | 19 | 56 | 57 | captured | `7b81929baf37…` | SC name-list hit expected (!ptr) |
| `NP-brittle-pad8` | 8 | 18 | 19 | 32 | 33 | captured | `ecc7c7d84085…` | SC name-list hit expected (!ptr) |
| `NP-idiomatic-nocheck` | n/a | 22 | 21 | 35 | 36 | captured | `84584b7274c9…` | rejecting NP template (missing check) |
| `NP-idiomatic-pad0` | 0 | 18 | 19 | 21 | 22 | captured | `a579a464e6ee…` | SC name-list miss expected (!entry) |
| `NP-idiomatic-pad32` | 32 | 18 | 19 | 56 | 57 | captured | `d25136325d9a…` | SC name-list miss expected (!entry) |
| `NP-idiomatic-pad8` | 8 | 18 | 19 | 32 | 33 | captured | `c7a70e2eb136…` | SC name-list miss expected (!entry) |

## PacketBounds (n=3)

| case_id | pad | loss marker | loss code | reject marker | reject code | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `PB-pad0` | 0 | 11 | 12 | 14 | 15 | captured | `f9c932fac4d1…` | packet under-check template |
| `PB-pad32` | 32 | 11 | 12 | 49 | 50 | captured | `da86563fc0ff…` | packet under-check template |
| `PB-pad8` | 8 | 11 | 12 | 25 | 26 | captured | `04566b403ec9…` | packet under-check template |

## PointerProvenance (n=3)

| case_id | pad | loss marker | loss code | reject marker | reject code | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `PP-pad0` | 0 | 13 | 14 | 16 | 17 | captured | `671448ef6c90…` | pkt⊕prandom wash (reject: unbounded pkt math) |
| `PP-pad32` | 32 | 13 | 14 | 51 | 52 | captured | `4782eda2d95c…` | pkt⊕prandom wash (reject: unbounded pkt math) |
| `PP-pad8` | 8 | 13 | 14 | 27 | 28 | captured | `0517861591a1…` | pkt⊕prandom wash (reject: unbounded pkt math) |

## ScalarRange (n=3)

| case_id | pad | loss marker | loss code | reject marker | reject code | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- | --- | --- |
| `SR-pad0` | 0 | 10 | 11 | 12 | 13 | captured | `da0ce735831d…` | unbound stack[prandom] (reject: unbounded mem) |
| `SR-pad32` | 32 | 10 | 11 | 47 | 48 | captured | `fa42f2ab68e9…` | unbound stack[prandom] (reject: unbounded mem) |
| `SR-pad8` | 8 | 10 | 11 | 23 | 24 | captured | `29f92d41180e…` | unbound stack[prandom] (reject: unbounded mem) |

**Summary:** 16 mutants · 16 lab-captured logs · 0 synthetic · 0 missing.

SC/VS scores on the lab captures are in `sc_vs_honesty.*`; the rename boundary is in `rename_honesty.*`; `np_pair_score.json` and `tier_disagreement.*` are synthetic-fixture illustrations. This matrix is the stratified coverage table for the four families.

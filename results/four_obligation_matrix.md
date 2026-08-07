# Four-obligation stratified mutant matrix (§6.5)

Construction-time oracle markers scanned from mutant sources.
Log tier: `captured` = lab bpftool; `synthetic` = fixture; `missing` = no log yet.

## NullablePointer (n=10)

| case_id | pad | loss | reject | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `NP-brittle-pad0` | 0 | 18 | 21 | captured | `6ef5414b7cec…` | SC name-list hit expected (!ptr) |
| `NP-brittle-pad32` | 32 | 18 | 56 | captured | `7b81929baf37…` | SC name-list hit expected (!ptr) |
| `NP-brittle-pad8` | 8 | 18 | 32 | captured | `ecc7c7d84085…` | SC name-list hit expected (!ptr) |
| `NP-idiomatic-nocheck-repaired-llm` | None | 24 | 37 | missing | `—` | RQ4 repaired program (wrong-tip protocol) |
| `NP-idiomatic-nocheck-repaired-ollama` | None | None | None | captured | `7f2d340b18eb…` | RQ4 repaired program (wrong-tip protocol) |
| `NP-idiomatic-nocheck-repaired` | None | 24 | 37 | missing | `—` | RQ4 repaired program (wrong-tip protocol) |
| `NP-idiomatic-nocheck` | None | 22 | 35 | captured | `84584b7274c9…` | RQ4 failing seed (missing check) |
| `NP-idiomatic-pad0` | 0 | 18 | 21 | captured | `a579a464e6ee…` | SC name-list miss expected (!entry) |
| `NP-idiomatic-pad32` | 32 | 18 | 56 | captured | `d25136325d9a…` | SC name-list miss expected (!entry) |
| `NP-idiomatic-pad8` | 8 | 18 | 32 | captured | `c7a70e2eb136…` | SC name-list miss expected (!entry) |

## PacketBounds (n=3)

| case_id | pad | loss | reject | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `PB-pad0` | 0 | 11 | 14 | captured | `f9c932fac4d1…` | packet under-check template |
| `PB-pad32` | 32 | 11 | 49 | captured | `da86563fc0ff…` | packet under-check template |
| `PB-pad8` | 8 | 11 | 25 | captured | `04566b403ec9…` | packet under-check template |

## PointerProvenance (n=3)

| case_id | pad | loss | reject | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `PP-pad0` | 0 | 13 | 16 | captured | `671448ef6c90…` | pkt⊕prandom wash (reject: unbounded pkt math) |
| `PP-pad32` | 32 | 13 | 51 | captured | `4782eda2d95c…` | pkt⊕prandom wash (reject: unbounded pkt math) |
| `PP-pad8` | 8 | 13 | 27 | captured | `0517861591a1…` | pkt⊕prandom wash (reject: unbounded pkt math) |

## ScalarRange (n=3)

| case_id | pad | loss | reject | log_tier | log_sha256 | note |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `SR-pad0` | 0 | 10 | 12 | captured | `da0ce735831d…` | unbound stack[prandom] (reject: unbounded mem) |
| `SR-pad32` | 32 | 10 | 47 | captured | `fa42f2ab68e9…` | unbound stack[prandom] (reject: unbounded mem) |
| `SR-pad8` | 8 | 10 | 23 | captured | `29f92d41180e…` | unbound stack[prandom] (reject: unbounded mem) |

**Summary:** 19 mutants · 17 lab-captured logs · 0 synthetic · 2 missing.

Honesty scores vs construction oracle for SC/VS remain in `rename_honesty.*`, `np_pair_score.json`, `tier_disagreement.*`; this matrix is the stratified coverage table for the four-obligation review.

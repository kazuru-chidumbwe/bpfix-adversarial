# Oracle-independence controls (minimal, SoftwareX-stamp)

Stamp filter `20260801T181331Z`. Offline only — no new lab captures.

| Control | Pass | n | Rate |
| --- | ---: | ---: | ---: |
| negative (markers + ACCEPT) | 6 | 6 | 100% |
| positive (PB stop ≠ injection) | 3 | 3 | 100% |
| compiler-preservation (source map) | 10 | 10 | 100% |

## Negative control

Injection markers present; lab load **ACCEPT**s.

| case_id | obligation | loss_code |
| --- | --- | ---: |
| `NP-brittle-pad0` | NullablePointer | 19 |
| `NP-brittle-pad32` | NullablePointer | 19 |
| `NP-brittle-pad8` | NullablePointer | 19 |
| `NP-idiomatic-pad0` | NullablePointer | 19 |
| `NP-idiomatic-pad32` | NullablePointer | 19 |
| `NP-idiomatic-pad8` | NullablePointer | 19 |

## Positive control (PacketBounds)

VerifierState stop-site outside injection span.

| case_id | loss | VS | SC top-1 | VS top-1 | diverge |
| --- | ---: | ---: | --- | --- | --- |
| `PB-pad0` | 12 | 15 | yes | no | yes |
| `PB-pad32` | 12 | 50 | yes | no | yes |
| `PB-pad8` | 12 | 26 | yes | no | yes |

## Compiler-preservation (verifier source map)

| case_id | injection in map | reject in map | pass |
| --- | --- | --- | --- |
| `NP-idiomatic-nocheck` | yes | yes | yes |
| `PB-pad0` | yes | yes | yes |
| `PB-pad32` | yes | yes | yes |
| `PB-pad8` | yes | yes | yes |
| `PP-pad0` | yes | no | yes |
| `PP-pad32` | yes | no | yes |
| `PP-pad8` | yes | no | yes |
| `SR-pad0` | yes | yes | yes |
| `SR-pad32` | yes | yes | yes |
| `SR-pad8` | yes | yes | yes |

JSON: `oracle_controls.json`.

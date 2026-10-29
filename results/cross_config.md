# main75 on two configurations

Rules `docs/MAIN75-PIN-PROTOCOL.md Section 8`. Pin run `campaigns/main75/lab/testbed-a-20261026T044355Z`; testbed-b run `campaigns/main75/lab/testbed-b-20261029T204226Z`.
Scored: pin 74, testbed-b 73, both 73.

## Included on one host only

| case | pin | testbed-b |
| --- | --- | --- |
| `rs_eunomia_wq_container_map_001` | scored | buggy-compile-fail |

## Primary location on a repair site, cases scored on both hosts (73)

| reporter | rule | pin | testbed-b | pin only | testbed-b only | McNemar p | same primary line |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| bpfix | R0 | 34 | 0 | 34 | 0 | 0.0000 | 0/73 |
| bpfix | R1 | 43 | 0 | 43 | 0 | 0.0000 |  |
| bpfix | R2 | 38 | 0 | 38 | 0 | 0.0000 |  |
| VerifierState | R0 | 34 | 0 | 34 | 0 | 0.0000 | 0/73 |
| VerifierState | R1 | 43 | 0 | 43 | 0 | 0.0000 |  |
| VerifierState | R2 | 38 | 0 | 38 | 0 | 0.0000 |  |
| SourceComment | R0 | 9 | 9 | 0 | 0 | n/a | 73/73 |
| SourceComment | R1 | 11 | 11 | 0 | 0 | n/a |  |
| SourceComment | R2 | 10 | 10 | 0 | 0 | n/a |  |
| PrettyVerifier | R0 | 27 | 27 | 0 | 0 | n/a | 72/73 |
| PrettyVerifier | R1 | 35 | 35 | 0 | 0 | n/a |  |
| PrettyVerifier | R2 | 31 | 31 | 0 | 0 | n/a |  |
| PREVAIL | R0 | 29 | 28 | 1 | 0 | 1.0000 | 67/73 |
| PREVAIL | R1 | 39 | 34 | 5 | 0 | 0.0625 |  |
| PREVAIL | R2 | 34 | 29 | 5 | 0 | 0.0625 |  |

## Claims of Sections 3.2 and 3.4, evaluated on each host's own results

| claim | pin | holds | testbed-b | holds |
| --- | --- | --- | --- | --- |
| the four locating reporters at least twice the random line (R0) | bpfix 34, VerifierState 34, PrettyVerifier 27, PREVAIL 29; random 7.0 | yes | bpfix 0, VerifierState 0, PrettyVerifier 27, PREVAIL 28; random 6.97 | no |
| the four locating reporters at least twice the random line (R1) | bpfix 44, VerifierState 44, PrettyVerifier 35, PREVAIL 40; random 14.67 | yes | bpfix 0, VerifierState 0, PrettyVerifier 35, PREVAIL 34; random 14.59 | no |
| the four locating reporters at least twice the random line (R2) | bpfix 38, VerifierState 38, PrettyVerifier 31, PREVAIL 34; random 10.22 | yes | bpfix 0, VerifierState 0, PrettyVerifier 31, PREVAIL 29; random 10.2 | no |
| SourceComment less than twice the random line (R0) | 9; random 7.0 | yes | 9; random 6.97 | yes |
| SourceComment less than twice the random line (R1) | 11; random 14.67 | yes | 11; random 14.59 | yes |
| SourceComment less than twice the random line (R2) | 10; random 10.22 | yes | 10; random 10.2 | yes |
| bpfix and VerifierState tie (R0) | discordant 0 / 0 | yes | discordant 0 / 0 | yes |
| bpfix and VerifierState tie (R1) | discordant 0 / 0 | yes | discordant 0 / 0 | yes |
| bpfix and VerifierState tie (R2) | discordant 0 / 0 | yes | discordant 0 / 0 | yes |
| bpfix above Pretty Verifier, p < 0.05 (R0) | 7 / 0, p = 0.015625 | yes | 0 / 27, p = 0.0 | no |
| bpfix above Pretty Verifier, p < 0.05 (R1) | 9 / 0, p = 0.003906 | yes | 0 / 35, p = 0.0 | no |
| bpfix above Pretty Verifier, p < 0.05 (R2) | 7 / 0, p = 0.015625 | yes | 0 / 31, p = 0.0 | no |
| bpfix and PREVAIL not significantly different (R0) | 6 / 1, p = 0.125 | yes | 0 / 28, p = 0.0 | no |
| bpfix and PREVAIL not significantly different (R1) | 6 / 2, p = 0.289062 | yes | 0 / 34, p = 0.0 | no |
| bpfix and PREVAIL not significantly different (R2) | 4 / 0, p = 0.125 | yes | 0 / 29, p = 0.0 | no |
| SourceComment below every other reporter, p < 0.001 (R0) | 30 / 5, p = 2.2e-05; 30 / 5, p = 2.2e-05; 23 / 5, p = 0.000912; 25 / 5, p = 0.000325 | yes | 0 / 9, p = 0.003906; 0 / 9, p = 0.003906; 23 / 5, p = 0.000912; 24 / 5, p = 0.000546 | no |
| SourceComment below every other reporter, p < 0.001 (R1) | 38 / 5, p = 0.0; 38 / 5, p = 0.0; 31 / 7, p = 0.000116; 35 / 6, p = 5e-06 | yes | 0 / 11, p = 0.000977; 0 / 11, p = 0.000977; 31 / 7, p = 0.000116; 29 / 6, p = 0.000117 | no |
| SourceComment below every other reporter, p < 0.001 (R2) | 33 / 5, p = 4e-06; 33 / 5, p = 4e-06; 26 / 5, p = 0.000192; 29 / 5, p = 3.9e-05 | yes | 0 / 10, p = 0.001953; 0 / 10, p = 0.001953; 26 / 5, p = 0.000192; 25 / 6, p = 0.000878 | no |
| bpfix labels reach more repair sites than its arrow (R0) | 34 vs 50 | yes | 0 vs 0 | no |
| bpfix labels reach more repair sites than its arrow (R1) | 44 vs 64 | yes | 0 vs 0 | no |
| bpfix labels reach more repair sites than its arrow (R2) | 38 vs 54 | yes | 0 vs 0 | no |
| NullablePointer: labels well above arrow (R0) | 6 vs 16 of 20 | yes | 0 vs 0 of 20 | no |
| pad8: the four locating reporters lose no hit | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes |
| pad32: the four locating reporters lose no hit | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes |
| rename: the four locating reporters lose no hit | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes |
| pad8: the control loses all its hits | 33 of 33 | yes | 0 of 0 | no |
| pad32: the control loses all its hits | 33 of 33 | yes | 0 of 0 | no |
| MACRO: no hit changes for the four locating reporters (R0) | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes |
| INLINE: no hit changes for the four locating reporters (R0) | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes |
| VPADC: every lost hit is with the primary line unmoved | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes | {'bpfix': 0, 'VerifierState': 0, 'PrettyVerifier': 0, 'PREVAIL': 0} | yes |

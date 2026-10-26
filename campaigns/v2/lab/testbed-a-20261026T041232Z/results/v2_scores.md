# Campaign v2 scores

Host: testbed-a · kernel 6.12.86+deb13-amd64 · Debian clang version 19.1.7 (3+b1) · bpftool v7.5.0 | using libbpf v1.5 · stamp `20261026T041232Z`.

## A. Rename on rejecting NullablePointer programs

| pair | verdicts | error | `-->` equal | structure equal | check line labelled (listed / idiomatic) | labels only with listed name |
| --- | --- | --- | --- | --- | --- | --- |
| `RR-branch-ptr-entry` | REJECT/REJECT | E002/E002 | yes | yes | no / no | none |
| `RR-branch-tmp-slot` | REJECT/REJECT | E002/E002 | yes | yes | no / no | none |
| `RR-flag-valid-ok` | REJECT/REJECT | E002/E002 | yes | no | yes / no | 20 (secondary): nearby source context for nullable pointer |
| `RR-reassign-ptr-entry` | REJECT/REJECT | E002/E002 | yes | no | yes / no | 18 (secondary): nearby source context for nullable pointer |
| `RR-reassign-tmp-slot` | REJECT/REJECT | E002/E002 | yes | no | yes / no | 18 (secondary): nearby source context for nullable pointer |
| `RR-wrongptr-ptr-entry` | REJECT/REJECT | E002/E002 | yes | no | yes / no | 20 (secondary): nearby source context for nullable pointer |
| `RR-wrongptr-tmp-slot` | REJECT/REJECT | E002/E002 | yes | no | yes / no | 20 (secondary): nearby source context for nullable pointer |

Pairs whose rendered diagnostic changes under rename: 5/7; pairs whose `-->` line changes: 0/7.

## B. Padding that survives compilation

| family | pad | verdict | insns | VS stop | VS in injection | bpfix error (upstream obligation) | `-->` | top1_line | top1_span | injection in labels | distance |
| --- | ---: | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- | ---: |
| NPV | 0 | REJECT | 7 | 20 | no | E002 (NullablePointer) | 20 | no | no | yes | 3 |
| NPV | 8 | REJECT | 32 | 30 | no | E002 (NullablePointer) | 30 | no | no | yes | 13 |
| NPV | 32 | REJECT | 104 | 54 | no | E002 (NullablePointer) | 54 | no | no | yes | 37 |
| PBS | 0 | REJECT | 7 | 15 | no | E001 (PacketBounds) | 15 | no | no | yes | 3 |
| PBS | 8 | REJECT | 23 | 25 | no | E001 (PacketBounds) | 25 | no | no | yes | 13 |
| PBS | 32 | REJECT | 71 | 49 | no | E001 (PacketBounds) | 49 | no | no | yes | 37 |
| PBV | 0 | REJECT | 7 | 15 | no | E001 (PacketBounds) | 15 | no | no | yes | 3 |
| PBV | 8 | REJECT | 33 | 25 | no | E001 (PacketBounds) | 25 | no | no | yes | 13 |
| PBV | 32 | REJECT | 105 | 49 | no | E001 (PacketBounds) | 49 | no | no | yes | 37 |
| PPM | 0 | REJECT | 16 | 28 | no | E011 (ContextAccess) | 28 | no | no | yes | 3 |
| PPM | 8 | REJECT | 42 | 38 | no | E011 (ContextAccess) | 38 | no | no | yes | 13 |
| PPM | 32 | REJECT | 114 | 62 | no | E011 (ContextAccess) | 62 | no | no | yes | 37 |
| SRV | 0 | REJECT | 7 | 13 | no | E005 (ScalarRange) | 13 | no | no | no | 2 |
| SRV | 8 | REJECT | 33 | 23 | no | E005 (ScalarRange) | 23 | no | no | no | 12 |
| SRV | 32 | REJECT | 105 | 47 | no | E005 (ScalarRange) | 47 | no | no | no | 36 |

- **NPV**: instructions grow with pad: yes; injection labelled at every pad: yes; error ID stable: yes.
- **PBS**: instructions grow with pad: yes; injection labelled at every pad: yes; error ID stable: yes.
- **PBV**: instructions grow with pad: yes; injection labelled at every pad: yes; error ID stable: yes.
- **PPM**: instructions grow with pad: yes; injection labelled at every pad: yes; error ID stable: yes.
- **SRV**: instructions grow with pad: yes; injection labelled at every pad: no; error ID stable: yes.

## C. Upstream cases under padding and rename (repair-site oracle)

| variant | pairs | orig `-->` on site | variant `-->` on site | lost | gained | exact McNemar p |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| pad8 | 20 | 16 | 16 | 0 | 0 | n/a (no discordant pairs) |
| pad32 | 20 | 16 | 16 | 0 | 0 | n/a (no discordant pairs) |
| rename | 8 | 7 | 7 | 0 | 0 | n/a (no discordant pairs) |

Per-case rows: `v2_scores.json`. Repair sites are mapped into each variant's line numbers (campaigns/v2/upstream/<case>/transform.json).


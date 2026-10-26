# Marker isolation (construct validity)

Stamp filter `20260801T181331Z`. Offline suite always; lab A/B when host reachable.

| Check | Pass | n |
| --- | ---: | ---: |
| no ORACLE_* in verifier logs | 16 | 16 |
| SC bearing ≡ neutral | 16 | 16 |
| ORACLE lines ≠ heuristic hits | 16 | 16 |
| lab bearing≡neutral load (app-test-server, 6.8.0-136-generic) | 16 | 16 |

## What these checks isolate

Offline checks isolate **reporter inputs/outputs** from marker text.
The lab A/B ran on the Ubuntu 6.8 host, not the Debian 6.12.86 cite pin. Its logs carry no `@ file:line` maps, so VS-line and source-map agreement are not comparable there (`vs_comparable` / `source_map_comparable` in `marker_isolation_lab.json`). The markers sit on comment-only lines, so compile identity is expected from C semantics.
Full **log identity** under compile+load still requires `python tools/lab_marker_isolation_ab.py` on the pin host.

JSON: `marker_isolation.json`.

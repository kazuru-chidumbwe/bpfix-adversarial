# Marker isolation (Gates construct validity)

SoftwareX-stamp filter `20260801T181331Z`. Offline suite always; lab A/B when host reachable.

| Check | Pass | n | Rate |
| --- | ---: | ---: | ---: |
| no ORACLE_* in verifier logs | 16 | 16 | 100% |
| SC bearing ≡ neutral | 16 | 16 | 100% |
| ORACLE lines ≠ heuristic hits | 16 | 16 | 100% |
| lab bearing≡neutral load | 16 | 16 | 100% |

## Gates mapping

Offline checks isolate **reporter inputs/outputs** from marker text.
Full **log identity** under compile+load still requires `python tools/lab_marker_isolation_ab.py` on the SoftwareX pin host.

JSON: `marker_isolation.json`.

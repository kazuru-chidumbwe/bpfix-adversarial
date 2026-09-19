# RQ2 inset — rename honesty of `looks_like_null_check`

| Original check | Renamed check | `looks_like_null_check` before | after | Honesty break |
| --- | --- | --- | --- | --- |
| `if (!tmp)` | `if (!entry)` | yes | no | yes |
| `if (!val)` | `if (!entry)` | yes | no | yes |
| `if (!ptr)` | `if (!entry)` | yes | no | yes |
| `if (!value)` | `if (!entry)` | yes | no | yes |

Full combinatorial matrix: all **32** brittle-name x idiomatic-rename pairs (of 32) flip the SourceComment null-check recognition boundary under idiomatic rename. Exhaustive enumeration of the 4x8 grid, not a sampled rate over an empirical population.

Helper-anchored control: `bpf_map_lookup_elem` remains recognized under identifier rename (rename-insensitive).

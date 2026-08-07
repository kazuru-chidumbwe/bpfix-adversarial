# RQ2 inset — rename honesty of `looks_like_null_check`

| Original check | Renamed check | `looks_like_null_check` before | after | Honesty break |
| --- | --- | --- | --- | --- |
| `if (!tmp)` | `if (!entry)` | yes | no | yes |
| `if (!val)` | `if (!entry)` | yes | no | yes |
| `if (!ptr)` | `if (!entry)` | yes | no | yes |
| `if (!value)` | `if (!entry)` | yes | no | yes |

Full combinatorial matrix: **32/32** (100.0%) honesty breaks (SourceComment null-check flips under idiomatic rename).

Helper-anchored control: `bpf_map_lookup_elem` remains recognized under identifier rename (rename-insensitive).

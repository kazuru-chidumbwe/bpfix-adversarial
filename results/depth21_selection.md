# Depth-21 stratified selection (campaign `20260728`)

Upstream pin: `eunomia-bpf/bpfix` @ `81d97e4a528456e0082a77f4fb6edd13fa092b7b`
Selection: balanced obligation guess · target ≤6/obligation · **n=21** (SR pool only 3).
Sources: sparse-fetched under `fixtures/upstream/bpfix-bench-cases/<id>/` (no full vendor tree).

## Counts

| Obligation | n |
| --- | ---: |
| PointerProvenance | 6 |
| ScalarRange | 3 |
| NullablePointer | 6 |
| PacketBounds | 6 |

**Total** | **21** |

## Selection table

| # | upstream_case_id | Obligation | buggy.bpf.c | Template-family evidence |
| ---: | --- | --- | --- | --- |
| 1 | `dynptr_slice_short_mem_001` | PointerProvenance | yes (1063 B) | reject 3/3; SC 0/3; VS 3/3 |
| 2 | `dynptr_slice_stack_buffer_001` | PointerProvenance | yes (950 B) | reject 3/3; SC 0/3; VS 3/3 |
| 3 | `dynptr_stack_copy_001` | PointerProvenance | yes (1200 B) | reject 3/3; SC 0/3; VS 3/3 |
| 4 | `dynptr_uninitialized_slice_arg_001` | PointerProvenance | yes (722 B) | reject 3/3; SC 0/3; VS 3/3 |
| 5 | `helper_csum_diff_stack_len_001` | PointerProvenance | yes (1633 B) | reject 3/3; SC 0/3; VS 3/3 |
| 6 | `helper_map_arg_stack_001` | PointerProvenance | yes (1294 B) | reject 3/3; SC 0/3; VS 3/3 |
| 7 | `alu32_pointer_cookie_001` | ScalarRange | yes (1176 B) | reject 3/3; SC 0/3; VS 0/3 |
| 8 | `map_value_index_guard_oob_001` | ScalarRange | yes (1052 B) | reject 3/3; SC 0/3; VS 0/3 |
| 9 | `map_value_signed_index_001` | ScalarRange | yes (971 B) | reject 3/3; SC 0/3; VS 0/3 |
| 10 | `dynptr_slice_missing_null_check_001` | NullablePointer | yes (1006 B) | reject 1/7 (nocheck); 6/7 accept controls; SC rename matrix 32/32 breaks + brittle hits; VS n/a on accepts; nocheck miss vs loss-span |
| 11 | `ringbuf_branch_cookie_001` | NullablePointer | yes (1449 B) | reject 1/7 (nocheck); 6/7 accept controls; SC rename matrix 32/32 breaks + brittle hits; VS n/a on accepts; nocheck miss vs loss-span |
| 12 | `ringbuf_double_submit_001` | NullablePointer | yes (1176 B) | reject 1/7 (nocheck); 6/7 accept controls; SC rename matrix 32/32 breaks + brittle hits; VS n/a on accepts; nocheck miss vs loss-span |
| 13 | `ringbuf_missing_null_check_001` | NullablePointer | yes (1074 B) | reject 1/7 (nocheck); 6/7 accept controls; SC rename matrix 32/32 breaks + brittle hits; VS n/a on accepts; nocheck miss vs loss-span |
| 14 | `ringbuf_nested_missing_null_001` | NullablePointer | yes (1145 B) | reject 1/7 (nocheck); 6/7 accept controls; SC rename matrix 32/32 breaks + brittle hits; VS n/a on accepts; nocheck miss vs loss-span |
| 15 | `ringbuf_nested_reserve_leak_001` | NullablePointer | yes (1184 B) | reject 1/7 (nocheck); 6/7 accept controls; SC rename matrix 32/32 breaks + brittle hits; VS n/a on accepts; nocheck miss vs loss-span |
| 16 | `packet_checked_wrong_base_001` | PacketBounds | yes (692 B) | reject 3/3; SC 3/3; VS 0/3 |
| 17 | `packet_eth_off_by_one_001` | PacketBounds | yes (976 B) | reject 3/3; SC 3/3; VS 0/3 |
| 18 | `packet_ihl_udp_undercheck_001` | PacketBounds | yes (1725 B) | reject 3/3; SC 3/3; VS 0/3 |
| 19 | `packet_inline_return_cookie_001` | PacketBounds | yes (1346 B) | reject 3/3; SC 3/3; VS 0/3 |
| 20 | `packet_l4_branch_cookie_001` | PacketBounds | yes (1676 B) | reject 3/3; SC 3/3; VS 0/3 |
| 21 | `packet_macro_cookie_001` | PacketBounds | yes (1257 B) | reject 3/3; SC 3/3; VS 0/3 |

## Status

- **Corpus selection & sourcing: done** — 21 `upstream_case_id`s + local buggy/fixed/diagnostic/verifier.log
- **Per-case lab validation: not started** — family-level template SC/VS scores in the table are **inherited**, not independently measured on these upstream programs
- **SoftwareX scope:** curated real-world validation *target* only — not RQ1/RQ3 evidence
- **SR pool:** n=3 vs target 6 — corpus-availability limitation
- **Next (EuroSys / future):** per-case pad/rename mutants + individual lab / bpfix re-captures

Manifest: `fixtures/upstream/depth21_manifest.json`
Artifacts: `results/depth21_selection.md` · `results/depth21_selection.json`


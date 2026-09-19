# Depth-21 stratified selection (campaign `20260728`)

Upstream pin: `eunomia-bpf/bpfix` @ `81d97e4a528456e0082a77f4fb6edd13fa092b7b`
Selection: stratified on case-name keyword labels (target 6 per label; ScalarRange pool only 3), **n=21**.
Sources: sparse-fetched under `fixtures/upstream/bpfix-bench-cases/<id>/`.

**These cases are not scored.** They are a curated target for later per-case work.

## Keyword-label counts

| Keyword label | n |
| --- | ---: |
| PointerProvenance | 6 |
| ScalarRange | 3 |
| NullablePointer | 6 |
| PacketBounds | 6 |
| **Total** | **21** |

Keyword labels agree with upstream's own obligation on **8/21** of these cases (see `upstream_obligations.md` for all 75).

## Selection table

| # | upstream_case_id | Keyword label | Upstream obligation (error ID) | buggy.bpf.c |
| ---: | --- | --- | --- | --- |
| 1 | `dynptr_slice_short_mem_001` | PointerProvenance | ScalarRange (E005) | yes (1063 B) |
| 2 | `dynptr_slice_stack_buffer_001` | PointerProvenance | StackInitialized (E003) | yes (950 B) |
| 3 | `dynptr_stack_copy_001` | PointerProvenance | DynptrSafety (E012) | yes (1200 B) |
| 4 | `dynptr_uninitialized_slice_arg_001` | PointerProvenance | DynptrSafety (E012) | yes (722 B) |
| 5 | `helper_csum_diff_stack_len_001` | PointerProvenance | StackInitialized (E003) | yes (1633 B) |
| 6 | `helper_map_arg_stack_001` | PointerProvenance | TypeContract (E008) | yes (1294 B) |
| 7 | `alu32_pointer_cookie_001` | ScalarRange | PointerProvenance (E006) | yes (1176 B) |
| 8 | `map_value_index_guard_oob_001` | ScalarRange | ScalarRange (E005) | yes (1052 B) |
| 9 | `map_value_signed_index_001` | ScalarRange | ScalarRange (E005) | yes (971 B) |
| 10 | `dynptr_slice_missing_null_check_001` | NullablePointer | NullablePointer (E002) | yes (1006 B) |
| 11 | `ringbuf_branch_cookie_001` | NullablePointer | PointerProvenance (E006) | yes (1449 B) |
| 12 | `ringbuf_double_submit_001` | NullablePointer | PointerProvenance (E006) | yes (1176 B) |
| 13 | `ringbuf_missing_null_check_001` | NullablePointer | NullablePointer (E002) | yes (1074 B) |
| 14 | `ringbuf_nested_missing_null_001` | NullablePointer | NullablePointer (E002) | yes (1145 B) |
| 15 | `ringbuf_nested_reserve_leak_001` | NullablePointer | ReferenceLifecycle (E004) | yes (1184 B) |
| 16 | `packet_checked_wrong_base_001` | PacketBounds | PacketBounds (E001) | yes (692 B) |
| 17 | `packet_eth_off_by_one_001` | PacketBounds | PacketBounds (E001) | yes (976 B) |
| 18 | `packet_ihl_udp_undercheck_001` | PacketBounds | PacketBounds (E001) | yes (1725 B) |
| 19 | `packet_inline_return_cookie_001` | PacketBounds | PointerProvenance (E006) | yes (1346 B) |
| 20 | `packet_l4_branch_cookie_001` | PacketBounds | PointerProvenance (E006) | yes (1676 B) |
| 21 | `packet_macro_cookie_001` | PacketBounds | PointerProvenance (E006) | yes (1257 B) |

## Template evidence by family

Results on the hand-authored templates (paper Section 3.2), listed per family for orientation. They are not measurements on the upstream cases above.

| Family | Lab reject | SourceComment | VerifierState |
| --- | --- | --- | --- |
| PointerProvenance | 3/3 | N/A (no upstream PointerProvenance predicate) | top1_span 3/3, top1_line 0/3 |
| ScalarRange | 3/3 | top1_line 0/3 (no scalar-guard line to match) | top1_line 0/3 |
| NullablePointer | 1/7 (nocheck); 6 ACCEPT controls | nocheck top1_line hit (construction-determined); rename boundary is an exhaustive 4x8 enumeration, not a rate | nocheck top1_line miss; n/a on ACCEPT controls |
| PacketBounds | 3/3 | top1_line 3/3 (construction-determined) | top1_line 0/3 |

Manifest: `fixtures/upstream/depth21_manifest.json`
Artifacts: `results/depth21_selection.md` · `results/depth21_selection.json`

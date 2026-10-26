# Upstream diagnostics vs upstream fixes (repair-site oracle)

Reporter: upstream's committed `diagnostic.txt` (bpfix @ `81d97e4a5284`). Oracle: lines touched by the semantic hunks of upstream's `buggy.bpf.c` → `fixed.bpf.c` diff, in buggy line numbers (an insertion marks the lines on both sides of the gap). Neither input is authored by this harness.

Cases: 21 vendored (depth-21 selection); scorable: 21. `-->` line 0 (no primary): 1.

| Metric | Hits |
| --- | ---: |
| primary `-->` on a repair site | 16/21 (95% CI 0.55–0.89) |
| any snippet label on a repair site | 18/21 (95% CI 0.65–0.95) |
| primary within 3 lines of a repair site | 19/21 (95% CI 0.71–0.97) |
| chance: expected primary hits for a uniformly random executable line | 3.6/21 |

## By upstream obligation

| Upstream obligation | primary on site | any label on site | n |
| --- | ---: | ---: | ---: |
| DynptrSafety | 1 | 1 | 2 |
| NullablePointer | 3 | 3 | 3 |
| PacketBounds | 1 | 2 | 3 |
| PointerProvenance | 6 | 6 | 6 |
| ReferenceLifecycle | 0 | 0 | 1 |
| ScalarRange | 2 | 3 | 3 |
| StackInitialized | 2 | 2 | 2 |
| TypeContract | 1 | 1 | 1 |

## Per case

| case | error | primary | repair sites | primary on site | label on site | distance |
| --- | --- | ---: | --- | --- | --- | ---: |
| `alu32_pointer_cookie_001` | E006 | 42 | 28,41,42,43,44 | yes | yes | 0 |
| `dynptr_slice_missing_null_check_001` | E002 | 33 | 24,25,27,28,32,33,36,37 | yes | yes | 0 |
| `dynptr_slice_short_mem_001` | E005 | 35 | 24,25,28,29,32,38 | no | yes | 3 |
| `dynptr_slice_stack_buffer_001` | E003 | 30 | 20,21,22,23,25,26,30,34 | yes | yes | 0 |
| `dynptr_stack_copy_001` | E012 | 36 | 27,28,29,31,32,36,37,43 | yes | yes | 0 |
| `dynptr_uninitialized_slice_arg_001` | E012 | 27 | 19,20,23,24,25,26 | no | no | 1 |
| `helper_csum_diff_stack_len_001` | E003 | 61 | 34,35,36,37,59,61,65,66 | yes | yes | 0 |
| `helper_map_arg_stack_001` | E008 | 57 | 27,54,57 | yes | yes | 0 |
| `map_value_index_guard_oob_001` | E005 | 48 | 21,35,36,41,42,43,48 | yes | yes | 0 |
| `map_value_signed_index_001` | E005 | 47 | 33,34,41,42,47 | yes | yes | 0 |
| `packet_checked_wrong_base_001` | E001 | 31 | 24,27,30,31 | yes | yes | 0 |
| `packet_eth_off_by_one_001` | E001 | 36 | 33,42 | no | yes | 3 |
| `packet_ihl_udp_undercheck_001` | E001 | 0 (none) | 63,67,68,69,75,76 | no | no | n/a |
| `packet_inline_return_cookie_001` | E006 | 54 | 54 | yes | yes | 0 |
| `packet_l4_branch_cookie_001` | E006 | 61 | 60,61,62,63 | yes | yes | 0 |
| `packet_macro_cookie_001` | E006 | 39 | 38,39,40,41,42 | yes | yes | 0 |
| `ringbuf_branch_cookie_001` | E006 | 59 | 59,60 | yes | yes | 0 |
| `ringbuf_double_submit_001` | E006 | 53 | 52,53,54 | yes | yes | 0 |
| `ringbuf_missing_null_check_001` | E002 | 35 | 28,29,34,35,36,37,38 | yes | yes | 0 |
| `ringbuf_nested_missing_null_001` | E002 | 48 | 48 | yes | yes | 0 |
| `ringbuf_nested_reserve_leak_001` | E004 | 55 | 48,50 | no | no | 5 |

Hunk-level agreement with upstream's fix, not root-cause ground truth: a fix can touch more lines than the fault or repair elsewhere. The 21 cases are the keyword-stratified depth-21 selection, not a random sample of main75; intervals are Wilson 95% over cases.

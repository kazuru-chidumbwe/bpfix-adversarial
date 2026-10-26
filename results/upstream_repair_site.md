# Upstream diagnostics vs upstream fixes (repair-site oracle)

Reporter: upstream's committed `diagnostic.txt` (bpfix @ `81d97e4a5284`). Oracle: lines touched by the semantic hunks of upstream's `buggy.bpf.c` → `fixed.bpf.c` diff, in buggy line numbers (an insertion marks the lines on both sides of the gap). Neither input is authored by this harness.

Cases: 75 vendored (the full main75 split); scorable: 67. `-->` line 0 (no primary): 1.

| Metric | Hits |
| --- | ---: |
| primary `-->` on a repair site | 30/67 (95% CI 0.33–0.57) |
| any snippet label on a repair site | 45/67 (95% CI 0.55–0.77) |
| primary within 3 lines of a repair site | 47/67 (95% CI 0.58–0.80) |
| chance: expected primary hits for a uniformly random executable line | 6.4/67 |

## By upstream obligation

| Upstream obligation | primary on site | any label on site | n |
| --- | ---: | ---: | ---: |
| ContextAccess | 2 | 2 | 5 |
| DynptrSafety | 1 | 1 | 2 |
| EnvironmentCapability | 0 | 0 | 4 |
| HelperArgument | 1 | 1 | 1 |
| NullablePointer | 6 | 16 | 19 |
| PacketBounds | 4 | 6 | 11 |
| PointerProvenance | 8 | 8 | 8 |
| ReferenceLifecycle | 0 | 2 | 5 |
| ScalarRange | 4 | 5 | 6 |
| StackInitialized | 3 | 3 | 4 |
| TypeContract | 1 | 1 | 2 |

## By case kind

| Case kind | primary on site | any label on site | n |
| --- | ---: | ---: | ---: |
| canary | 20/35 (95% CI 0.41–0.72) | 25/35 (95% CI 0.55–0.84) | 35 |
| real-project seed | 10/32 (95% CI 0.18–0.49) | 20/32 (95% CI 0.45–0.77) | 32 |

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
| `map_value_branch_merge_001` | E002 | 65 | 39,40,56,57,58,59,60 | no | yes | 5 |
| `map_value_index_guard_oob_001` | E005 | 48 | 21,35,36,41,42,43,48 | yes | yes | 0 |
| `map_value_inline_cookie_001` | E002 | 67 | 63,64 | no | no | 3 |
| `map_value_pointer_cookie_001` | E002 | 67 | 61,62,63 | no | yes | 4 |
| `map_value_signed_index_001` | E005 | 47 | 33,34,41,42,47 | yes | yes | 0 |
| `map_value_spill_cookie_001` | E002 | 62 | 58,59 | no | yes | 3 |
| `packet_checked_wrong_base_001` | E001 | 31 | 24,27,30,31 | yes | yes | 0 |
| `packet_eth_off_by_one_001` | E001 | 36 | 33,42 | no | yes | 3 |
| `packet_ihl_udp_undercheck_001` | E001 | 0 (none) | 63,67,68,69,75,76 | no | no | n/a |
| `packet_inline_return_cookie_001` | E006 | 54 | 54 | yes | yes | 0 |
| `packet_l4_branch_cookie_001` | E006 | 61 | 60,61,62,63 | yes | yes | 0 |
| `packet_macro_cookie_001` | E006 | 39 | 38,39,40,41,42 | yes | yes | 0 |
| `packet_macro_payload_undercheck_001` | E001 | 52 | 50 | no | no | 2 |
| `packet_vlan_cookie_001` | E006 | 67 | 66,67,68,69,70 | yes | yes | 0 |
| `perf_event_packet_payload_001` | E010 | 43 | 33,34,43 | yes | yes | 0 |
| `ringbuf_branch_cookie_001` | E006 | 59 | 59,60 | yes | yes | 0 |
| `ringbuf_double_submit_001` | E006 | 53 | 52,53,54 | yes | yes | 0 |
| `ringbuf_missing_null_check_001` | E002 | 35 | 28,29,34,35,36,37,38 | yes | yes | 0 |
| `ringbuf_nested_missing_null_001` | E002 | 48 | 48 | yes | yes | 0 |
| `ringbuf_nested_reserve_leak_001` | E004 | 55 | 48,50 | no | no | 5 |
| `ringbuf_pointer_cookie_001` | E006 | 64 | 40,71,72,73,74,75,77 | no | no | 7 |
| `ringbuf_ref_leak_001` | E004 | 53 | 40,41,42 | no | no | 11 |
| `ringbuf_stack_discard_001` | E008 | 27 | 25,32,33 | no | no | 2 |
| `ringbuf_stack_submit_001` | E008 | 30 | 25,32,34,37 | no | no | 2 |
| `ringbuf_submit_after_discard_001` | E008 | 49 | 40,46,47,48,50 | no | no | 1 |
| `ringbuf_two_record_cookie_001` | E006 | 63 | 62,63,64,65 | yes | yes | 0 |
| `rs_actplane_cap_dynptr_payload_null_001` | E002 | 94 | 90,91,92,106,107,108 | no | no | 2 |
| `rs_actplane_lsm_bpf_ringbuf_merge_001` | E002 | 54 | 44,45,50 | no | no | 4 |
| `rs_actplane_mmap_pending_merge_001` | E002 | 217 | 195,209,210,211,212,213,214,217,222 | yes | yes | 0 |
| `rs_actplane_policy_map_merge_001` | E002 | 57 | 51,52,53,54 | no | yes | 3 |
| `rs_actplane_taint_loop_count_bound_001` | E005 | 29 | 28,29 | yes | yes | 0 |
| `rs_agentsight_fs_overflow_counter_merge_001` | E002 | 123 | 118,119,120 | no | yes | 3 |
| `rs_agentsight_process_ringbuf_null_001` | E002 | 45 | 44,45 | yes | yes | 0 |
| `rs_agentsight_stdiocap_user_copy_len_001` | E005 | 57 | 56,57 | yes | yes | 0 |
| `rs_agentsight_write_ctx_merge_001` | E002 | 132 | 126,127,128,129,130,131 | no | yes | 1 |
| `rs_bpftime_opensnoop_ringbuf_filter_ref_001` | E004 | 82 | 62,63,66,67,68 | no | yes | 14 |
| `rs_bpftime_opensnoop_stack_wrong_prog_type_001` | E009 | 50 | 57,58,60,61,62 | no | no | 7 |
| `rs_bpftime_sslsniff_perf_copy_len_001` | E005 | 101 | none | no | no | n/a |
| `rs_cilium_change_proto_stale_001` | E011 | 43 | 42,43 | yes | yes | 0 |
| `rs_cilium_fib_lookup_param_len_001` | E003 | 46 | 46 | yes | yes | 0 |
| `rs_cilium_ip_options_traceid_payload_bound_001` | E001 | 37 | 36,37 | yes | yes | 0 |
| `rs_cilium_ipv6_exthdr_l4_offset_001` | E001 | 87 | 58,60,74,75,82,83,86 | no | no | 1 |
| `rs_cilium_mcast_igmpv3_grec_bound_001` | E001 | 86 | 85,86 | yes | yes | 0 |
| `rs_cilium_proxy_skc_assign_ref_leak_001` | E004 | 34 | 28,29,32 | no | yes | 2 |
| `rs_cilium_srv6_segment_bound_001` | E001 | 60 | 50 | no | yes | 10 |
| `rs_datrail_browsertrace_start_ns_merge_001` | E002 | 69 | 60,61,62,63 | no | yes | 6 |
| `rs_datrail_cgroup_filter_key_width_001` | E003 | 42 | 41 | no | no | 1 |
| `rs_eunomia_energy_runtime_merge_001` | E002 | 130 | 124,125,126,127,128,129 | no | yes | 1 |
| `rs_eunomia_http_doff_copy_bound_001` | E001 | 131 | 116,117 | no | no | 14 |
| `rs_eunomia_wq_container_map_001` | E010 | 99 | 70,99 | yes | yes | 0 |
| `rs_nccl_cpu_observer_slot_merge_001` | E002 | 102 | 94,95,97,98 | no | yes | 4 |
| `rs_tetragon_data_event_size_guard_001` | E005 | 51 | 96 | no | no | 45 |
| `rs_tutorial_dynptr_tc_ref_leak_001` | E004 | 137 | 120,121,122,124,125,126 | no | no | 11 |
| `rs_tutorial_memleak_free_info_merge_001` | E002 | 73 | 67,68,69,70,73 | yes | yes | 0 |
| `rs_tutorial_pidhide_tailcall_map_type_001` | E009 | 34 | 19 | no | no | 15 |
| `rs_tutorial_user_ringbuf_dynptr_merge_001` | E002 | 50 | 39,40,41,42,43,44 | no | yes | 6 |
| `rs_xdp_tools_ihl_macro_wrong_base_001` | E001 | 30 | 41,53,55 | no | no | 11 |
| `rs_xdp_tools_load_bytes_stack_len_001` | E003 | 27 | 30 | no | no | 3 |
| `rs_xdp_tools_xdpdump_perf_map_type_001` | E009 | 62 | 29,31 | no | no | 31 |
| `rs_xdp_tools_xdpfilt_udp_macro_bound_001` | E001 | 92 | 91,92 | yes | yes | 0 |
| `rs_xdp_tools_xdpsock_redirect_map_type_001` | E009 | 38 | 18 | no | no | 20 |
| `subprog_adjust_tail_stale_001` | E011 | 37 | 36,37 | yes | yes | 0 |
| `subprog_map_value_null_001` | E002 | 53 | 53,54 | yes | yes | 0 |
| `xdp_adjust_head_map_value_001` | E011 | 59 | 48,51,52,53 | no | no | 6 |
| `xdp_adjust_head_ringbuf_001` | E011 | 59 | 55,56 | no | no | 3 |
| `xdp_adjust_head_stale_001` | E011 | 46 | 44 | no | yes | 2 |
| `xdp_adjust_tail_stale_001` | E011 | 43 | 39,40 | no | no | 3 |

Hunk-level agreement with upstream's fix, not root-cause ground truth: a fix can touch more lines than the fault or repair elsewhere. Cases are the full main75 split; intervals are Wilson 95% over cases.

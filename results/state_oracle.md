# Verifier-state oracle: agreement with the repair-site oracle

Rules `docs/STATE-ORACLE.md`. The state oracle is read from the buggy log only; the stop line is never one of its sites.
Agreement: the two site sets share at least one line. Intervals: Wilson 95% over distinct cases.

| corpus | cases | covered (NP / PB) | with sites | agree R0 | agree R1 | agree R2 | mean chance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main75 | 74 | 31 (20 / 11) | 30 | 22/30 (0.56–0.86) | 26/30 (0.70–0.95) | 23/30 (0.59–0.88) | 0.047 |
| wild | 1 | 0 (0 / 0) | 0 | 0/0 | 0/0 | 0/0 | n/a |

Context only, not a ranking (rule 6): cases where a reporter's primary line is a state-oracle site.

| corpus | PREVAIL | PrettyVerifier | SourceComment | VerifierState | bpfix |
| --- | ---: | ---: | ---: | ---: | ---: |
| main75 | 0/30 | 0/30 | 8/30 | 0/30 | 0/30 |
| wild | 0/0 | 0/0 | 0/0 | 0/0 | 0/0 |

## Per case

| corpus | case | kind | first loss | sites | agree R0 | note |
| --- | --- | --- | --- | --- | --- | --- |
| main75 | `dynptr_slice_missing_null_check_001` | NullablePointer | buggy.bpf.c:32 | buggy.bpf.c:32 | yes |  |
| main75 | `map_value_branch_merge_001` | NullablePointer | buggy.bpf.c:60 | buggy.bpf.c:60, buggy.bpf.c:61 | yes |  |
| main75 | `map_value_inline_cookie_001` | NullablePointer | buggy.bpf.c:39 | buggy.bpf.c:39 | no |  |
| main75 | `map_value_pointer_cookie_001` | NullablePointer | buggy.bpf.c:63 | buggy.bpf.c:63 | yes |  |
| main75 | `map_value_spill_cookie_001` | NullablePointer | buggy.bpf.c:58 | buggy.bpf.c:58 | yes |  |
| main75 | `packet_checked_wrong_base_001` | PacketBounds | buggy.bpf.c:27 | buggy.bpf.c:27 | yes |  |
| main75 | `packet_eth_off_by_one_001` | PacketBounds | buggy.bpf.c:33 | buggy.bpf.c:33 | yes |  |
| main75 | `packet_ihl_udp_undercheck_001` | PacketBounds | buggy.bpf.c:63 | buggy.bpf.c:63, buggy.bpf.c:66 | yes |  |
| main75 | `packet_macro_payload_undercheck_001` | PacketBounds | buggy.bpf.c:46 | buggy.bpf.c:46 | no |  |
| main75 | `ringbuf_missing_null_check_001` | NullablePointer | buggy.bpf.c:34 | buggy.bpf.c:34 | yes |  |
| main75 | `ringbuf_nested_missing_null_001` | NullablePointer | buggy.bpf.c:47 | buggy.bpf.c:47 | no |  |
| main75 | `rs_actplane_cap_dynptr_payload_null_001` | NullablePointer | buggy.bpf.c:64 | buggy.bpf.c:64, buggy.bpf.c:65, buggy.bpf.c:70, buggy.bpf.c:71, buggy.bpf.c:73, buggy.bpf.c:77, buggy.bpf.c:80, buggy.bpf.c:81, buggy.bpf.c:84, buggy.bpf.c:92 | yes |  |
| main75 | `rs_actplane_lsm_bpf_ringbuf_merge_001` | NullablePointer | buggy.bpf.c:49 | buggy.bpf.c:49, buggy.bpf.c:50 | yes |  |
| main75 | `rs_actplane_mmap_pending_merge_001` | NullablePointer | buggy.bpf.c:214 | buggy.bpf.c:214 | yes |  |
| main75 | `rs_actplane_policy_map_merge_001` | NullablePointer | buggy.bpf.c:54 | buggy.bpf.c:54 | yes |  |
| main75 | `rs_agentsight_fs_overflow_counter_merge_001` | NullablePointer | buggy.bpf.c:120 | buggy.bpf.c:120 | yes |  |
| main75 | `rs_agentsight_process_ringbuf_null_001` | NullablePointer | none | none | n/a | R0 never shown as *_or_null on the failing path |
| main75 | `rs_agentsight_write_ctx_merge_001` | NullablePointer | buggy.bpf.c:129 | buggy.bpf.c:129 | yes |  |
| main75 | `rs_cilium_ip_options_traceid_payload_bound_001` | PacketBounds | buggy.bpf.c:88 | buggy.bpf.c:34, buggy.bpf.c:88, buggy.bpf.c:91, buggy.bpf.c:92 | no |  |
| main75 | `rs_cilium_ipv6_exthdr_l4_offset_001` | PacketBounds | buggy.bpf.c:77 | buggy.bpf.c:77 | no |  |
| main75 | `rs_cilium_mcast_igmpv3_grec_bound_001` | PacketBounds | buggy.bpf.c:74 | buggy.bpf.c:74, buggy.bpf.c:78, buggy.bpf.c:79, buggy.bpf.c:84 | no |  |
| main75 | `rs_cilium_srv6_segment_bound_001` | PacketBounds | buggy.bpf.c:50 | buggy.bpf.c:50, buggy.bpf.c:52, buggy.bpf.c:56 | yes |  |
| main75 | `rs_datrail_browsertrace_start_ns_merge_001` | NullablePointer | buggy.bpf.c:59 | buggy.bpf.c:59, buggy.bpf.c:60, buggy.bpf.c:65, buggy.bpf.c:66 | yes |  |
| main75 | `rs_eunomia_energy_runtime_merge_001` | NullablePointer | buggy.bpf.c:127 | buggy.bpf.c:127 | yes |  |
| main75 | `rs_eunomia_http_doff_copy_bound_001` | PacketBounds | buggy.bpf.c:107 | buggy.bpf.c:59, buggy.bpf.c:107, buggy.bpf.c:112, buggy.bpf.c:113, buggy.bpf.c:118, buggy.bpf.c:119, buggy.bpf.c:124, buggy.bpf.c:125, buggy.bpf.c:126, buggy.bpf.c:127, buggy.bpf.c:130 | no |  |
| main75 | `rs_nccl_cpu_observer_slot_merge_001` | NullablePointer | buggy.bpf.c:94 | buggy.bpf.c:94, buggy.bpf.c:96 | yes |  |
| main75 | `rs_tutorial_memleak_free_info_merge_001` | NullablePointer | buggy.bpf.c:65 | buggy.bpf.c:65, buggy.bpf.c:67, buggy.bpf.c:72 | yes |  |
| main75 | `rs_tutorial_user_ringbuf_dynptr_merge_001` | NullablePointer | buggy.bpf.c:32 | buggy.bpf.c:32, buggy.bpf.c:34, buggy.bpf.c:36, buggy.bpf.c:37, buggy.bpf.c:40, buggy.bpf.c:45 | yes |  |
| main75 | `rs_xdp_tools_ihl_macro_wrong_base_001` | PacketBounds | buggy.bpf.c:55 | buggy.bpf.c:54, buggy.bpf.c:55 | yes |  |
| main75 | `rs_xdp_tools_xdpfilt_udp_macro_bound_001` | PacketBounds | buggy.bpf.c:61 | buggy.bpf.c:61, buggy.bpf.c:66, buggy.bpf.c:87 | no |  |
| main75 | `subprog_map_value_null_001` | NullablePointer | buggy.bpf.c:35 | buggy.bpf.c:35, buggy.bpf.c:53 | yes |  |

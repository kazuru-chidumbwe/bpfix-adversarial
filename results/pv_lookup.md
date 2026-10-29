# Pretty Verifier: sensitivity to its line lookup

Generator: `tools/score_pv_lookup.py`. Released scores (results/main75_pin.json, results/wild.json) are unchanged; `log line` re-scores the cases where Pretty Verifier's printed line differs from the verifier log's own annotation of the same statement, with the log's line.

## main75: 74 cases, 60 with a location, 3 with a different line

Cases: `rs_cilium_proxy_skc_assign_ref_leak_001`, `rs_tutorial_user_ringbuf_dynptr_merge_001`, `rs_xdp_tools_xdpdump_perf_map_type_001`.

| scoring | R0 primary | R0 label | R1 primary | R1 label | R2 primary | R2 label |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| released | 27/74 | 27/74 | 35/74 | 35/74 | 31/74 | 31/74 |
| log line | 27/74 | 27/74 | 35/74 | 35/74 | 31/74 | 31/74 |

## wild: 5 cases, 5 with a location, 2 with a different line

Cases: `2043`, `4049`.

| scoring | R0 primary | R0 label | R1 primary | R1 label | R2 primary | R2 label |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| released | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 |
| printed in its file | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 | 2/5 |
| log line | 2/5 | 2/5 | 3/5 | 3/5 | 2/5 | 2/5 |

## Per case

| corpus | case | printed | log |
| --- | --- | --- | --- |
| main75 | `rs_cilium_proxy_skc_assign_ref_leak_001` | buggy.bpf.c:14 | buggy.bpf.c:24 |
| main75 | `rs_tutorial_user_ringbuf_dynptr_merge_001` | buggy.bpf.c:51 | buggy.bpf.c:50 |
| main75 | `rs_xdp_tools_xdpdump_perf_map_type_001` | buggy.bpf.c:44 | buggy.bpf.c:62 |
| wild | `2043` | context.h:63 | buffer.h:368 |
| wild | `4049` | native.bpf.c:519 | native.bpf.c:491 |

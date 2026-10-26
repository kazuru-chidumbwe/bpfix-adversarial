# Reports to upstream bpfix

Observed with bpfix 0.1.9 built from `81d97e4a528456e0082a77f4fb6edd13fa092b7b`.
Each report gives the input file in this repository so maintainers can reproduce it.

## 1. PacketBounds: secondary label contradicts the primary label on proven range

Input: `fixtures/logs/captured/PB-pad8.20260801T181331Z.log` (also `PB-pad0`,
`PB-pad32`). Output: `results/rq1_bpfix_cli_raw/PB-pad8.txt`.

```
12 | if (data + 1 > data_end)
   | ------------------------ verifier only proves packet range 0 bytes on this path, but the rejected access requires 8 bytes
26 | return *(__u64 *)data;
   | ^^^^^^^^^^^^^^^^^^^^^^ rejected here: verifier needs R1 packet range >= 8, but only 1 bytes are proven
```

The verifier state after the check is `R3_w=pkt(off=1,r=1)`, and the rejected
access reports `R1(id=0,off=0,r=1)`. The proven range is 1 byte. The secondary
label says 0, the primary label says 1. Reproduced on all three PB logs.

## 2. `-->` line 0 for a rejected access with a known source line

Input: upstream `bpfix-bench/cases/packet_ihl_udp_undercheck_001/diagnostic.txt`
(committed upstream). bpfix prints `--> buggy.bpf.c:0`, while the snippet labels
line 66 (`dport = *(__u16 *)(udp + 2);`) as the access. Line 0 is not a source
line; tools that consume the `-->` location (including this harness) treat it
as "no location".

## 3. Name-listed `if (!x)` on a non-pointer flag becomes nullable-pointer context

Input: `campaigns/v2/lab/testbed-a-20261026T041232Z/templates/RR-flag-valid.20261026T041232Z.log`. Source
`campaigns/v2/mutants/RenameReject/RR-flag-valid.c`:

```c
__u64 *entry = bpf_map_lookup_elem(&m, &key);
__u32 valid = bpf_get_prandom_u32() & 1;
if (!valid)
    return 0;
return *entry;
```

bpfix labels `if (!valid)` "nearby source context for nullable pointer". The
check is on a flag, not on `entry`. With the flag named `ok` the label
disappears. Cause: `looks_like_null_check` matches the substring `!val`. Related:
an uncredited check on the wrong pointer (`RR-wrongptr-*`) or before a
reassignment (`RR-reassign-*`) is also labelled, and only when the identifier is
on the `!tmp`/`!val`/`!ptr`/`!value` list.


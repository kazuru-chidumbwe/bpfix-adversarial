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


## 5. Modified context pointer reported as "a scalar where a pointer is required"

Input: `fixtures/wild/cases/3285/buggy.log` (landscape `xdp_lan_root`, parent of
fc3fafd; Debian 13, 6.12.86, clang 19.1.7). Output:
`fixtures/wild/cases/3285/buggy.bpfix.txt`.

```
17 | __builtin_memcpy(meta, data_meta, sizeof(*meta));
   | ------------------------------------------------- verifier state changes from pkt to scalar before the rejected access
41 | void *data_meta = (void *)(long)ctx->data_meta;
   | ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ rejected here: verifier sees a scalar where a pointer is required
   = verifier[127]: dereference of modified ctx ptr R2 off=8 disallowed
```

The log shows R2 as a context pointer at the rejected load:

```
42: (bf) r2 = r6                      ; R2_w=ctx() R6=ctx()
43: (0f) r2 += r9
44: R2_w=ctx(off=8) R9=8
47: (61) r2 = *(u32 *)(r2 +0)
dereference of modified ctx ptr R2 off=8 disallowed
```

R2 is a pointer, a context pointer moved by a register add; the verifier
requires context loads at a constant offset in the instruction. The label on
line 17 describes an earlier use of R2 (insn 13, a byte loaded from `pkt_meta`
during the copy), not the value that reaches the rejected load. The class (E006
lowering_artifact) and the help text are right, and the project's fix (context
fields read through asm accessors) matches the help. Unchanged in 0.1.10
(4b9deca), which changes only version numbers under `crates/`.

// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u64);
} m SEC(".maps");

SEC("socket")
int np_entry_pad32(void *ctx)
{
	__u32 key = 0;
	__u64 *entry = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_LOSS_LINE: null-check (SourceComment name-shaped vs idiomatic) */
	if (!entry)
		return 0;
	/* distance pad: 32 scalar ops */
	__u64 __pad = 0;
	__pad += 1;
	__pad += 2;
	__pad += 3;
	__pad += 4;
	__pad += 5;
	__pad += 6;
	__pad += 7;
	__pad += 8;
	__pad += 9;
	__pad += 10;
	__pad += 11;
	__pad += 12;
	__pad += 13;
	__pad += 14;
	__pad += 15;
	__pad += 16;
	__pad += 17;
	__pad += 18;
	__pad += 19;
	__pad += 20;
	__pad += 21;
	__pad += 22;
	__pad += 23;
	__pad += 24;
	__pad += 25;
	__pad += 26;
	__pad += 27;
	__pad += 28;
	__pad += 29;
	__pad += 30;
	__pad += 31;
	__pad += 32;
	(void)__pad;
	/* ORACLE_REJECT_LINE: use after check */
	return *entry;
}

char _license[] SEC("license") = "MIT";
/* case_id=NP-idiomatic-pad32 obligation=NullablePointer var=entry pad=32 */

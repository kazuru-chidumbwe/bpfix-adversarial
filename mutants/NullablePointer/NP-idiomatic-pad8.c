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
int np_entry_pad8(void *ctx)
{
	__u32 key = 0;
	__u64 *entry = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_LOSS_LINE: null-check (SourceComment name-shaped vs idiomatic) */
	if (!entry)
		return 0;
	/* distance pad: 8 scalar ops */
	__u64 __pad = 0;
	__pad += 1;
	__pad += 2;
	__pad += 3;
	__pad += 4;
	__pad += 5;
	__pad += 6;
	__pad += 7;
	__pad += 8;
	(void)__pad;
	/* ORACLE_REJECT_LINE: use after check */
	return *entry;
}

char _license[] SEC("license") = "MIT";
/* case_id=NP-idiomatic-pad8 obligation=NullablePointer var=entry pad=8 */

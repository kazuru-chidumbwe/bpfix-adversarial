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
int np_ptr_pad0(void *ctx)
{
	__u32 key = 0;
	__u64 *ptr = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_LOSS_LINE: null-check (SourceComment name-shaped vs idiomatic) */
	if (!ptr)
		return 0;
	/* ORACLE_REJECT_LINE: use after check */
	return *ptr;
}

char _license[] SEC("license") = "MIT";
/* case_id=NP-brittle-pad0 obligation=NullablePointer var=ptr pad=0 */

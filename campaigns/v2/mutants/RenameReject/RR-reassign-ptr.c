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
int rr_reassign(void *ctx)
{
	__u32 key = 0;
	__u64 *ptr = bpf_map_lookup_elem(&m, &key);
	if (!ptr)
		return 0;
	/* ORACLE_LOSS_LINE: pointer reassigned after its check */
	ptr = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_REJECT_LINE: reassigned pointer dereferenced */
	return *ptr;
}

char _license[] SEC("license") = "GPL";
/* case_id=RR-reassign-ptr family=RenameReject construct=reassign name=ptr */

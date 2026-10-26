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
	__u64 *tmp = bpf_map_lookup_elem(&m, &key);
	if (!tmp)
		return 0;
	/* ORACLE_LOSS_LINE: pointer reassigned after its check */
	tmp = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_REJECT_LINE: reassigned pointer dereferenced */
	return *tmp;
}

char _license[] SEC("license") = "GPL";
/* case_id=RR-reassign-tmp family=RenameReject construct=reassign name=tmp */

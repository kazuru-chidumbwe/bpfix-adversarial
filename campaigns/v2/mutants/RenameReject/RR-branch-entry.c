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
int rr_branch(void *ctx)
{
	__u32 key = 0;
	__u64 *entry = bpf_map_lookup_elem(&m, &key);
	__u32 flag = bpf_get_prandom_u32() & 1;
	/* ORACLE_LOSS_LINE: check only on one branch */
	if (flag) {
		if (!entry)
			return 0;
	}
	/* ORACLE_REJECT_LINE: other branch reaches the use unchecked */
	return *entry;
}

char _license[] SEC("license") = "GPL";
/* case_id=RR-branch-entry family=RenameReject construct=branch name=entry */

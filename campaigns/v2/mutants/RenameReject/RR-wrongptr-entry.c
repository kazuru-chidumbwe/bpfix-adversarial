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
int rr_wrongptr(void *ctx)
{
	__u32 key = 0;
	__u64 *entry = bpf_map_lookup_elem(&m, &key);
	__u64 *other = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_LOSS_LINE: check guards the wrong pointer */
	if (!entry)
		return 0;
	/* ORACLE_REJECT_LINE: unchecked pointer dereferenced */
	return *other;
}

char _license[] SEC("license") = "GPL";
/* case_id=RR-wrongptr-entry family=RenameReject construct=wrongptr name=entry */

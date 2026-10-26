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
int rr_flag(void *ctx)
{
	__u32 key = 0;
	__u64 *entry = bpf_map_lookup_elem(&m, &key);
	/* ORACLE_LOSS_LINE: null check on entry omitted; flag check is not one */
	__u32 ok = bpf_get_prandom_u32() & 1;
	if (!ok)
		return 0;
	/* ORACLE_REJECT_LINE: unchecked map value dereferenced */
	return *entry;
}

char _license[] SEC("license") = "GPL";
/* case_id=RR-flag-ok family=RenameReject construct=flag name=ok */

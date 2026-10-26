// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_ARRAY);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u64);
} slot SEC(".maps");

SEC("xdp")
int ppm_pad8(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	__u32 key = 0;
	if (data + 8 > data_end)
		return XDP_DROP;
	__u64 *cell = bpf_map_lookup_elem(&slot, &key);
	if (!cell)
		return XDP_DROP;
	/* ORACLE_LOSS_LINE: packet pointer round-tripped through a map value */
	*(volatile __u64 *)cell = (__u64)(long)data;
	void *back = (void *)(long)*(volatile __u64 *)cell;
	/* distance pad (volatile): 8 ops */
	volatile __u64 __pad = 0;
	__pad += 1;
	__pad += 2;
	__pad += 3;
	__pad += 4;
	__pad += 5;
	__pad += 6;
	__pad += 7;
	__pad += 8;
	/* ORACLE_REJECT_LINE: scalar dereferenced as a packet pointer */
	return *(__u8 *)back;
}

char _license[] SEC("license") = "GPL";
/* case_id=PPM-pad8 family=ProvenanceMap base=PointerProvenance pad=8 */

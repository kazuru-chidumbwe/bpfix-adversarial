// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int pbs_pad32(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	/* ORACLE_LOSS_LINE: under-check, only 1 byte proven */
	if (data + 1 > data_end)
		return XDP_DROP;
	/* distance pad (pointer spill): 32 round trips */
	void * volatile __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	__pad_slot = data; data = __pad_slot;
	/* ORACLE_REJECT_LINE: 8-byte load needs a larger packet range */
	return *(__u64 *)data;
}

char _license[] SEC("license") = "GPL";
/* case_id=PBS-pad32 family=VolatilePad base=PacketBounds-spill pad=32 */

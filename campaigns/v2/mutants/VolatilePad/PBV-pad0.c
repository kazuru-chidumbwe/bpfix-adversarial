// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int pbv_pad0(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	/* ORACLE_LOSS_LINE: under-check, only 1 byte proven */
	if (data + 1 > data_end)
		return XDP_DROP;
	/* ORACLE_REJECT_LINE: 8-byte load needs a larger packet range */
	return *(__u64 *)data;
}

char _license[] SEC("license") = "GPL";
/* case_id=PBV-pad0 family=VolatilePad base=PacketBounds pad=0 */

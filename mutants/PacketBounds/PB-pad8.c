// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int pb_pad8(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	/* ORACLE_LOSS_LINE: under-check — only 1 byte proven */
	if (data + 1 > data_end)
		return XDP_DROP;
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
	/* ORACLE_REJECT_LINE: 8-byte load needs larger packet range */
	return *(__u64 *)data;
}

char _license[] SEC("license") = "MIT";
/* case_id=PB-pad8 obligation=PacketBounds pad=8 */

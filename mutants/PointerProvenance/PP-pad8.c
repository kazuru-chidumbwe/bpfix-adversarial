// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int pp_pad8(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	if (data + 8 > data_end)
		return XDP_DROP;
	/* ORACLE_LOSS_LINE: provenance washed — pkt pointer XOR prandom → scalar */
	__u64 cookie = (__u64)data;
	cookie ^= bpf_get_prandom_u32();
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
	/* ORACLE_REJECT_LINE: dereference unbound scalar as pointer */
	return *(__u64 *)(void *)cookie;
}

char _license[] SEC("license") = "MIT";
/* case_id=PP-pad8 obligation=PointerProvenance pad=8 */

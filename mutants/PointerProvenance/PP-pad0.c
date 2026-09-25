// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("xdp")
int pp_pad0(struct xdp_md *ctx)
{
	void *data = (void *)(long)ctx->data;
	void *data_end = (void *)(long)ctx->data_end;
	if (data + 8 > data_end)
		return XDP_DROP;
	/* ORACLE_LOSS_LINE: provenance washed — pkt pointer XOR prandom → scalar */
	__u64 cookie = (__u64)data;
	cookie ^= bpf_get_prandom_u32();
	/* ORACLE_REJECT_LINE: dereference unbound scalar as pointer */
	return *(__u64 *)(void *)cookie;
}

char _license[] SEC("license") = "MIT";
/* case_id=PP-pad0 obligation=PointerProvenance pad=0 */

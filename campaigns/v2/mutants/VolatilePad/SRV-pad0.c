// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("socket")
int srv_pad0(void *ctx)
{
	__u64 table[4] = {0, 1, 2, 3};
	/* ORACLE_LOSS_LINE: missing scalar range guard on idx */
	__u32 idx = bpf_get_prandom_u32();
	/* ORACLE_REJECT_LINE: load with unbounded index */
	return table[idx];
}

char _license[] SEC("license") = "GPL";
/* case_id=SRV-pad0 family=VolatilePad base=ScalarRange pad=0 */

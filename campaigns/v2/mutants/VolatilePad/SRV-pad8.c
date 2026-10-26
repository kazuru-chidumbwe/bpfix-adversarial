// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("socket")
int srv_pad8(void *ctx)
{
	__u64 table[4] = {0, 1, 2, 3};
	/* ORACLE_LOSS_LINE: missing scalar range guard on idx */
	__u32 idx = bpf_get_prandom_u32();
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
	/* ORACLE_REJECT_LINE: load with unbounded index */
	return table[idx];
}

char _license[] SEC("license") = "GPL";
/* case_id=SRV-pad8 family=VolatilePad base=ScalarRange pad=8 */

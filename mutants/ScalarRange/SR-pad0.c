// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("socket")
int sr_pad0(void *ctx)
{
	__u64 stack[4] = {0, 1, 2, 3};
	/* ORACLE_LOSS_LINE: missing scalar range guard on idx */
	__u32 idx = bpf_get_prandom_u32();
	/* ORACLE_REJECT_LINE: stack load with unbound index */
	return stack[idx];
}

char _license[] SEC("license") = "MIT";
/* case_id=SR-pad0 obligation=ScalarRange pad=0 */

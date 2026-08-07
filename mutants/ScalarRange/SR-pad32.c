// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

SEC("socket")
int sr_pad32(void *ctx)
{
	__u64 stack[4] = {0, 1, 2, 3};
	/* ORACLE_LOSS_LINE: missing scalar range guard on idx */
	__u32 idx = bpf_get_prandom_u32();
	/* distance pad: 32 scalar ops */
	__u64 __pad = 0;
	__pad += 1;
	__pad += 2;
	__pad += 3;
	__pad += 4;
	__pad += 5;
	__pad += 6;
	__pad += 7;
	__pad += 8;
	__pad += 9;
	__pad += 10;
	__pad += 11;
	__pad += 12;
	__pad += 13;
	__pad += 14;
	__pad += 15;
	__pad += 16;
	__pad += 17;
	__pad += 18;
	__pad += 19;
	__pad += 20;
	__pad += 21;
	__pad += 22;
	__pad += 23;
	__pad += 24;
	__pad += 25;
	__pad += 26;
	__pad += 27;
	__pad += 28;
	__pad += 29;
	__pad += 30;
	__pad += 31;
	__pad += 32;
	(void)__pad;
	/* ORACLE_REJECT_LINE: stack load with unbound index */
	return stack[idx];
}

char _license[] SEC("license") = "MIT";
/* case_id=SR-pad32 obligation=ScalarRange pad=32 */

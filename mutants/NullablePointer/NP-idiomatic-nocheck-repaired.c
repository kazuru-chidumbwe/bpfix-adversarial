// SPDX-License-Identifier: MIT
// Lab-only adversarial mutant — not for production.
// RQ4 honesty≠utility arm: same idiomatic `entry` naming as NP-idiomatic-pad8,
// but the null check is deliberately omitted so the program fails verification.
// Construction oracle: proof is lost because the required null check was never
// established at the intended site (LOSS); reject at the unchecked dereference.
#include <linux/bpf.h>
#include <bpf/bpf_helpers.h>

struct {
	__uint(type, BPF_MAP_TYPE_HASH);
	__uint(max_entries, 1);
	__type(key, __u32);
	__type(value, __u64);
} m SEC(".maps");

SEC("socket")
int np_entry_nocheck(void *ctx)
{
	__u32 key = 0;
	__u64 *entry = bpf_map_lookup_elem(&m, &key);
	if (!entry)
		return 0;
	/* ORACLE_LOSS_LINE: missing idiomatic null-check establish on map value */
	/* intentionally omitted for RQ4 failing seed */
	/* distance pad: 8 scalar ops (noise between loss and reject) */
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
	/* ORACLE_REJECT_LINE: use of possibly-null map value */
	return *entry;
}

char _license[] SEC("license") = "MIT";
/* case_id=NP-idiomatic-nocheck obligation=NullablePointer var=entry pad=8 rq4=1 */

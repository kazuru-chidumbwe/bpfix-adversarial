// SPDX-License-Identifier: GPL-2.0 OR BSD-3-Clause
#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#ifndef XDP_DROP
#define XDP_DROP 1
#endif
#ifndef XDP_PASS
#define XDP_PASS 2
#endif

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 16);
    __type(key, __u64);
    __type(value, __u8);
} tracked_cgroups SEC(".maps");

const volatile bool filter_cgroup = true;
const volatile bool filter_cgroup_children = true;
const volatile __u64 target_cgroup_id = (0x42ULL << 32) | 0x07;
volatile __u64 child_hit_count;
volatile __u32 last_child_selector;

static __always_inline int datrail_is_cgroup_tracked_from_packet(__u8 tenant, __u8 selector)
{
    if (!filter_cgroup)
        return 1;

    __u64 current_cgroup_id = ((__u64)tenant << 32) | selector;
    if (current_cgroup_id == target_cgroup_id)
        return 1;

    if (!filter_cgroup_children)
        return 0;

    __u32 child_cgroup_id = selector;
    /* bpfix-adversarial v2 distance pad (volatile): 32 ops */
    volatile __u64 __bpfix_pad = 0;
    __bpfix_pad += 1;
    __bpfix_pad += 2;
    __bpfix_pad += 3;
    __bpfix_pad += 4;
    __bpfix_pad += 5;
    __bpfix_pad += 6;
    __bpfix_pad += 7;
    __bpfix_pad += 8;
    __bpfix_pad += 9;
    __bpfix_pad += 10;
    __bpfix_pad += 11;
    __bpfix_pad += 12;
    __bpfix_pad += 13;
    __bpfix_pad += 14;
    __bpfix_pad += 15;
    __bpfix_pad += 16;
    __bpfix_pad += 17;
    __bpfix_pad += 18;
    __bpfix_pad += 19;
    __bpfix_pad += 20;
    __bpfix_pad += 21;
    __bpfix_pad += 22;
    __bpfix_pad += 23;
    __bpfix_pad += 24;
    __bpfix_pad += 25;
    __bpfix_pad += 26;
    __bpfix_pad += 27;
    __bpfix_pad += 28;
    __bpfix_pad += 29;
    __bpfix_pad += 30;
    __bpfix_pad += 31;
    __bpfix_pad += 32;
    __u8 *tracked = bpf_map_lookup_elem(&tracked_cgroups, &child_cgroup_id);

    if (!tracked)
        return 0;
    return *tracked != 0;
}

static __always_inline void datrail_update_agg(__u8 selector)
{
    child_hit_count += 1;
    last_child_selector = selector;
}

SEC("xdp")
int rs_datrail_cgroup_filter_key_width(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    if (data + 2 > data_end)
        return XDP_PASS;

    __u8 tenant = *(__u8 *)data;
    __u8 selector = *((__u8 *)data + 1);
    if (selector == 0)
        return XDP_PASS;

    if (!datrail_is_cgroup_tracked_from_packet(tenant, selector))
        return XDP_PASS;

    datrail_update_agg(selector);
    return XDP_DROP;
}

char _license[] SEC("license") = "GPL";

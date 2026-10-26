// SPDX-License-Identifier: GPL-2.0
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

struct alloc_info {
    __u64 size;
    __u64 timestamp_ns;
    __u64 stack_id;
};

struct combined_alloc_info {
    __u64 total_size;
    __u64 number_of_allocs;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 16);
    __type(key, __u64);
    __type(value, struct alloc_info);
} allocs SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 16);
    __type(key, __u64);
    __type(value, struct combined_alloc_info);
} combined_allocs SEC(".maps");

static __always_inline void update_statistics_del(__u64 stack_id, __u64 sz)
{
    struct combined_alloc_info *existing;

    existing = bpf_map_lookup_elem(&combined_allocs, &stack_id);
    if (!existing)
        return;

    existing->total_size -= sz;
    existing->number_of_allocs -= 1;
}

SEC("xdp")
int rs_tutorial_memleak_free_info_merge(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    if (data + 2 > data_end)
        return XDP_PASS;

    __u8 selector = *(__u8 *)data;
    __u8 guarded_path = *(__u8 *)(data + 1);
    __u64 addr = selector;
    const struct alloc_info *info = bpf_map_lookup_elem(&allocs, &addr);

    if (guarded_path & 1) {
        if (!info)
            return XDP_PASS;
    }

    bpf_map_delete_elem(&allocs, &addr);
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
    update_statistics_del(info->stack_id, info->size);
    return XDP_DROP;
}

char _license[] SEC("license") = "GPL";

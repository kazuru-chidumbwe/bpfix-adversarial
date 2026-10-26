#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#ifndef XDP_ABORTED
#define XDP_ABORTED 0
#endif
#ifndef XDP_DROP
#define XDP_DROP 1
#endif
#ifndef XDP_PASS
#define XDP_PASS 2
#endif

#define SLOT_COUNT 8
#define LOOP_COUNT 16

struct scan_ctx {
    __u32 hits;
    __u8 slots[SLOT_COUNT];
};

static long scan_slot_cb(__u32 idx, void *data)
{
    struct scan_ctx *ctx = data;
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
    __u8 marker = ctx->slots[idx];

    if (marker == 0xaa)
        ctx->hits++;
    return 0;
}

SEC("xdp")
int rs_actplane_taint_loop_count_bound(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    __u8 *bytes = data;
    struct scan_ctx scan = {};

    if ((void *)(bytes + SLOT_COUNT) > data_end)
        return XDP_PASS;

    #pragma unroll
    for (int i = 0; i < SLOT_COUNT; i++)
        scan.slots[i] = bytes[i];

    bpf_loop(LOOP_COUNT, scan_slot_cb, &scan, 0);
    return scan.hits >= 2 ? XDP_DROP : XDP_PASS;
}

char _license[] SEC("license") = "GPL";

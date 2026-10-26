#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#ifndef XDP_PASS
#define XDP_PASS 2
#endif

struct event {
    __u32 mark;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4096);
} events SEC(".maps");

SEC("xdp")
int ringbuf_stack_discard(struct xdp_md *ctx)
{
    struct event *audit;
    struct event rec = {};

    /* bpfix-adversarial v2 distance pad (volatile): 8 ops */
    volatile __u64 __bpfix_pad = 0;
    __bpfix_pad += 1;
    __bpfix_pad += 2;
    __bpfix_pad += 3;
    __bpfix_pad += 4;
    __bpfix_pad += 5;
    __bpfix_pad += 6;
    __bpfix_pad += 7;
    __bpfix_pad += 8;
    audit = bpf_ringbuf_reserve(&events, sizeof(*audit), 0);
    if (!audit)
        return XDP_PASS;
    audit->mark = 3;

    rec.mark = 7;
    bpf_ringbuf_discard(&rec, 0);
    bpf_ringbuf_submit(audit, 0);
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

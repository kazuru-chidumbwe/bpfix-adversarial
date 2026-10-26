#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#ifndef XDP_PASS
#define XDP_PASS 2
#endif
#ifndef XDP_DROP
#define XDP_DROP 1
#endif
#ifndef ETH_P_IP
#define ETH_P_IP 0x0800
#endif

struct event {
    __u32 mark;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4096);
} events SEC(".maps");

SEC("xdp")
int ringbuf_nested_missing_null(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    struct event *audit;
    struct event *rec;
    __u32 is_ip;

    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    is_ip = bpf_ntohs(eth->h_proto) == ETH_P_IP;
    audit = bpf_ringbuf_reserve(&events, sizeof(*audit), 0);
    if (!audit)
        return XDP_PASS;
    audit->mark = 3;

    rec = bpf_ringbuf_reserve(&events, sizeof(*rec), 0);
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
    rec->mark = is_ip ? 7 : 11;

    bpf_ringbuf_submit(audit, 0);
    bpf_ringbuf_submit(rec, 0);
    return is_ip ? XDP_DROP : XDP_PASS;
}

char _license[] SEC("license") = "GPL";

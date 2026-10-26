#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#ifndef XDP_PASS
#define XDP_PASS 2
#endif
#ifndef BPF_F_CURRENT_CPU
#define BPF_F_CURRENT_CPU 0xffffffffULL
#endif

#define MAX_CPUS 64
#define SNAPLEN 64

struct pkt_trace_metadata {
    __u32 prog_index;
    __u32 ifindex;
    __u32 rx_queue;
    __u16 pkt_len;
    __u16 cap_len;
    __u32 action;
    __u32 flags;
};

struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __uint(max_entries, MAX_CPUS);
    __type(key, int);
    __type(value, __u32);
} xdpdump_perf_map SEC(".maps");

static __always_inline __u16 rs_min_u16(__u16 left, __u16 right)
{
    return left < right ? left : right;
}

SEC("xdp")
int rs_xdp_tools_xdpdump_perf_map_type(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;
    struct pkt_trace_metadata metadata = {};
    __u16 pkt_len;
    __u64 flags;

    if (data >= data_end)
        return XDP_PASS;

    pkt_len = (__u16)(data_end - data);
    metadata.prog_index = 7;
    metadata.ifindex = ctx->ingress_ifindex;
    metadata.rx_queue = ctx->rx_queue_index;
    metadata.pkt_len = pkt_len;
    metadata.cap_len = rs_min_u16(pkt_len, SNAPLEN);
    metadata.action = XDP_PASS;
    metadata.flags = 0;

    flags = ((__u64)metadata.cap_len << 32) | BPF_F_CURRENT_CPU;
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
    bpf_perf_event_output(ctx, &xdpdump_perf_map, flags,
                          &metadata, sizeof(metadata));

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

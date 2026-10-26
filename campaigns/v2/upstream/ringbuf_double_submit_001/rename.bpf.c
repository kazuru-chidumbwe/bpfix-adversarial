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
    __u32 proto;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4096);
} events SEC(".maps");

SEC("xdp")
int ringbuf_double_submit(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    struct event *ptr;
    struct event *audit;
    __u32 is_ip;

    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    is_ip = bpf_ntohs(eth->h_proto) == ETH_P_IP;
    ptr = bpf_ringbuf_reserve(&events, sizeof(*ptr), 0);
    if (!ptr)
        return XDP_PASS;

    ptr->mark = 7;
    ptr->proto = bpf_ntohs(eth->h_proto);
    bpf_ringbuf_submit(ptr, 0);

    if (is_ip) {
        audit = ptr;
        audit->mark = 99;
        bpf_ringbuf_submit(audit, 0);
    }

    return is_ip ? XDP_DROP : XDP_PASS;
}

char _license[] SEC("license") = "GPL";

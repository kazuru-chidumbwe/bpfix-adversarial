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
#ifndef IPPROTO_UDP
#define IPPROTO_UDP 17
#endif

#define XDPFILT_REQUIRE_ROOM(ptr, bytes) \
    do { \
        if ((void *)(ptr) + (bytes) > data_end) \
            return XDP_PASS; \
    } while (0)

static __always_inline int rs_xdp_tools_dport_policy(struct udphdr *udp)
{
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
    return bpf_ntohs(udp->dest) == 53 ? XDP_DROP : XDP_PASS;
}

SEC("xdp")
int rs_xdp_tools_ihl_macro_wrong_base(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    struct iphdr *iph;
    struct udphdr *udp;
    void *checked_l4;
    void *actual_l4;

    XDPFILT_REQUIRE_ROOM(eth, sizeof(*eth));
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    iph = data + sizeof(*eth);
    XDPFILT_REQUIRE_ROOM(iph, sizeof(*iph));
    if (iph->protocol != IPPROTO_UDP)
        return XDP_PASS;

    checked_l4 = (void *)(iph + 1);
    actual_l4 = (void *)iph + ((__u32)iph->ihl << 2);
    XDPFILT_REQUIRE_ROOM(checked_l4, sizeof(*udp));

    udp = actual_l4;
    return rs_xdp_tools_dport_policy(udp);
}

char _license[] SEC("license") = "GPL";

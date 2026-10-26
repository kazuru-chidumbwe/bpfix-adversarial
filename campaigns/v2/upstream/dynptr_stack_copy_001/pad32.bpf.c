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

extern int bpf_dynptr_from_xdp(struct xdp_md *x, __u64 flags, struct bpf_dynptr *ptr__uninit) __ksym;
extern void *bpf_dynptr_slice(const struct bpf_dynptr *p, __u32 offset, void *buffer__opt, __u32 buffer__szk) __ksym;

SEC("xdp")
int dynptr_stack_copy(struct xdp_md *ctx)
{
    struct bpf_dynptr ptr;
    struct bpf_dynptr copy;
    struct ethhdr *eth;
    struct iphdr *iph;

    if (bpf_dynptr_from_xdp(ctx, 0, &ptr))
        return XDP_PASS;

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
    __builtin_memcpy(&copy, &ptr, sizeof(copy));
    eth = bpf_dynptr_slice(&copy, 0, 0, sizeof(*eth));
    if (!eth)
        return XDP_PASS;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    iph = bpf_dynptr_slice(&copy, sizeof(*eth), 0, sizeof(*iph));
    if (!iph)
        return XDP_PASS;

    return iph->protocol == IPPROTO_UDP ? XDP_DROP : XDP_PASS;
}

char _license[] SEC("license") = "GPL";

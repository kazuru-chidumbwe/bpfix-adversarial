#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#ifndef XDP_PASS
#define XDP_PASS 2
#endif
#ifndef ETH_P_IP
#define ETH_P_IP 0x0800
#endif
#ifndef AF_INET
#define AF_INET 2
#endif
#ifndef ETH_ALEN
#define ETH_ALEN 6
#endif

SEC("xdp")
int rs_cilium_fib_lookup_param_len(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;

    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    if (eth->h_proto != bpf_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);

    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    struct bpf_fib_lookup fib = {};

    fib.family = AF_INET;
    fib.ipv4_src = iph->saddr;
    fib.ipv4_dst = iph->daddr;
    fib.ifindex = ctx->ingress_ifindex;

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
    long rc = bpf_fib_lookup(ctx, &fib, sizeof(fib) + 4, 0);

    if (rc == BPF_FIB_LKUP_RET_SUCCESS) {
        __builtin_memcpy(eth->h_dest, fib.dmac, ETH_ALEN);
        __builtin_memcpy(eth->h_source, fib.smac, ETH_ALEN);
        return bpf_redirect(fib.ifindex, 0);
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

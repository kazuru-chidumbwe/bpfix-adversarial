#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#ifndef XDP_DROP
#define XDP_DROP 1
#endif
#ifndef XDP_PASS
#define XDP_PASS 2
#endif
#ifndef ETH_P_IP
#define ETH_P_IP 0x0800
#endif
#ifndef IPPROTO_UDP
#define IPPROTO_UDP 17
#endif

static __always_inline struct udphdr *parse_udp(void *data, void *data_end)
{
    struct ethhdr *eth = data;

    if ((void *)(eth + 1) > data_end)
        return 0;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return 0;

    struct iphdr *iph = data + sizeof(*eth);
    if ((void *)(iph + 1) > data_end)
        return 0;
    if (iph->protocol != IPPROTO_UDP)
        return 0;

    struct udphdr *udp = (void *)(iph + 1);
    if ((void *)(udp + 1) > data_end)
        return 0;
    return udp;
}

SEC("xdp")
int packet_inline_return_cookie(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct udphdr *udp = parse_udp(data, data_end);

    if (!udp)
        return XDP_PASS;

    __u64 cookie = (__u64)(long)udp;
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
    asm volatile("%[cookie] <<= 32; %[cookie] >>= 32" : [cookie] "+r"(cookie));
    udp = (struct udphdr *)(long)cookie;

    return bpf_ntohs(udp->dest) == 53 ? XDP_DROP : XDP_PASS;
}

char _license[] SEC("license") = "GPL";

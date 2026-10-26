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
#ifndef ETH_P_8021Q
#define ETH_P_8021Q 0x8100
#endif
#ifndef IPPROTO_TCP
#define IPPROTO_TCP 6
#endif

struct vlan_hdr_local {
    __be16 tci;
    __be16 proto;
};

SEC("xdp")
int packet_vlan_cookie(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    void *cursor;
    __u16 proto;

    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    cursor = eth + 1;
    proto = bpf_ntohs(eth->h_proto);
    if (proto == ETH_P_8021Q) {
        struct vlan_hdr_local *vlan = cursor;

        if ((void *)(vlan + 1) > data_end)
            return XDP_PASS;
        proto = bpf_ntohs(vlan->proto);
        cursor = vlan + 1;
    }

    if (proto != ETH_P_IP)
        return XDP_PASS;

    struct iphdr *iph = cursor;
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;
    if (iph->protocol != IPPROTO_TCP)
        return XDP_PASS;

    struct tcphdr *tcp = (void *)(iph + 1);
    if ((void *)(tcp + 1) > data_end)
        return XDP_PASS;

    __u64 cookie = (__u64)(long)tcp;
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

    struct tcphdr *shadow = (void *)(long)cookie;
    return bpf_ntohs(shadow->dest) == 443 ? XDP_DROP : XDP_PASS;
}

char _license[] SEC("license") = "GPL";

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

struct config {
    __u32 drop_proto;
    __u32 seen_packets;
    __u32 pass_proto;
    __u32 key_xor;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 2);
    __type(key, __u32);
    __type(value, struct config);
} configs SEC(".maps");

static __noinline struct config *lookup_config(__u32 key)
{
    return bpf_map_lookup_elem(&configs, &key);
}

SEC("xdp")
int subprog_map_value_null(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    struct ethhdr *eth = data;
    struct config *cfg;
    __u32 key;
    __u16 proto;

    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    proto = bpf_ntohs(eth->h_proto);
    key = eth->h_dest[5] & 1;
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
    cfg = lookup_config(key);
    cfg->seen_packets += 1;
    cfg->key_xor ^= key;
    if (cfg->drop_proto == proto)
        return XDP_DROP;
    if (cfg->pass_proto == proto)
        return XDP_PASS;
    return XDP_DROP;
}

char _license[] SEC("license") = "GPL";

#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#ifndef XDP_ABORTED
#define XDP_ABORTED 0
#endif
#ifndef XDP_DROP
#define XDP_DROP 1
#endif
#ifndef XDP_PASS
#define XDP_PASS 2
#endif

#define HEAD_BYTES 12
#define TAIL_BYTES 6
#define WIRE_OFFSET 2
#define WIRE_BYTES (HEAD_BYTES + TAIL_BYTES)

SEC("xdp")
int rs_xdp_tools_load_bytes_stack_len(struct xdp_md *ctx)
{
    __u8 head[HEAD_BYTES];
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
    __u8 tail[TAIL_BYTES];
    int err;

    err = bpf_xdp_load_bytes(ctx, WIRE_OFFSET, head, WIRE_BYTES);
    if (err)
        return XDP_ABORTED;

    if (head[0] == 'B' && head[9] == 'X' && tail[1] == 'Z' && tail[5] == '!')
        return XDP_DROP;
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

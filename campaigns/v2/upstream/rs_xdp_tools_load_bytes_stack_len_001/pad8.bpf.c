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
    /* bpfix-adversarial v2 distance pad (volatile): 8 ops */
    volatile __u64 __bpfix_pad = 0;
    __bpfix_pad += 1;
    __bpfix_pad += 2;
    __bpfix_pad += 3;
    __bpfix_pad += 4;
    __bpfix_pad += 5;
    __bpfix_pad += 6;
    __bpfix_pad += 7;
    __bpfix_pad += 8;
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

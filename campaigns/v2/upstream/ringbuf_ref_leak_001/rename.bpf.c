#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

#ifndef XDP_PASS
#define XDP_PASS 2
#endif
#ifndef XDP_DROP
#define XDP_DROP 1
#endif

struct event {
    __u32 mark;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 4096);
} events SEC(".maps");

SEC("xdp")
int ringbuf_ref_leak(struct xdp_md *ctx)
{
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    bool drop_branch = false;
    struct event *audit;
    struct event *ptr = bpf_ringbuf_reserve(&events, sizeof(*ptr), 0);

    if (data + 1 <= data_end && *(__u8 *)data == 0)
        drop_branch = true;

    if (!ptr)
        return XDP_PASS;

    ptr->mark = 7;
    if (drop_branch)
        return XDP_DROP;

    audit = bpf_ringbuf_reserve(&events, sizeof(*audit), 0);
    if (!audit) {
        bpf_ringbuf_submit(ptr, 0);
        return XDP_PASS;
    }
    audit->mark = 11;

    bpf_ringbuf_submit(ptr, 0);
    bpf_ringbuf_submit(audit, 0);
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

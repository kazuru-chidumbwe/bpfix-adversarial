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

struct args_t {
    int flags;
};

struct event_t {
    __u32 pid;
    __s32 ret;
    __u64 callers[2];
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u32);
    __type(value, struct args_t);
} start SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, sizeof(__u32));
} events SEC(".maps");

static __always_inline int emit_open_stack(void *ctx, __s32 ret)
{
    __u32 pid = bpf_get_current_pid_tgid();
    struct args_t *args = bpf_map_lookup_elem(&start, &pid);
    struct event_t event = {};
    __u64 stack[3] = {};

    if (!args)
        return 0;

    event.pid = bpf_get_current_pid_tgid() >> 32;
    event.ret = ret;
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
    bpf_get_stack(ctx, &stack, sizeof(stack), BPF_F_USER_STACK);
    event.callers[0] = stack[1];
    event.callers[1] = stack[2];
    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU, &event, sizeof(event));
    return args->flags;
}

SEC("xdp")
int rs_bpftime_opensnoop_stack_wrong_prog_type(struct xdp_md *ctx)
{
    if (emit_open_stack(ctx, 0))
        return XDP_DROP;
    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";

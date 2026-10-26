#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

struct user_msg {
    __u32 pid;
    __u32 op;
    char comm[16];
};

struct kernel_msg {
    __u32 pid;
    __u32 op;
    char comm[16];
};

struct {
    __uint(type, BPF_MAP_TYPE_USER_RINGBUF);
    __uint(max_entries, 256 * 1024);
} user_ringbuf SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} kernel_ringbuf SEC(".maps");

static long handle_user_sample(struct bpf_dynptr *dynptr, void *ctx)
{
    struct user_msg *msg = bpf_dynptr_data(dynptr, 0, sizeof(*msg));
    struct kernel_msg *out;
    __u32 current_pid = bpf_get_current_pid_tgid() >> 32;

    out = bpf_ringbuf_reserve(&kernel_ringbuf, sizeof(*out), 0);
    if (!out)
        return 0;

    if (current_pid == 0) {
        if (!msg) {
            bpf_ringbuf_discard(out, 0);
            return 0;
        }
        out->pid = msg->pid;
    } else {
        out->pid = current_pid;
    }

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
    out->op = msg->op;
    __builtin_memcpy(out->comm, msg->comm, sizeof(out->comm));
    bpf_ringbuf_submit(out, 0);
    return 0;
}

SEC("tracepoint/syscalls/sys_exit_kill")
int rs_tutorial_user_ringbuf_dynptr_merge(struct trace_event_raw_sys_exit *ctx)
{
    return bpf_user_ringbuf_drain(&user_ringbuf, handle_user_sample, NULL, 0);
}

char _license[] SEC("license") = "GPL";

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
    struct kernel_msg *ptr;
    __u32 current_pid = bpf_get_current_pid_tgid() >> 32;

    ptr = bpf_ringbuf_reserve(&kernel_ringbuf, sizeof(*ptr), 0);
    if (!ptr)
        return 0;

    if (current_pid == 0) {
        if (!msg) {
            bpf_ringbuf_discard(ptr, 0);
            return 0;
        }
        ptr->pid = msg->pid;
    } else {
        ptr->pid = current_pid;
    }

    ptr->op = msg->op;
    __builtin_memcpy(ptr->comm, msg->comm, sizeof(ptr->comm));
    bpf_ringbuf_submit(ptr, 0);
    return 0;
}

SEC("tracepoint/syscalls/sys_exit_kill")
int rs_tutorial_user_ringbuf_dynptr_merge(struct trace_event_raw_sys_exit *ctx)
{
    return bpf_user_ringbuf_drain(&user_ringbuf, handle_user_sample, NULL, 0);
}

char _license[] SEC("license") = "GPL";

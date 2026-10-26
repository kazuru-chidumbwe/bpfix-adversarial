#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>

struct io_args_t {
    __u64 buf;
    __s32 fd;
    __u8 is_read;
};

struct stdio_event_t {
    __u32 pid;
    __s32 fd;
    __u32 len;
    __u8 is_read;
    __u8 pad[3];
    char buf[8];
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 12);
} rb SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 1024);
    __type(key, __u64);
    __type(value, struct io_args_t);
} io_args SEC(".maps");

SEC("tp/syscalls/sys_exit_read")
int rs_agentsight_stdiocap_user_copy_len(struct trace_event_raw_sys_exit *ctx)
{
    __u64 pid_tgid = bpf_get_current_pid_tgid();
    struct io_args_t *args;
    struct stdio_event_t *event;
    __u32 copy_size = 16;

    args = bpf_map_lookup_elem(&io_args, &pid_tgid);
    if (!args)
        return 0;
    if (ctx->ret <= 0)
        goto cleanup;

    event = bpf_ringbuf_reserve(&rb, sizeof(*event), 0);
    if (!event)
        goto cleanup;

    event->pid = pid_tgid >> 32;
    event->fd = args->fd;
    event->len = (__u32)ctx->ret;
    event->is_read = args->is_read;
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
    bpf_probe_read_user(event->buf, copy_size, (const void *)args->buf);
    bpf_ringbuf_submit(event, 0);

cleanup:
    bpf_map_delete_elem(&io_args, &pid_tgid);
    return 0;
}

char _license[] SEC("license") = "GPL";

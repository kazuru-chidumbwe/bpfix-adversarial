#ifndef __TARGET_ARCH_x86
#define __TARGET_ARCH_x86 1
#endif

#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

#ifndef EPERM
#define EPERM 1
#endif

struct decision_event {
    __u32 pid;
    __u32 cmd;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 1 << 12);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 256);
    __type(key, __u32);
    __type(value, __u32);
} protected_pids SEC(".maps");

static __always_inline int active_policy(__u32 pid)
{
    __u32 *flag = bpf_map_lookup_elem(&protected_pids, &pid);
    return flag && *flag == 7;
}

SEC("lsm/bpf")
int BPF_PROG(rs_actplane_lsm_bpf_ringbuf_merge, int cmd, union bpf_attr *attr,
             unsigned int size, bool privileged)
{
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    struct decision_event *event;

    (void)attr;
    (void)size;

    if (!active_policy(pid))
        return 0;

    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);
    if (!event && privileged)
        return 0;

    event->pid = pid;
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
    event->cmd = (__u32)cmd;
    bpf_ringbuf_submit(event, 0);
    return -EPERM;
}

char _license[] SEC("license") = "GPL";

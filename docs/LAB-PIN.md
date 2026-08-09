# Lab pin — SoftwareX template-oracle host

**Purpose:** Reproduce the SoftwareX **template-oracle** capture environment (not
cross-kernel portability). SoftwareX cite evidence uses this pin; offline inset
emitters do **not** need it.

**Cite stamp:** `20260801T181331Z`  
**Recorded pin:** [`results/env_pins/lab-test.20260801T181331Z.env.txt`](../results/env_pins/lab-test.20260801T181331Z.env.txt)

| Field | SoftwareX template-oracle value |
| --- | --- |
| Host label | `lab-server` |
| Distro | Debian 13 (trixie) |
| Kernel | `6.12.86+deb13-amd64` (`uname -r`) |
| Arch | `x86_64` |
| clang | Debian clang 19.1.7 |
| bpftool | v7.5.0 (libbpf v1.5) |
| Capture | `bpftool prog load … -d` |

Separation demonstration (not template-oracle scores): Ubuntu 24.04
`app-test-server`, kernel `6.8.0-136-generic`, clang 18.1.3, bpftool v7.4.0 —
see `results/env_pins/app-test-server.20260807T112233Z.env.txt`. The SoftwareX
Ollama localization–repair separation capture on that host recorded ACCEPT on
2026-08-07 (stdlib `urllib` HTTP client; no `ollama` PyPI package).

| Role | Host | Notes |
| --- | --- | --- |
| Template-oracle scores | `lab-server` (Debian 13 / `6.12.86+deb13-amd64`) | SoftwareX cite pin |
| Separation + marker A/B | `app-test-server` (Ubuntu 24.04 / `6.8.0-136-generic`) | Not portability claim |
| Offline bpfix CLI replay | WSL/Linux developer host | Reads stamped logs only; does not re-verify |

Optional RQ1 offline CLI replay uses upstream bpfix at immutable commit
`81d97e4a528456e0082a77f4fb6edd13fa092b7b` (see `docs/UPSTREAM.md`).

## What reviewers must match

SoftwareX template-oracle **scores** depend on verifier text from this kernel.
Matching userspace (clang/bpftool) without matching `uname -r` is **not** the
cite pin. Exact bit-identical kernel rebuild from source is **not** required if
you install Debian 13’s published `linux-image-6.12.86+deb13-amd64` (or the
successor package that reports the same `uname -r`) and record a new env pin
when the string differs.

## Bootstrap (Debian 13 / x86_64)

Run on a fresh Debian 13 VM (Hyper-V, QEMU, Vagrant — see `Vagrantfile`):

```bash
sudo apt-get update
sudo apt-get install -y \
  build-essential clang llvm \
  linux-headers-$(uname -r) \
  libbpf-dev bpftool \
  python3 python3-venv python3-pip \
  git make

# Prefer the SoftwareX-recorded kernel package when available:
#   apt-cache search linux-image | grep 6.12.86
#   sudo apt-get install -y linux-image-6.12.86+deb13-amd64
# then reboot into that image.

clang --version          # expect 19.x on SoftwareX pin
bpftool version          # expect v7.5.0 class
uname -r                 # SoftwareX cite: 6.12.86+deb13-amd64
uname -m                 # x86_64

# Passwordless sudo recommended for bpftool prog load on the lab account.
```

Clone and capture (credentials in gitignored `lab/.env`):

```bash
git clone https://github.com/kazuru-chidumbwe/bpfix-adversarial.git
cd bpfix-adversarial
git checkout v1.0.0   # or SoftwareX cite tag
python3 -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .
# LAB_TEST_HOST / LAB_TEST_SSH_KEY or PASSWORD — see docs/TAGS.md
python tools/lab_capture_via_env.py
```

## Privilege and failure notes

- Loading programs needs CAP_BPF / CAP_PERFMON or root via sudo.
- Missing clang → compile fails before load.
- Missing bpftool → no verifier log.
- Nested virt / Hyper-V: used by the author for SoftwareX; not required if you
  have a bare-metal or cloud Debian 13 host with the pin.

## Offline path (no lab)

```bash
make smoke && make insets
# or: docker build -t bpfix-adversarial:offline . && docker run --rm bpfix-adversarial:offline
```

Replays committed fixtures/logs only. Does **not** exercise this kernel pin.

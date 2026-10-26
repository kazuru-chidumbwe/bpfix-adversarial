# Running campaign v2 on the lab host

Runs **on the lab host itself** from a clone of this repository. No SSH helpers,
no `lab/.env` and no password files are involved. One command does everything:
capture, bpfix replay, scoring, and the v1.0.2 pin-reproduction check. About
100 compile+load cycles take a few minutes. Building bpfix the first time takes
about a minute.

## 1. Host

Cite pin: Debian 13 (trixie), x86_64, kernel `6.12.86+deb13-amd64`
([`LAB-PIN.md`](LAB-PIN.md)). Check first:

```bash
uname -r        # must print 6.12.86+deb13-amd64 for cite evidence
uname -m        # x86_64
```

If the kernel differs, install `linux-image-6.12.86+deb13-amd64` and reboot
into it ([`LAB-PIN.md`](LAB-PIN.md) § Bootstrap). The driver refuses another
kernel unless `ALLOW_OTHER_KERNEL=1` is set, and that run is not cite evidence.

## 2. Packages (once)

```bash
sudo apt-get update
sudo apt-get install -y build-essential clang llvm libbpf-dev bpftool \
  python3 python3-venv git make curl pkg-config
# Rust toolchain for building bpfix at the pin
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
. "$HOME/.cargo/env"
```

Loading programs needs root. Either give the lab account passwordless sudo
**for bpftool only**:

```bash
echo "$USER ALL=(root) NOPASSWD: /usr/sbin/bpftool" | sudo tee /etc/sudoers.d/bpfix-bpftool
sudo chmod 0440 /etc/sudoers.d/bpfix-bpftool
sudo -n bpftool version          # must work without a prompt
```

…or run the driver as root with `BPFTOOL=bpftool`. Check bpffs:

```bash
mountpoint -q /sys/fs/bpf || sudo mount -t bpf bpf /sys/fs/bpf
```

## 3. Clone the repository

```bash
git clone https://github.com/kazuru-chidumbwe/bpfix-adversarial.git
cd bpfix-adversarial
git checkout improvements-v2         # or the tag cut from it
python3 -m venv .venv && . .venv/bin/activate
pip install -U pip && pip install -e .
make smoke                           # offline sanity: version + unit tests + rename demo
python tools/check_results_fresh.py  # committed tables still match their emitters
```

## 4. Run

```bash
LABEL=lab-server lab/run_v2_campaign.sh
```

What it does, in order:

1. **Host checks:** kernel pin, clang, libbpf headers, `sudo -n bpftool`, bpffs.
2. **bpfix:** clones `eunomia-bpf/bpfix` into `~/src/bpfix`, checks out
   `81d97e4a528456e0082a77f4fb6edd13fa092b7b`, and runs `cargo build --release -p bpfix`.
   It refuses a source tree at any other commit.
3. **`vmlinux.h`:** `bpftool btf dump file /sys/kernel/btf/vmlinux format c`
   into `.cache/vmlinux-<kernel>/`. The upstream cases include `<vmlinux.h>`.
4. **Sources:** regenerates `campaigns/v2/mutants` and `campaigns/v2/upstream`
   and fails if they differ from the committed tree.
5. **Capture** with `tools/capture_local.py` into
   `campaigns/v2/lab/<LABEL>-<UTC stamp>/`:
   - `templates/`: 29 v2 mutants (`clang -O2 -g -target bpf -I/usr/include/<multiarch> -idirafter /usr/include`, the v1 flags)
   - `upstream/`: 69 upstream variants (`clang -target bpf -O2 -g -I /usr/include -D__TARGET_ARCH_x86 -I <vmlinux dir>`, upstream's `bpf_case.py` flags; program type inferred by libbpf)
   - `v1-recapture/`: the 16 v1.0.2 mutants
   Each directory gets `env.<stamp>.txt` (uname, clang, bpftool),
   `manifest.<stamp>.jsonl` (source and log SHA-256, verdict, processed
   instructions) and one `.log` per case.
6. **Replay:** `tools/replay_bpfix_dir.py` writes `<case>.<stamp>.bpfix.txt`
   and `bpfix.<stamp>.json` (version, source commit, pin match, binary SHA-256).
7. **Score:** `tools/score_v2_campaign.py` → `results/v2_scores.{md,json}`, and
   `tools/compare_v1_recapture.py` → `v1-recapture/v1_recapture_compare.json`.

Options: `BPFTOOL="bpftool"` (when root), `BPFIX_SRC=/path`,
`BPFIX=/path/to/binary`, `SKIP_V1=1`, `ALLOW_OTHER_KERNEL=1`.

## 5. Check the run before committing

```bash
RUN=$(ls -d campaigns/v2/lab/*/ | tail -1)
cat "$RUN/templates/env."*.txt                     # kernel 6.12.86+deb13-amd64, clang 19.1.7, bpftool v7.5.0
grep -h '"verdict"' "$RUN"/*/manifest.*.jsonl | grep -c COMPILE_FAIL   # expect 0
python3 -c "import json,sys;d=json.load(open('$RUN/v1-recapture/v1_recapture_compare.json'));print(d['identical'],'/',d['n'])"
less "$RUN/results/v2_scores.md"
```

Expected on the pin:

| Check | Expected | If not |
| --- | --- | --- |
| v1 recapture | 16/16 identical normalized program-load logs | The host is not the pin (kernel, clang or bpftool drift). Record it; do not cite the v2 run as pin evidence. |
| templates | 29 REJECT | A template accepted on 6.12.86 (most likely PPM, if a pointer store into a map value is refused or optimised) is a finding; report it, do not retune silently. |
| upstream | 69 REJECT | A variant that no longer rejects means the transform changed semantics; exclude that pair and say so. |
| VolatilePad | `insns grow with pad: yes` for every family | The pad was optimised away on this clang. |

Then commit the run:

```bash
git add "$RUN" && git commit -m "Campaign v2 lab capture ($(basename "$RUN"))"
git push -u origin improvements-v2
```

## 6. Optional

- **Marker A/B on the pin** (the committed A/B ran on Ubuntu 6.8):
  `python tools/lab_marker_isolation_ab.py --out results/marker_isolation_lab.pin.json`.
  This uses the SSH helpers and `lab/.env` ([`LAB-PIN.md`](LAB-PIN.md)).
  Passwords now travel over the SSH channel's stdin.
- **Remote driving** from a workstation instead of logging in: run
  `ssh lab-server 'cd bpfix-adversarial && LABEL=lab-server lab/run_v2_campaign.sh'`
  and pull the results with `git pull` after the lab host pushes them, or with
  `scp -r`.
- **All 75 main75 cases:** extend `fixtures/upstream/subset_seed.json` (or a
  copy) to the full split, run `tools/fetch_depth21_upstream.py`, then
  `tools/score_upstream_repair_site.py` and `make v2-mutants` before the lab run.

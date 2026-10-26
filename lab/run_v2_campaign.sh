#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Campaign v2 on the lab host, end to end. Run ON the lab host from a clone of
# this repository (no SSH helpers, no password files). See docs/LAB-RUN-V2.md.
#
#   lab/run_v2_campaign.sh                    # cite pin: refuses another kernel
#   ALLOW_OTHER_KERNEL=1 LABEL=x lab/run_v2_campaign.sh   # any other host
#
# Environment (all optional):
#   LABEL        host label written into env pins        (default: lab-server)
#   BPFTOOL      bpftool command                          (default: "sudo -n bpftool")
#   BPFIX_SRC    bpfix checkout; cloned+built if missing  (default: $HOME/src/bpfix)
#   BPFIX        bpfix binary                             (default: $BPFIX_SRC/target/release/bpfix)
#   SKIP_V1=1    skip the v1.0.2 recapture / pin-reproduction check
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PIN_KERNEL="6.12.86+deb13-amd64"
BPFIX_PIN="81d97e4a528456e0082a77f4fb6edd13fa092b7b"
LABEL="${LABEL:-lab-server}"
BPFTOOL="${BPFTOOL:-sudo -n bpftool}"
BPFIX_SRC="${BPFIX_SRC:-$HOME/src/bpfix}"
BPFIX="${BPFIX:-$BPFIX_SRC/target/release/bpfix}"
PY="${PYTHON:-python3}"

say() { printf '\n== %s\n' "$*"; }

say "host checks"
KERNEL="$(uname -r)"
echo "kernel=$KERNEL arch=$(uname -m)"
if [[ "$KERNEL" != "$PIN_KERNEL" && "${ALLOW_OTHER_KERNEL:-0}" != "1" ]]; then
  echo "kernel $KERNEL is not the cite pin $PIN_KERNEL." >&2
  echo "Boot the pinned kernel (docs/LAB-PIN.md) or set ALLOW_OTHER_KERNEL=1 for a non-cite run." >&2
  exit 1
fi
command -v clang >/dev/null || { echo "clang missing (apt-get install clang llvm)" >&2; exit 1; }
[[ -f /usr/include/bpf/bpf_helpers.h ]] || { echo "libbpf headers missing (apt-get install libbpf-dev)" >&2; exit 1; }
$BPFTOOL version >/dev/null || { echo "bpftool not usable as: $BPFTOOL (passwordless sudo needed for -n)" >&2; exit 1; }
mountpoint -q /sys/fs/bpf || { echo "bpffs not mounted: sudo mount -t bpf bpf /sys/fs/bpf" >&2; exit 1; }
clang --version | head -1
$BPFTOOL version | head -2

say "bpfix @ $BPFIX_PIN"
if [[ ! -x "$BPFIX" ]]; then
  command -v cargo >/dev/null || { echo "cargo missing: https://rustup.rs (stable toolchain)" >&2; exit 1; }
  if [[ ! -d "$BPFIX_SRC/.git" ]]; then
    git clone https://github.com/eunomia-bpf/bpfix "$BPFIX_SRC"
  fi
  git -C "$BPFIX_SRC" fetch --quiet origin "$BPFIX_PIN" || true
  git -C "$BPFIX_SRC" checkout --quiet "$BPFIX_PIN"
  (cd "$BPFIX_SRC" && cargo build --release -p bpfix)
fi
HEAD="$(git -C "$BPFIX_SRC" rev-parse HEAD)"
[[ "$HEAD" == "$BPFIX_PIN" ]] || { echo "bpfix source at $HEAD, expected $BPFIX_PIN" >&2; exit 1; }
"$BPFIX" --version

say "vmlinux.h for the upstream cases"
VMLINUX_DIR="$ROOT/.cache/vmlinux-$KERNEL"
mkdir -p "$VMLINUX_DIR"
$BPFTOOL btf dump file /sys/kernel/btf/vmlinux format c > "$VMLINUX_DIR/vmlinux.h"
wc -l "$VMLINUX_DIR/vmlinux.h"

say "regenerate sources and confirm they equal the committed ones"
$PY tools/generate_v2_mutants.py
$PY tools/gen_upstream_metamorphic.py > /dev/null
git diff --exit-code -- campaigns/v2/mutants campaigns/v2/upstream \
  || { echo "generated sources differ from the committed tree; commit or revert first" >&2; exit 1; }

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="campaigns/v2/lab/${LABEL}-${STAMP}"
mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/harness-commit.txt"

say "capture: v2 templates (29)"
$PY tools/capture_local.py --src campaigns/v2/mutants --out "$OUT/templates" --bpftool "$BPFTOOL" --label "$LABEL"

say "capture: upstream metamorphic variants (69)"
$PY tools/capture_local.py --profile upstream --vmlinux-dir "$VMLINUX_DIR" \
  --src campaigns/v2/upstream --glob '*/*.bpf.c' --out "$OUT/upstream" --bpftool "$BPFTOOL" --label "$LABEL"

if [[ "${SKIP_V1:-0}" != "1" ]]; then
  say "capture: v1.0.2 mutants (pin-reproduction check)"
  $PY tools/capture_local.py --src mutants --out "$OUT/v1-recapture" --bpftool "$BPFTOOL" --label "$LABEL"
fi

say "bpfix replay"
for d in templates upstream v1-recapture; do
  [[ -d "$OUT/$d" ]] || continue
  $PY tools/replay_bpfix_dir.py --captured "$OUT/$d" --bpfix "$BPFIX" --bpfix-src "$BPFIX_SRC" | grep -E 'n_replayed|matches_pin'
done

say "score"
$PY tools/score_v2_campaign.py --captured "$OUT/templates" --upstream-captured "$OUT/upstream" --out "$OUT/results"
if [[ -d "$OUT/v1-recapture" ]]; then
  $PY tools/compare_v1_recapture.py --recaptured "$OUT/v1-recapture" | tail -1
fi

say "done"
echo "results: $OUT/results/v2_scores.md"
echo "commit:  git add $OUT && git commit -m 'Campaign v2 lab capture ($LABEL $STAMP)'"

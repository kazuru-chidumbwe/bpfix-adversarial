#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Verifier-visible rewrites of main75 (docs/MAIN75-PIN-PROTOCOL.md Section 7) on
# the cite pin: capture every rewritten buggy and fixed file, then replay bpfix
# and every registered external reporter that is installed. Run ON the lab host.
#
# Environment (optional): LABEL, BPFTOOL, BPFIX_SRC, BPFIX, ALLOW_OTHER_KERNEL,
# PRETTY_VERIFIER, PREVAIL (+ _SRC). bpfix must already be built (lab/run_v2_campaign.sh).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PIN_KERNEL="6.12.86+deb13-amd64"
LABEL="${LABEL:-lab-server}"
BPFTOOL="${BPFTOOL:-sudo -n bpftool}"
BPFIX_SRC="${BPFIX_SRC:-$HOME/src/bpfix}"
BPFIX="${BPFIX:-$BPFIX_SRC/target/release/bpfix}"
PY="${PYTHON:-python3}"

say() { printf '\n== %s\n' "$*"; }

KERNEL="$(uname -r)"
if [[ "$KERNEL" != "$PIN_KERNEL" && "${ALLOW_OTHER_KERNEL:-0}" != "1" ]]; then
  echo "kernel $KERNEL is not the cite pin $PIN_KERNEL" >&2
  exit 1
fi
git diff --quiet HEAD -- campaigns/n3 || { echo "rewrites differ from the committed tree" >&2; exit 1; }

VMLINUX_DIR="$ROOT/.cache/vmlinux-$KERNEL"
mkdir -p "$VMLINUX_DIR"
$BPFTOOL btf dump file /sys/kernel/btf/vmlinux format c > "$VMLINUX_DIR/vmlinux.h"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="campaigns/n3/lab/${LABEL}-${STAMP}"
mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/harness-commit.txt"

say "capture: rewrites"
$PY tools/capture_local.py --profile upstream --vmlinux-dir "$VMLINUX_DIR" \
  --src campaigns/n3 --glob '*/*.bpf.c' --out "$OUT/rewrites" --bpftool "$BPFTOOL" --label "$LABEL"

say "bpfix replay"
$PY tools/replay_bpfix_dir.py --captured "$OUT/rewrites" --bpfix "$BPFIX" --bpfix-src "$BPFIX_SRC" \
  | grep -E 'n_replayed|matches_pin'

if [[ -n "${PRETTY_VERIFIER:-}" ]]; then
  say "Pretty Verifier replay"
  $PY tools/replay_reporter.py --reporter PrettyVerifier --captured "$OUT/rewrites" \
    --vmlinux-dir "$VMLINUX_DIR" | grep -E 'n_replayed|n_compile_failed'
fi

if [[ -n "${PREVAIL:-}" ]]; then
  say "PREVAIL replay"
  $PY tools/replay_reporter.py --reporter PREVAIL --captured "$OUT/rewrites" \
    --vmlinux-dir "$VMLINUX_DIR" | grep -E 'n_replayed|n_compile_failed'
fi

say "done"
echo "run: $OUT"

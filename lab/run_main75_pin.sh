#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# main75 on the cite pin: buggy + fixed of all 75 cases and their metamorphic
# variants, captured on this host and replayed through bpfix. Scoring rules:
# docs/MAIN75-PIN-PROTOCOL.md. Run ON the lab host from a clone of this repo.
#
#   lab/run_main75_pin.sh                     # cite pin: refuses another kernel
#
# Environment (all optional): LABEL, BPFTOOL, BPFIX_SRC, BPFIX, ALLOW_OTHER_KERNEL
# (same meaning as in lab/run_v2_campaign.sh). bpfix must already be built
# (lab/run_v2_campaign.sh builds it).
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

say "host checks"
KERNEL="$(uname -r)"
echo "kernel=$KERNEL"
if [[ "$KERNEL" != "$PIN_KERNEL" && "${ALLOW_OTHER_KERNEL:-0}" != "1" ]]; then
  echo "kernel $KERNEL is not the cite pin $PIN_KERNEL" >&2
  exit 1
fi
[[ -x "$BPFIX" ]] || { echo "bpfix binary missing: $BPFIX (run lab/run_v2_campaign.sh first)" >&2; exit 1; }
git diff --quiet HEAD -- fixtures/upstream campaigns/v2/upstream \
  || { echo "case sources differ from the committed tree" >&2; exit 1; }

VMLINUX_DIR="$ROOT/.cache/vmlinux-$KERNEL"
mkdir -p "$VMLINUX_DIR"
$BPFTOOL btf dump file /sys/kernel/btf/vmlinux format c > "$VMLINUX_DIR/vmlinux.h"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="campaigns/main75/lab/${LABEL}-${STAMP}"
mkdir -p "$OUT"
git rev-parse HEAD > "$OUT/harness-commit.txt"

for which in buggy fixed; do
  say "capture: $which (75)"
  $PY tools/capture_local.py --profile upstream --vmlinux-dir "$VMLINUX_DIR" \
    --src fixtures/upstream/bpfix-bench-cases --glob "*/$which.bpf.c" \
    --out "$OUT/$which" --bpftool "$BPFTOOL" --label "$LABEL"
done

say "capture: metamorphic variants"
$PY tools/capture_local.py --profile upstream --vmlinux-dir "$VMLINUX_DIR" \
  --src campaigns/v2/upstream --glob '*/*.bpf.c' --out "$OUT/variants" \
  --bpftool "$BPFTOOL" --label "$LABEL"

say "bpfix replay"
for d in buggy variants; do
  $PY tools/replay_bpfix_dir.py --captured "$OUT/$d" --bpfix "$BPFIX" --bpfix-src "$BPFIX_SRC" \
    | grep -E 'n_replayed|matches_pin'
done

say "done"
echo "run: $OUT"

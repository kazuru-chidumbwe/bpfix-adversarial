#!/bin/bash
# Replay pinned-lab verifier logs through upstream bpfix CLI (offline).
# Requires: built bpfix binary (default ~/src/bpfix/target/release/bpfix).
set -euo pipefail
source "${HOME}/.cargo/env" 2>/dev/null || true
BPFIX="${BPFIX:-${HOME}/src/bpfix/target/release/bpfix}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Allow Windows/WSL mount path override
ROOT="${BPFIX_ADV_ROOT:-$ROOT}"
STAMP="${STAMP:-20260801T181331Z}"
OUTDIR="$ROOT/results/rq1_bpfix_cli_raw"
mkdir -p "$OUTDIR"

CASES=(
  PB-pad0 PB-pad8 PB-pad32
  PP-pad0 PP-pad8 PP-pad32
  SR-pad0 SR-pad8 SR-pad32
)

if [[ ! -x "$BPFIX" ]]; then
  echo "bpfix binary not found/executable: $BPFIX" >&2
  echo "Build upstream bpfix @ 81d97e4a… then re-run, or set BPFIX=." >&2
  exit 1
fi

BPFIX_VERSION="$("$BPFIX" --version 2>&1)"
# Record it: every other pin in this artifact is hash- or manifest-backed,
# and the emitter reads this file rather than carrying a literal.
printf '%s
' "$BPFIX_VERSION" > "$OUTDIR/bpfix-version.txt"
echo "bpfix=$BPFIX_VERSION"
echo "root=$ROOT"
echo "stamp=$STAMP"

for c in "${CASES[@]}"; do
  LOG="$ROOT/fixtures/logs/captured/${c}.${STAMP}.log"
  if [[ ! -f "$LOG" ]]; then
    echo "MISSING $LOG" >&2
    exit 1
  fi
  set +e
  "$BPFIX" "$LOG" > "$OUTDIR/${c}.txt" 2>"$OUTDIR/${c}.err"
  rc=$?
  set -e
  echo "ran $c rc=$rc bytes=$(wc -c < "$OUTDIR/${c}.txt")"
done

echo "DONE. Next: python tools/emit_rq1_bpfix_cli.py"

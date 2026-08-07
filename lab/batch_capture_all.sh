#!/usr/bin/env bash
# Batch capture all mutants on Linux lab. Run ON lab-test (not Windows PowerShell).
# Usage: bash lab/batch_capture_all.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUT_DIR="fixtures/logs/captured"
META_DIR="results/env_pins"
OBJ_DIR="/tmp/bpfix-adv-objs"
mkdir -p "$OUT_DIR" "$META_DIR" "$OBJ_DIR"

{
  echo "host=$(hostname)"
  echo "user=$(whoami)"
  echo "utc=$STAMP"
  uname -a
  clang --version | head -2
  bpftool version
} | tee "$META_DIR/lab-test.${STAMP}.env.txt"

MANIFEST="$META_DIR/capture-manifest.${STAMP}.jsonl"
: > "$MANIFEST"

capture_one() {
  local src="$1"
  local case_id
  case_id="$(basename "$src" .c)"
  local obj="$OBJ_DIR/${case_id}.o"
  local log="$OUT_DIR/${case_id}.${STAMP}.log"
  local pin="/sys/fs/bpf/bpfix_adv_${case_id}"
  local ptype=socket
  if grep -q 'SEC("xdp")' "$src"; then ptype=xdp; fi

  echo "=== CAPTURE $case_id type=$ptype ==="
  if ! clang -O2 -g -target bpf \
      -I/usr/include/x86_64-linux-gnu \
      -idirafter /usr/include \
      -c "$src" -o "$obj" 2>"$log.compile"; then
    echo "COMPILE_FAIL $case_id" | tee "$log"
    cat "$log.compile" >> "$log" || true
    return 0
  fi
  if command -v sudo >/dev/null 2>&1; then
    sudo bpftool prog load "$obj" "$pin" type "$ptype" log_level 2 2>"$log" || true
    sudo rm -f "$pin" 2>/dev/null || true
  else
    bpftool prog load "$obj" "$pin" type "$ptype" log_level 2 2>"$log" || true
    rm -f "$pin" 2>/dev/null || true
  fi
  local src_hash log_hash
  src_hash="$(sha256sum "$src" | awk '{print $1}')"
  log_hash="$(sha256sum "$log" | awk '{print $1}')"
  printf '{"case_id":"%s","src":"%s","src_sha256":"%s","log":"%s","log_sha256":"%s","utc":"%s"}\n' \
    "$case_id" "$src" "$src_hash" "$log" "$log_hash" "$STAMP" | tee -a "$MANIFEST"
  echo "--- tail $case_id ---"
  tail -n 20 "$log" || true
}

mapfile -t SRCS < <(find mutants -name '*.c' | sort)
for src in "${SRCS[@]}"; do
  capture_one "$src"
done

echo "DONE stamp=$STAMP n=${#SRCS[@]}"
echo "Manifest: $MANIFEST"
wc -l "$MANIFEST"

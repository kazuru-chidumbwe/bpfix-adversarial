#!/usr/bin/env bash
# Phase 3 — env-pin + dual-tier capture (do NOT overwrite fixtures/logs/synthetic/).
# Usage on lab host after syncing repo:
#   ./lab/capture_env_pin.sh NP-idiomatic-pad8 mutants/NullablePointer/NP-idiomatic-pad8.c
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASE_ID="${1:?case id}"
SRC="${2:?path to .c}"
OUT_DIR="${ROOT}/fixtures/logs/captured"
META_DIR="${ROOT}/results/env_pins"
mkdir -p "$OUT_DIR" "$META_DIR"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
HOST="$(hostname -s 2>/dev/null || hostname)"
RAW_LOG="${OUT_DIR}/${CASE_ID}.${STAMP}.log"
META="${META_DIR}/${CASE_ID}.${STAMP}.json"

{
  echo "=== uname ==="; uname -a
  echo "=== clang ==="; clang --version | head -3 || true
  echo "=== llc ==="; llc --version 2>/dev/null | head -3 || true
  echo "=== bpftool ==="; bpftool version 2>/dev/null || true
  echo "=== kernel ==="; uname -r
} > "${META%.json}.env.txt"

# Placeholder compile/load hook — wire to lab/Makefile targets.
echo "; captured stub — replace with real verifier -l2 reject log" > "$RAW_LOG"
echo "; CASE_ID=${CASE_ID}" >> "$RAW_LOG"
echo "; SRC=${SRC}" >> "$RAW_LOG"

SRC_HASH="$(sha256sum "$SRC" | awk '{print $1}')"
LOG_HASH="$(sha256sum "$RAW_LOG" | awk '{print $1}')"

python3 - <<PY
import json
from pathlib import Path
meta = {
  "case_id": "${CASE_ID}",
  "src": "${SRC}",
  "host": "${HOST}",
  "utc": "${STAMP}",
  "src_sha256": "${SRC_HASH}",
  "log_sha256": "${LOG_HASH}",
  "log_path": "fixtures/logs/captured/${CASE_ID}.${STAMP}.log",
  "note": "dual-tier: synthetic fixtures untouched",
}
Path(r"${META}").write_text(json.dumps(meta, indent=2) + "\n")
print(meta)
PY

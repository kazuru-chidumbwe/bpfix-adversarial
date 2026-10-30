#!/usr/bin/env bash
# Which factor removes " @ file:line" from verifier-log source lines?
#   xload.sh compile <repo> <out>          build the 75 main75 buggy objects with this host's clang
#   xload.sh load <objdir> <out> [bpftool]  load each object, keep the log, count annotated lines
set -uo pipefail
mode=$1
if [[ $mode == compile ]]; then
  repo=$2; out=$3; mkdir -p "$out"
  K=$(uname -r); V="$repo/.cache/vmlinux-$K"; mkdir -p "$V"
  sudo -n bpftool btf dump file /sys/kernel/btf/vmlinux format c > "$V/vmlinux.h"
  clang --version | head -1 > "$out/CLANG"
  for src in "$repo"/fixtures/upstream/bpfix-bench-cases/*/buggy.bpf.c; do
    c=$(basename "$(dirname "$src")")
    clang -target bpf -O2 -g -I /usr/include -D__TARGET_ARCH_x86 -I "$V" -c "$src" -o "$out/$c.o" 2>/dev/null \
      || echo "$c" >> "$out/COMPILE_FAIL"
  done
  ls "$out"/*.o | wc -l
  exit 0
fi
objdir=$2; out=$3; bt=${4:-bpftool}
mkdir -p "$out"
{ echo "kernel=$(uname -r)"; echo "bpftool=$(sudo -n $bt version | head -2 | tr '\n' ' ')"; echo "objects=$(cat "$objdir/CLANG")"; } > "$out/ENV"
n=0; src=0; ann=0; rej=0
for o in "$objdir"/*.o; do
  c=$(basename "$o" .o); pin="/sys/fs/bpf/xload_$$_${c:0:60}"
  sudo -n $bt -d prog load "$o" "$pin" > "$out/$c.log" 2>&1
  sudo -n rm -f "$pin"
  n=$((n+1))
  grep -q "^processed [0-9]* insns" "$out/$c.log" && grep -q "^-- END PROG LOAD LOG --\|^libbpf: prog '.*': -- BEGIN PROG LOAD LOG --" "$out/$c.log" && rej=$((rej+1))
  s=$(grep -c '^; ' "$out/$c.log"); a=$(grep -cE '^; .* @ [^ ]+:[0-9]+$' "$out/$c.log")
  [[ $s -gt 0 ]] && src=$((src+1))
  [[ $a -gt 0 ]] && ann=$((ann+1))
done
echo "objects=$n logs_with_verifier_output=$rej logs_with_source_lines=$src logs_with_file_line=$ann" | tee "$out/COUNTS"

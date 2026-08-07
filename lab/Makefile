# Lab runner (Linux) — compile + load for verifier log capture
#
# Usage (on a Linux lab host with clang, llvm, libbpf, bpftool):
#   make -C lab NP=mutants/NullablePointer/NP-brittle-pad8.c
#
# Windows/CI uses fixtures/logs/*.log instead.

CLANG ?= clang
BPFTOOL ?= bpftool
NP ?= ../mutants/NullablePointer/NP-brittle-pad8.c
OUT ?= /tmp/bpfix-adv.o
LOG ?= /tmp/bpfix-adv.log

.PHONY: verify-log
# clang -target bpf needs multiarch includes on Debian/Ubuntu
BPF_INCLUDES ?= -I/usr/include/x86_64-linux-gnu -idirafter /usr/include

verify-log:
	$(CLANG) -O2 -g -target bpf $(BPF_INCLUDES) -c $(NP) -o $(OUT)
	$(BPFTOOL) prog load $(OUT) /sys/fs/bpf/bpfix_adv_probe 2>$(LOG) || true
	@echo "Verifier log (tail):"
	@tail -n 40 $(LOG)

.PHONY: help
help:
	@echo "Linux only. Capture reject logs then score with tools/score_np_pair.py after replacing fixtures."

# Verifier-state oracle

A second oracle, read only from the verifier's own log. It does not use the fix, the source text, or any reporter's output, so it is independent of the repair-site oracle (`bpfix_adversarial/repair_site.py`). These rules were written on 28 Oct 2026 after reading two logs to learn their layout (main75 `packet_checked_wrong_base_001` and `dynptr_slice_missing_null_check_001`), before the oracle was computed on any case. Code: `bpfix_adversarial/state_oracle.py`; results: `tools/score_state_oracle.py` writes `results/state_oracle.{json,md}`.

## 1. What is read

The program-load log at log level 2 (every capture of main75 and of the wild cases has it). Each instruction line `N: (op) insn ; state` is one step; a source annotation `; text @ file:line` gives the line of the steps after it; `from A to B: state` starts a branch the verifier resumes. Steps after the error message are ignored.

## 2. The failing path

The steps the verifier walked to reach the rejected instruction: the last segment of the log (after the last `from A to B` marker, or the whole log if there is none), preceded by the path to instruction `A`, which is taken from the most recent earlier segment holding `A` (up to its last occurrence there), recursively.

## 3. Which cases

Decided from the verifier's error message alone (`logparse.verifier_error_block`), not from any classifier:

- **NullablePointer:** the message names a type ending in `_or_null`.
- **PacketBounds:** the message contains `invalid access to packet`.

Other cases are not covered and are reported as such.

## 4. The first-loss point

- **NullablePointer:** the rejected register is the first `R<n>` in the message. Walking the failing path back from the rejected instruction, the last state that shows that register as `*_or_null(id=K, ...)` gives `K`. The first-loss point is the first step on the path whose state shows any register with `_or_null(id=K`: where the possibly-null value was created. The null check had to come after it.
- **PacketBounds:** the last step on the failing path that is a conditional jump (`if ...`) with `pkt_end` in its state: the last bound the program established. If there is none, the first step on the path whose state shows a `pkt(` pointer: where packet access began without a bound.

## 5. The oracle's sites

The source lines (file base name, line) of every step on the failing path from the first-loss point to the rejected instruction, both included. A step with no source line adds nothing.

## 6. What is reported

Per covered case: the first-loss step and its line, the site set, its size and its chance (sites over code lines, `oracle.code_line_mask`, of the files involved), and **agreement** with the repair-site oracle under R0, R1 and R2 (the two site sets share at least one line). Per reporter: primary on a state-oracle site, with Wilson 95% intervals over distinct cases, next to the same reporter's R0 result on the same cases. Both corpora: main75 (`results/main75_pin.json` cases) and the scored wild cases.

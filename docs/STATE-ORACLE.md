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

The source lines (file base name, line) of the steps on the failing path from the first-loss point up to the rejected instruction, **without the rejected instruction's own line** (the stop line). The sites are where the missing proof could still have been established; the stop line is where its absence was noticed. Excluding it keeps the oracle from agreeing by construction with any reporter that names the stop line (bpfix's `-->`, VerifierState). A step with no source line adds nothing. A case whose first-loss point is on the stop line has no sites and is reported as such.

## 6. What is reported

Per covered case: the first-loss step and its line, the site set, its size and its chance (sites over code lines, `oracle.code_line_mask`, of the files involved), and **agreement** with the repair-site oracle under R0, R1 and R2 (the two site sets share at least one line). Both corpora: main75 (`results/main75_pin.json` cases) and the scored wild cases.

The oracle is used only to check the repair-site oracle. Reporters are **not** ranked against it, because it is read from the same log that log-based reporters read. For context only, the result lists per reporter how often its primary line is a state-oracle site, marked as not a ranking.

## Changes

- 28 Oct 2026, before any case was scored, after the oracle had been run on the two format logs above and on wild rank 111 (not a covered kind): rule 5 now leaves out the stop line, and rule 6 no longer ranks reporters against the oracle. With the stop line as a site, every reporter that names it would have agreed with the oracle by construction.

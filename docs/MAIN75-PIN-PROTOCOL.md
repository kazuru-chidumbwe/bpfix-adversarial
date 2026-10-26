# main75 on the cite pin: scoring rules

These rules apply to the capture of all 75 main75 cases (upstream `eunomia-bpf/bpfix` at `81d97e4a…`) on the cite pin (Debian 13, `6.12.86+deb13-amd64`, clang 19.1.7, bpftool v7.5.0). They were committed before that capture was scored.

Background: the repair-site oracle (`bpfix_adversarial/repair_site.py`) was developed on the 21-case depth-21 slice. It was also applied, offline, to upstream's committed diagnostics for all 75 (`results/upstream_repair_site.*`). Those diagnostics were produced by upstream on its own build. The pin capture regenerates every diagnostic from the vendored source.

## 1. Capture

- `buggy.bpf.c` and `fixed.bpf.c` of every case, with upstream's compile flags (`tools/capture_local.py --profile upstream`, vmlinux.h dumped from the pin kernel), loaded with `bpftool -d prog load`.
- The metamorphic variants of every case (`campaigns/v2/upstream/<case>/`: `orig`, `pad8`, `pad32`, `rename` where generated).
- bpfix CLI at the upstream pin replays every captured log (`tools/replay_bpfix_dir.py`).

## 2. Inclusion

A case is scored only if, on the pin:

1. `buggy` compiles and is REJECTED, and
2. `fixed` compiles and is ACCEPTED, and
3. the buggy to fixed diff has at least one semantic hunk (comment, blank and preprocessor-only hunks dropped).

Each excluded case is listed with its reason: `buggy-accepts`, `buggy-compile-fail`, `fixed-rejects`, `fixed-compile-fail` or `no-semantic-hunk`. Exclusions are decided from verdicts and diffs before any reporter output is read.

## 3. Reporter outputs

- A reporter that names no line scores a miss, never an exclusion.
- A label whose quoted source text differs from the buggy source at that line counts as that reporter naming that line. It is not excluded: on the pin the diagnostic is built from this exact source, so a mismatch is the reporter's error.
- Reporters: bpfix CLI (primary `-->` line and every snippet label), VerifierState (stop line from the captured log's source map), SourceComment (Python port of upstream `source.rs`), uniform random executable line (expected value), and any adapter added later, scored by the same rules.

## 4. Oracle variants

Every headline result is reported under three repair-site rules. A claim is made only if it holds under all three.

- **R0** lines changed by semantic hunks, in buggy line numbers; an insertion marks both neighbouring lines (the existing rule).
- **R1** R0 plus or minus one executable line.
- **R2** whole hunk span: every buggy line from the first to the last line of each semantic hunk.

## 5. Informative cases

A case is informative for the primary-location metric when a uniformly random executable line of `buggy.bpf.c` would hit the R0 repair site with probability below 0.25. Headline rates are given over all scored cases and over informative cases only.

## 6. Metrics and strata

- Primary location on a repair site, any label on a repair site, primary within 3 lines, per reporter.
- Wilson 95% intervals over distinct cases; exact McNemar between reporters on the same cases; paired orig to variant McNemar per transform.
- Strata: upstream obligation (upstream's own classifier) and case kind (`rs_` prefix: upstream's real-project seeds; otherwise canary).

## 7. Verifier-visible rewrites (added 26 Oct 2026, before any rewrite was generated)

Five source rewrites, each applied to **both** `buggy.bpf.c` and `fixed.bpf.c` of a case (`tools/gen_main75_rewrites.py`). The anchor is the statement on bpfix's primary line in the pin capture of `buggy`, which is the verifier's stop statement. A rewrite applies to a case only where its precondition holds. Otherwise the case is listed as not applicable, with the reason.

| ID | Rewrite | Precondition |
| --- | --- | --- |
| VPAD | 8 lines of verifier-visible padding (`{ volatile __u32 __adv_pad = 0; __adv_pad++; }`) inserted before the anchor statement | anchor line found once in each file; the previous code line ends a statement (`;`, `{` or `}`) |
| MACRO | the anchor statement wrapped as `ADV_STMT(<stmt>);` with a multi-line `#define ADV_STMT(...)` placed after the last `#include` | anchor is one complete statement on one line, ending in `;`, and is not a declaration, `return` or `break`/`continue` |
| INLINE | the nearest `if (COND)` above the anchor in the same function moved into `static __always_inline int __adv_guard(...) { return (COND); }`, called as `if (__adv_guard(args))` | every identifier in COND is a local or parameter declared on one line with a simple type, and COND has no assignment, call or `sizeof` |
| REORDER | the anchor statement swapped with the statement on the previous code line | both are single-line statements ending in `;`; neither contains a call, `return`, a label or a brace; they share no identifier |
| SPLIT | a one-line `if (A && B)` above the anchor rewritten as `if (A) if (B)`, or `if (A \|\| B) return X;` as `if (A) return X; if (B) return X;` | top-level `&&` or `\|\|` only; the `if` has no `else`; the `\|\|` form only with a `return` body |

**Validity (two-sided):** a rewritten pair is scored only if rewritten `buggy` REJECTS and rewritten `fixed` ACCEPTS on the pin. Otherwise it is excluded and listed with its verdicts. This tests empirically that the rewrite keeps what the verifier checks for that pair.

**Oracle:** recomputed from the rewritten pair (the R0, R1 and R2 rules applied to the rewritten `buggy` to rewritten `fixed` diff), not mapped by hand.

**Scoring:** for every reporter, paired McNemar of on-site hit (original pair vs rewritten pair, R0), and the share of pairs whose primary line moved, mapped through the diff from `buggy` to rewritten `buggy`. Positive control: `StaleLine` as in Section 6.

## Changes after the freeze

- **26 Oct 2026, after generating the rewrites, before compiling or scoring any of them. Anchor in `fixed` defined.** Section 7 defines the anchor on `buggy` only. The first generator also required the anchor line, unchanged, in `fixed` for every rewrite. That excludes the 27 cases where the fix edits the anchor line itself, which are mostly cases where bpfix's primary is on the repair site, so the rewritten set would have been biased towards misses. For MACRO, INLINE, REORDER and SPLIT, the anchor in `fixed` is now its counterpart in the `buggy` to `fixed` diff (equal blocks one to one; a replaced block maps to its replacement's first line; a deleted anchor has none). VPAD keeps the found-once rule its precondition states. Applicability (cases): VPAD 46, MACRO 32, INLINE 48, REORDER 0, SPLIT 3.
- **26 Oct 2026, before any pin result was scored. R2 clarified.** As first written, R2 ("every buggy line from the first to the last line of each semantic hunk") is identical to R0, because each difflib hunk is already a contiguous run of changed lines. R2 now uses the unified-diff hunk, as `git diff` groups it: changes within 3 lines of each other form one hunk (`difflib.SequenceMatcher.get_grouped_opcodes(3)`), and R2 covers every buggy line from the first to the last changed line of each hunk that contains a semantic change. Insertions mark both neighbours, as in R0.

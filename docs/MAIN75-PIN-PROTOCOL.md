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

## Changes after the freeze

None yet.

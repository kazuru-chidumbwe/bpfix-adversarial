# Metrics — injection-site agreement

SoftwareX / cite-pin terminology. Historical script and filename strings may still say “honesty”; the **construct** scored against markers is injection-site agreement.

## Primary

| Metric | Definition |
| --- | --- |
| **top1_line** | Primary reported location equals `oracle_loss_code` (first executable line of the injection span; **one-based** source lines as in the mutant `.c` file, before preprocessing) |
| **top1_span** | Primary reported location is any member of `oracle_loss_span` (multi-line wash). Lab SC/VS inset reports this separately from top1_line |
| **set_recall_message** | **CLI-path only.** Exact **decimal line number** of `oracle_loss_code` appears as a parsed source line in the rendered bpfix CLI diagnostic (default). With span opt-in: any decimal line in `oracle_loss_span`. CLI implementation: primary `--> path:LINE` plus snippet lines matching `^\s*(\d+)\s+\|`. Path match is **not** required; matching source text alone does **not** count. Not a harness-wide SC/VS score. |
| **distance_error** | `d = abs(predicted - oracle_loss_code)` (absolute source-line localization error) |
| **signed_offset** | `predicted - oracle_loss_code` (direction; positive means predicted is after the injection primary line) |
| Rename stability | Same injection-site agreement outcome after idiomatic renames (esp. null-check heuristics) |

Do **not** use the bare label “top-1” for both line equality and span membership.

### Missing predictions and aggregates

- Missing prediction → `distance_error` is **undefined** (`null` in JSON).
- Any mean / summary distance **excludes** undefined rows and reports a separate **missing-prediction count**.
- SoftwareX surfaces report **per-row** distances and **per-template** matrices (e.g. PB pads 0/8/32). Pad repeats are not independent semantic cases.
- Fractions such as 3/10 on the rejecting campaign are **row-weighted descriptive tallies**, not template-weighted estimates and not a single campaign-wide “accuracy.”

## Secondary

| Metric | Definition |
| --- | --- |
| Obligation confusion | Wrong `ProofObligation` family labeled |
| Tier dependence | Accuracy when only `SourceComment` vs when `VerifierState` is available |
| Localization–repair separation | Documented case where repair succeeds despite a wrong tip (existence / counterexample; not a rate) |

## Oracle

Each template case declares `oracle.loss_*` and `oracle.reject_*` (source and/or insn) at generation time. Scoring never uses the diagnostic’s output as ground truth.

**Independence (SoftwareX):** markers are assigned before diagnostics run and do not read bpfix or kernel logs to choose the injection site. **Tested reporter/log invariance** (`results/marker_isolation.*`): SoftwareX-stamp logs contain no `ORACLE_*` tokens; SourceComment primary lines are invariant under line-preserving marker neutralization; Ubuntu 6.8 lab bearing/neutral compile+load yields identical verdicts and normalized verifier logs. Debug (`-O2 -g`) object identity is **not** invariant: compiler-generated debug/source metadata retains differences in the authored source text; on the Ubuntu A/B campaign both `.BTF` and `.BTF.ext` section dumps differ (`llvm-objdump -s -j`; 16/16). DWARF was not compared. Scoring still reads markers via `oracle_sites` for ground truth only. SoftwareX still does **not** claim these markers equal a machine-verified verifier-state transition (semantic proof-loss). That stronger oracle is future work.

**Scoring rule (locked):** top1_line, top1_span, and distance_error are always computed against the construction-time **injection** site. When injection and reject/use markers diverge, do **not** score against the marked reject/use line.

### Span / line rules (reproducibility)

| Concept | Rule |
| --- | --- |
| Marker lines | Comment lines containing `ORACLE_LOSS_LINE` / `ORACLE_REJECT_LINE` (names kept for fixture compatibility; SoftwareX prose: injection / terminal-or-use span). `ORACLE_REJECT_LINE` is **author-assigned source** (expected use or terminal *source* site)—not the kernel’s terminal verifier instruction and not a compiler-emitted BPF insn index. |
| Line numbering | **One-based** lines in the mutant source file as stored (pre-preprocessor). `#` lines are preprocessor directives and are skipped when building the executable span; they can appear inside a marker span but do not count as executable. |
| First executable line | Determined on the **pre-preprocessor** mutant text: first non-blank, non-comment, non-`#`, non-pad line strictly between markers (`oracle.py`). |
| Effective injection span | Executable lines strictly between markers; skip blanks, `//` `/*` comments, `#` preprocessor, and distance pads (`__pad` / `distance pad`) |
| Empty span fallback | If `oracle_loss_span` is empty after filtering, `oracle_loss_code` is the last **executable** line *before* the LOSS marker (omitted-check seeds such as `NP-idiomatic-nocheck`); `top1_span` / `in_loss_span` then degrades to **top1_line** equality on that code. |
| top1_line target | Primary code line = first span line, else prior-executable empty-span fallback (`oracle_loss_code`); equality only on that line |
| top1_span | Any line in `oracle_loss_span` |
| set_recall_message | See Primary table (decimal line numbers in rendered diagnostic) |
| Missing BPF for a source line | SoftwareX distance uses **source-line** numbers from markers / log maps; PC distance is uninformative when pads compile away under `-O2` |
| Macros / continuations | Not specially expanded; scoring is source-text / line-table based as emitted |

Implemented in `bpfix_adversarial/oracle.py` (`oracle_sites`) and `bpfix_adversarial/score.py` (`score_honesty`).

### What each reporter consumes

| Reporter | Input | Notes |
| --- | --- | --- |
| SourceComment (SC port) | Mutant **source text** | Predicate port of upstream `looks_like_*`; reporter = first top-down match (not upstream log-comment + `latest_source_before`) |
| VerifierState (VS) | **Captured verifier log** only | Parses `; text @ path:line` maps already present in the log; does **not** load object BTF |
| Upstream bpfix CLI | Captured **log file** only (offline replay) | No mutant C; no object file; **set_recall_message** lives here |

Lab captures use clang **`-O2 -g -target bpf`** so the verifier log carries BTF-backed source maps for VS; scalar pads still DCE under `-O2`, which is why distance is source-line based.

## Log normalization contract (marker A/B)

Implemented by `tools/lab_marker_isolation_ab.py::normalize_log_body`. Used only to compare bearing vs neutral verifier logs for reporter/log invariance—not as a second scoring channel.

| Rule | Behavior |
| --- | --- |
| Dropped lines | `META …`; sole-token `ACCEPT`/`REJECT`/`COMPILE_FAIL`; `EXIT:…`; `connecting …` / `ssh ok…`; `verification time N usec`; `processed N insns (limit …) …` accounting trailer |
| Hex addresses | Every `0x[0-9a-fA-F]+` → `0xADDR` (ASLR / map bases) |
| Paths / ids | `/tmp/bpfix-iso-…` → `/tmp/bpfix-iso-STAMP`; `bpfix_iso_…` → `bpfix_iso_ID`; `markeriso-(bearing\|neutral)` → `markeriso-VARIANT` |
| Whitespace | Trailing whitespace stripped per line (`rstrip`); interior whitespace otherwise preserved; no blank-line collapse |
| Instruction numbers | Retained (not rewritten) |
| Source paths in maps | Retained except the tmp/stamp substitutions above |
| Ordering | Preserved; if `BEGIN PROG LOAD LOG` is present, only the suffix from that marker is kept |
| Timestamps / truncation | No dedicated timestamp strip beyond the dropped timing/accounting lines; truncation notices are not specially rewritten |
| Score after normalize | SHA-256 of the normalized body must match for A/B pass |

## Reported-site modes (methodological parameter)

| Mode | SoftwareX name | What counts as “reported” | Used by |
| --- | --- | --- | --- |
| Headline line | **top1_line** | rustc-style `--> file:LINE` / stop-site map equals `oracle_loss_code` | Default `score_honesty`; CLI primary when compared to primary line |
| Headline span | **top1_span** | Stop-site map ∈ injection span | Lab SC/VS inset (multi-line wash) |
| Full message | **set_recall_message** | Decimal injection line (or span lines) appears among parsed source lines in the rendered CLI diagnostic | `bpfix_loss_mentioned` in `rq1_bpfix_cli.*` (CLI path only) |

The harness records both line and span thresholds. PacketBounds can be a set-recall hit and a top1_line miss on the same log: that is a scoring-mode feature for choosing a threshold, not an inset inconsistency.

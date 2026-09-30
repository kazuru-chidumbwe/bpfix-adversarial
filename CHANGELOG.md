# Changelog

## v1.0.2 - 2026-09-30

Minor-revision cite pin for the software paper (SOFTX-D-26-01022).

### Accuracy notes and lab-helper host keys

- README: the tree builds rejecting mutants plus accepting controls, not only
  failing programs; `helper_anchored_stable` is labelled true by construction
  (the helper line is fixed and never renamed).
- `results/oracle_controls.md`: `verdict = construction` is stated to confirm
  the committed templates, not to predict verdicts independently, because the
  ScalarRange template was retuned once after an earlier version was accepted.
- README and `mutants/README.md` state that `NP-idiomatic-nocheck`, the only
  rejecting NullablePointer row, has no committed capture-time copy, and that
  the ScalarRange reject comment's "stack load" wording predates the `.rodata`
  finding and is kept to preserve the capture hashes.
- Lab SSH helpers verify host keys (`~/.ssh/known_hosts`, plus
  `LAB_TEST_KNOWN_HOSTS`) and refuse unknown hosts instead of accepting any key.

### Offline, Windows and provenance fixes

No scored value changes: every `top1_line`, `top1_span`, distance, baseline,
control and CLI field is unchanged.

- The offline suite and CI failed on a stdlib-only install:
  `tools/check_results_fresh.py` runs `tools/lab_marker_isolation_ab.py --rescore`,
  which imported paramiko at module level. paramiko is now imported only where an
  SSH connection is opened, so `make smoke`, the Docker image and CI pass without
  the `lab` extra. A missing paramiko fails with a message naming the `lab` extra,
  and `tests/test_offline_imports_are_stdlib_only.py` fails if any module under
  `tools/` or `bpfix_adversarial/` imports an optional dependency at module scope.
- The Windows CI job failed: emitters wrote `results/*.md` in text mode, which is
  CRLF on Windows, and the markdown freshness check compares bytes. Every writer
  now pins `newline="\n"`, and the markdown comparison is newline-normalised.
- The Docker image did not copy `figures/`, which the freshness check has required
  since `v1.0.1`, so `docker run` failed its own `make smoke`. `make insets` also
  skipped three emitters the freshness check covers (`score_np_pair.py`,
  `emit_rq1_bpfix_cli.py`, the marker A/B rescore); it now runs the same set.
- A documentation pass had rewritten comment text (em dash to comma) in all 16
  mutants, including the ORACLE marker comments, so the tree no longer held the
  source files the committed logs were captured from. `mutants/` and the generator
  strings are restored to the captured bytes, and the new
  `tests/test_capture_provenance.py` checks the capture manifest (15/16; the
  hand-written `NP-idiomatic-nocheck` seed's capture-time copy was never
  committed) and the marker A/B hashes (16/16).
- PointerProvenance disclosure: the verifier rejects the pointer XOR itself,
  inside the injection span, and never reaches the marked dereference; upstream
  bpfix labels these captures E005, which its classifier maps to ScalarRange.
  `rq1_bpfix_cli.*` now shows each row's error ID and upstream obligation, and the
  `sc_vs_honesty.md`, `rq1_bpfix_cli.md` and `baseline_battery.md` text says the PP
  rows carry no stop-site distance evidence.
- The negative control is selected by construction (templates built to be
  well-formed) instead of by the observed ACCEPT, so it can now fail, and
  `oracle_controls.*` adds `verdict_matches_construction` over all 16 templates.
- `marker_isolation_lab.json` stated a pass criterion (`-g` ELF and
  `llvm-objdump -d` identity) that the code does not apply and that the data
  fail in 16/16 pairs. Both the capture path and `--rescore` now write one note
  that matches `pair_match`.
- `score_sc_vs_honesty.py` checks each rejecting row's construction reason
  before it emits the "construction-determined" takeaway, and
  `emit_depth21_selection.py` checks its per-family evidence text against
  `sc_vs_honesty.json`.
- `tier_disagreement.json` no longer publishes `tiers_agree` against an asserted
  VerifierState line.
- The port-fidelity behaviour test compares against outputs recorded from the
  vendored Rust predicates instead of a Python restatement.
- `check_version_sync.py` now also checks C1 in `CODE_METADATA.md`, which
  `docs/TAGS.md` said it did, and that C2 names the `v1.0.2` tree and pins no
  commit hash.
- `analyze.py` skipped preprocessor lines unless they contained `if`, which also
  matched inside `endif`; only `#if`, `#ifdef`, `#ifndef` and `#elif` are now kept.
- `heuristics.py` no longer claims the predicates match upstream
  character-for-character; the docstring states what the port-fidelity test
  checks.
- The lab upload tarball no longer includes `lab/.env`, and it is deleted after
  upload; sudo password files are set to 0600 before the password is written.
- Documentation: C2 names only the tag, lab environment variables are documented
  in `docs/LAB-PIN.md`, `fixtures/upstream/NOTICE` separates copied from generated
  files, and leftover find-and-replace damage is fixed.

### Oracle and marker hardening

No scored value, committed result or figure changes (`tools/check_results_fresh.py`
passes unchanged).

- `oracle.py`: executable-line detection tracks `/* … */` state across lines. A
  leading `*` was always treated as a comment, so a pointer store such as
  `*p = 0;` was dropped from the injection span, and the interior of a
  multi-line comment was counted as code. No committed mutant hits either case.
- `marker_isolation.strip_oracle_markers`: replaces the ORACLE comment itself,
  not the whole line, so code sharing a line with a marker survives and a
  multi-line marker comment leaves no dangling `*/`. Output for the committed
  mutants is byte-identical; a test pins it to the 16 neutral hashes in
  `marker_isolation_lab.json`.
- `emit_rq1_bpfix_cli.py`: the `-->` arrow parser also accepts `path:LINE:COL`;
  previously a column would have been read as the line.
- `emit_figures.py`: an undefined distance is drawn N/A, not 0.
- `check_results_fresh.py`: fails on a `results/*.md` with no registered JSON
  or a `figures/*.svg` no emitter produces.
- `docs/METRICS.md`: dropped the `set_recall_message` "span opt-in", which was
  never implemented.
- `.gitattributes`: LF for `fixtures/**/*.compile` and the CLI replay `*.err`.

### Pre-submission review fixes and release hygiene

An external pre-submission review of the tree, folded in before the revision was
uploaded so that one tree is published.

- Two committed insets scored against oracles that disagreed with the repository's
  own `oracle_sites`. The synthetic fixture logs pointed their `@` paths at the
  committed mutants while citing line numbers that do not exist there; they now
  carry their own fixture coordinates and say so, and `score_np_pair.py` and
  `emit_tier_table.py` read the oracle from each fixture's `ORACLE_*` annotation
  instead of hardcoding it.
- `tier_disagreement` published a VerifierState column set equal to the oracle
  and then compared against it, so it could never disagree. The VS line is now
  labelled asserted, is not scored, and the inset carries a disclaimer.
- `four_obligation_matrix` headed its marker-comment lines `loss`/`reject`. The
  marker and code columns are now separate and named.
- `lab_marker_isolation_ab.py --rescore` recomputed object hashes it cannot
  recover from log text, rewriting the inset from 1.0 to 0.0 and failing the
  suite. Capture-time metadata is carried forward, so rescoring is idempotent,
  and the inset is now covered by `check_results_fresh.py` rather than skipped.
- `check_results_fresh.py` now compares `results/*.md` as well as the JSON. The
  markdown tables are what the paper reproduces and were previously unguarded.
- The upstream CLI version is recorded by the replay script and read by the
  emitter instead of being asserted as a literal, and the pad-indexed replay's
  exclusion of the omitted-check seed is recorded with a reason.
- The random baseline reports its analytic expectation (0.645, SD 0.768) beside
  the single drawn tally, whose standard deviation exceeds its mean.
- `check_version_sync.py` now covers CITATION.cff and codemeta.json, version and
  release date, which is what `docs/TAGS.md` already claimed it did.
- New test: every `path:LINE` in the stamped captures still names the same source
  text in the committed mutants (76/76). Suite is 44 tests.
- `fixtures/upstream/NOTICE` carries the upstream MIT notice, pin and inventory
  for the vendored material.

No scored result changed: `sc_vs_honesty`, `rq1_lab_distance`, `rename_honesty`,
`distance_sweep`, `upstream_obligations`, `depth21_selection` and
`pad_rename_invariance` are unchanged.

### Committed takeaways, Windows line endings and CI

Findings from a pre-submission review, folded in before the revision was
uploaded. No reported number changes.

- `results/sc_vs_honesty.md` and `results/rq1_bpfix_cli.md` still described the
  three PacketBounds rows as an "informative SC sample" and the SC port as
  "PB honest". Both contradicted the manuscript's Limitation 1, which states that
  all ten rejecting-row SourceComment outcomes are construction-determined, the
  PacketBounds rows included. The emitter strings and the regenerated tables now
  say so.
- `.gitattributes` had no LF rule for `*.svg` (nor for `Makefile`, `Dockerfile`,
  `Vagrantfile`, `*.txt`, `*.cff`, `LICENSE`). On a default Windows clone
  (`core.autocrlf=true`) the committed figures were rewritten with CRLF and
  `tools/check_results_fresh.py` reported them stale, so the suite ran 42/43,
  the paper's "43/43 on Windows" claim had never been exercised by CI, which
  runs `ubuntu-latest` only. Rules added, tree renormalized, and the CI matrix
  extended with a `windows-latest` entry that forces `core.autocrlf=true` before
  checkout, so both platforms run the same hygiene steps.
- Review follow-up on the above: `tools/score_sc_vs_honesty.py` derives the takeaway counts from the scored rows
  (`SC_CONSTRUCTION_REASONS`) instead of hard-coding them (at the time
  `results/*.md` was not yet covered by `tools/check_results_fresh.py`).
  Regenerated output is unchanged.

### Manuscript and release reconciliation

Reconciles the released tree with the revised manuscript and the response letter,
which name `v1.0.2`.

Corrections:
- Removed the one-shot localization–repair demonstration (repair tool, legacy
  summary emitter, committed prompt/response dumps, three repaired mutants and
  their one capture, and the optional cloud-API install extra). Its prompt
  contained the fix and the injection marker, so it did not isolate the effect it
  claimed.
- main75 obligation coverage now comes from upstream's own classification (error ID
  in each case's `diagnostic.txt` → `ProofObligation` declared in upstream
  `classifier.rs`, vendored): the four templated families cover 47/75. The previous
  labels were a case-name keyword heuristic, now named `keyword_label` (was
  `upstream_proof_obligation`); they agree with upstream on 16/75.
- `four_obligation_matrix.json`: `rejected_or_error` used a substring scan that
  matched `r0` in every log; now the same verdict check as `sc_vs_honesty.json`
  (7 of 19 rows were wrong).
- Results wording aligned with the scoring contract: the rename matrix is an
  exhaustive 4x8 enumeration, not a rate (`break_rate` removed); span-membership
  tallies labelled `top1_span`; the synthetic distance sweep is a unit check, not an
  accuracy; research-question labels removed from result titles.
- The `-g` object difference is no longer attributed to marker text in
  `docs/METRICS.md`, `tools/lab_marker_isolation_ab.py` or the
  `marker_isolation_lab.json` note (note corrected by hand; not re-captured).
- SC/VS figure: PointerProvenance SourceComment drawn as N/A, not a zero bar.
- Figure emitter writes LF on every platform (the Windows suite previously failed
  the figure-freshness test).

Additions:
- `results/pad_rename_invariance.*`: verdict, processed-instruction count, reject
  message and verifier-listed instruction sequence are identical across pads and
  within each rename pair.
- Tests: generator reproduction of all 15 generated mutants, upstream classifier
  pin, pad/rename invariance (43 tests).
- `tools/measure_coverage.py` (`pip install -e ".[dev]"`): single-command
  statement and branch coverage.
- Zenodo version DOI recorded in `CITATION.cff`, `codemeta.json`,
  `CODE_METADATA.md` and `docs/ZENODO.md`.

Removed: superseded `tools/emit_obligation_matrix.py`; unreferenced
`lab/batch_capture_all.sh` and `lab/Makefile`; the `LAB_TEST_USER` default in the
lab SSH helpers (the variable is now required).

Kept for provenance: `mutants/NullablePointer/NP-idiomatic-nocheck.c` is kept
byte-identical to its first public version. The
2026-08-07 env pin under `results/env_pins/` remains a historical host record;
tip wording there no longer names the removed repair path.

Unchanged: every template tally the paper reports (SC/VS rejecting inset, lab
distance, baselines 3/10 · 1/10 · 10/10, CLI replay, marker isolation 16/16).

### Scoring contract and offline refinements

- CLI scoring: `top1_line` = exact `oracle_loss_code`; `top1_span` separate; `set_recall_message` = decimal loss line in diagnostic text (fixes span-as-top1 bug)
- Empty injection span: `oracle_loss_code` = last executable line *before* LOSS marker (`NP-idiomatic-nocheck` → lookup/assignment line)
- `.gitattributes`: LF for `*.rs` / vendored Rust
- CLI: UTF-8 stdout/stderr reconfigure on Windows
- Regenerated offline results: `rq1_bpfix_cli.*`, `sc_vs_honesty.*`, `baseline_battery.*`, `oracle_controls.*`, `four_obligation_matrix.*`, `rq1_lab_distance.*`, figures
- `emit_baseline_battery.py` / `docs/METRICS.md`: do not zero `distance_error` on a span-only hit (PP terminal `d=1`; PP-pad32 random `d=1`; top1_span rates unchanged 3/10, 1/10, 10/10)
- `emit_figures.py`: SVG titles carry no embedded “Fig. N” prefix (manuscript captions are authoritative)
- `sc_vs_honesty.md` takeaways: NP-nocheck SC is a construction-determined **top1_line** hit, not a miss; informative SC sample is 3 PacketBounds rows
- Named regression test `test_np_idiomatic_nocheck_oracle_loss_code_is_executable`
- C2 remains GitHub `tree/v1.0.2`; Zenodo DOI archival in C7 only. Do **not** label Zenodo `10.5281/zenodo.21860453` as this version (that DOI is the **v1.0.1** archive)


## v1.0.1 - 2026-08-09

Major/minor revision patch for the software paper (cite pin for resubmission).

- Optional dependencies: core install is stdlib-only; extras `lab` / optional API / `all`
- `tools/emit_figures.py` + committed the paper's Figs 2–4 SVGs (wired into `make insets` / freshness CI)
- Port-fidelity test against vendored `source.rs` @ `81d97e4` (SHA-256 pinned)
- SC PointerProvenance scored as N/A (`sc_applicable=false`), not 0/3
- Robustness: libbpf-anchored `lab_rejected`, named `libbpf:` regex, `oracle_loss_code` API
- Docs: WSL environment, UPSTREAM labelling rubric, empty-span fallback, concept DOI in CITATION.cff

## v1.0.0 - 2026-08-07

First public release (initial cite pin for the software paper).

Pinned-kernel template instrument for controlled stress testing of eBPF diagnostic
localization (injection-site agreement under pad/rename). Includes scoring contract
(top1_line / top1_span / set_recall_message), absolute distance, offline bpfix CLI
replay, reporter/log invariance evidence, results-freshness CI, and committed insets.

Prior private review iterations of the paper used `v1.1.x` tags; those tags are retired
in favor of this single public root. Reviewers were informed of the retag.

# Changelog

## v1.1.0 (unreleased)

Scores diagnostics against developers' fixes on programs this project did not write, adds external reporters, a second oracle and a second configuration. Every v1.0.2 template result is unchanged.

### Corpora and capture
- main75: all 75 cases of upstream bpfix's main split vendored at the pinned commit (`fixtures/upstream/`), captured buggy and fixed on the laboratory pin with bpfix replay (`lab/run_main75_pin.sh`), under rules committed before capture (`docs/MAIN75-PIN-PROTOCOL.md`).
- Verifier-visible rewrites of main75 (VPAD, VPADC, MACRO, INLINE, SPLIT, REORDER) of both programs, scored only when the rewritten buggy program REJECTS and the rewritten fixed one ACCEPTS (`tools/gen_main75_rewrites.py`, `lab/run_n3_pin.sh`); padding and renaming of the buggy program (`tools/gen_upstream_metamorphic.py`).
- Developer-fixed corpus: GitHub commit search, file and message screening, build at the parent and fix commits, per-program loading (`tools/wildload.c`, with a libbpf 0.8.3 build for legacy `maps` sections) and a decision rule, under `docs/WILD-CORPUS-PROTOCOL.md`; included cases stored with sources, objects and logs (`fixtures/wild/`); host setup in `docs/LAB-RUN-WILD.md`.
- Campaign v2 template sets that reach bpfix's output: rejecting rename pairs, padding that survives `-O2`, and a provenance template that rejects outside the injection span (`campaigns/v2/`).

### Reporters and oracles
- Reporter registry (`bpfix_adversarial/reporters.py`) with a generic replay driver (`tools/replay_reporter.py`) and adapters for Pretty Verifier and PREVAIL; `docs/ADDING-A-REPORTER.md`.
- Repair-site oracle from each case's `buggy` to `fixed` diff under three rules (R0, R1, R2), per file for multi-file fixes (`bpfix_adversarial/repair_site.py`).
- Verifier-state oracle read from the log alone (`bpfix_adversarial/state_oracle.py`, `docs/STATE-ORACLE.md`).
- Random-line baseline as an expected hit count, overall and per case kind and obligation; StaleLine control for rewrite tests; Wilson intervals and exact McNemar tests.
- bpfix output parser: a location inside the verifier log (`--> <verifier-log>:N`, printed on kernels before 6.9) is no source line.

### Results and checks
- `results/main75_pin.*`, `main75_rewrites.*`, `wild.*`, `state_oracle.*`, `pv_lookup.*`; second configuration `main75_pin.testbed-b.*`, `main75_rewrites.testbed-b.*` and `cross_config.*` (`tools/compare_configs.py`), with `lab/xload_attribution.sh` and its logs.
- `make natural` rescores every natural corpus from the committed captures; CI runs it and fails if a committed result changes.
- The freshness check stops on unreadable tracked files and never scores a missing reporter output as a miss.
- `tools/check_zenodo_archive.py` compares a Zenodo zip with a git tag.
- Docker image verifies committed results instead of regenerating them.

## v1.0.2 - 2026-09-30

### Accuracy notes and lab-helper host keys
- README: the tree builds rejecting mutants and accepting controls; `helper_anchored_stable` is true by construction.
- `results/oracle_controls.md`: `verdict = construction` confirms the committed templates and is not an independent prediction.
- README and `mutants/README.md` document that `NP-idiomatic-nocheck` has no committed capture-time copy.
- Lab SSH helpers verify host keys and refuse unknown hosts.

### Offline, Windows and provenance
No scored value changes.
- Optional dependencies are imported only where used, so the offline suite, Docker image and CI run on a standard-library install; a test enforces it.
- Emitters write LF on every platform; the Markdown freshness comparison is newline-normalised.
- The Docker image includes `figures/`; `make insets` runs the same emitters as the freshness check.
- `mutants/` restored to the bytes the committed logs were captured from; `tests/test_capture_provenance.py` checks the capture manifest and the marker A/B hashes.
- `rq1_bpfix_cli.*` shows each row's error ID and upstream obligation; PointerProvenance rows are marked as carrying no stop-site distance evidence.
- The negative control is selected by construction; `oracle_controls.*` adds `verdict_matches_construction`.
- `marker_isolation_lab.json`, `tier_disagreement.json`, `score_sc_vs_honesty.py` and `emit_depth21_selection.py` state only what their code checks.
- The port-fidelity test compares against outputs recorded from the vendored Rust predicates.
- `check_version_sync.py` also checks C1 and C2.
- `analyze.py` keeps only `#if`, `#ifdef`, `#ifndef` and `#elif` preprocessor lines.
- Lab upload excludes `lab/.env`; password files are 0600 before writing.

### Oracle and marker hardening
No scored value, committed result or figure changes.
- `oracle.py` tracks `/* … */` state across lines when finding executable lines.
- `marker_isolation.strip_oracle_markers` replaces the marker comment only.
- `emit_rq1_bpfix_cli.py` accepts `path:LINE:COL` arrows.
- `emit_figures.py` draws an undefined distance as N/A.
- `check_results_fresh.py` fails on unregistered results or figures.
- `.gitattributes`: LF for `fixtures/**/*.compile` and replay `*.err`.

### Release checks
- Synthetic fixture logs carry their own coordinates; `score_np_pair.py` and `emit_tier_table.py` read the oracle from each fixture's annotation.
- `tier_disagreement` labels the VerifierState line as asserted and does not score it.
- `four_obligation_matrix` separates marker and code columns.
- `lab_marker_isolation_ab.py --rescore` carries capture-time metadata forward and is idempotent.
- `check_results_fresh.py` compares `results/*.md` as well as JSON.
- The CLI version is recorded by the replay script; the random baseline reports its analytic expectation.
- `check_version_sync.py` covers `CITATION.cff` and `codemeta.json`.
- New test: every `path:LINE` in the stamped captures names the same source text in the committed mutants.
- `fixtures/upstream/NOTICE` carries the upstream MIT notice, pin and inventory.
- `score_sc_vs_honesty.py` derives its takeaway counts from the scored rows.
- `.gitattributes` LF rules for SVG and build files; CI adds a Windows job with `core.autocrlf=true`.

### Release reconciliation
- Removed the one-shot localization and repair demonstration and its optional dependency.
- main75 obligation coverage from upstream's own classification (error ID to `ProofObligation`, vendored `classifier.rs`).
- `four_obligation_matrix.json` uses the same verdict check as `sc_vs_honesty.json`.
- Result wording follows the scoring contract (`top1_span`, enumeration rather than rate for the rename matrix).
- SC/VS figure draws PointerProvenance SourceComment as N/A.
- Added `results/pad_rename_invariance.*`, generator-reproduction and classifier-pin tests, `tools/measure_coverage.py`, and the Zenodo version DOI in the metadata files.
- Removed `tools/emit_obligation_matrix.py`, `lab/batch_capture_all.sh`, `lab/Makefile` and the `LAB_TEST_USER` default.

### Scoring contract and offline refinements
- CLI scoring: `top1_line` is the exact `oracle_loss_code`, `top1_span` is separate, `set_recall_message` is the loss line in the diagnostic text.
- Empty injection span: `oracle_loss_code` is the last executable line before the loss marker.
- `emit_baseline_battery.py` keeps `distance_error` on a span-only hit.
- CLI: UTF-8 output on Windows.

## v1.0.1 - 2026-08-09

- Optional dependencies; the core install is standard-library only.
- `tools/emit_figures.py` and the committed figure SVGs, in `make insets` and the freshness check.
- Port-fidelity test against vendored `source.rs` at `81d97e4` (SHA-256 pinned).
- SourceComment PointerProvenance scored as N/A.
- libbpf-anchored `lab_rejected`; `oracle_loss_code` API.

## v1.0.0 - 2026-08-07

First public release: pinned-kernel template harness for stress-testing eBPF diagnostic localization (injection-site agreement under padding and renaming), with the scoring contract (top1_line, top1_span, set_recall_message), offline bpfix CLI replay, results-freshness CI and committed results.

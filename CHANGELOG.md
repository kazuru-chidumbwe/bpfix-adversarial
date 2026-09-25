# Changelog

## v1.0.2 - 2026-09-25

Minor-revision cite pin for the software paper (SOFTX-D-26-01022).

### Tag history

`v1.0.2` was first cut on 2026-09-03 and has been re-cut during revision so
that one tree matches the manuscript and the response letter. Every target it
has had, oldest first:

| Date | Commit | Reason |
| --- | --- | --- |
| 2026-09-03 | `46a709e` | first cut |
| 2026-09-14 | `899f112` | fold interim `v1.0.3` refinements; `v1.0.3` label retired |
| 2026-09-19 | `bbfebe6` | reconcile with revised manuscript and response letter |
| 2026-09-20 | `653dde7` | pre-submission review follow-ups |
| 2026-09-21 | `95d4184` | inset oracle fixes, wider drift guard |
| 2026-09-21 | `f04c923` | release hygiene and documentation pass |
| 2026-09-25 | this tree | final re-cut, below |

A clone made before the final re-cut still has an older local tag. Refresh it
with `git fetch --tags --force` (a plain `git pull` leaves an existing local tag
in place). The GitHub release notes give the commit SHA of the final tag.

### Final re-cut (2026-09-25)

No scored value changes: every `top1_line`, `top1_span`, distance, baseline,
control and CLI field is identical to `f04c923`.

- The offline suite and CI failed on a stdlib-only install from `f04c923`:
  `tools/check_results_fresh.py` runs `tools/lab_marker_isolation_ab.py --rescore`,
  which imported paramiko at module level. paramiko is now imported only where an
  SSH connection is opened, so `make smoke`, the Docker image and CI pass without
  the `lab` extra.
- The Windows CI job failed from `95d4184`: emitters wrote `results/*.md` in text
  mode, which is CRLF on Windows, and the markdown freshness check compares bytes.
  Every writer now pins `newline="\n"`.
- The Docker image did not copy `figures/`, which the freshness check has required
  since `v1.0.1`, so `docker run` failed its own `make smoke`. `make insets` also
  skipped three emitters the freshness check covers (`score_np_pair.py`,
  `emit_rq1_bpfix_cli.py`, the marker A/B rescore); it now runs the same set.
- `f04c923` had rewritten comment text (em dash to comma) in all 16 mutants,
  including the ORACLE marker comments. The tree then held none of the source
  files the committed logs were captured from. `mutants/` and the generator
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
  `docs/TAGS.md` said it did.
- The lab upload tarball no longer includes `lab/.env`, and it is deleted after
  upload; sudo password files are set to 0600 before the password is written.
- Documentation: tag history restored (README, `docs/TAGS.md`, this file),
  `docs/ZENODO.md` states which tree the record holds, C2 no longer names a commit
  other than the tag, lab environment variables documented in
  `docs/LAB-PIN.md`, `fixtures/upstream/NOTICE` separates copied from generated
  files, and leftover find-and-replace damage fixed.

### Pre-submission review fixes and release hygiene (re-cuts of 2026-09-21)

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

### Committed takeaways, Windows line endings and CI (re-cut of 2026-09-20)

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
- Review follow-ups on the above: `docs/TAGS.md` now repeats the
  `git fetch --tags --force` reminder, and
  `tools/score_sc_vs_honesty.py` derives the takeaway counts from the scored rows
  (`SC_CONSTRUCTION_REASONS`) instead of hard-coding them (at the time
  `results/*.md` was not yet covered by `tools/check_results_fresh.py`).
  Regenerated output is unchanged.

### Manuscript and release reconciliation (re-cut of 2026-09-19)

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
byte-identical to its first public version (`f04c923` changed it; the final
re-cut restores it). The
2026-08-07 env pin under `results/env_pins/` remains a historical host record;
tip wording there no longer names the removed repair path.

Unchanged: every template tally the paper reports (SC/VS rejecting inset, lab
distance, baselines 3/10 · 1/10 · 10/10, CLI replay, marker isolation 16/16).

### Scoring contract and offline refinements (2026-09-03 release and 2026-09-14 re-cut)

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

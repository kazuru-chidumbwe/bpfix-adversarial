# Changelog

## Unreleased (`master` after `v1.0.2`)

Cite `v1.0.2`.

- Dropped IDE-named attribution guard files from the tip tree
  from the repository.
- Softened tip wording that named a removed one-shot repair demonstration and its
  optional API extra (`CHANGELOG` history bullets below; `results/env_pins/` host
  note). `NP-idiomatic-nocheck.c` is left byte-identical so committed `src_sha256`
  pins stay valid.

## v1.0.2 - 2026-09-21

the paper's minor-revision cite pin (SOFTX-D-26-01022).

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
- Review follow-ups on the above: `docs/TAGS.md` now repeats the
  the tag-citation note, and
  `tools/score_sc_vs_honesty.py` derives the takeaway counts from the scored rows
  (`SC_CONSTRUCTION_REASONS`) instead of hard-coding them, since `results/*.md` is
  not covered by `tools/check_results_fresh.py`. Regenerated output is unchanged.

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

Kept for provenance: `mutants/NullablePointer/NP-idiomatic-nocheck.c` stays
byte-identical (its `src_sha256` is recorded with committed results). The
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

the paper's Major/Minor revision patch (cite pin for resubmission).

- Optional dependencies: core install is stdlib-only; extras `lab` / optional API / `all`
- `tools/emit_figures.py` + committed the paper's Figs 2–4 SVGs (wired into `make insets` / freshness CI)
- Port-fidelity test against vendored `source.rs` @ `81d97e4` (SHA-256 pinned)
- SC PointerProvenance scored as N/A (`sc_applicable=false`), not 0/3
- Robustness: libbpf-anchored `lab_rejected`, named `libbpf:` regex, `oracle_loss_code` API
- Docs: WSL environment, UPSTREAM labelling rubric, empty-span fallback, concept DOI in CITATION.cff

## v1.0.0 - 2026-08-07

First public release (initial the paper's cite pin).

Pinned-kernel template instrument for controlled stress testing of eBPF diagnostic
localization (injection-site agreement under pad/rename). Includes scoring contract
(top1_line / top1_span / set_recall_message), absolute distance, offline bpfix CLI
replay, reporter/log invariance evidence, results-freshness CI, and committed insets.

Prior private the paper's review iterations used `v1.1.x` tags; those tags are retired
in favor of this single public root. Reviewers were informed of the retag.

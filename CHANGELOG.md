# Changelog

## Unreleased (`master` after `v1.0.2`)

Cite `v1.0.2`.

## v1.0.2 — 2026-09-03 (tag re-cut 2026-09-14 and 2026-09-19)

SoftwareX minor-revision cite pin (SOFTX-D-26-01022).

### 2026-09-19 re-cut (previous commit `899f112`)

The tag was re-cut a second time so the cited tree matches the revised manuscript
and the minor-revision response letter, which name `v1.0.2`. If you cloned before
19 Sep 2026, refresh with `git fetch --tags --force` (a plain `git pull` leaves an
existing local tag in place).

Corrections:
- Removed the localization–repair demonstration (`tools/rq4_llm_repair.py`, its
  legacy summary emitter, `results/rq4_ollama/`, `results/honesty_utility_rq4.*`,
  the three repaired mutants and their one capture, the `openai` extra). Its prompt
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
`lab/batch_capture_all.sh` and `lab/Makefile`.

Unchanged: every template tally the paper reports (SC/VS rejecting inset, lab
distance, baselines 3/10 · 1/10 · 10/10, CLI replay, marker isolation 16/16).

- CLI RQ1 scoring: `top1_line` = exact `oracle_loss_code`; `top1_span` separate; `set_recall_message` = decimal loss line in diagnostic text (fixes span-as-top1 bug)
- Empty injection span: `oracle_loss_code` = last executable line *before* LOSS marker (`NP-idiomatic-nocheck` → lookup/assignment line)
- `.gitattributes`: LF for `*.rs` / vendored Rust
- CLI: UTF-8 stdout/stderr reconfigure on Windows
- Regenerated offline results: `rq1_bpfix_cli.*`, `sc_vs_honesty.*`, `baseline_battery.*`, `oracle_controls.*`, `four_obligation_matrix.*`, `rq1_lab_distance.*`, figures
- `emit_baseline_battery.py` / `docs/METRICS.md`: do not zero `distance_error` on a span-only hit (PP terminal `d=1`; PP-pad32 random `d=1`; top1_span rates unchanged 3/10, 1/10, 10/10)
- `emit_figures.py`: SVG titles carry no embedded “Fig. N —” (manuscript captions are authoritative)
- `sc_vs_honesty.md` takeaways: NP-nocheck SC is a construction-determined **top1_line** hit, not a miss; informative SC sample is 3 PacketBounds rows
- Named regression test `test_np_idiomatic_nocheck_oracle_loss_code_is_executable`
- C2 remains GitHub `tree/v1.0.2`; Zenodo DOI archival in C7 only. Do **not** label Zenodo `10.5281/zenodo.21860453` as this version (that DOI is the **v1.0.1** archive)

> **2026-09-14 note.** The `v1.0.2` tag was re-cut to fold in the offline-only refinements listed above (no-zeroing rule, regression test, figure-title cleanup, takeaway wording) so the cited GitHub tree matches the minor-revision response letter and the submitted manuscript. Headline localization outcomes are unchanged; the interim `v1.0.3` label was retired in favour of the single cited pin.

## v1.0.1 — 2026-08-09

SoftwareX Major/Minor revision patch (cite pin for resubmission).

- Optional dependencies: core install is stdlib-only; extras `lab` / `openai` / `all`
- `tools/emit_figures.py` + committed SoftwareX Figs 2–4 SVGs (wired into `make insets` / freshness CI)
- Port-fidelity test against vendored `source.rs` @ `81d97e4` (SHA-256 pinned)
- SC PointerProvenance scored as N/A (`sc_applicable=false`), not 0/3
- Robustness: libbpf-anchored `lab_rejected`, named `libbpf:` regex, `oracle_loss_code` API
- Docs: WSL environment, UPSTREAM labelling rubric, empty-span fallback, concept DOI in CITATION.cff

## v1.0.0 — 2026-08-07

First public release (initial SoftwareX cite pin).

Pinned-kernel template instrument for controlled stress testing of eBPF diagnostic
localization (injection-site agreement under pad/rename). Includes scoring contract
(top1_line / top1_span / set_recall_message), absolute distance, offline bpfix CLI
replay, reporter/log invariance evidence, results-freshness CI, and committed insets.

Prior private SoftwareX review iterations used `v1.1.x` tags; those tags are retired
in favor of this single public root. Reviewers were informed of the retag.

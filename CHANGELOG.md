# Changelog

## v1.0.2 — 2026-09-03

SoftwareX minor-revision cite pin (SOFTX-D-26-01022).

- CLI RQ1 scoring: `top1_line` = exact `oracle_loss_code`; `top1_span` separate; `set_recall_message` = decimal loss line in diagnostic text (fixes span-as-top1 bug)
- Empty injection span: `oracle_loss_code` = last executable line *before* LOSS marker (`NP-idiomatic-nocheck` → lookup/assignment line)
- `.gitattributes`: LF for `*.rs` / vendored Rust
- CLI: UTF-8 stdout/stderr reconfigure on Windows
- Regenerated offline results: `rq1_bpfix_cli.*`, `sc_vs_honesty.*`, `baseline_battery.*`, `oracle_controls.*`, `four_obligation_matrix.*`, `rq1_lab_distance.*`, figures
- C2 remains GitHub `tree/v1.0.2`; Zenodo DOI archival in C7 only

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

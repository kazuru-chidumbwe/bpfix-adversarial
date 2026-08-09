# Changelog

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

# python3 where it exists (Debian and Ubuntu ship no `python`), else python; override with make PYTHON=...
PYTHON ?= $(shell command -v python3 2>/dev/null || echo python)

.PHONY: help smoke test rename-demo insets natural figures version v2-mutants

help:
	@echo "Targets: smoke | test | rename-demo | insets | natural | figures | version | v2-mutants"

version:
	$(PYTHON) -c "import bpfix_adversarial as m; print(m.__version__)"

test:
	$(PYTHON) -m unittest discover -s tests -q

rename-demo:
	$(PYTHON) -m bpfix_adversarial rename-demo --breaks-only --limit 2

# Offline inset emitters (no lab SSH). Same set as tools/check_results_fresh.py.
insets:
	$(PYTHON) tools/emit_rename_table.py
	$(PYTHON) tools/emit_distance_sweep.py
	$(PYTHON) tools/score_np_pair.py
	$(PYTHON) tools/emit_tier_table.py
	$(PYTHON) tools/emit_four_obligation_matrix.py
	$(PYTHON) tools/emit_upstream_obligations.py
	$(PYTHON) tools/score_upstream_repair_site.py
	$(PYTHON) tools/score_sc_vs_honesty.py
	$(PYTHON) tools/emit_rq1_lab_distance.py
	$(PYTHON) tools/emit_pad_rename_invariance.py
	$(PYTHON) tools/emit_depth21_selection.py
	$(PYTHON) tools/emit_baseline_battery.py
	$(PYTHON) tools/emit_oracle_controls.py
	$(PYTHON) tools/lab_marker_isolation_ab.py --rescore
	$(PYTHON) tools/emit_marker_isolation.py
	$(PYTHON) tools/emit_rq1_bpfix_cli.py
	$(PYTHON) tools/emit_figures.py

# The two natural corpora (main75 on the cite pin, rewrites, wild cases) and the verifier-state oracle,
# re-scored offline from the committed logs. Run dirs: the same as tools/check_results_fresh.py.
natural:
	$(PYTHON) tools/score_main75_pin.py --run campaigns/main75/lab/testbed-a-20261026T044355Z
	$(PYTHON) tools/score_main75_rewrites.py --run campaigns/n3/lab/testbed-a-20261026T060709Z
	$(PYTHON) tools/score_wild.py
	$(PYTHON) tools/score_state_oracle.py

# Campaign v2 sources (campaigns/v2/README.md); committed, checked by tests.
v2-mutants:
	$(PYTHON) tools/generate_v2_mutants.py
	$(PYTHON) tools/gen_upstream_metamorphic.py

figures:
	$(PYTHON) tools/emit_figures.py

smoke: version test rename-demo
	@echo "SMOKE COMPLETE"

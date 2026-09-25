.PHONY: help smoke test rename-demo insets figures version

help:
	@echo "Targets: smoke | test | rename-demo | insets | figures | version"

version:
	python -c "import bpfix_adversarial as m; print(m.__version__)"

test:
	python -m unittest discover -s tests -q

rename-demo:
	python -m bpfix_adversarial rename-demo --breaks-only --limit 2

# Offline inset emitters (no lab SSH). Same set as tools/check_results_fresh.py.
insets:
	python tools/emit_rename_table.py
	python tools/emit_distance_sweep.py
	python tools/score_np_pair.py
	python tools/emit_tier_table.py
	python tools/emit_four_obligation_matrix.py
	python tools/emit_upstream_obligations.py
	python tools/score_sc_vs_honesty.py
	python tools/emit_rq1_lab_distance.py
	python tools/emit_pad_rename_invariance.py
	python tools/emit_depth21_selection.py
	python tools/emit_baseline_battery.py
	python tools/emit_oracle_controls.py
	python tools/lab_marker_isolation_ab.py --rescore
	python tools/emit_marker_isolation.py
	python tools/emit_rq1_bpfix_cli.py
	python tools/emit_figures.py

figures:
	python tools/emit_figures.py

smoke: version test rename-demo
	@echo "SMOKE COMPLETE"

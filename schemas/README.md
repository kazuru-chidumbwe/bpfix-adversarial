# JSON schemas (optional interchange contracts)

`case.schema.json` and `result.schema.json` describe the shape of case and
scoring records for future tooling and packaging. They are **not** required
to run the committed evidence pipeline (`tools/emit_*.py` and `results/` insets).
They predate the source-line scoring contract: `case.schema.json` still describes
an instruction-index oracle (`loss_insn` / `reject_insn`) and `result.schema.json`
has no `top1_line` / `top1_span` / `set_recall_message`. The scored contract is
`docs/METRICS.md`.

CI loads both files as JSON (`tests/test_schemas.py`) so they stay
well-formed. Emitters write tables directly from Python objects, so there is no
runtime validation step against live mutant JSON.

# JSON schemas (optional interchange contracts)

`case.schema.json` and `result.schema.json` describe the shape of case and
scoring records for future tooling and packaging. They are **not** required
to run the committed evidence pipeline (`tools/emit_*.py` and `results/` insets).

CI loads both files as JSON (`tests/test_schemas.py`) so they stay
well-formed. Runtime validation against live mutant JSON is out of scope for
`v1.0.0` (emitters write tables directly from Python objects).

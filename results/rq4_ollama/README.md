# RQ4 Ollama capture artifacts

Frozen dumps from the SoftwareX-cited RQ4 run (`llama3.2:3b`, digest + seed pinned).

Reproduce (optional):

```bash
ollama pull llama3.2:3b   # digest was recorded at capture time under model_pin.json
python tools/rq4_llm_repair.py --backend ollama
```

Committed files:

- `system_prompt.txt` / `user_prompt.txt` — frozen prompts
- `response_raw.txt` — model output (C source)
- `repair.diff` — unified diff vs seed mutant
- `api_meta.json` — timings + seed/temperature + digest
- `model_pin.json` — tag → digest pin from `/api/tags` + `/api/show`

Paper-facing summary was written to `../honesty_utility_rq4.{md,json}`.

Lab load (2026-08-07, `app-test-server`): repaired → **ACCEPT**, seed → **REJECT**.
Re-check:

```bash
python tools/lab_load_one.py mutants/NullablePointer/NP-idiomatic-nocheck-repaired-ollama.c socket
python tools/lab_load_one.py mutants/NullablePointer/NP-idiomatic-nocheck.c socket
```

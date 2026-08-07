# RQ4 — Honesty ≠ utility (documented case)

**Claim frame:** existence / protocol demonstration — **n=1** mutant (`NP-idiomatic-nocheck`), **one** pinned Ollama repair call. Not a rate, prevalence, or multi-seed statistic. SoftwareX should cite this as a worked separator case the harness can record, not a generalizable finding.

**Status:** llm_ollama_pinned  
**UTC:** 2026-08-07T11:09:11.579372+00:00  
**Mutant:** `mutants/NullablePointer/NP-idiomatic-nocheck.c` (sha256 `1fc06b347754…`)  
**Backend:** `ollama`  
**Model:** llama3.2:3b · digest `a80c4f17acd55265fee…` · temperature `0.0`

## Construction oracle

- `ORACLE_LOSS_LINE` ≈ 22 (missing `if (!entry)` establish site)
- `ORACLE_REJECT_LINE` ≈ 36 (`return *entry`)
- Fed tip (wrong by construction): line 36 (terminal reject)

## Result

| Check | Value |
| --- | --- |
| Fed tip matches oracle loss? | False |
| Repair inserted `if (!entry)`? | True |
| Structural pass | True |
| Separator class | `A_wrong_localization_repair_succeeds` |
| Lab load (repaired) | **ACCEPT** (`NP-idiomatic-nocheck-repaired-ollama.20260807T112057Z.log`) |
| Lab load (seed) | **REJECT** (`NP-idiomatic-nocheck.20260807T112100Z.log`) |
| Lab host | `app-test-server` · Ubuntu 24.04 · kernel `6.8.0-136-generic` · clang 18.1.3 · bpftool v7.4.0 (alternate; SoftwareX primary pin remains Debian 13 lab-server — see `results/env_pins/`) |

## Reproducibility pins

- Script: `tools/rq4_llm_repair.py --backend ollama`
- Ollama model tag: `llama3.2:3b` · digest `a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72`
- options: temperature `0.0` · seed `42`
- System prompt sha256: `aabd23658347…`
- User prompt sha256: `e56cb2b25bd0…`
- Full prompt/response dumps: `results/rq4_ollama/`
- Determinism caveat: Local Ollama runs are best-effort reproducible: we pin model *digest*, temperature=0, and seed, and freeze prompts/response dumps. GPU/driver/Ollama-version drift can still change tokens. Treat the committed inset + lab ACCEPT as the SoftwareX evidence; re-runs should match digest and structural checks even if token text differs slightly.

## Unified diff (seed → repaired)

```diff
--- NP-idiomatic-nocheck.c
+++ NP-idiomatic-nocheck-repaired-ollama.c
@@ -15,12 +15,13 @@
 } m SEC(".maps");
 
 SEC("socket")
-int np_entry_nocheck(void *ctx)
+int np_entry(void *ctx)
 {
 	__u32 key = 0;
 	__u64 *entry = bpf_map_lookup_elem(&m, &key);
-	/* ORACLE_LOSS_LINE: missing idiomatic null-check establish on map value */
-	/* intentionally omitted for RQ4 failing seed */
+	if (!entry) {
+		return -1; // or some other error value
+	}
 	/* distance pad: 8 scalar ops (noise between loss and reject) */
 	__u64 __pad = 0;
 	__pad += 1;
@@ -32,7 +33,6 @@
 	__pad += 7;
 	__pad += 8;
 	(void)__pad;
-	/* ORACLE_REJECT_LINE: use of possibly-null map value */
 	return *entry;
 }
```

## Paper paragraph

Despite SourceComment-style localization failing on idiomatic `entry` naming
(and despite feeding a pinned repair call the terminal reject site rather than the
construction-time loss site), repair still succeeded by inserting `if (!entry)`
from surrounding map-lookup context. Localization honesty and repair utility
therefore diverge on this case. Reproduce with `python tools/rq4_llm_repair.py --backend ollama` (Ollama daemon + `ollama pull llama3.2:3b`).

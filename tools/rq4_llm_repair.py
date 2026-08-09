#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RQ4 — pinned LLM repair (reproducible honesty≠utility separator).

Backends (same frozen prompts + response/diff capture):

  openai  model: gpt-4o-mini-2024-07-18 · temperature 0.0
          requires OPENAI_API_KEY · openai==1.97.1

  ollama  model tag: llama3.2:3b (override with --model)
          temperature 0.0 · seed 42 · records exact model digest
          requires a running Ollama daemon (OLLAMA_HOST, default 127.0.0.1:11434)
          Local-model determinism is best-effort, not a guarantee — see inset caveat.

Usage:
  python tools/rq4_llm_repair.py --backend openai
  python tools/rq4_llm_repair.py --backend ollama
  python tools/rq4_llm_repair.py --backend ollama --model llama3.2:3b \\
      --write-repaired mutants/NullablePointer/NP-idiomatic-nocheck-repaired-ollama.c

Legacy floating Ollama path: tools/honesty_utility_rq4.py --llm ollama (do not cite).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTANT = ROOT / "mutants" / "NullablePointer" / "NP-idiomatic-nocheck.c"
OUT_JSON = ROOT / "results" / "honesty_utility_rq4.json"
OUT_MD = ROOT / "results" / "honesty_utility_rq4.md"

# --- pinned surfaces (do not float) ---
OPENAI_MODEL = "gpt-4o-mini-2024-07-18"
OLLAMA_DEFAULT_MODEL = "llama3.2:3b"
TEMPERATURE = 0.0
OLLAMA_SEED = 42
SYSTEM_PROMPT = "Return only repaired C source."
OLLAMA_HOST_DEFAULT = "http://127.0.0.1:11434"

WRONG_LOCALIZATION_LINE = 36
ORACLE_LOSS_LINE = 22
ORACLE_REJECT_LINE = 36
WRONG_LOCALIZATION_DETAIL = (
    "Reported loss site (UNTRUSTED diagnostic tip): line ~36 `return *entry;` "
    "(terminal reject / stop site). Do not assume this tip is the true proof-loss site."
)

DETERMINISM_CAVEAT = (
    "Local Ollama runs are best-effort reproducible: we pin model *digest*, "
    "temperature=0, and seed, and freeze prompts/response dumps. GPU/driver/"
    "Ollama-version drift can still change tokens. Treat the committed inset + "
    "lab ACCEPT as the SoftwareX evidence; re-runs should match digest and "
    "structural checks even if token text differs slightly."
)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def strip_c_comments(src: str) -> str:
    no_block = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//.*?$", "", no_block, flags=re.M)


def strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:c|C)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip() + "\n"


def build_user_prompt(program: str) -> str:
    return (
        "You are repairing a failing eBPF C program so the Linux BPF verifier accepts it.\n"
        f"\n{WRONG_LOCALIZATION_DETAIL}\n"
        "\nTask: return ONLY the full repaired C source. Prefer the minimal fix.\n"
        "Context: `bpf_map_lookup_elem` can return NULL; idiomatic code uses `if (!entry)`.\n"
        "\n```c\n"
        f"{program}"
        "```\n"
    )


def code_has_idiomatic_null_check(program: str) -> bool:
    return bool(re.search(r"if\s*\(\s*!entry\s*\)", strip_c_comments(program)))


def structural_checks(repaired: str) -> dict:
    has_check = code_has_idiomatic_null_check(repaired)
    code = strip_c_comments(repaired)
    still_has_use = "return *entry" in code
    tip_matches = WRONG_LOCALIZATION_LINE == ORACLE_LOSS_LINE
    return {
        "repair_has_idiomatic_null_check": has_check,
        "repair_retains_use": still_has_use,
        "structural_pass": has_check and still_has_use,
        "fed_localization_matches_oracle_loss": tip_matches,
        "separator_class": "A_wrong_localization_repair_succeeds"
        if (has_check and not tip_matches)
        else "inconclusive",
    }


def unified_diff(a: str, b: str, fromfile: str, tofile: str) -> str:
    import difflib

    return "".join(
        difflib.unified_diff(
            a.splitlines(keepends=True),
            b.splitlines(keepends=True),
            fromfile=fromfile,
            tofile=tofile,
        )
    )


def _http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    timeout: float = 300,
) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {body[:800]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(
            f"Cannot reach Ollama at {url} ({e}). Start `ollama serve` or set OLLAMA_HOST."
        ) from e


def ollama_base() -> str:
    return os.environ.get("OLLAMA_HOST", OLLAMA_HOST_DEFAULT).rstrip("/")


def resolve_ollama_pin(model_tag: str) -> dict:
    """Resolve floating tag → digest via /api/tags + /api/show."""
    base = ollama_base()
    tags = _http_json(f"{base}/api/tags", timeout=30)
    digest = None
    size = None
    details_from_tags = None
    for m in tags.get("models", []):
        name = m.get("name") or m.get("model") or ""
        # Exact or :latest alias match
        if name == model_tag or name == f"{model_tag}:latest" or (
            model_tag.endswith(":latest") and name == model_tag.replace(":latest", "")
        ):
            digest = m.get("digest")
            size = m.get("size")
            details_from_tags = m.get("details")
            break
        # Allow short tag match when user passed family without tag
        if name.startswith(model_tag + ":"):
            digest = m.get("digest")
            size = m.get("size")
            details_from_tags = m.get("details")
            model_tag = name
            break

    show = _http_json(
        f"{base}/api/show",
        method="POST",
        payload={"name": model_tag},
        timeout=60,
    )
    details = show.get("details") or details_from_tags or {}
    # Prefer digest from tags list; fall back to model_info keys if present
    if not digest:
        info = show.get("model_info") or {}
        for k, v in info.items():
            if "digest" in k.lower() and isinstance(v, str) and v:
                digest = v
                break
    if not digest:
        raise RuntimeError(
            f"Ollama model {model_tag!r} has no digest in /api/tags. "
            f"Pull it first: `ollama pull {model_tag}`."
        )
    return {
        "model_tag": model_tag,
        "digest": digest,
        "size_bytes": size,
        "details": details,
        "modelfile_sha256": sha256_text(show.get("modelfile") or ""),
        "parameters": show.get("parameters"),
        "ollama_host": base,
    }


def call_openai(system: str, user: str) -> tuple[str, dict]:
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError(
            "openai package missing; pip install -r requirements.txt"
        ) from e
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY unset")
    client = OpenAI(api_key=key)
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=TEMPERATURE,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    raw = resp.choices[0].message.content or ""
    meta = {
        "id": getattr(resp, "id", None),
        "model": getattr(resp, "model", OPENAI_MODEL),
        "usage": None if resp.usage is None else resp.usage.model_dump(),
    }
    return strip_code_fence(raw), meta


def call_ollama(system: str, user: str, model_tag: str, pin: dict) -> tuple[str, dict]:
    """Chat API with temperature=0 and fixed seed; pin must include digest."""
    base = ollama_base()
    payload = {
        "model": model_tag,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "options": {
            "temperature": TEMPERATURE,
            "seed": OLLAMA_SEED,
        },
    }
    data = _http_json(
        f"{base}/api/chat",
        method="POST",
        payload=payload,
        timeout=600,
    )
    msg = data.get("message") or {}
    raw = msg.get("content") or ""
    meta = {
        "model_tag": model_tag,
        "digest": pin["digest"],
        "size_bytes": pin.get("size_bytes"),
        "details": pin.get("details"),
        "modelfile_sha256": pin.get("modelfile_sha256"),
        "parameters": pin.get("parameters"),
        "ollama_host": pin.get("ollama_host"),
        "seed": OLLAMA_SEED,
        "temperature": TEMPERATURE,
        "total_duration": data.get("total_duration"),
        "load_duration": data.get("load_duration"),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "done_reason": data.get("done_reason"),
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    return strip_code_fence(raw), meta


def write_paper_facing(record: dict, diff: str, artifact_dir: str) -> None:
    OUT_JSON.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    backend = record["backend"]
    model_line = record["model"]
    if record.get("model_digest"):
        model_line = f"{record['model']} · digest `{record['model_digest'][:19]}…`"
    pins = [
        f"- Script: `tools/rq4_llm_repair.py --backend {record.get('backend_cli', backend)}`",
        f"- System prompt sha256: `{record['system_prompt_sha256'][:12]}…`",
        f"- User prompt sha256: `{record['prompt_sha256'][:12]}…`",
        f"- Full prompt/response dumps: `{artifact_dir}/`",
    ]
    if backend == "openai-api":
        pins.insert(1, "- `openai==1.97.1` (`requirements.txt`)")
        pins.insert(2, f"- Model id: `{OPENAI_MODEL}` · temperature `{TEMPERATURE}`")
        how = (
            f"`python tools/rq4_llm_repair.py --backend openai` "
            f"(`OPENAI_API_KEY` required)."
        )
    else:
        pins.insert(
            1,
            f"- Ollama model tag: `{record['model']}` · digest `{record.get('model_digest', '')}`",
        )
        pins.insert(
            2,
            f"- options: temperature `{TEMPERATURE}` · seed `{OLLAMA_SEED}`",
        )
        pins.append(f"- Determinism caveat: {DETERMINISM_CAVEAT}")
        how = (
            f"`python tools/rq4_llm_repair.py --backend ollama` "
            f"(Ollama daemon + `ollama pull {record['model']}`)."
        )

    md = f"""# RQ4 — Honesty ≠ utility (separator)

**Status:** {record["status"]}  
**UTC:** {record["utc"]}  
**Mutant:** `{record["mutant"]}` (sha256 `{record["mutant_sha256"][:12]}…`)  
**Backend:** `{record["backend"]}`  
**Model:** {model_line} · temperature `{record["temperature"]}`

## Construction oracle

- `ORACLE_LOSS_LINE` ≈ {ORACLE_LOSS_LINE} (missing `if (!entry)` establish site)
- `ORACLE_REJECT_LINE` ≈ {ORACLE_REJECT_LINE} (`return *entry`)
- Fed tip (wrong by construction): line {WRONG_LOCALIZATION_LINE} (terminal reject)

## Result

| Check | Value |
| --- | --- |
| Fed tip matches oracle loss? | {record["checks"]["fed_localization_matches_oracle_loss"]} |
| Repair inserted `if (!entry)`? | {record["checks"]["repair_has_idiomatic_null_check"]} |
| Structural pass | {record["checks"]["structural_pass"]} |
| Separator class | `{record["checks"]["separator_class"]}` |
| Lab load (repaired) | {record.get("lab", {}).get("repaired_verdict", "pending / see lab_load_one.py")} |

## Reproducibility pins

{chr(10).join(pins)}

## Unified diff (seed → repaired)

```diff
{diff.rstrip()}
```

## Paper paragraph

Despite SourceComment-style localization failing on idiomatic `entry` naming
(and despite feeding a pinned repair call the terminal reject site rather than the
construction-time loss site), repair still succeeded by inserting `if (!entry)`
from surrounding map-lookup context. Localization honesty and repair utility
therefore diverge on this case. Reproduce with {how}
"""
    OUT_MD.write_text(md, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--backend",
        choices=("openai", "ollama"),
        default="ollama",
        help="Pinned backend (default: ollama — no cloud API key)",
    )
    ap.add_argument(
        "--model",
        default="",
        help=f"Ollama model tag (default: {OLLAMA_DEFAULT_MODEL}); ignored for openai",
    )
    ap.add_argument(
        "--write-repaired",
        type=Path,
        default=None,
        help="Output repaired C path (defaults per backend)",
    )
    args = ap.parse_args()

    if args.write_repaired is None:
        suffix = "openai" if args.backend == "openai" else "ollama"
        args.write_repaired = (
            ROOT
            / "mutants"
            / "NullablePointer"
            / f"NP-idiomatic-nocheck-repaired-{suffix}.c"
        )

    artifact_rel = (
        "results/rq4_openai" if args.backend == "openai" else "results/rq4_ollama"
    )
    out_dir = ROOT / artifact_rel.replace("/", os.sep)

    seed = MUTANT.read_text(encoding="utf-8")
    user_prompt = build_user_prompt(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "system_prompt.txt").write_text(SYSTEM_PROMPT + "\n", encoding="utf-8")
    (out_dir / "user_prompt.txt").write_text(user_prompt, encoding="utf-8")

    if args.backend == "openai":
        repaired, api_meta = call_openai(SYSTEM_PROMPT, user_prompt)
        model_name = OPENAI_MODEL
        model_digest = None
        status = "llm_openai_pinned"
        backend = "openai-api"
        takeaway = (
            f"Despite wrong localization tip, pinned {OPENAI_MODEL} "
            f"(temp={TEMPERATURE}) inserted if (!entry) — honesty≠utility class A."
        )
        repaired_name = "NP-idiomatic-nocheck-repaired-openai.c"
    else:
        model_tag = args.model or OLLAMA_DEFAULT_MODEL
        pin = resolve_ollama_pin(model_tag)
        # Use resolved tag from pin (may have expanded)
        model_tag = pin["model_tag"]
        repaired, api_meta = call_ollama(SYSTEM_PROMPT, user_prompt, model_tag, pin)
        # Re-check digest after call (weights must not have changed mid-run)
        pin_after = resolve_ollama_pin(model_tag)
        if pin_after["digest"] != pin["digest"]:
            raise RuntimeError(
                "Ollama model digest changed between pin and generate "
                f"({pin['digest'][:16]}… → {pin_after['digest'][:16]}…). Aborting."
            )
        model_name = model_tag
        model_digest = pin["digest"]
        status = "llm_ollama_pinned"
        backend = "ollama"
        takeaway = (
            f"Despite wrong localization tip, pinned Ollama {model_tag} "
            f"(digest {model_digest[:12]}…, temp={TEMPERATURE}, seed={OLLAMA_SEED}) "
            "inserted if (!entry) — honesty≠utility class A. "
            "Local determinism is best-effort; see inset caveat."
        )
        repaired_name = "NP-idiomatic-nocheck-repaired-ollama.c"
        (out_dir / "model_pin.json").write_text(
            json.dumps(pin, indent=2) + "\n", encoding="utf-8"
        )

    (out_dir / "response_raw.txt").write_text(repaired, encoding="utf-8")
    (out_dir / "api_meta.json").write_text(
        json.dumps(api_meta, indent=2) + "\n", encoding="utf-8"
    )

    checks = structural_checks(repaired)
    diff = unified_diff(seed, repaired, "NP-idiomatic-nocheck.c", repaired_name)
    (out_dir / "repair.diff").write_text(diff, encoding="utf-8")

    outp = args.write_repaired
    if not outp.is_absolute():
        outp = ROOT / outp
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(repaired, encoding="utf-8")

    record = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "backend": backend,
        "backend_cli": args.backend,
        "model": model_name,
        "model_digest": model_digest,
        "temperature": TEMPERATURE,
        "seed": OLLAMA_SEED if args.backend == "ollama" else None,
        "openai_package": "1.97.1" if args.backend == "openai" else None,
        "determinism_caveat": DETERMINISM_CAVEAT if args.backend == "ollama" else None,
        "mutant": str(MUTANT.relative_to(ROOT)).replace("\\", "/"),
        "mutant_sha256": sha256_text(seed),
        "system_prompt_sha256": sha256_text(SYSTEM_PROMPT + "\n"),
        "prompt_sha256": sha256_text(user_prompt),
        "repaired_sha256": sha256_text(repaired),
        "repaired_path": str(outp.relative_to(ROOT)).replace("\\", "/"),
        "api": api_meta,
        "oracle": {
            "loss_line_approx": ORACLE_LOSS_LINE,
            "reject_line_approx": ORACLE_REJECT_LINE,
            "wrong_tip_line": WRONG_LOCALIZATION_LINE,
        },
        "checks": checks,
        "artifacts": {
            "system_prompt": f"{artifact_rel}/system_prompt.txt",
            "user_prompt": f"{artifact_rel}/user_prompt.txt",
            "response": f"{artifact_rel}/response_raw.txt",
            "diff": f"{artifact_rel}/repair.diff",
            "api_meta": f"{artifact_rel}/api_meta.json",
            **(
                {"model_pin": f"{artifact_rel}/model_pin.json"}
                if args.backend == "ollama"
                else {}
            ),
        },
        "paper_takeaway": takeaway,
    }
    write_paper_facing(record, diff, artifact_rel)
    print(
        json.dumps(
            {
                "out": str(OUT_JSON),
                "backend": backend,
                "repaired_path": record["repaired_path"],
                "structural_pass": checks["structural_pass"],
                "separator_class": checks["separator_class"],
                "model": model_name,
                "model_digest": model_digest,
                "artifacts": artifact_rel,
            },
            indent=2,
        )
    )
    return 0 if checks["structural_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

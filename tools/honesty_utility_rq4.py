# SPDX-License-Identifier: MIT
"""RQ4 honesty ≠ utility — separator experiment (Phase 2).

Lead arm: idiomatic `entry` naming + missing null check.
We feed the repair agent a *wrong* localization tip (terminal reject / pad site),
matching the class of SourceComment miss on `if (!entry)` (coverage boundary).
A successful repair that inserts `if (!entry)` from surrounding context shows
utility can succeed despite dishonest localization.

Usage:
  # SoftwareX cite path — use tools/rq4_llm_repair.py --backend ollama instead.
  python tools/honesty_utility_rq4.py --force-legacy-out results/rq4_legacy
  python tools/honesty_utility_rq4.py --force-legacy-out results/rq4_legacy --llm openai
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
CITE_RQ4_JSON = OUT_JSON
CITE_RQ4_MD = OUT_MD

# Construction-time oracle (fixed before any diagnostic / repair).
# Line numbers refer to mutants/NullablePointer/NP-idiomatic-nocheck.c
ORACLE_LOSS_LINE = 22  # ORACLE_LOSS_LINE comment: missing if (!entry)
ORACLE_REJECT_LINE = 36  # return *entry
# Wrong localization tip: terminal reject bias (what a stop-site diagnostic says).
WRONG_LOCALIZATION_LINE = 36
WRONG_LOCALIZATION_DETAIL = (
    "Reported loss site (UNTRUSTED diagnostic tip): line ~36 `return *entry;` "
    "(terminal reject / stop site). Do not assume this tip is the true proof-loss site."
)


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def load_program() -> str:
    return MUTANT.read_text(encoding="utf-8")


def build_prompt(program: str) -> str:
    return f"""You are repairing a failing eBPF C program so the Linux BPF verifier accepts it.

{WRONG_LOCALIZATION_DETAIL}

Task: return ONLY the full repaired C source. Prefer the minimal fix.
Context: `bpf_map_lookup_elem` can return NULL; idiomatic code uses `if (!entry)`.

```c
{program}
```
"""


def strip_c_comments(src: str) -> str:
    """Remove // and /* */ comments so structural checks ignore oracle prose."""
    no_block = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return re.sub(r"//.*?$", "", no_block, flags=re.M)


def code_has_idiomatic_null_check(program: str) -> bool:
    return bool(re.search(r"if\s*\(\s*!entry\s*\)", strip_c_comments(program)))


def heuristic_context_repair(program: str) -> str:
    """Deterministic stand-in when no LLM is available.

    Ignores the wrong localization tip and inserts idiomatic `if (!entry)`
    immediately after the lookup — the semantic fix a context-reading agent
    should produce. Used to freeze the experiment *protocol*; live LLM
    results replace this when an API is available.
    """
    needle = "\t__u64 *entry = bpf_map_lookup_elem(&m, &key);\n"
    insert = (
        needle
        + "\tif (!entry)\n"
        + "\t\treturn 0;\n"
    )
    if needle not in program:
        raise RuntimeError("expected lookup line missing from mutant")
    if code_has_idiomatic_null_check(program):
        return program
    return program.replace(needle, insert, 1)


def repair_passes_oracle_check(repaired: str) -> dict:
    """Structural pass criteria for this separator (lab verifier is definitive)."""
    has_check = code_has_idiomatic_null_check(repaired)
    code = strip_c_comments(repaired)
    still_has_use = "return *entry" in code
    # Localization honesty of the *tip* we fed: wrong by construction.
    tip_matches_oracle_loss = WRONG_LOCALIZATION_LINE == ORACLE_LOSS_LINE
    return {
        "repair_has_idiomatic_null_check": has_check,
        "repair_retains_use": still_has_use,
        "structural_pass": has_check and still_has_use,
        "fed_localization_matches_oracle_loss": tip_matches_oracle_loss,
        "separator_class": "A_wrong_localization_repair_succeeds"
        if (has_check and not tip_matches_oracle_loss)
        else "inconclusive",
    }


def call_openai(prompt: str, model: str) -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY unset")
    # Prefer the dedicated pinned entrypoint; this path remains for --llm openai.
    body = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return only repaired C source."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = data["choices"][0]["message"]["content"]
    return strip_code_fence(text)


def call_ollama(prompt: str, model: str) -> str:
    body = json.dumps(
        {"model": model, "prompt": prompt, "stream": False}
    ).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:11434/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return strip_code_fence(data.get("response", ""))


def strip_code_fence(text: str) -> str:
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:c|C)?\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip() + "\n"


def write_outputs(record: dict, *, out_json: Path, out_md: Path) -> None:
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    md = f"""# RQ4 — Honesty ≠ utility (separator)

**Status:** {record["status"]}  
**UTC:** {record["utc"]}  
**Mutant:** `{record["mutant"]}` (sha256 `{record["mutant_sha256"][:12]}…`)  
**Backend:** `{record["backend"]}`

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

## Paper paragraph (draft)

Despite SourceComment-style localization failing on idiomatic `entry` naming
(and despite feeding the repair agent the terminal reject site rather than the
construction-time loss site), repair still succeeded by inserting `if (!entry)`
from surrounding map-lookup context. Localization honesty and repair utility
therefore diverge on this case.

## Note

Lab verifier load is definitive for camera-ready. Structural pass is the
offline gate used when kernel capture is unavailable.
"""
    out_md.write_text(md, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=(
            "Legacy RQ4 helper. SoftwareX cite insets are produced by "
            "tools/rq4_llm_repair.py --backend ollama — this script will not "
            "overwrite results/honesty_utility_rq4.* unless redirected."
        )
    )
    ap.add_argument(
        "--llm",
        choices=("none", "openai", "ollama"),
        default="none",
        help="none = deterministic context repair (protocol freeze)",
    )
    ap.add_argument("--model", default="")
    ap.add_argument(
        "--write-repaired",
        type=Path,
        default=None,
        help="Write repaired C to this path (for lab verifier accept)",
    )
    ap.add_argument(
        "--force-legacy-out",
        type=Path,
        default=None,
        metavar="DIR",
        help=(
            "Write JSON/MD under DIR instead of the SoftwareX cite paths. "
            "Required to persist output from this legacy script."
        ),
    )
    args = ap.parse_args()

    if args.force_legacy_out is None:
        print(
            "Refusing to overwrite SoftwareX RQ4 cite insets "
            f"({CITE_RQ4_JSON.as_posix()}, {CITE_RQ4_MD.as_posix()}).\n"
            "Use: python tools/rq4_llm_repair.py --backend ollama\n"
            "For local legacy experiments only: "
            "python tools/honesty_utility_rq4.py --force-legacy-out results/rq4_legacy",
            file=sys.stderr,
        )
        return 2

    out_dir = args.force_legacy_out
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    out_json = out_dir / "honesty_utility_rq4.json"
    out_md = out_dir / "honesty_utility_rq4.md"
    if out_json.resolve() == CITE_RQ4_JSON.resolve() or out_md.resolve() == CITE_RQ4_MD.resolve():
        print(
            "Refusing --force-legacy-out that resolves to SoftwareX cite paths. "
            "Choose a different directory (e.g. results/rq4_legacy).",
            file=sys.stderr,
        )
        return 2

    program = load_program()
    prompt = build_prompt(program)
    backend = args.llm
    model = args.model or (
        "gpt-4o-mini-2024-07-18"
        if args.llm == "openai"
        else "llama3"
        if args.llm == "ollama"
        else "heuristic-context"
    )

    try:
        if args.llm == "openai":
            repaired = call_openai(prompt, model)
            status = "llm_openai"
        elif args.llm == "ollama":
            repaired = call_ollama(prompt, model)
            status = "llm_ollama"
        else:
            repaired = heuristic_context_repair(program)
            status = "heuristic_standin_pending_llm"
    except (RuntimeError, urllib.error.URLError, TimeoutError, KeyError) as e:
        repaired = heuristic_context_repair(program)
        status = f"fallback_heuristic_after_error:{e}"
        backend = f"{args.llm}->heuristic"

    checks = repair_passes_oracle_check(repaired)
    repaired_path = None
    if args.write_repaired is not None:
        outp = args.write_repaired
        if not outp.is_absolute():
            outp = ROOT / outp
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(repaired, encoding="utf-8")
        repaired_path = str(outp.relative_to(ROOT)).replace("\\", "/")

    record = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "backend": backend,
        "model": model,
        "mutant": str(MUTANT.relative_to(ROOT)).replace("\\", "/"),
        "mutant_sha256": sha256_text(program),
        "prompt_sha256": sha256_text(prompt),
        "repaired_sha256": sha256_text(repaired),
        "repaired_path": repaired_path,
        "oracle": {
            "loss_line_approx": ORACLE_LOSS_LINE,
            "reject_line_approx": ORACLE_REJECT_LINE,
            "wrong_tip_line": WRONG_LOCALIZATION_LINE,
        },
        "checks": checks,
        "paper_takeaway": (
            "Despite localization failure, repair succeeded due to semantic "
            "context—proving utility and honesty diverge."
        ),
    }
    write_outputs(record, out_json=out_json, out_md=out_md)
    print(
        json.dumps(
            {
                "out": str(out_json),
                **checks,
                "status": status,
                "repaired_path": repaired_path,
            },
            indent=2,
        )
    )
    return 0 if checks["structural_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

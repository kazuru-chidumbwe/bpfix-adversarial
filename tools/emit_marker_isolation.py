#!/usr/bin/env python3
"""Marker isolation evidence (Gates primary validity threat).

Offline SoftwareX-stamp suite (no lab required):
  1. ORACLE_* tokens absent from captured verifier logs (VS / bpfix CLI inputs).
  2. SourceComment reports identical lines on marker-bearing vs line-preserving
     marker-neutral sources (reporter output invariant to marker text).
  3. looks_like_* heuristics never fire on ORACLE comment lines themselves.

Optional lab A/B (tools/lab_marker_isolation_ab.py) compares bearing vs neutral
compile+load logs on the pinned host when reachable; merges into this report if
results/marker_isolation_lab.json exists.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.heuristics import (  # noqa: E402
    looks_like_null_check,
    looks_like_nullable_return,
    looks_like_packet_bounds_check,
    looks_like_scalar_guard,
)
from bpfix_adversarial.marker_isolation import (  # noqa: E402
    oracle_tokens_in_text,
    strip_oracle_markers,
)
from bpfix_adversarial.oracle import oracle_sites  # noqa: E402

STAMP = "20260801T181331Z"
OUT_JSON = ROOT / "results" / "marker_isolation.json"
OUT_MD = ROOT / "results" / "marker_isolation.md"
LAB_JSON = ROOT / "results" / "marker_isolation_lab.json"


def _load_sc_report():
    spec = importlib.util.spec_from_file_location(
        "score_sc_vs_honesty", ROOT / "tools" / "score_sc_vs_honesty.py"
    )
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod.sc_report


def heuristic_hit(line: str) -> bool:
    t = line.strip()
    return bool(
        looks_like_null_check(t)
        or looks_like_nullable_return(t)
        or looks_like_packet_bounds_check(t)
        or (looks_like_scalar_guard(t) and "data_end" not in t)
    )


def main() -> None:
    sc_report = _load_sc_report()
    sc = json.loads((ROOT / "results" / "sc_vs_honesty.json").read_text(encoding="utf-8"))
    rows = [
        r
        for r in sc["rows"]
        if STAMP in (r.get("log") or "")
        and r.get("src")
        and (ROOT / r["src"]).is_file()
        and "repaired" not in r["case_id"]
    ]

    log_isolation = []
    for r in rows:
        text = (ROOT / r["log"]).read_text(encoding="utf-8", errors="replace")
        toks = oracle_tokens_in_text(text)
        log_isolation.append(
            {
                "case_id": r["case_id"],
                "log": r["log"],
                "oracle_token_lines": len(toks),
                "pass": len(toks) == 0,
            }
        )

    sc_ab = []
    for r in rows:
        src = ROOT / r["src"]
        bearing = src.read_text(encoding="utf-8")
        neutral = strip_oracle_markers(bearing, preserve_lines=True)
        assert "ORACLE_" not in neutral
        assert bearing.count("\n") == neutral.count("\n")
        # Write temp neutral only in-memory via TemporaryDirectory pattern:
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            nb = Path(td) / "bearing.c"
            nn = Path(td) / "neutral.c"
            nb.write_text(bearing, encoding="utf-8")
            nn.write_text(neutral, encoding="utf-8")
            b_line, b_note = sc_report(nb, r["obligation"], r["case_id"])
            n_line, n_note = sc_report(nn, r["obligation"], r["case_id"])
        sc_ab.append(
            {
                "case_id": r["case_id"],
                "obligation": r["obligation"],
                "sc_bearing": b_line,
                "sc_neutral": n_line,
                "sc_note_bearing": b_note,
                "pass": b_line == n_line,
            }
        )

    heuristic_isolation = []
    for r in rows:
        src = ROOT / r["src"]
        bad = []
        for i, raw in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
            if "ORACLE_" in raw and heuristic_hit(raw):
                bad.append(i)
        heuristic_isolation.append(
            {
                "case_id": r["case_id"],
                "oracle_lines_matching_heuristics": bad,
                "pass": len(bad) == 0,
            }
        )

    def rate(rows_in: list[dict]) -> dict:
        n = len(rows_in)
        hits = sum(1 for x in rows_in if x.get("pass"))
        return {"hits": hits, "n": n, "pass_rate": round(hits / n, 4) if n else 0.0}

    lab = None
    if LAB_JSON.is_file():
        lab = json.loads(LAB_JSON.read_text(encoding="utf-8"))

    summary = {
        "log_input_no_oracle_tokens": rate(log_isolation),
        "sc_bearing_vs_neutral_identical": rate(sc_ab),
        "oracle_comments_not_heuristic_hits": rate(heuristic_isolation),
        "lab_bearing_vs_neutral_load": (
            lab["summary"]
            if lab
            else {
                "hits": 0,
                "n": 0,
                "pass_rate": None,
                "status": "not_run_or_host_unreachable",
            }
        ),
    }

    payload = {
        "generator": "tools/emit_marker_isolation.py",
        "stamp_filter": STAMP,
        "summary": summary,
        "log_input_no_oracle_tokens": log_isolation,
        "sc_bearing_vs_neutral_identical": sc_ab,
        "oracle_comments_not_heuristic_hits": heuristic_isolation,
        "lab_ab": {
            "path": str(LAB_JSON.relative_to(ROOT)).replace("\\", "/")
            if lab
            else None,
            "present": lab is not None,
            "summary": lab["summary"] if lab else None,
            "host_probe": lab.get("host_probe") if lab else None,
        },
        "gates_mapping": {
            "what_this_establishes": [
                "Captured SoftwareX-stamp verifier logs contain no ORACLE_* tokens "
                "(VS / upstream bpfix CLI cannot read markers from log text).",
                "SourceComment reported line is invariant under line-preserving "
                "marker neutralization on the same SoftwareX-stamp sources.",
                "ORACLE comment lines themselves are not looks_like_* hits.",
            ],
            "what_requires_lab_ab": [
                "Compile+load identity: marker-bearing vs marker-neutral produce "
                "identical ACCEPT/REJECT, VS stop site, and source-map pairs "
                "(tools/lab_marker_isolation_ab.py on the SoftwareX pin host).",
            ],
        },
        "note": (
            "Scoring still reads ORACLE_* via oracle_sites for ground truth only. "
            "That path is not a diagnostic reporter input."
        ),
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Marker isolation (Gates construct validity)",
        "",
        f"SoftwareX-stamp filter `{STAMP}`. Offline suite always; lab A/B when host reachable.",
        "",
        "| Check | Pass | n | Rate |",
        "| --- | ---: | ---: | ---: |",
    ]
    for key, label in (
        ("log_input_no_oracle_tokens", "no ORACLE_* in verifier logs"),
        ("sc_bearing_vs_neutral_identical", "SC bearing ≡ neutral"),
        ("oracle_comments_not_heuristic_hits", "ORACLE lines ≠ heuristic hits"),
    ):
        s = summary[key]
        lines.append(f"| {label} | {s['hits']} | {s['n']} | {s['pass_rate']:.0%} |")
    lab_s = summary["lab_bearing_vs_neutral_load"]
    if lab_s.get("pass_rate") is None:
        lines.append("| lab bearing≡neutral load | — | 0 | not run |")
    else:
        lines.append(
            f"| lab bearing≡neutral load | {lab_s['pass']} | {lab_s['n']} | "
            f"{lab_s['pass_rate']:.0%} |"
        )
    lines += [
        "",
        "## Gates mapping",
        "",
        "Offline checks isolate **reporter inputs/outputs** from marker text.",
        "Full **log identity** under compile+load still requires "
        "`python tools/lab_marker_isolation_ab.py` on the SoftwareX pin host.",
        "",
        "JSON: `marker_isolation.json`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

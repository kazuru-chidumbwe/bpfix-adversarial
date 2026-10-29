#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Sensitivity of Pretty Verifier's scores to its source-line lookup.

Pretty Verifier prints the verifier log's own source annotation of the failing
statement (``<code> @ file:line``) next to a line number it looks up itself in
``llvm-objdump`` output of the whole object. Where the two disagree, this
re-scores Pretty Verifier with the log's line, using each scorer's own
``outcome`` rule, and writes results/pv_lookup.{json,md}. The released scores in
results/main75_pin.json and results/wild.json are not changed.

Wild cases are also scored with the printed location in its own file, since the
adapter keeps only locations in the case's source file.

Usage: python tools/score_pv_lookup.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import score_main75_pin as m75  # noqa: E402
from tools import score_wild as sw  # noqa: E402

MAIN75 = ROOT / "results" / "main75_pin.json"
WILD = ROOT / "results" / "wild.json"
OUT_JSON = ROOT / "results" / "pv_lookup.json"
OUT_MD = ROOT / "results" / "pv_lookup.md"
RULES = ("R0", "R1", "R2")
METRICS = ("primary_on_site", "label_on_site", "primary_within_3")
REP = "PrettyVerifier"

PV_LINE = re.compile(r"^\s*(\d+) \| .*@ (\S+):(\d+)\s*$")
PV_FILE = re.compile(r"^\s*\| in file (.+?)\s*$")


def locations(text: str) -> dict | None:
    """First location of a Pretty Verifier output: printed (file, line) and the log's own (file, line)."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = PV_LINE.match(ln)
        if not m:
            continue
        f = PV_FILE.match(lines[i + 1]) if i + 1 < len(lines) else None
        return {"printed": [Path(f.group(1)).name if f else None, int(m.group(1))],
                "log": [Path(m.group(2)).name, int(m.group(3))]}
    return None


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def main75_rows() -> list[dict]:
    d = json.loads(read(MAIN75))
    run = ROOT / d["run"] / "buggy"
    rows = []
    for r in d["rows"]:
        if r.get("excluded"):
            continue
        pv = sorted(run.glob(f"{r['case_id']}__buggy.*.prettyverifier.txt"))
        loc = locations(read(pv[-1])) if pv else None
        row = {"case": r["case_id"], "loc": loc,
               "released": {rule: r["outcomes"][REP][rule] for rule in RULES}}
        if loc and loc["printed"] != loc["log"]:
            f, ln = loc["log"]
            # main75 programs are one source file; a line in another file is no hit
            row["log_line"] = {rule: m75.outcome(ln if f == "buggy.bpf.c" else None,
                                                  [ln] if f == "buggy.bpf.c" else [],
                                                  r["repair_sites"][rule]) for rule in RULES}
        rows.append(row)
    return rows


def wild_rows() -> list[dict]:
    d = json.loads(read(WILD))
    rows = []
    for r in d["rows"]:
        if r.get("excluded"):
            continue
        loc = locations(read(sw.CASES / str(r["rank"]) / "buggy.prettyverifier.txt"))
        row = {"case": str(r["rank"]), "loc": loc,
               "released": {rule: r["outcomes"][REP][rule] for rule in RULES}}
        if loc:
            sites = r["repair_sites"]
            pf, pl = loc["printed"]
            lf, ll = loc["log"]
            row["printed_in_its_file"] = {rule: sw.outcome(pf, pl, [pl], r["unit"], sites[rule]) for rule in RULES}
            if [pf, pl] != [lf, ll]:
                row["log_line"] = {rule: sw.outcome(lf, ll, [ll], r["unit"], sites[rule]) for rule in RULES}
        rows.append(row)
    return rows


def tally(rows: list[dict], key: str) -> dict:
    """Hits per rule and metric, taking `key` where a row has it and the released outcome otherwise."""
    return {rule: {m: sum(1 for r in rows if r.get(key, r["released"])[rule][m]) for m in METRICS}
            for rule in RULES}


def summarise(rows: list[dict], keys: tuple[str, ...]) -> dict:
    with_loc = [r for r in rows if r["loc"]]
    return {
        "n": len(rows),
        "with_location": len(with_loc),
        "line_differs": [r["case"] for r in with_loc if r["loc"]["printed"] != r["loc"]["log"]],
        "hits": {k: tally(rows, k) for k in keys},
    }


def frac(k: int, n: int) -> str:
    return f"{k}/{n}"


def render_md(p: dict) -> str:
    L = ["# Pretty Verifier: sensitivity to its line lookup", "",
         f"Generator: `{p['generator']}`. Released scores (results/main75_pin.json, results/wild.json) are unchanged; "
         "`log line` re-scores the cases where Pretty Verifier's printed line differs from the verifier log's own "
         "annotation of the same statement, with the log's line.", ""]
    for corpus, s in p["corpora"].items():
        L += [f"## {corpus}: {s['n']} cases, {s['with_location']} with a location, "
              f"{len(s['line_differs'])} with a different line", ""]
        if s["line_differs"]:
            L += ["Cases: " + ", ".join(f"`{c}`" for c in s["line_differs"]) + ".", ""]
        L += ["| scoring | " + " | ".join(f"{rule} primary | {rule} label" for rule in RULES) + " |",
              "| --- |" + " ---: | ---: |" * len(RULES)]
        for k, h in s["hits"].items():
            L.append(f"| {k.replace('_', ' ')} | " + " | ".join(
                f"{frac(h[rule]['primary_on_site'], s['n'])} | {frac(h[rule]['label_on_site'], s['n'])}"
                for rule in RULES) + " |")
        L.append("")
    L += ["## Per case", "", "| corpus | case | printed | log |", "| --- | --- | --- | --- |"]
    for corpus, rows in p["rows"].items():
        for r in rows:
            if r["loc"] and r["loc"]["printed"] != r["loc"]["log"]:
                pr, lg = r["loc"]["printed"], r["loc"]["log"]
                L.append(f"| {corpus} | `{r['case']}` | {pr[0]}:{pr[1]} | {lg[0]}:{lg[1]} |")
    return "\n".join(L) + "\n"


def main(argv: list[str] | None = None) -> int:
    rows = {"main75": main75_rows(), "wild": wild_rows()}
    payload = {
        "generator": "tools/score_pv_lookup.py",
        "inputs": ["results/main75_pin.json", "results/wild.json"],
        "corpora": {"main75": summarise(rows["main75"], ("released", "log_line")),
                    "wild": summarise(rows["wild"], ("released", "printed_in_its_file", "log_line"))},
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")
    OUT_MD.write_text(render_md(payload), encoding="utf-8", newline="\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

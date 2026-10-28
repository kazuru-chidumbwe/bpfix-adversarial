#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Agreement of the verifier-state oracle with the repair-site oracle, by docs/STATE-ORACLE.md.

Reads the main75 pin capture (the run results/main75_pin.json was scored from)
and the scored wild cases, computes the state oracle from each buggy log, and
writes results/state_oracle.{json,md}. Reporters are not ranked against the
oracle; the per-reporter column is context only (rule 6).

Usage: python tools/score_state_oracle.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.oracle import code_line_mask  # noqa: E402
from bpfix_adversarial.repair_site import wilson  # noqa: E402
from bpfix_adversarial.state_oracle import compute  # noqa: E402
from tools.score_main75_pin import CASES as MAIN75_CASES, load_manifest  # noqa: E402

MAIN75 = ROOT / "results" / "main75_pin.json"
WILD = ROOT / "results" / "wild.json"
WILD_CASES = ROOT / "fixtures" / "wild" / "cases"
OUT_JSON = ROOT / "results" / "state_oracle.json"
OUT_MD = ROOT / "results" / "state_oracle.md"
RULES = ("R0", "R1", "R2")


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def n_code(text: str) -> int:
    return sum(code_line_mask([ln.rstrip() for ln in text.splitlines()]))


def row_for(corpus: str, case: str, log: Path, repair: dict[str, dict[str, list[int]]], code: int,
            predictions: dict, unit: str) -> dict:
    o = compute(read(log))
    r: dict = {"corpus": corpus, "case": case, "kind": o.kind, "message": o.message[:200], "note": o.note}
    if o.kind is None:
        return r
    sites = [list(s) for s in o.sites]
    r.update(first_loss=None if o.first_loss is None else {"insn": o.first_loss.idx, "line": o.first_loss.src},
             stop_line=o.stop_line, sites=sites, n_sites=len(sites),
             chance=round(len(sites) / code, 4) if code else None)
    if not sites:
        return r
    on = {rule: {(f, ln) for f, lines in repair[rule].items() for ln in lines} for rule in RULES}
    st = {(f, ln) for f, ln in o.sites}
    r["agrees"] = {rule: bool(st & on[rule]) for rule in RULES}
    r["primary_on_state_site"] = {
        rep: p.get("primary") is not None and (Path(p.get("file") or unit).name, p["primary"]) in st
        for rep, p in predictions.items()}
    return r


def main75_rows() -> list[dict]:
    d = json.loads(read(MAIN75))
    buggy = load_manifest(ROOT / d["run"] / "buggy")
    out = []
    for row in d["rows"]:
        if row.get("excluded"):
            continue
        cid = row["case_id"]
        log = ROOT / buggy[f"{cid}__buggy"]["log"]
        src = MAIN75_CASES / cid / "buggy.bpf.c"
        repair = {rule: {src.name: row["repair_sites"][rule]} for rule in RULES}
        out.append(row_for("main75", cid, log, repair, n_code(read(src)), row["predictions"], src.name))
    return out


def wild_rows() -> list[dict]:
    d = json.loads(read(WILD))
    out = []
    for row in d["rows"]:
        if row.get("excluded"):
            continue
        cdir = WILD_CASES / f"{row['rank']:03d}"
        meta = json.loads(read(cdir / "meta.json"))
        code = sum(n_code(read(cdir / "parent" / rel)) for rel in meta["changed_files"] if (cdir / "parent" / rel).is_file())
        out.append(row_for("wild", str(row["rank"]), cdir / "buggy.log", row["repair_sites"], code,
                           row["predictions"], row["unit"]))
    return out


def summary(rows: list[dict]) -> dict:
    cov = [r for r in rows if r["kind"]]
    with_sites = [r for r in cov if r.get("sites")]
    s: dict = {"cases": len(rows), "covered": len(cov), "with_sites": len(with_sites),
               "by_kind": {k: sum(1 for r in cov if r["kind"] == k) for k in ("NullablePointer", "PacketBounds")}}
    for rule in RULES:
        k = sum(1 for r in with_sites if r["agrees"][rule])
        s[f"agree_{rule}"] = {"hits": k, "n": len(with_sites), "wilson95": wilson(k, len(with_sites))}
    s["mean_chance"] = round(sum(r["chance"] for r in with_sites) / len(with_sites), 4) if with_sites else None
    reps = sorted({rep for r in with_sites for rep in r["primary_on_state_site"]})
    s["context_primary_on_state_site"] = {rep: sum(1 for r in with_sites if r["primary_on_state_site"].get(rep))
                                          for rep in reps}
    return s


def main(argv: list[str] | None = None) -> int:
    rows = main75_rows() + wild_rows()
    payload = {
        "generator": "tools/score_state_oracle.py",
        "protocol": "docs/STATE-ORACLE.md",
        "summary": {c: summary([r for r in rows if r["corpus"] == c]) for c in ("main75", "wild")},
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")
    OUT_MD.write_text(render_md(payload), encoding="utf-8", newline="\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return 0


def frac(t: dict) -> str:
    ci = t["wilson95"]
    return f"{t['hits']}/{t['n']}" + (f" ({ci[0]:.2f}–{ci[1]:.2f})" if ci else "")


def render_md(p: dict) -> str:
    L = ["# Verifier-state oracle: agreement with the repair-site oracle", "",
         f"Rules `{p['protocol']}`. The state oracle is read from the buggy log only; the stop line is never one of its sites.",
         "Agreement: the two site sets share at least one line. Intervals: Wilson 95% over distinct cases.", "",
         "| corpus | cases | covered (NP / PB) | with sites | agree R0 | agree R1 | agree R2 | mean chance |",
         "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for c, s in p["summary"].items():
        bk = s["by_kind"]
        mc = "n/a" if s["mean_chance"] is None else f"{s['mean_chance']:.3f}"
        L.append(f"| {c} | {s['cases']} | {s['covered']} ({bk['NullablePointer']} / {bk['PacketBounds']}) | {s['with_sites']} | "
                 f"{frac(s['agree_R0'])} | {frac(s['agree_R1'])} | {frac(s['agree_R2'])} | {mc} |")
    L += ["", "Context only, not a ranking (rule 6): cases where a reporter's primary line is a state-oracle site.", "",
          "| corpus | " + " | ".join(sorted({r for s in p["summary"].values() for r in s["context_primary_on_state_site"]})) + " |"]
    reps = sorted({r for s in p["summary"].values() for r in s["context_primary_on_state_site"]})
    L.append("| --- | " + " | ".join("---:" for _ in reps) + " |")
    for c, s in p["summary"].items():
        L.append(f"| {c} | " + " | ".join(f"{s['context_primary_on_state_site'].get(r, 0)}/{s['with_sites']}" for r in reps) + " |")
    L += ["", "## Per case", "", "| corpus | case | kind | first loss | sites | agree R0 | note |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in p["rows"]:
        if not r["kind"]:
            continue
        fl = r.get("first_loss") or {}
        line = fl.get("line")
        loc = f"{line[0]}:{line[1]}" if line else "none"
        sites = ", ".join(f"{f}:{ln}" for f, ln in r.get("sites", [])) or "none"
        ag = r.get("agrees", {}).get("R0")
        L.append(f"| {r['corpus']} | `{r['case']}` | {r['kind']} | {loc} | {sites} | "
                 f"{'n/a' if ag is None else ('yes' if ag else 'no')} | {r['note']} |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())

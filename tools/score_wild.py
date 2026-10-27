#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score the included wild cases by the rules in docs/WILD-CORPUS-PROTOCOL.md.

Reads fixtures/wild/cases/<rank>/ (parent and fix versions of every changed
file, buggy.log, the reporter outputs stored beside it, meta.json) and
fixtures/wild/hand_check.tsv, and writes ``results/wild.{json,md}``: per
reporter, primary on a repair site, any label on a repair site and primary
within 3 lines, under R0, R1 and R2, per batch and pooled.

Usage: python tools/score_wild.py
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.bpfix_output import parse_bpfix  # noqa: E402
from bpfix_adversarial.oracle import code_line_mask  # noqa: E402
from bpfix_adversarial.repair_site import (  # noqa: E402
    diff_hunks,
    min_distance,
    repair_sites,
    repair_sites_r1,
    repair_sites_r2,
    wilson,
)
from bpfix_adversarial.reporters import CaseContext, registry  # noqa: E402
from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION  # noqa: E402
from tools.wild_replay import case_source  # noqa: E402

WILD = ROOT / "fixtures" / "wild"
CASES = WILD / "cases"
HAND = WILD / "hand_check.tsv"
OUT_JSON = ROOT / "results" / "wild.json"
OUT_MD = ROOT / "results" / "wild.md"
NEAR = 3
INFORMATIVE_CHANCE = 0.25
RULES = ("R0", "R1", "R2")
METRICS = ("primary_on_site", "label_on_site", "primary_within_3")
REGISTRY = registry()
REPORTERS = tuple(REGISTRY)


def batch_of(rank: int) -> str:
    return "batch 3" if rank >= 2000 else "batch 2" if rank >= 1000 else "batch 1"


BATCHES = ("batch 1", "batch 2", "batch 3")
CODES = ("included", "I3", "I4", "C", "E4", "E5")


def jsonl(p: Path) -> list[dict]:
    return [json.loads(ln) for ln in read(p).splitlines() if ln.strip()] if p.is_file() else []


def yields() -> dict:
    """Per batch: candidates, pass-1 survivors, screened, outcome codes (protocol, batch 3 item 7)."""
    from tools.wild_pass4 import final_outcome

    out: dict = {}
    b1 = {r["screen_rank"]: r for r in jsonl(WILD / "pass3.jsonl")}
    b1.update({r["screen_rank"]: {**r, "outcome": final_outcome(r)} for r in jsonl(WILD / "pass4.jsonl")})
    if (WILD / "pass5.jsonl").is_file():  # batch 1 rebuilt with the final build step replaces passes 3 and 4
        b1 = {r["screen_rank"]: r for r in jsonl(WILD / "pass5.jsonl")}
    layout = {"batch 1": (WILD / "candidates.json", WILD / "screen_files.jsonl", list(b1.values())),
              "batch 2": (WILD / "batch2/candidates.json", WILD / "batch2/screen_files.jsonl", jsonl(WILD / "batch2/build.jsonl")),
              "batch 3": (WILD / "batch3/candidates.json", WILD / "batch3/screen_files.jsonl", jsonl(WILD / "batch3/build.jsonl"))}
    for b, (cands, files, rows) in layout.items():
        if not cands.is_file():
            continue
        n = json.loads(read(cands))["n"]
        p1 = sum(1 for r in jsonl(files) if r["pass1"] == "bpf-c")
        codes = {c: sum(1 for r in rows if r["outcome"] == c) for c in CODES}
        out[b] = {"candidates": n, "pass1_survivors": p1, "screened": len(rows), "outcomes": codes,
                  "included_over_screened": wilson(codes["included"], len(rows)) and
                  {"rate": round(codes["included"] / len(rows), 4), "wilson95": wilson(codes["included"], len(rows))}}
    tot = {"candidates": sum(v["candidates"] for v in out.values()),
           "pass1_survivors": sum(v["pass1_survivors"] for v in out.values()),
           "screened": sum(v["screened"] for v in out.values()),
           "outcomes": {c: sum(v["outcomes"][c] for v in out.values()) for c in CODES}}
    k, m = tot["outcomes"]["included"], tot["screened"]
    tot["included_over_screened"] = {"rate": round(k / m, 4), "wilson95": wilson(k, m)} if m else None
    out["pooled"] = tot
    return out


def hand_checks() -> dict[int, dict]:
    if not HAND.is_file():
        return {}
    return {int(r["rank"]): r for r in csv.DictReader(HAND.open(encoding="utf-8"), delimiter="\t")}


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")


def file_sites(d: Path, changed: list[str]) -> tuple[dict, dict, bool]:
    """Sites per rule as {rule: {basename: [lines]}}, code-line count per basename, any semantic hunk."""
    sites: dict[str, dict[str, list[int]]] = {r: {} for r in RULES}
    code: dict[str, int] = {}
    semantic = False
    for rel in changed:
        pa, fx = d / "parent" / rel, d / "fix" / rel
        if not (pa.is_file() and fx.is_file()):
            continue  # added or deleted by the fix: no sites (rule 2)
        a, b = read(pa), read(fx)
        hunks = diff_hunks(a, b)
        semantic |= any(h.semantic for h in hunks)
        name = Path(rel).name
        for rule, s in (("R0", repair_sites(hunks)), ("R1", repair_sites_r1(a, hunks)), ("R2", repair_sites_r2(a, b))):
            sites[rule].setdefault(name, [])
            sites[rule][name] = sorted(set(sites[rule][name]) | set(s))
        code[name] = code.get(name, 0) + sum(code_line_mask([ln.rstrip() for ln in a.splitlines()]))
    return sites, code, semantic


def outcome(file: str | None, primary: int | None, labels: list[int], unit: str, sites: dict[str, list[int]]) -> dict:
    """Rule 3: a location is (file, line); labels without a file are in the primary's file."""
    f = Path(file).name if file else unit
    on = sites.get(f, [])
    dist = min_distance(primary, on)
    return {
        "file": f,
        "primary_on_site": primary is not None and primary in on,
        "label_on_site": (primary is not None and primary in on) or any(x in on for x in labels),
        "primary_within_3": dist is not None and dist <= NEAR,
        "distance": dist,
    }


def score_case(d: Path, hand: dict | None) -> dict:
    meta = json.loads(read(d / "meta.json"))
    rank = int(meta["screen_rank"])
    row: dict = {"rank": rank, "batch": batch_of(rank), "repo": meta["repo"], "commit": meta["commit"],
                 "program": meta["program"], "section": meta.get("section"), "build_type": meta.get("build_type")}
    if hand is None:
        row["excluded"] = "pending hand check"
        return row
    if hand["verdict"] != "ok":
        row["excluded"] = f"hand check: {hand['verdict']} ({hand.get('note', '')})"
        return row
    sites, code, semantic = file_sites(d, meta["changed_files"])
    if not semantic:
        row["excluded"] = "no-semantic-hunk"
        return row
    row["excluded"] = None
    src = case_source(d, meta)
    unit = src.name
    row["unit"] = unit
    row["repair_sites"] = sites
    n_code = sum(code.values())
    row["chance"] = {r: round(sum(len(v) for v in sites[r].values()) / n_code, 4) if n_code else 0.0 for r in RULES}
    row["informative"] = row["chance"]["R0"] < INFORMATIVE_CHANCE

    bp = d / "buggy.bpfix.txt"
    diag = parse_bpfix(read(bp)) if bp.is_file() else None
    obligation = UPSTREAM_ERROR_OBLIGATION.get((diag.error_id if diag else None) or "")
    row["bpfix_error_id"] = diag.error_id if diag else None
    row["upstream_obligation"] = obligation

    ctx = CaseContext(str(rank), src, d / "buggy.log", obligation)
    pred = {name: rep.predict(ctx) for name, rep in REGISTRY.items()}
    row["predictions"] = {n: {"file": p.file, "primary": p.primary, "labels": p.labels, "note": p.note}
                          for n, p in pred.items()}
    row["outcomes"] = {n: {r: outcome(p.file, p.primary, p.labels, unit, sites[r]) for r in RULES}
                       for n, p in pred.items()}
    return row


def tally(rows: list[dict], key) -> dict:
    k = sum(1 for r in rows if key(r))
    return {"hits": k, "n": len(rows), "wilson95": wilson(k, len(rows))}


def summarise(rows: list[dict]) -> dict:
    out: dict = {}
    for name, subset in (("all", rows), ("informative", [r for r in rows if r["informative"]])):
        out[name] = {rep: {rule: {m: tally(subset, lambda r, rep=rep, rule=rule, m=m: r["outcomes"][rep][rule][m])
                                  for m in METRICS} for rule in RULES} for rep in REPORTERS}
        out[name]["random_expected"] = {rule: round(sum(r["chance"][rule] for r in subset), 2) for rule in RULES}
        out[name]["n"] = len(subset)
    return out


def main(argv: list[str] | None = None) -> int:
    hand = hand_checks()
    dirs = sorted((p for p in CASES.iterdir() if (p / "meta.json").is_file()), key=lambda p: int(p.name))
    rows = [score_case(d, hand.get(int(d.name))) for d in dirs]
    scored = [r for r in rows if not r["excluded"]]
    groups = {"pooled": scored}
    for b in BATCHES:
        groups[b] = [r for r in scored if r["batch"] == b]
    payload = {
        "generator": "tools/score_wild.py",
        "protocol": "docs/WILD-CORPUS-PROTOCOL.md (scoring rules for the wild cases)",
        "n_cases": len(rows),
        "n_scored": len(scored),
        "excluded": [{"rank": r["rank"], "reason": r["excluded"]} for r in rows if r["excluded"]],
        "yield": yields(),
        "summary": {g: summarise(rs) for g, rs in groups.items()},
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
    L = ["# Wild cases on the cite pin", "",
         f"Rules `{p['protocol']}`. Included cases {p['n_cases']}; scored {p['n_scored']}.",
         "Oracle: lines of the developer's own parent → fix edit, per file. Intervals: Wilson 95% over distinct cases.", ""]
    L += ["## Yield per batch", "", "| batch | candidates | pass 1 | screened | " + " | ".join(CODES)
          + " | included / screened |", "| --- | " + " | ".join("---:" for _ in range(4 + len(CODES))) + " |"]
    for b, y in p["yield"].items():
        r = y["included_over_screened"]
        rate = f"{r['rate']:.3f} ({r['wilson95'][0]:.3f}–{r['wilson95'][1]:.3f})" if r else "n/a"
        L.append(f"| {b} | {y['candidates']} | {y['pass1_survivors']} | {y['screened']} | "
                 + " | ".join(str(y["outcomes"][c]) for c in CODES) + f" | {rate} |")
    L.append("")
    if p["excluded"]:
        L += ["Not scored: " + ", ".join(f"rank {e['rank']} ({e['reason']})" for e in p["excluded"]), ""]
    for g, s in p["summary"].items():
        if not s["all"]["n"]:
            continue
        L += [f"## Primary location on a repair site, {g} ({s['all']['n']} cases, {s['informative']['n']} informative)", "",
              "| reporter | R0 | R1 | R2 | any label R0 | within 3 R0 |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
        for rep in REPORTERS:
            t = s["all"][rep]
            L.append(f"| {rep} | " + " | ".join(frac(t[r]["primary_on_site"]) for r in RULES)
                     + f" | {frac(t['R0']['label_on_site'])} | {frac(t['R0']['primary_within_3'])} |")
        L.append("| uniform random (expected hits) | " + " | ".join(
            f"{s['all']['random_expected'][r]:.2f}" for r in RULES) + " | | |")
        L.append("")
    L += ["## Per case (R0)", "", "| rank | repo | program | " + " | ".join(REPORTERS) + " |",
          "| ---: | --- | --- | " + " | ".join("---" for _ in REPORTERS) + " |"]
    for r in p["rows"]:
        if r["excluded"]:
            continue
        cells = []
        for rep in REPORTERS:
            o, pr = r["outcomes"][rep]["R0"], r["predictions"][rep]
            loc = f"{o['file']}:{pr['primary']}" if pr["primary"] is not None else "none"
            cells.append(("**hit** " if o["primary_on_site"] else "") + loc)
        L.append(f"| {r['rank']} | {r['repo']} | `{r['program']}` | " + " | ".join(cells) + " |")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())

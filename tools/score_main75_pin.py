#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score the main75 pin capture by the rules in docs/MAIN75-PIN-PROTOCOL.md.

Reads one run directory written by lab/run_main75_pin.sh and writes
``results/main75_pin.{json,md}``:

* inclusion per case (buggy REJECT, fixed ACCEPT, at least one semantic hunk);
* per reporter (bpfix CLI, VerifierState, SourceComment, uniform random):
  primary on a repair site, any label on a repair site, primary within 3 lines,
  under the repair-site rules R0, R1 and R2, over all and informative cases;
* strata by upstream obligation and case kind; exact McNemar between reporters;
* metamorphic pairs (orig vs pad8 / pad32 / rename) for bpfix and VerifierState.

Usage: python tools/score_main75_pin.py --run campaigns/main75/lab/<run>
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.bpfix_output import parse_bpfix  # noqa: E402
from bpfix_adversarial.oracle import code_line_mask  # noqa: E402
from bpfix_adversarial.repair_site import (  # noqa: E402
    diff_hunks,
    mcnemar_exact,
    min_distance,
    repair_sites,
    repair_sites_r1,
    repair_sites_r2,
    wilson,
)
from bpfix_adversarial.reporters import CaseContext, registry  # noqa: E402
from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION  # noqa: E402

CASES = ROOT / "fixtures" / "upstream" / "bpfix-bench-cases"
VARIANTS = ROOT / "campaigns" / "v2" / "upstream"
OUT_JSON = ROOT / "results" / "main75_pin.json"
OUT_MD = ROOT / "results" / "main75_pin.md"
NEAR = 3
INFORMATIVE_CHANCE = 0.25
RULES = ("R0", "R1", "R2")
REGISTRY = registry()
REPORTERS = tuple(REGISTRY)
METRICS = ("primary_on_site", "label_on_site", "primary_within_3")


def case_kind(case_id: str) -> str:
    return "real-project seed" if case_id.startswith("rs_") else "canary"


def load_manifest(d: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for mf in sorted(d.glob("manifest.*.jsonl")):
        for line in mf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["case_id"]] = r
    return rows


def bpfix_for(log_rel: str):
    p = ROOT / (log_rel[: -len(".log")] + ".bpfix.txt")
    return parse_bpfix(p.read_text(encoding="utf-8", errors="replace")) if p.is_file() else None


def chance(code: list[int], sites: list[int]) -> float:
    return sum(1 for c in code if c in set(sites)) / len(code) if code else 0.0


def outcome(primary: int | None, labels: list[int], sites: list[int]) -> dict:
    dist = min_distance(primary, sites)
    return {
        "primary_on_site": primary is not None and primary in sites,
        "label_on_site": any(x in sites for x in labels) or (primary is not None and primary in sites),
        "primary_within_3": dist is not None and dist <= NEAR,
        "distance": dist,
    }


def tally(rows: list[dict], key) -> dict:
    k = sum(1 for r in rows if key(r))
    return {"hits": k, "n": len(rows), "wilson95": wilson(k, len(rows))}


def score_case(cid: str, buggy_m: dict, fixed_m: dict) -> dict:
    cdir = CASES / cid
    buggy = (cdir / "buggy.bpf.c").read_text(encoding="utf-8")
    fixed = (cdir / "fixed.bpf.c").read_text(encoding="utf-8")
    bm, fm = buggy_m.get(f"{cid}__buggy"), fixed_m.get(f"{cid}__fixed")
    hunks = diff_hunks(buggy, fixed)
    row: dict = {"case_id": cid, "kind": case_kind(cid)}

    reason = None
    if bm is None or bm["verdict"] == "COMPILE_FAIL":
        reason = "buggy-compile-fail"
    elif bm["verdict"] != "REJECT":
        reason = "buggy-accepts"
    elif fm is None or fm["verdict"] == "COMPILE_FAIL":
        reason = "fixed-compile-fail"
    elif fm["verdict"] != "ACCEPT":
        reason = "fixed-rejects"
    elif not any(h.semantic for h in hunks):
        reason = "no-semantic-hunk"
    row["excluded"] = reason
    if reason:
        return row

    sites = {"R0": repair_sites(hunks), "R1": repair_sites_r1(buggy, hunks), "R2": repair_sites_r2(buggy, fixed)}
    mask = code_line_mask([ln.rstrip() for ln in buggy.replace("\r\n", "\n").splitlines()])
    code = [i for i, c in enumerate(mask, 1) if c]
    row["repair_sites"] = sites
    row["chance"] = {r: round(chance(code, s), 4) for r, s in sites.items()}
    row["informative"] = row["chance"]["R0"] < INFORMATIVE_CHANCE

    diag = bpfix_for(bm["log"])
    obligation = UPSTREAM_ERROR_OBLIGATION.get((diag.error_id if diag else None) or "")
    row["bpfix_error_id"] = diag.error_id if diag else None
    row["upstream_obligation"] = obligation

    ctx = CaseContext(cid, cdir / "buggy.bpf.c", ROOT / bm["log"], obligation)
    pred = {name: rep.predict(ctx) for name, rep in REGISTRY.items()}
    row["predictions"] = {
        name: {"primary": p.primary, "labels": p.labels, "note": p.note} for name, p in pred.items()
    }
    row["outcomes"] = {
        name: {rule: outcome(p.primary, p.labels, sites[rule]) for rule in RULES} for name, p in pred.items()
    }
    return row


CONTROL = "StaleLine (control)"


def variant_pairs(rows: list[dict], var_m: dict[str, dict]) -> dict:
    """orig vs pad8 / pad32 / rename for every reporter, R0 sites mapped per variant.

    ``StaleLine (control)`` is a positive control: in the variant it repeats
    bpfix's primary line number from the original, unmapped. It must lose hits
    wherever a transform moves the repair site; if it did not, the pair test
    could not see movement.
    """
    out: dict = {}
    for variant in ("pad8", "pad32", "rename"):
        per_rep: dict = {}
        for rep in (*REPORTERS, CONTROL):
            pairs, excluded = [], []
            for r in rows:
                if r.get("excluded"):
                    continue
                tf_p = VARIANTS / r["case_id"] / "transform.json"
                if not tf_p.is_file():
                    continue
                tf = json.loads(tf_p.read_text(encoding="utf-8"))
                if variant not in tf["variants"]:
                    continue
                o_m = var_m.get(f"{r['case_id']}__orig")
                v_m = var_m.get(f"{r['case_id']}__{variant}")
                if not o_m or not v_m or o_m["verdict"] != "REJECT" or v_m["verdict"] != "REJECT":
                    excluded.append({"case_id": r["case_id"],
                                     "reason": f"orig {o_m and o_m['verdict']} / {variant} {v_m and v_m['verdict']}"})
                    continue
                tv = tf["variants"][variant]
                o_sites, v_sites = tf["variants"]["orig"]["repair_sites"], tv["repair_sites"]
                cdir = VARIANTS / r["case_id"]
                ob = r.get("upstream_obligation")
                ctx_o = CaseContext(r["case_id"], cdir / "orig.bpf.c", ROOT / o_m["log"], ob)
                ctx_v = CaseContext(r["case_id"], cdir / f"{variant}.bpf.c", ROOT / v_m["log"], ob)
                if rep == CONTROL:
                    op = REGISTRY["bpfix"].predict(ctx_o).primary
                    vp = op
                else:
                    op = REGISTRY[rep].predict(ctx_o).primary
                    vp = REGISTRY[rep].predict(ctx_v).primary
                shift_from, shift = tv.get("shift_from"), tv.get("shift", 0)
                mapped = op + shift if (op is not None and shift_from is not None and op >= shift_from) else op
                pairs.append({
                    "case_id": r["case_id"],
                    "orig_on_site": op is not None and op in o_sites,
                    "variant_on_site": vp is not None and vp in v_sites,
                    "primary_moved": vp != mapped,
                })
            lost = sum(1 for p in pairs if p["orig_on_site"] and not p["variant_on_site"])
            gained = sum(1 for p in pairs if not p["orig_on_site"] and p["variant_on_site"])
            moved = sum(1 for p in pairs if p["primary_moved"])
            per_rep[rep] = {
                "pairs": len(pairs),
                "orig_on_site": sum(1 for p in pairs if p["orig_on_site"]),
                "variant_on_site": sum(1 for p in pairs if p["variant_on_site"]),
                "lost": lost,
                "gained": gained,
                "mcnemar_p": mcnemar_exact(lost, gained),
                "primary_moved": moved,
                "primary_moved_wilson95": wilson(moved, len(pairs)),
                "excluded": excluded,
                "rows": pairs,
            }
        out[variant] = per_rep
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args(argv)
    run = args.run if args.run.is_absolute() else ROOT / args.run

    buggy_m, fixed_m, var_m = (load_manifest(run / d) for d in ("buggy", "fixed", "variants"))
    case_ids = sorted(p.name for p in CASES.iterdir() if p.is_dir())
    rows = [score_case(cid, buggy_m, fixed_m) for cid in case_ids]
    scored = [r for r in rows if not r["excluded"]]
    informative = [r for r in scored if r["informative"]]

    summary: dict = {}
    for subset_name, subset in (("all", scored), ("informative", informative)):
        summary[subset_name] = {
            rep: {
                rule: {m: tally(subset, lambda r, rep=rep, rule=rule, m=m: r["outcomes"][rep][rule][m]) for m in METRICS}
                for rule in RULES
            }
            for rep in REPORTERS
        }
        summary[subset_name]["random_expected"] = {
            rule: round(sum(r["chance"][rule] for r in subset), 2) for rule in RULES
        }

    strata: dict = {}
    for key in ("upstream_obligation", "kind"):
        groups: dict[str, list[dict]] = defaultdict(list)
        for r in scored:
            groups[r[key] or "unmapped"].append(r)
        strata[key] = {
            g: {rep: tally(rs, lambda r, rep=rep: r["outcomes"][rep]["R0"]["primary_on_site"]) for rep in REPORTERS}
            | {"bpfix_any_label": tally(rs, lambda r: r["outcomes"]["bpfix"]["R0"]["label_on_site"])}
            for g, rs in sorted(groups.items())
        }

    mcnemar: dict = {}
    for a, b in (("bpfix", "VerifierState"), ("bpfix", "SourceComment"), ("VerifierState", "SourceComment")):
        per_rule = {}
        for rule in RULES:
            ab = sum(1 for r in scored if r["outcomes"][a][rule]["primary_on_site"] and not r["outcomes"][b][rule]["primary_on_site"])
            ba = sum(1 for r in scored if r["outcomes"][b][rule]["primary_on_site"] and not r["outcomes"][a][rule]["primary_on_site"])
            per_rule[rule] = {f"{a}_only": ab, f"{b}_only": ba, "p": mcnemar_exact(ab, ba)}
        mcnemar[f"{a}_vs_{b}"] = per_rule

    pairs = variant_pairs(rows, var_m)
    payload = {
        "generator": "tools/score_main75_pin.py",
        "protocol": "docs/MAIN75-PIN-PROTOCOL.md",
        "run": run.relative_to(ROOT).as_posix(),
        "harness_commit": (run / "harness-commit.txt").read_text(encoding="utf-8").strip()
        if (run / "harness-commit.txt").is_file() else None,
        "n_cases": len(rows),
        "n_scored": len(scored),
        "n_informative": len(informative),
        "excluded": [{"case_id": r["case_id"], "reason": r["excluded"]} for r in rows if r["excluded"]],
        "summary": summary,
        "strata": strata,
        "mcnemar_primary_on_site": mcnemar,
        "metamorphic": {v: {rep: {k: x for k, x in d.items() if k != "rows"} for rep, d in per.items()}
                        for v, per in pairs.items()},
        "rows": rows,
        "metamorphic_rows": {v: {rep: d["rows"] for rep, d in per.items()} for v, per in pairs.items()},
    }
    OUT_JSON.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")
    OUT_MD.write_text(render_md(payload), encoding="utf-8", newline="\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return 0


def frac(t: dict) -> str:
    ci = t["wilson95"]
    return f"{t['hits']}/{t['n']}" + (f" ({ci[0]:.2f}–{ci[1]:.2f})" if ci else "")


def render_md(p: dict) -> str:
    s = p["summary"]
    L = [
        "# main75 on the cite pin",
        "",
        f"Run `{p['run']}` · harness `{(p['harness_commit'] or '?')[:7]}` · rules `{p['protocol']}`.",
        f"Cases {p['n_cases']}; scored {p['n_scored']}; informative (R0 chance < {INFORMATIVE_CHANCE}) {p['n_informative']}.",
        "Oracle: lines of upstream's own buggy → fixed edit. Intervals: Wilson 95% over distinct cases.",
        "",
    ]
    if p["excluded"]:
        L += ["Excluded: " + ", ".join(f"`{e['case_id']}` ({e['reason']})" for e in p["excluded"]), ""]
    for subset in ("all", "informative"):
        L += [f"## Primary location on a repair site ({subset} cases)", "",
              "| reporter | R0 | R1 | R2 |", "| --- | ---: | ---: | ---: |"]
        for rep in REPORTERS:
            L.append(f"| {rep} | " + " | ".join(frac(s[subset][rep][r]["primary_on_site"]) for r in RULES) + " |")
        L.append("| uniform random (expected hits) | " + " | ".join(
            f"{s[subset]['random_expected'][r]:.1f}" for r in RULES) + " |")
        L += ["", f"bpfix, any label on a repair site ({subset}): " + ", ".join(
            f"{r} {frac(s[subset]['bpfix'][r]['label_on_site'])}" for r in RULES)
            + f"; primary within {NEAR} lines: " + ", ".join(
            f"{r} {frac(s[subset]['bpfix'][r]['primary_within_3'])}" for r in RULES), ""]
    for key, title in (("kind", "case kind"), ("upstream_obligation", "upstream obligation")):
        L += [f"## By {title} (R0, all cases)", "",
              f"| {title} | bpfix primary | bpfix any label | VerifierState | SourceComment |",
              "| --- | ---: | ---: | ---: | ---: |"]
        for g, t in p["strata"][key].items():
            L.append(f"| {g} | {frac(t['bpfix'])} | {frac(t['bpfix_any_label'])} | "
                     f"{frac(t['VerifierState'])} | {frac(t['SourceComment'])} |")
        L.append("")
    L += ["## Exact McNemar, primary on a repair site", "", "| pair | rule | only first | only second | p |",
          "| --- | --- | ---: | ---: | ---: |"]
    for pair, per in p["mcnemar_primary_on_site"].items():
        for rule, d in per.items():
            vals = list(d.values())
            L.append(f"| {pair.replace('_vs_', ' vs ')} | {rule} | {vals[0]} | {vals[1]} | "
                     f"{'n/a' if vals[2] is None else f'{vals[2]:.4f}'} |")
    L += ["", "## Metamorphic pairs (R0 sites mapped into each variant)", "",
          "| variant | reporter | pairs | orig on site | variant on site | lost | gained | McNemar p | primary moved |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for v, per in p["metamorphic"].items():
        for rep, d in per.items():
            mp = "n/a" if d["mcnemar_p"] is None else f"{d['mcnemar_p']:.4f}"
            ci = d["primary_moved_wilson95"]
            moved = f"{d['primary_moved']}/{d['pairs']}" + (f" ({ci[0]:.2f}–{ci[1]:.2f})" if ci else "")
            L.append(f"| {v} | {rep} | {d['pairs']} | {d['orig_on_site']} | {d['variant_on_site']} | "
                     f"{d['lost']} | {d['gained']} | {mp} | {moved} |")
    excl = [(v, e) for v, per in p["metamorphic"].items() for e in per["bpfix"]["excluded"]]
    if excl:
        L += ["", "Metamorphic pairs excluded: " + "; ".join(f"`{e['case_id']}` {v} ({e['reason']})" for v, e in excl)]
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    sys.exit(main())

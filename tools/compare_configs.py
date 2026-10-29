#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare main75 results between the cite pin and a second configuration.

Rules: docs/MAIN75-PIN-PROTOCOL.md Section 8. Reads results/main75_pin.json and
results/main75_rewrites.json (the pin) and the same files tagged with the second
configuration (results/main75_pin.<tag>.json, results/main75_rewrites.<tag>.json),
and writes results/cross_config.{json,md}:

* inclusion on each host, and the cases included on one host only;
* on cases included on both hosts: hits per reporter and rule on each host, with
  the paired exact McNemar test between hosts, and how often each reporter names
  the same primary line on both hosts;
* the Section 3.2 and 3.4 claims of the paper, each evaluated by the same
  predicate on each host's own results and reported as holding or not.

Usage: python tools/compare_configs.py --tag testbed-b
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.repair_site import mcnemar_exact  # noqa: E402

RESULTS = ROOT / "results"
RULES = ("R0", "R1", "R2")
REPORTERS = ("bpfix", "VerifierState", "SourceComment", "PrettyVerifier", "PREVAIL")
REWRITES = ("VPADC", "MACRO", "INLINE")


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def hits(res: dict, rep: str, rule: str = "R0", metric: str = "primary_on_site") -> int:
    return res["summary"]["all"][rep][rule][metric]["hits"]


def mc(res: dict, a: str, b: str, rule: str = "R0") -> tuple[int, int, float | None]:
    key = f"{a}_vs_{b}"
    if key in res["mcnemar_primary_on_site"]:
        d = res["mcnemar_primary_on_site"][key][rule]
        return d[f"{a}_only"], d[f"{b}_only"], d["p"]
    d = res["mcnemar_primary_on_site"][f"{b}_vs_{a}"][rule]
    return d[f"{a}_only"], d[f"{b}_only"], d["p"]


def claims(res: dict, rw: dict) -> list[tuple[str, str, bool]]:
    """The paper's Section 3.2 and 3.4 claims as predicates on one host's results."""
    out = []
    rnd = res["summary"]["all"]["random_expected"]
    locating = [r for r in REPORTERS if r != "SourceComment"]
    for rule in RULES:
        above = all(hits(res, r, rule) >= 2 * rnd[rule] for r in locating)
        out.append((f"the four locating reporters at least twice the random line ({rule})",
                    ", ".join(f"{r} {hits(res, r, rule)}" for r in locating) + f"; random {rnd[rule]}", above))
    for rule in RULES:
        sc = hits(res, "SourceComment", rule)
        out.append((f"SourceComment less than twice the random line ({rule})", f"{sc}; random {rnd[rule]}",
                    sc < 2 * rnd[rule]))
    for rule in RULES:
        a, b, _ = mc(res, "bpfix", "VerifierState", rule)
        out.append((f"bpfix and VerifierState tie ({rule})", f"discordant {a} / {b}", a == 0 and b == 0))
    for rule in RULES:
        a, b, p = mc(res, "bpfix", "PrettyVerifier", rule)
        out.append((f"bpfix above Pretty Verifier, p < 0.05 ({rule})", f"{a} / {b}, p = {p}",
                    a > b and p is not None and p < 0.05))
    for rule in RULES:
        a, b, p = mc(res, "bpfix", "PREVAIL", rule)
        out.append((f"bpfix and PREVAIL not significantly different ({rule})", f"{a} / {b}, p = {p}",
                    p is None or p >= 0.05))
    for rule in RULES:
        ps = [mc(res, other, "SourceComment", rule) for other in REPORTERS if other != "SourceComment"]
        ok = all(a > b and p is not None and p < 0.001 for a, b, p in ps)
        out.append((f"SourceComment below every other reporter, p < 0.001 ({rule})",
                    "; ".join(f"{a} / {b}, p = {p}" for a, b, p in ps), ok))
    for rule in RULES:
        arrow, label = hits(res, "bpfix", rule), hits(res, "bpfix", rule, "label_on_site")
        out.append((f"bpfix labels reach more repair sites than its arrow ({rule})", f"{arrow} vs {label}",
                    label > arrow))
    np_ = res["strata"]["upstream_obligation"].get("NullablePointer", {})
    if np_:
        arrow, label = np_["bpfix"]["hits"], np_["bpfix_any_label"]["hits"]
        out.append(("NullablePointer: labels well above arrow (R0)", f"{arrow} vs {label} of {np_['bpfix']['n']}",
                    label >= 2 * max(arrow, 1)))
    for v in ("pad8", "pad32", "rename"):
        per = res["metamorphic"][v]
        lost = {r: per[r]["lost"] for r in ("bpfix", "VerifierState", "PrettyVerifier", "PREVAIL")}
        out.append((f"{v}: the four locating reporters lose no hit", str(lost), not any(lost.values())))
    for v in ("pad8", "pad32"):
        c = res["metamorphic"][v]["StaleLine (control)"]
        out.append((f"{v}: the control loses all its hits", f"{c['lost']} of {c['orig_on_site']}",
                    c["orig_on_site"] > 0 and c["lost"] == c["orig_on_site"]))
    for rid in ("MACRO", "INLINE"):
        s = rw["rewrites"][rid]["summary"]
        ch = {r: s[r]["lost"] + s[r]["gained"] for r in ("bpfix", "VerifierState", "PrettyVerifier", "PREVAIL")}
        out.append((f"{rid}: no hit changes for the four locating reporters (R0)", str(ch), not any(ch.values())))
    s = rw["rewrites"]["VPADC"]["summary"]
    moved = {r: s[r].get("lost_primary_moved", 0) for r in ("bpfix", "VerifierState", "PrettyVerifier", "PREVAIL")}
    out.append(("VPADC: every lost hit is with the primary line unmoved", str(moved), not any(moved.values())))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args(argv)
    a, b = load("main75_pin.json"), load(f"main75_pin.{args.tag}.json")
    rwa, rwb = load("main75_rewrites.json"), load(f"main75_rewrites.{args.tag}.json")

    rows_a = {r["case_id"]: r for r in a["rows"]}
    rows_b = {r["case_id"]: r for r in b["rows"]}
    both = sorted(c for c in rows_a if not rows_a[c]["excluded"] and c in rows_b and not rows_b[c]["excluded"])
    one = [{"case_id": c, "pin": rows_a[c]["excluded"] or "scored", args.tag: rows_b.get(c, {}).get("excluded", "absent")
            or "scored"} for c in sorted(set(rows_a) | set(rows_b))
           if bool(rows_a.get(c, {}).get("excluded", True)) != bool(rows_b.get(c, {}).get("excluded", True))]

    paired: dict = {}
    for rep in REPORTERS:
        paired[rep] = {}
        for rule in RULES:
            ha = [rows_a[c]["outcomes"][rep][rule]["primary_on_site"] for c in both]
            hb = [rows_b[c]["outcomes"][rep][rule]["primary_on_site"] for c in both]
            only_a = sum(x and not y for x, y in zip(ha, hb))
            only_b = sum(y and not x for x, y in zip(ha, hb))
            paired[rep][rule] = {"pin": sum(ha), args.tag: sum(hb), "pin_only": only_a, f"{args.tag}_only": only_b,
                                 "p": mcnemar_exact(only_a, only_b)}
        same = sum(rows_a[c]["predictions"][rep]["primary"] == rows_b[c]["predictions"][rep]["primary"] for c in both)
        paired[rep]["same_primary"] = same

    ca, cb = claims(a, rwa), claims(b, rwb)
    claim_rows = [{"claim": x[0], "pin": x[1], "pin_holds": x[2], args.tag: y[1], f"{args.tag}_holds": y[2]}
                  for x, y in zip(ca, cb)]

    payload = {"generator": "tools/compare_configs.py", "protocol": "docs/MAIN75-PIN-PROTOCOL.md Section 8",
               "tag": args.tag, "runs": {"pin": a["run"], args.tag: b["run"],
                                          "pin_rewrites": rwa["run"], f"{args.tag}_rewrites": rwb["run"]},
               "scored": {"pin": a["n_scored"], args.tag: b["n_scored"], "both": len(both)},
               "included_on_one_host": one, "paired": paired, "claims": claim_rows}
    out_json, out_md = RESULTS / "cross_config.json", RESULTS / "cross_config.md"
    out_json.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")

    t = args.tag
    L = ["# main75 on two configurations", "",
         f"Rules `{payload['protocol']}`. Pin run `{a['run']}`; {t} run `{b['run']}`.",
         f"Scored: pin {a['n_scored']}, {t} {b['n_scored']}, both {len(both)}.", ""]
    if one:
        L += ["## Included on one host only", "", f"| case | pin | {t} |", "| --- | --- | --- |"]
        L += [f"| `{r['case_id']}` | {r['pin']} | {r[t]} |" for r in one]
        L.append("")
    L += [f"## Primary location on a repair site, cases scored on both hosts ({len(both)})", "",
          f"| reporter | rule | pin | {t} | pin only | {t} only | McNemar p | same primary line |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for rep in REPORTERS:
        for rule in RULES:
            d = paired[rep][rule]
            p = "n/a" if d["p"] is None else f"{d['p']:.4f}"
            same = f"{paired[rep]['same_primary']}/{len(both)}" if rule == "R0" else ""
            L.append(f"| {rep} | {rule} | {d['pin']} | {d[t]} | {d['pin_only']} | {d[f'{t}_only']} | {p} | {same} |")
    L += ["", "## Claims of Sections 3.2 and 3.4, evaluated on each host's own results", "",
          f"| claim | pin | holds | {t} | holds |", "| --- | --- | --- | --- | --- |"]
    for r in claim_rows:
        L.append(f"| {r['claim']} | {r['pin']} | {'yes' if r['pin_holds'] else 'no'} | {r[t]} | "
                 f"{'yes' if r[f'{t}_holds'] else 'no'} |")
    L.append("")
    out_md.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"wrote {out_json.relative_to(ROOT)} and {out_md.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

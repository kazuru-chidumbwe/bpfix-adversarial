#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score the verifier-visible rewrites (docs/MAIN75-PIN-PROTOCOL.md Section 7).

For every rewrite and case: the rewritten pair is valid only if the rewritten
buggy REJECTS and the rewritten fixed ACCEPTS on the pin. On valid pairs, every
registered reporter is scored against the repair sites recomputed from the
rewritten pair (R0) and compared, paired, with its result on the original pair
(results/main75_pin.json). ``StaleLine (control)`` repeats bpfix's original
primary line number unmapped. Writes results/main75_rewrites.{json,md}.

Usage: python tools/score_main75_rewrites.py --run campaigns/n3/lab/<run>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.reporters import CaseContext, registry  # noqa: E402
from bpfix_adversarial.repair_site import diff_hunks, mcnemar_exact, repair_sites, wilson  # noqa: E402
from tools.gen_main75_rewrites import REWRITES, counterpart  # noqa: E402

N3 = ROOT / "campaigns" / "n3"
CASES = ROOT / "fixtures" / "upstream" / "bpfix-bench-cases"
MAIN = ROOT / "results" / "main75_pin.json"
OUT_JSON = ROOT / "results" / "main75_rewrites.json"
OUT_MD = ROOT / "results" / "main75_rewrites.md"
CONTROL = "StaleLine (control)"
REGISTRY = registry()


def load_manifest(d: Path) -> dict[str, dict]:
    rows: dict[str, dict] = {}
    for mf in sorted(d.glob("manifest.*.jsonl")):
        for line in mf.read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["case_id"]] = r
    return rows


def lines_of(p: Path) -> list[str]:
    return p.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args(argv)
    run = args.run if args.run.is_absolute() else ROOT / args.run
    man = load_manifest(run / "rewrites")
    main75 = {r["case_id"]: r for r in json.loads(MAIN.read_text(encoding="utf-8"))["rows"]}
    meta = json.loads((N3 / "rewrites.json").read_text(encoding="utf-8"))
    reporters = (*REGISTRY, CONTROL)

    per_rewrite: dict = {}
    for rid in REWRITES:
        valid, invalid = [], []
        for cid, row in sorted(meta["cases"].items()):
            if not row[rid]["applied"] or main75.get(cid, {}).get("excluded", True):
                continue
            bm, fm = man.get(f"{cid}__{rid}.buggy"), man.get(f"{cid}__{rid}.fixed")
            vb, vf = (bm or {}).get("verdict"), (fm or {}).get("verdict")
            if vb != "REJECT" or vf != "ACCEPT":
                invalid.append({"case_id": cid, "buggy": vb, "fixed": vf})
                continue
            src_b, src_f = N3 / cid / f"{rid}.buggy.bpf.c", N3 / cid / f"{rid}.fixed.bpf.c"
            sites = repair_sites(diff_hunks(src_b.read_text(encoding="utf-8"), src_f.read_text(encoding="utf-8")))
            orig_lines = lines_of(CASES / cid / "buggy.bpf.c")
            new_lines = lines_of(src_b)
            ctx = CaseContext(cid, src_b, ROOT / bm["log"], main75[cid]["upstream_obligation"])
            res: dict = {"case_id": cid, "repair_sites": sites, "by_reporter": {}}
            for rep in reporters:
                if rep == CONTROL:
                    op = main75[cid]["predictions"]["bpfix"]["primary"]
                    hit = main75[cid]["outcomes"]["bpfix"]["R0"]["primary_on_site"]
                    orig = {"primary_on_site": hit, "label_on_site": hit}  # the control has no labels
                    vp, vlabels = op, []
                else:
                    op = main75[cid]["predictions"][rep]["primary"]
                    orig = main75[cid]["outcomes"][rep]["R0"]
                    pred = REGISTRY[rep].predict(ctx)
                    vp, vlabels = pred.primary, pred.labels
                c = counterpart(orig_lines, new_lines, op - 1) if op else None
                mapped = c + 1 if c is not None else None
                res["by_reporter"][rep] = {
                    "orig_on_site": orig["primary_on_site"],
                    "rewrite_on_site": vp is not None and vp in sites,
                    "orig_label_on_site": orig["label_on_site"],
                    "rewrite_label_on_site": (vp is not None and vp in sites) or any(x in sites for x in vlabels),
                    "primary": vp,
                    "primary_moved": (vp != mapped) if mapped is not None else (vp is not None),
                }
            valid.append(res)
        summary = {}
        for rep in reporters:
            rs = [v["by_reporter"][rep] for v in valid]
            lost = sum(1 for r in rs if r["orig_on_site"] and not r["rewrite_on_site"])
            gained = sum(1 for r in rs if not r["orig_on_site"] and r["rewrite_on_site"])
            moved = sum(1 for r in rs if r["primary_moved"])
            l_lost = sum(1 for r in rs if r["orig_label_on_site"] and not r["rewrite_label_on_site"])
            l_gained = sum(1 for r in rs if not r["orig_label_on_site"] and r["rewrite_label_on_site"])
            # A lost hit whose primary did not move means the rewrite moved the repair site away from an
            # unchanged report (e.g. padding between an inserted check and the stop statement).
            lost_unmoved = sum(1 for r in rs if r["orig_on_site"] and not r["rewrite_on_site"] and not r["primary_moved"])
            summary[rep] = {"pairs": len(rs), "orig_on_site": sum(1 for r in rs if r["orig_on_site"]),
                            "rewrite_on_site": sum(1 for r in rs if r["rewrite_on_site"]),
                            "lost": lost, "gained": gained, "mcnemar_p": mcnemar_exact(lost, gained),
                            "lost_primary_unmoved": lost_unmoved, "lost_primary_moved": lost - lost_unmoved,
                            "label_orig_on_site": sum(1 for r in rs if r["orig_label_on_site"]),
                            "label_rewrite_on_site": sum(1 for r in rs if r["rewrite_label_on_site"]),
                            "label_lost": l_lost, "label_gained": l_gained,
                            "label_mcnemar_p": mcnemar_exact(l_lost, l_gained),
                            "primary_moved": moved, "primary_moved_wilson95": wilson(moved, len(rs))}
        per_rewrite[rid] = {"applied": meta["applied"][rid], "valid": len(valid), "invalid": invalid,
                            "summary": summary, "rows": valid}

    payload = {"generator": "tools/score_main75_rewrites.py", "protocol": "docs/MAIN75-PIN-PROTOCOL.md Section 7",
               "run": run.relative_to(ROOT).as_posix(), "rewrites": per_rewrite}
    OUT_JSON.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8", newline="\n")

    L = ["# Verifier-visible rewrites of main75 on the cite pin", "",
         f"Run `{payload['run']}` · rules `{payload['protocol']}`. A rewritten pair is valid when the rewritten "
         "buggy REJECTS and the rewritten fixed ACCEPTS. Repair sites are recomputed from the rewritten pair (R0).", "",
         "| rewrite | applied | valid | invalid |", "| --- | ---: | ---: | ---: |"]
    for rid, d in per_rewrite.items():
        L.append(f"| {rid} | {d['applied']} | {d['valid']} | {len(d['invalid'])} |")
    L += ["", "Primary location: on-site count before and after the rewrite, paired McNemar. Any label: the same for "
          "the primary or any labelled line. `orig` is the reporter's count on the applicable cases before the rewrite.", "",
          "| rewrite | reporter | pairs | primary orig → rewrite | lost / gained | p | any label orig → rewrite | lost / gained | p | primary moved |",
          "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]

    def pv(x):
        return "n/a" if x is None else f"{x:.4f}"

    for rid, d in per_rewrite.items():
        for rep, s in d["summary"].items():
            if not s["pairs"]:
                continue
            ci = s["primary_moved_wilson95"]
            moved = f"{s['primary_moved']}/{s['pairs']}" + (f" ({ci[0]:.2f}–{ci[1]:.2f})" if ci else "")
            L.append(f"| {rid} | {rep} | {s['pairs']} | {s['orig_on_site']} → {s['rewrite_on_site']} | "
                     f"{s['lost']} / {s['gained']} | {pv(s['mcnemar_p'])} | "
                     f"{s['label_orig_on_site']} → {s['label_rewrite_on_site']} | "
                     f"{s['label_lost']} / {s['label_gained']} | {pv(s['label_mcnemar_p'])} | {moved} |")
    L += ["", "Lost primary hits by mechanism: *unmoved* = the reporter's line is the same statement as before "
          "and the rewrite moved the repair site away from it; *moved* = the reporter's line changed.", "",
          "| rewrite | reporter | lost | unmoved | moved |", "| --- | --- | ---: | ---: | ---: |"]
    for rid, d in per_rewrite.items():
        for rep, s in d["summary"].items():
            if s["lost"]:
                L.append(f"| {rid} | {rep} | {s['lost']} | {s['lost_primary_unmoved']} | {s['lost_primary_moved']} |")
    inv = [(rid, x) for rid, d in per_rewrite.items() for x in d["invalid"]]
    if inv:
        L += ["", "Invalid pairs: " + "; ".join(f"{rid} `{x['case_id']}` (buggy {x['buggy']}, fixed {x['fixed']})"
                                              for rid, x in inv)]
    OUT_MD.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

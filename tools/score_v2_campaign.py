#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score a campaign v2 capture (see campaigns/v2/README.md, docs/LAB-RUN-V2.md).

Inputs (from tools/capture_local.py then tools/replay_bpfix_dir.py):
  --captured DIR            templates: campaigns/v2/mutants/** captured on one host
  --upstream-captured DIR   optional: campaigns/v2/upstream/*/*.bpf.c captured on the same host

Outputs, under --out: v2_scores.json and v2_scores.md.

Sections
  A. RenameReject pairs: does renaming the uncredited check's identifier change
     bpfix's rendered diagnostic? Compares error ID, `-->` line, and the set of
     (line, kind, message) labels with source text and file names removed.
  B. Surviving padding (VolatilePad, ProvenanceMap): processed instructions must
     grow with the pad (else the pad was compiled away), plus the verifier stop
     site and bpfix's `-->` / labels against the injection span.
  C. Upstream metamorphic: repair-site agreement on orig vs pad8 / pad32 / rename,
     with exact McNemar tests on the paired primary_in_repair outcomes.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.bpfix_output import parse_bpfix, structure_key  # noqa: E402
from bpfix_adversarial.gen_v2 import rename_reject_cases  # noqa: E402
from bpfix_adversarial.oracle import oracle_sites  # noqa: E402
from bpfix_adversarial.repair_site import mcnemar_exact, wilson  # noqa: E402
from bpfix_adversarial.upstream_corpus import UPSTREAM_ERROR_OBLIGATION  # noqa: E402
from tools.score_sc_vs_honesty import vs_stop_line  # noqa: E402

PAD_RE = re.compile(r"^(?P<prefix>[A-Z]+)-pad(?P<pad>\d+)$")


def load_capture(captured: Path) -> tuple[str, dict[str, dict]]:
    ms = sorted(captured.glob("manifest.*.jsonl"))
    if not ms:
        raise SystemExit(f"no manifest.*.jsonl in {captured}")
    manifest = ms[-1]
    stamp = manifest.name.split(".")[1]
    rows = {}
    for ln in manifest.read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        log = captured / Path(r["log"]).name
        r["_log_text"] = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
        bf = captured / f"{r['case_id']}.{stamp}.bpfix.txt"
        r["_bpfix"] = parse_bpfix(bf.read_text(encoding="utf-8")) if bf.is_file() else None
        rows[r["case_id"]] = r
    return stamp, rows


def env_summary(captured: Path) -> str:
    envs = sorted(captured.glob("env.*.txt"))
    if not envs:
        return "unknown host"
    kv = dict(ln.split("=", 1) for ln in envs[-1].read_text(encoding="utf-8").splitlines() if "=" in ln)
    return f"{kv.get('label') or '?'} · kernel {kv.get('uname_r', '?')} · {kv.get('clang', '?')} · {kv.get('bpftool', '?')}"


# ---------------------------------------------------------------- A. rename


def score_rename(rows: dict[str, dict]) -> list[dict]:
    pairs: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for case_id, construct, name, pair in rename_reject_cases():
        pairs[pair].append((case_id, construct, name))
    out = []
    for pair, members in sorted(pairs.items()):
        (a_id, construct, a_name), (b_id, _, b_name) = members
        a, b = rows.get(a_id), rows.get(b_id)
        rec = {"pair": pair, "construct": construct, "listed": a_name, "idiomatic": b_name,
               "verdicts": [a and a["verdict"], b and b["verdict"]]}
        if not a or not b or not a["_bpfix"] or not b["_bpfix"]:
            rec["status"] = "missing capture or bpfix output"
            out.append(rec)
            continue
        da, db = a["_bpfix"], b["_bpfix"]
        sa, sb = structure_key(da), structure_key(db)
        la, lb = {tuple(x) for x in sa["labels"]}, {tuple(x) for x in sb["labels"]}
        check_line = None
        src = ROOT / a["src"]
        if src.is_file():
            for i, ln in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
                if re.match(rf"\s*if \(!{re.escape(a_name)}\)", ln):
                    check_line = i
                    break
        rec.update({
            "status": "ok",
            "error_ids": [da.error_id, db.error_id],
            "primary": [da.primary_raw, db.primary_raw],
            "primary_equal": da.primary_raw == db.primary_raw,
            "error_equal": da.error_id == db.error_id,
            "structure_equal": sa == sb,
            "labels_only_listed": sorted(la - lb),
            "labels_only_idiomatic": sorted(lb - la),
            "check_line": check_line,
            "check_line_labelled": [check_line in da.label_lines, check_line in db.label_lines],
        })
        out.append(rec)
    return out


# ---------------------------------------------------------------- B. pads


def score_pads(rows: dict[str, dict]) -> list[dict]:
    groups: dict[str, list[dict]] = defaultdict(list)
    for case_id, r in rows.items():
        m = PAD_RE.match(case_id)
        if not m:
            continue
        src = ROOT / r["src"]
        sites = oracle_sites(src) if src.is_file() else {}
        span = set(sites.get("oracle_loss_span") or [])
        loss = sites.get("oracle_loss_code")
        if loss is not None:
            span.add(loss)
        vs_line, _, _ = vs_stop_line(r["_log_text"]) if r["verdict"] == "REJECT" else (None, None, None)
        d = r["_bpfix"]
        groups[m["prefix"]].append({
            "case_id": case_id,
            "pad": int(m["pad"]),
            "verdict": r["verdict"],
            "processed_insns": r.get("processed_insns"),
            "oracle_loss_code": loss,
            "oracle_loss_span": sorted(span),
            "oracle_reject_code": sites.get("oracle_reject_code"),
            "vs_stop_line": vs_line,
            "vs_stop_in_injection": vs_line in span if vs_line is not None else None,
            "bpfix_error": d.error_id if d else None,
            "bpfix_upstream_obligation": UPSTREAM_ERROR_OBLIGATION.get(d.error_id or "") if d else None,
            "bpfix_next_action": d.next_action if d else None,
            "bpfix_primary": d.primary_raw if d else None,
            "top1_line": (d.primary_raw == loss) if d else None,
            "top1_span": (d.primary_raw in span) if d else None,
            "injection_in_labels": bool(span & set(d.label_lines)) if d else None,
            "primary_distance": abs(d.primary_raw - loss) if d and d.primary_raw and loss else None,
        })
    out = []
    for prefix, rs in sorted(groups.items()):
        rs.sort(key=lambda x: x["pad"])
        insns = [x["processed_insns"] for x in rs]
        grows = all(isinstance(a, int) and isinstance(b, int) and b > a for a, b in zip(insns, insns[1:]))
        out.append({
            "family": prefix,
            "rows": rs,
            "insns_grow_with_pad": grows,
            "injection_in_labels_all_pads": all(x["injection_in_labels"] for x in rs) if rs else None,
            "error_stable": len({x["bpfix_error"] for x in rs}) == 1,
        })
    return out


# ---------------------------------------------------------------- C. upstream


def score_upstream(rows: dict[str, dict]) -> dict:
    by_case: dict[str, dict[str, dict]] = defaultdict(dict)
    for case_id, r in rows.items():
        if "__" not in case_id:
            continue
        case, variant = case_id.split("__", 1)
        tf = ROOT / "campaigns" / "v2" / "upstream" / case / "transform.json"
        if not tf.is_file():
            continue
        meta = json.loads(tf.read_text(encoding="utf-8"))
        sites = set(meta["variants"].get(variant, {}).get("repair_sites", []))
        d = r["_bpfix"]
        by_case[case][variant] = {
            "verdict": r["verdict"],
            "processed_insns": r.get("processed_insns"),
            "bpfix_error": d.error_id if d else None,
            "primary": d.primary_raw if d else None,
            "primary_in_repair": bool(d and d.primary_raw in sites),
            "any_label_in_repair": bool(d and sites & set(d.label_lines)),
            "_structure": structure_key(d) if d else None,
        }
    comparisons = {}
    for variant in ("pad8", "pad32", "rename"):
        pairs = [(c, v["orig"], v[variant]) for c, v in sorted(by_case.items()) if "orig" in v and variant in v]
        rows_out = []
        b = c_ = 0
        for case, o, t in pairs:
            if o["primary_in_repair"] and not t["primary_in_repair"]:
                b += 1
            if t["primary_in_repair"] and not o["primary_in_repair"]:
                c_ += 1
            rows_out.append({
                "case": case,
                "orig_primary_in_repair": o["primary_in_repair"],
                "variant_primary_in_repair": t["primary_in_repair"],
                "orig_label_in_repair": o["any_label_in_repair"],
                "variant_label_in_repair": t["any_label_in_repair"],
                "error_equal": o["bpfix_error"] == t["bpfix_error"],
                "insns": [o["processed_insns"], t["processed_insns"]],
                "structure_equal": (o["_structure"] == t["_structure"]) if variant == "rename" else None,
            })
        n = len(pairs)
        k_o = sum(1 for _, o, _ in pairs if o["primary_in_repair"])
        k_t = sum(1 for _, _, t in pairs if t["primary_in_repair"])
        comparisons[variant] = {
            "n_pairs": n,
            "orig_primary_in_repair": {"hits": k_o, "wilson95": wilson(k_o, n)},
            "variant_primary_in_repair": {"hits": k_t, "wilson95": wilson(k_t, n)},
            "lost_hits_b": b,
            "gained_hits_c": c_,
            "mcnemar_exact_p": mcnemar_exact(b, c_),
            "rows": rows_out,
        }
    return {"n_cases": len(by_case), "comparisons": comparisons}


# ---------------------------------------------------------------- render


def yn(v) -> str:
    return {True: "yes", False: "no"}.get(v, "n/a")


def render_md(payload: dict) -> str:
    L = ["# Campaign v2 scores", "", f"Host: {payload['host']} · stamp `{payload['stamp']}`.", ""]
    if payload.get("pilot_note"):
        L += [f"> {payload['pilot_note']}", ""]
    L += ["## A. Rename on rejecting NullablePointer programs", "",
          "| pair | verdicts | error | `-->` equal | structure equal | check line labelled (listed / idiomatic) | labels only with listed name |",
          "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in payload["rename"]:
        if r.get("status") != "ok":
            L.append(f"| `{r['pair']}` | {r['verdicts']} | n/a | n/a | n/a | n/a | {r.get('status')} |")
            continue
        extra = "; ".join(f"{ln} ({kind}): {msg}" for ln, kind, msg in r["labels_only_listed"]) or "none"
        L.append(
            f"| `{r['pair']}` | {'/'.join(map(str, r['verdicts']))} | {'/'.join(map(str, r['error_ids']))} | "
            f"{yn(r['primary_equal'])} | {yn(r['structure_equal'])} | "
            f"{yn(r['check_line_labelled'][0])} / {yn(r['check_line_labelled'][1])} | {extra} |"
        )
    ok = [r for r in payload["rename"] if r.get("status") == "ok"]
    L += ["", f"Pairs whose rendered diagnostic changes under rename: "
          f"{sum(1 for r in ok if not r['structure_equal'])}/{len(ok)}; "
          f"pairs whose `-->` line changes: {sum(1 for r in ok if not r['primary_equal'])}/{len(ok)}.", ""]

    L += ["## B. Padding that survives compilation", "",
          "| family | pad | verdict | insns | VS stop | VS in injection | bpfix error (upstream obligation) | `-->` | top1_line | top1_span | injection in labels | distance |",
          "| --- | ---: | --- | ---: | ---: | --- | --- | ---: | --- | --- | --- | ---: |"]
    for g in payload["pads"]:
        for x in g["rows"]:
            L.append(
                f"| {g['family']} | {x['pad']} | {x['verdict']} | {x['processed_insns']} | {x['vs_stop_line']} | "
                f"{yn(x['vs_stop_in_injection'])} | {x['bpfix_error']} ({x['bpfix_upstream_obligation']}) | "
                f"{x['bpfix_primary']} | {yn(x['top1_line'])} | {yn(x['top1_span'])} | {yn(x['injection_in_labels'])} | "
                f"{x['primary_distance'] if x['primary_distance'] is not None else 'n/a'} |"
            )
    L += [""]
    for g in payload["pads"]:
        L.append(f"- **{g['family']}**: instructions grow with pad: {yn(g['insns_grow_with_pad'])}; "
                 f"injection labelled at every pad: {yn(g['injection_in_labels_all_pads'])}; "
                 f"error ID stable: {yn(g['error_stable'])}.")
    L.append("")

    up = payload.get("upstream")
    if up:
        L += ["## C. Upstream cases under padding and rename (repair-site oracle)", "",
              "| variant | pairs | orig `-->` on site | variant `-->` on site | lost | gained | exact McNemar p |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
        for v, c in up["comparisons"].items():
            L.append(f"| {v} | {c['n_pairs']} | {c['orig_primary_in_repair']['hits']} | "
                     f"{c['variant_primary_in_repair']['hits']} | {c['lost_hits_b']} | {c['gained_hits_c']} | "
                     f"{c['mcnemar_exact_p'] if c['mcnemar_exact_p'] is not None else 'n/a (no discordant pairs)'} |")
        L += ["", "Per-case rows: `v2_scores.json`. Repair sites are mapped into each variant's line numbers "
              "(campaigns/v2/upstream/<case>/transform.json).", ""]
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--captured", type=Path, required=True)
    ap.add_argument("--upstream-captured", type=Path, default=None)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--pilot-note", default=None, help="banner text, e.g. 'pilot, not the cite pin'")
    args = ap.parse_args(argv)

    def absp(p: Path) -> Path:
        return p if p.is_absolute() else ROOT / p

    stamp, rows = load_capture(absp(args.captured))
    payload = {
        "generator": "tools/score_v2_campaign.py",
        "stamp": stamp,
        "host": env_summary(absp(args.captured)),
        "pilot_note": args.pilot_note,
        "rename": score_rename(rows),
        "pads": score_pads(rows),
    }
    if args.upstream_captured:
        _, urows = load_capture(absp(args.upstream_captured))
        payload["upstream_host"] = env_summary(absp(args.upstream_captured))
        payload["upstream"] = score_upstream(urows)
        for c in payload["upstream"]["comparisons"].values():
            for r in c["rows"]:
                r.pop("_structure", None)
    out = absp(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "v2_scores.json").write_text(json.dumps(payload, indent=2, default=list) + "\n", encoding="utf-8", newline="\n")
    (out / "v2_scores.md").write_text(render_md(payload) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {out / 'v2_scores.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

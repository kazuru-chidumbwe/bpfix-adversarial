#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RQ1 — full upstream bpfix CLI localizations on lab pad reject-oracles.

Parses `results/rq1_bpfix_cli_raw/<case>.txt` produced by
`tools/run_rq1_bpfix_cli.sh` (WSL/Linux host with a built bpfix binary).

    Scoring (locked loss-anchored rule from docs/METRICS.md):
  - primary_src = line from rustc-style `--> file:LINE` arrow
  - top1_line if primary_src == oracle_loss_code (exact equality only)
  - top1_span if primary_src ∈ oracle_loss_span (empty span → equality fallback)
  - set_recall_message if oracle_loss_code appears as a snippet/primary decimal line
  - distance error uses source lines: |d_reported − d_true|, d = reject − reported/loss
  - nearest BPF PC is recorded as bpfix's native PC localization (typically reject PC)

Note: template distance pads are `__pad += k` chains that clang DCE's, so reject BPF PC
is stable across pad 0/8/32 for these mutants; source-line distance still grows.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HONESTY = ROOT / "results" / "sc_vs_honesty.json"
RAW_DIR = ROOT / "results" / "rq1_bpfix_cli_raw"
OUT_MD = ROOT / "results" / "rq1_bpfix_cli.md"
OUT_JSON = ROOT / "results" / "rq1_bpfix_cli.json"

RE_ARROW = re.compile(r"^\s*-->\s+\S+:(\d+)\s*$", re.M)
RE_PC = re.compile(r"nearest BPF instruction pc\s+(\d+)")
RE_ERR = re.compile(r"^error\[(BPFIX-E\d+)\]:\s*(.+)$", re.M)
RE_SNIP_LINE = re.compile(r"^\s*(\d+)\s+\|", re.M)
RE_REJECT_HERE = re.compile(r"^\s*(\d+)\s+\|.*\n\s+\|\s+\^+\s+rejected here:", re.M)


def pad_of(case_id: str) -> int | None:
    m = re.search(r"pad(\d+)", case_id)
    return int(m.group(1)) if m else None


def parse_raw(text: str) -> dict:
    arrow = RE_ARROW.search(text)
    pc = RE_PC.search(text)
    err = RE_ERR.search(text)
    snip_lines = [int(x) for x in RE_SNIP_LINE.findall(text)]
    reject_here = RE_REJECT_HERE.search(text)
    primary = int(arrow.group(1)) if arrow else None
    # Related lines shown in the snippet excluding the primary reject-here line.
    related = [ln for ln in snip_lines if ln != primary]
    return {
        "error_id": err.group(1) if err else None,
        "error_msg": err.group(2).strip() if err else None,
        "primary_src": primary,
        "reject_here_src": int(reject_here.group(1)) if reject_here else None,
        "related_src_lines": related,
        "nearest_bpf_pc": int(pc.group(1)) if pc else None,
        "raw_bytes": len(text.encode("utf-8")),
    }


def top1_line(reported: int | None, loss_code: int | None) -> bool:
    return reported is not None and loss_code is not None and reported == loss_code


def top1_span(reported: int | None, loss_code: int | None, loss_span: list[int] | None) -> bool:
    if reported is None:
        return False
    if loss_span:
        return reported in loss_span
    return top1_line(reported, loss_code)


def set_recall_message(
    primary: int | None, related: list[int], loss_code: int | None
) -> bool:
    if loss_code is None:
        return False
    return any(ln == loss_code for ln in ([primary] + related) if ln is not None)


def dist_err(reported: int | None, loss: int | None, reject: int | None, top1: bool) -> int | None:
    if top1:
        return 0
    if reported is None or loss is None or reject is None:
        return None
    d_true = reject - loss
    d_rep = reject - reported
    return abs(d_rep - d_true)


def main() -> None:
    honesty = json.loads(HONESTY.read_text(encoding="utf-8"))["rows"]
    rows = []
    for r in honesty:
        if not r.get("lab_rejected"):
            continue
        case_id = r["case_id"]
        pad = pad_of(case_id)
        if pad is None:
            continue
        raw_path = RAW_DIR / f"{case_id}.txt"
        if not raw_path.is_file():
            raise SystemExit(f"missing raw bpfix output: {raw_path}")
        parsed = parse_raw(raw_path.read_text(encoding="utf-8"))
        loss = r.get("oracle_loss_code")
        reject = r.get("oracle_reject_code")
        span = r.get("oracle_loss_span") or []
        primary = parsed["primary_src"]
        line_hit = top1_line(primary, loss)
        span_hit = top1_span(primary, loss, span)
        recall = set_recall_message(primary, parsed["related_src_lines"], loss)
        d_true = (reject - loss) if loss is not None and reject is not None else None
        rows.append(
            {
                "obligation": r["obligation"],
                "case_id": case_id,
                "pad": pad,
                "oracle_loss_code": loss,
                "oracle_reject_code": reject,
                "oracle_loss_span": span,
                "d_true_src": d_true,
                "bpfix_error_id": parsed["error_id"],
                "bpfix_error_msg": parsed["error_msg"],
                "bpfix_primary_src": primary,
                "bpfix_related_src": parsed["related_src_lines"],
                "bpfix_nearest_pc": parsed["nearest_bpf_pc"],
                "bpfix_top1_line": line_hit,
                "bpfix_top1_span": span_hit,
                # Legacy alias kept for downstream readers: exact line only (METRICS top1_line).
                "bpfix_top1_vs_loss": line_hit,
                "bpfix_distance_error": dist_err(primary, loss, reject, line_hit),
                "bpfix_set_recall_message": recall,
                "bpfix_loss_mentioned": recall,
                "log": r.get("log"),
                "raw": str(raw_path.relative_to(ROOT).as_posix()),
            }
        )

    meta = {
        "n": len(rows),
        "bpfix_version": "0.1.9",
        "bpfix_pin": "81d97e4a528456e0082a77f4fb6edd13fa092b7b",
        "stamp_family": "20260801T181331Z",
        "host": "WSL (offline log replay; not lab-server)",
        "scoring": "loss-anchored; top1_line = primary==oracle_loss_code; top1_span = span membership; set_recall_message = decimal loss line in CLI text",
        "pad_note": "scalar __pad chains DCE under clang — nearest_bpf_pc stable across pads for these templates",
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    def yn(v: bool | None) -> str:
        if v is True:
            return "yes"
        if v is False:
            return "no"
        return "—"

    lines = [
        "# RQ1 — Full bpfix CLI localizations (lab pad reject-oracles)",
        "",
        f"Upstream bpfix **{meta['bpfix_version']}** @ `{meta['bpfix_pin'][:12]}…` · stamp `{meta['stamp_family']}` · {meta['host']}.",
        "Primary report = rustc-style `--> file:LINE`. **top1_line** = exact `oracle_loss_code`; **top1_span** = span membership (`docs/METRICS.md`).",
        f"Pad note: {meta['pad_note']}.",
        "",
        "| Obligation | case_id | pad | d_true | primary | PC | top1_line | top1_span | d_err | set_recall |",
        "| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |",
    ]
    for r in rows:
        derr = r["bpfix_distance_error"]
        lines.append(
            f"| {r['obligation']} | `{r['case_id']}` | {r['pad']} | {r['d_true_src']} | "
            f"{r['bpfix_primary_src']} | {r['bpfix_nearest_pc']} | {yn(r['bpfix_top1_line'])} | "
            f"{yn(r['bpfix_top1_span'])} | {derr if derr is not None else '—'} | "
            f"{yn(r['bpfix_set_recall_message'])} |"
        )

    pb = [r for r in rows if r["obligation"] == "PacketBounds"]
    pp = [r for r in rows if r["obligation"] == "PointerProvenance"]
    sr = [r for r in rows if r["obligation"] == "ScalarRange"]
    lines += [
        "",
        "## Reading (SoftwareX)",
        "",
        "- **PacketBounds:** primary `-->` tracks the wide load (reject). Under **top1_line** "
        "this is a miss; `d_err` tracks pad "
        f"({', '.join(str(r['bpfix_distance_error']) for r in pb)}). "
        "The E001 snippet still *mentions* the narrow `data_end` check (loss) as related context — "
        "`set_recall_message = yes`. This is **not** a contradiction with `rq1_lab_distance.*` "
        "(SC port: PB honest): SC keys on contextual loss pickup; CLI primary is the headline "
        "location. Both are correct measurements of different things (headline vs full message).",
        "- **PointerProvenance:** primary lands on a later XOR-wash line in the loss **span** "
        f"(top1_line={yn(all(r['bpfix_top1_line'] for r in pp))}; "
        f"top1_span={yn(all(r['bpfix_top1_span'] for r in pp))}); nearest PC stable (DCE) — "
        "span hit without exact first-line hit.",
        "- **ScalarRange:** primary stays on the unbound stack load (reject); loss (`prandom` idx) "
        f"not in snippet — miss (top1_line={yn(any(r['bpfix_top1_line'] for r in sr))}), matching lab SC/VS.",
        "- Offline WSL replay of stamped lab logs (not lab-server): bpfix diagnoses log text and does "
        "not re-verify, so the offline host is not a kernel-version confound.",
        "- Complements `rq1_lab_distance.*` (SC-port / VS stop-site) with native upstream CLI output "
        "on the same logs.",
        "",
        f"Raw CLI dumps: `{RAW_DIR.relative_to(ROOT).as_posix()}/`. "
        f"Artifacts: `{OUT_MD.relative_to(ROOT).as_posix()}` · `{OUT_JSON.relative_to(ROOT).as_posix()}`.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_MD} n={len(rows)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Emit four-obligation stratified score table (Bomb #1).

Scores SourceComment heuristics against construction-time oracle markers
embedded in mutant .c files. Lab verifier accept/reject is filled when
fixtures/logs/captured/*.log exist (else lab_status=PENDING).
"""

from __future__ import annotations

import hashlib
import json
import re
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
from bpfix_adversarial.score import score_honesty  # noqa: E402

ORACLE_LOSS_RE = re.compile(r"ORACLE_LOSS_LINE")
ORACLE_REJECT_RE = re.compile(r"ORACLE_REJECT_LINE")


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def oracle_lines(src: Path) -> tuple[int | None, int | None]:
    loss = reject = None
    for i, line in enumerate(src.read_text(encoding="utf-8").splitlines(), start=1):
        if ORACLE_LOSS_RE.search(line) and loss is None:
            loss = i
        if ORACLE_REJECT_RE.search(line) and reject is None:
            reject = i
    return loss, reject


def sc_reported_loss(src: Path, obligation: str) -> tuple[int | None, str]:
    """Best-effort SourceComment loss line from source text (no verifier log)."""
    lines = src.read_text(encoding="utf-8").splitlines()
    texts = [(i, ln.strip()) for i, ln in enumerate(lines, start=1)]

    if obligation == "NullablePointer":
        for i, t in texts:
            if looks_like_null_check(t):
                return i, "SC: null-check establish"
        for i, t in texts:
            if looks_like_nullable_return(t):
                return i, "SC: nullable-return loss (fallback)"
        return None, "SC: no NP heuristic hit"

    if obligation == "PacketBounds":
        for i, t in texts:
            if looks_like_packet_bounds_check(t):
                return i, "SC: data_end establish"
        return None, "SC: no packet-bounds heuristic hit"

    if obligation == "ScalarRange":
        for i, t in texts:
            if looks_like_scalar_guard(t) and "data_end" not in t:
                return i, "SC: scalar-guard establish"
        return None, "SC: no scalar-guard heuristic hit"

    if obligation == "PointerProvenance":
        # No dedicated SC name heuristic in port — expect miss / None
        return None, "SC: no PP-specific SourceComment heuristic"

    return None, "SC: unknown obligation"


def latest_captured_log(case_id: str) -> Path | None:
    cap = ROOT / "fixtures" / "logs" / "captured"
    if not cap.is_dir():
        return None
    hits = sorted(cap.glob(f"{case_id}.*.log"))
    return hits[-1] if hits else None


def lab_status(case_id: str) -> dict:
    log = latest_captured_log(case_id)
    if log is None:
        return {"lab_status": "PENDING", "log": None, "log_sha256": None, "rejected": None}
    text = log.read_text(encoding="utf-8", errors="replace")
    rejected = any(
        k in text.lower()
        for k in ("invalid", "rejected", "permission denied", "r0", "failure")
    ) or "processed" in text.lower()
    # crude: compile fail vs verifier reject
    if "COMPILE_FAIL" in text:
        return {
            "lab_status": "COMPILE_FAIL",
            "log": str(log.relative_to(ROOT)).replace("\\", "/"),
            "log_sha256": sha256_file(log),
            "rejected": False,
        }
    return {
        "lab_status": "CAPTURED",
        "log": str(log.relative_to(ROOT)).replace("\\", "/"),
        "log_sha256": sha256_file(log),
        "rejected": rejected,
    }


def main() -> None:
    rows = []
    for src in sorted((ROOT / "mutants").rglob("*.c")):
        parts = src.parts
        obligation = parts[-2]
        case_id = src.stem
        loss, reject = oracle_lines(src)
        reported, note = sc_reported_loss(src, obligation)
        honesty = score_honesty(
            oracle_loss_code=loss or -1,
            oracle_reject_line=reject or -1,
            reported_loss_line=reported,
        )
        lab = lab_status(case_id)
        rows.append(
            {
                "obligation": obligation,
                "case_id": case_id,
                "src": str(src.relative_to(ROOT)).replace("\\", "/"),
                "src_sha256": sha256_file(src),
                "oracle_loss_line": loss,
                "oracle_reject_line": reject,
                "sc_reported_loss_line": reported,
                "sc_note": note,
                "top1_vs_oracle": honesty["top1_loss_match"] if loss is not None else None,
                "distance_true_src_lines": honesty["distance_true"] if loss is not None else None,
                "distance_error_src_lines": honesty["distance_error"],
                **lab,
            }
        )

    out_json = ROOT / "results" / "obligation_matrix.json"
    out_md = ROOT / "results" / "obligation_matrix.md"
    out_json.write_text(json.dumps({"n": len(rows), "rows": rows}, indent=2) + "\n", encoding="utf-8")

    by_ob: dict[str, list] = {}
    for r in rows:
        by_ob.setdefault(r["obligation"], []).append(r)

    lines = [
        "# Four-obligation stratified score table (Bomb #1)",
        "",
        "Construction oracle from `ORACLE_*` markers in mutant sources.",
        "SourceComment column = heuristic port on source text (no circularity with bpfix CLI).",
        "`d` distances are **source lines** (`reject_line − loss_line`); BPF-insn distances filled after lab capture.",
        "",
        "| Obligation | case_id | pad/arm | SC top-1 vs oracle | SC note | lab_status | log_sha256 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for ob in ("NullablePointer", "PointerProvenance", "ScalarRange", "PacketBounds"):
        for r in by_ob.get(ob, []):
            arm = r["case_id"]
            top = r["top1_vs_oracle"]
            top_s = "yes" if top is True else ("no" if top is False else "n/a")
            sha = (r["log_sha256"] or "—")[:12]
            if r["log_sha256"]:
                sha = r["log_sha256"][:12] + "…"
            else:
                sha = "—"
            lines.append(
                f"| {ob} | `{arm}` | `{arm}` | {top_s} | {r['sc_note']} | {r['lab_status']} | {sha} |"
            )

    # summary counts
    lines += ["", "## Summary by obligation", ""]
    lines.append("| Obligation | n | SC top-1 yes | SC top-1 no | lab CAPTURED |")
    lines.append("| --- | ---: | ---: | ---: | ---: |")
    for ob, rs in by_ob.items():
        yes = sum(1 for r in rs if r["top1_vs_oracle"] is True)
        no = sum(1 for r in rs if r["top1_vs_oracle"] is False)
        cap = sum(1 for r in rs if r["lab_status"] == "CAPTURED")
        lines.append(f"| {ob} | {len(rs)} | {yes} | {no} | {cap} |")

    lines += [
        "",
        "## Notes",
        "",
        "- Negative / no-disagreement cells are valid outcomes (bpfix SC may match oracle).",
        "- `lab_status=PENDING` until `lab/batch_capture_all.sh` runs on Linux 6.8 host.",
        "- RQ2 combinatorial rename (32/32) remains the NP lead mechanistic finding.",
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_json} and {out_md} ({len(rows)} rows)")


if __name__ == "__main__":
    main()

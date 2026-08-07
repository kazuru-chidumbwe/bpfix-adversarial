"""Emit §6.5 four-obligation stratified score table from mutants + available logs."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUT = ROOT / "mutants"
CAP = ROOT / "fixtures" / "logs" / "captured"
SYN = ROOT / "fixtures" / "logs" / "synthetic"
OUT_MD = ROOT / "results" / "four_obligation_matrix.md"
OUT_JSON = ROOT / "results" / "four_obligation_matrix.json"

ORACLE_LOSS_RE = re.compile(r"ORACLE_LOSS_LINE")
ORACLE_REJECT_RE = re.compile(r"ORACLE_REJECT_LINE")


def sha256_file(p: Path) -> str:
    # Normalize CRLF→LF so Windows/Linux checkouts yield the same src_sha256.
    data = p.read_bytes().replace(b"\r\n", b"\n")
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def oracle_lines(src: Path) -> tuple[int | None, int | None]:
    loss = reject = None
    for i, line in enumerate(src.read_text(encoding="utf-8").splitlines(), 1):
        if "ORACLE_LOSS_LINE" in line:
            loss = i
        if "ORACLE_REJECT_LINE" in line:
            reject = i
    return loss, reject


def latest_log(case_id: str) -> Path | None:
    caps = sorted(
        p
        for p in CAP.glob(f"{case_id}.*.log")
        if not p.name.endswith(".compile")
    )
    preferred = [p for p in caps if "20260801T181331Z" in p.name]
    if preferred:
        return preferred[-1]
    if caps:
        return caps[-1]
    syn = SYN / f"{case_id}.log"
    return syn if syn.exists() else None


def log_status(log: Path | None) -> dict:
    if log is None:
        return {
            "log_tier": "missing",
            "rejected_or_error": None,
            "log_sha256": None,
            "log_path": None,
        }
    text = log.read_text(encoding="utf-8", errors="replace")
    tier = "captured" if log.parent.name == "captured" else "synthetic"
    rejected = any(
        s in text.lower()
        for s in (
            "permission denied",
            "invalid",
            "r0",
            "fail",
            "error",
            "rejected",
            "cannot",
        )
    ) or "COMPILE_FAIL" in text
    # empty successful load often has little text
    nonempty = len(text.strip()) > 0
    return {
        "log_tier": tier,
        "rejected_or_error": rejected if nonempty else False,
        "log_bytes": len(text.encode("utf-8")),
        "log_sha256": sha256_file(log),
        "log_path": str(log.relative_to(ROOT)).replace("\\", "/"),
        "log_head": text.strip().splitlines()[:3],
    }


def rename_honesty_note(case_id: str) -> str:
    if "repaired" in case_id:
        return "RQ4 repaired program (wrong-tip protocol)"
    if "idiomatic" in case_id and "nocheck" not in case_id:
        return "SC name-list miss expected (!entry)"
    if "brittle" in case_id:
        return "SC name-list hit expected (!ptr)"
    if "nocheck" in case_id:
        return "RQ4 failing seed (missing check)"
    if case_id.startswith("PB-"):
        return "packet under-check template"
    if case_id.startswith("PP-"):
        return "pkt⊕prandom wash (reject: unbounded pkt math)"
    if case_id.startswith("SR-"):
        return "unbound stack[prandom] (reject: unbounded mem)"
    return ""


def main() -> None:
    rows = []
    for src in sorted(MUT.glob("*/*.c")):
        obligation = src.parent.name
        case_id = src.stem
        loss, reject = oracle_lines(src)
        log = latest_log(case_id)
        st = log_status(log)
        rows.append(
            {
                "obligation": obligation,
                "case_id": case_id,
                "pad": int(re.search(r"pad(\d+)", case_id).group(1))
                if re.search(r"pad(\d+)", case_id)
                else None,
                "oracle_loss_line": loss,
                "oracle_reject_line": reject,
                "src_sha256": sha256_file(src),
                "note": rename_honesty_note(case_id),
                **st,
            }
        )

    by_ob = {}
    for r in rows:
        by_ob.setdefault(r["obligation"], []).append(r)

    lines = [
        "# Four-obligation stratified mutant matrix (§6.5)",
        "",
        "Construction-time oracle markers scanned from mutant sources.",
        "Log tier: `captured` = lab bpftool; `synthetic` = fixture; `missing` = no log yet.",
        "",
    ]
    for ob, items in sorted(by_ob.items()):
        lines.append(f"## {ob} (n={len(items)})")
        lines.append("")
        lines.append(
            "| case_id | pad | loss | reject | log_tier | log_sha256 | note |"
        )
        lines.append("| --- | ---: | ---: | ---: | --- | --- | --- |")
        for r in items:
            h = (r.get("log_sha256") or "—")[:12]
            if r.get("log_sha256"):
                h = r["log_sha256"][:12] + "…"
            lines.append(
                f"| `{r['case_id']}` | {r['pad']} | {r['oracle_loss_line']} | "
                f"{r['oracle_reject_line']} | {r['log_tier']} | `{h}` | {r['note']} |"
            )
        lines.append("")

    captured_n = sum(1 for r in rows if r["log_tier"] == "captured")
    lines.append(
        f"**Summary:** {len(rows)} mutants · {captured_n} lab-captured logs · "
        f"{sum(1 for r in rows if r['log_tier']=='synthetic')} synthetic · "
        f"{sum(1 for r in rows if r['log_tier']=='missing')} missing."
    )
    lines.append("")
    lines.append(
        "Honesty scores vs construction oracle for SC/VS remain in "
        "`rename_honesty.*`, `np_pair_score.json`, `tier_disagreement.*`; "
        "this matrix is the stratified coverage table for the four-obligation review."
    )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_JSON.write_text(json.dumps({"rows": rows}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_JSON}")
    print(f"mutants={len(rows)} captured={captured_n}")


if __name__ == "__main__":
    main()

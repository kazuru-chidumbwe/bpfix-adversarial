#!/usr/bin/env python3
"""SC vs VS honesty on lab-captured mutants (loss-anchored scoring).

General rule (locked): top-1 and distance are measured against the construction-time
**loss** site whenever loss and reject markers diverge — not against the marked
reject/use line.

SourceComment (SC): bpfix heuristic port on mutant source.
VerifierState (VS): last BTF source-mapped line in the captured verifier log
immediately before the terminal reject message (stop site).
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
from bpfix_adversarial.logparse import parse_verifier_log  # noqa: E402
from bpfix_adversarial.oracle import oracle_sites  # noqa: E402
from bpfix_adversarial.score import score_honesty  # noqa: E402

SOURCE_AT_RE = re.compile(r";\s*(.*?)\s*@\s*([^:]+):(\d+)\s*$")
REJECT_HINTS = (
    "invalid",
    "math between",
    "unbounded",
    "permission denied",
    "failed to load",
    "r0 invalid",
    "r1 unbounded",
    "r1 offset",
)


def sha256_file(p: Path) -> str:
    # Normalize CRLF→LF so Windows/Linux checkouts yield the same src_sha256.
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def latest_captured_log(case_id: str) -> Path | None:
    cap = ROOT / "fixtures" / "logs" / "captured"
    hits = sorted(
        p
        for p in cap.glob(f"{case_id}.*.log")
        if not p.name.endswith(".compile")
    )
    # Prefer SoftwareX template-oracle stamp when present; else newest stamp.
    preferred = [p for p in hits if "20260801T181331Z" in p.name]
    if preferred:
        return preferred[-1]
    return hits[-1] if hits else None


def lab_rejected(text: str) -> bool:
    low = text.lower()
    return any(
        s in low
        for s in (
            "failed to load",
            "invalid",
            "math between",
            "unbounded memory",
            "permission denied",
        )
    ) and "BEGIN PROG LOAD LOG" in text


def vs_stop_line(text: str) -> tuple[int | None, str | None, str]:
    """Last source-mapped line before terminal reject; else last mapped line."""
    locs: list[tuple[int, str]] = []
    reject_idx: int | None = None
    raw_lines = text.splitlines()
    for idx, line in enumerate(raw_lines):
        m = SOURCE_AT_RE.search(line)
        if m:
            locs.append((int(m.group(3)), m.group(1).strip()))
        low = line.lower()
        if any(h in low for h in REJECT_HINTS) and "libbpf:" not in low[:8]:
            if "invalid" in low or "math between" in low or "unbounded" in low:
                reject_idx = idx
                break
    if not locs:
        return None, None, "VS: no source mappings in log"
    if reject_idx is not None:
        # last mapping appearing before reject line
        before: list[tuple[int, str]] = []
        for idx, line in enumerate(raw_lines[:reject_idx]):
            m = SOURCE_AT_RE.search(line)
            if m:
                before.append((int(m.group(3)), m.group(1).strip()))
        if before:
            ln, txt = before[-1]
            return ln, txt, "VS: stop-site source map before reject"
    ln, txt = locs[-1]
    return ln, txt, "VS: last source map in log"


def sc_report(src: Path, obligation: str, case_id: str) -> tuple[int | None, str]:
    lines = src.read_text(encoding="utf-8").splitlines()
    texts = [(i, ln.strip()) for i, ln in enumerate(lines, 1)]

    if obligation == "NullablePointer":
        for i, t in texts:
            if looks_like_null_check(t):
                return i, "SC: null-check establish"
        for i, t in texts:
            if looks_like_nullable_return(t):
                return i, "SC: nullable-return (fallback / nocheck)"
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
        return None, "SC: no scalar-guard heuristic hit (expected on unbound-index templates)"

    if obligation == "PointerProvenance":
        return None, "SC: no PP-specific SourceComment heuristic (coverage gap)"

    return None, f"SC: unknown obligation ({obligation})"


def in_loss_span(reported: int | None, sites: dict) -> bool:
    if reported is None:
        return False
    span = sites["oracle_loss_span"] or []
    if reported in span:
        return True
    return reported == sites["oracle_loss_code"]


def score_reported(reported: int | None, sites: dict) -> dict:
    """Score with separate top1_line / top1_span and absolute distance.

    - top1_line: predicted == oracle_loss_code (first executable injection line)
    - top1_span: predicted ∈ oracle_loss_span (multi-line wash membership)
    - set_recall_message: not computed here (message-text scan elsewhere)
    - distance_error: |predicted − oracle_loss_code| (never zeroed by span hit)
    - top1_vs_loss: legacy alias of top1_span (lab inset historical field)
    """
    loss = sites["oracle_loss_code"]
    reject = sites["oracle_reject_code"] or sites["oracle_reject_marker"] or (loss or 0)
    if loss is None:
        return {
            "top1_line": None,
            "top1_span": None,
            "top1_vs_loss": None,
            "distance_true": None,
            "distance_error": None,
            "signed_offset": None,
            "reported": reported,
        }
    h = score_honesty(
        oracle_loss_line=loss,
        oracle_reject_line=reject,
        reported_loss_line=reported,
    )
    top1_line = bool(h["top1_line"]) if reported is not None else False
    top1_span = in_loss_span(reported, sites)
    h["match_via"] = "exact_loss_code" if top1_line else ("loss_span" if top1_span else "miss")
    return {
        "top1_line": top1_line if reported is not None else False,
        "top1_span": top1_span,
        "top1_vs_loss": top1_span,  # legacy alias — lab inset used span membership
        "distance_true": h["distance_true"],
        "distance_error": h["distance_error"],
        "signed_offset": h.get("signed_offset"),
        "reported": reported,
        "detail": h,
    }


def main() -> None:
    rows = []
    for src in sorted((ROOT / "mutants").rglob("*.c")):
        obligation = src.parts[-2]
        case_id = src.stem
        sites = oracle_sites(src)
        sc_line, sc_note = sc_report(src, obligation, case_id)
        sc_score = score_reported(sc_line, sites)

        log = latest_captured_log(case_id)
        if log is None:
            vs_line = vs_txt = None
            vs_note = "VS: missing captured log"
            rejected = None
            log_rel = None
            log_sha = None
        else:
            text = log.read_text(encoding="utf-8", errors="replace")
            rejected = lab_rejected(text)
            vs_line, vs_txt, vs_note = vs_stop_line(text)
            if not rejected:
                vs_note = "VS: load accepted — stop-site N/A for reject honesty"
                # still record last map for transparency but don't claim honesty
            log_rel = str(log.relative_to(ROOT)).replace("\\", "/")
            log_sha = sha256_file(log)
            # corroborate parse_verifier_log still works
            _ = parse_verifier_log(text)

        vs_score = (
            score_reported(vs_line, sites)
            if rejected
            else {
                "top1_line": None,
                "top1_span": None,
                "top1_vs_loss": None,
                "distance_true": sites["oracle_loss_code"]
                and (sites["oracle_reject_code"] or 0) - (sites["oracle_loss_code"] or 0),
                "distance_error": None,
                "signed_offset": None,
                "reported": vs_line,
            }
        )

        rows.append(
            {
                "obligation": obligation,
                "case_id": case_id,
                "src": str(src.relative_to(ROOT)).replace("\\", "/"),
                "src_sha256": sha256_file(src),
                **sites,
                "lab_rejected": rejected,
                "log": log_rel,
                "log_sha256": log_sha,
                "sc_reported_line": sc_line,
                "sc_note": sc_note,
                "sc_top1_line": sc_score["top1_line"],
                "sc_top1_span": sc_score["top1_span"],
                "sc_top1_vs_loss": sc_score["top1_vs_loss"],  # legacy = top1_span
                "sc_distance_error": sc_score["distance_error"],
                "sc_signed_offset": sc_score.get("signed_offset"),
                "vs_reported_line": vs_line,
                "vs_source_text": vs_txt,
                "vs_note": vs_note,
                "vs_top1_line": vs_score["top1_line"],
                "vs_top1_span": vs_score["top1_span"],
                "vs_top1_vs_loss": vs_score["top1_vs_loss"],  # legacy = top1_span
                "vs_distance_error": vs_score["distance_error"],
                "vs_signed_offset": vs_score.get("signed_offset"),
                "tiers_agree": (
                    sc_score["top1_span"] == vs_score["top1_span"]
                    if sc_score["top1_span"] is not None
                    and vs_score["top1_span"] is not None
                    else None
                ),
                "disagreement": (
                    sc_score["top1_span"] != vs_score["top1_span"]
                    if sc_score["top1_span"] is not None
                    and vs_score["top1_span"] is not None
                    else None
                ),
            }
        )

    out_json = ROOT / "results" / "sc_vs_honesty.json"
    out_md = ROOT / "results" / "sc_vs_honesty.md"
    payload = {
        "generator": "tools/score_sc_vs_honesty.py",
        "oracle_module": "bpfix_adversarial.oracle",
        "scoring_rule": (
            "top1_line = predicted==oracle_loss_code; "
            "top1_span = predicted in oracle_loss_span; "
            "distance_error = |predicted-oracle_loss_code|; "
            "legacy top1_vs_loss aliases top1_span"
        ),
        "n": len(rows),
        "rows": rows,
    }
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# SC vs VS injection-site agreement — lab stamp family `20260801T181331Z`",
        "",
        "Scoring: **top1_line** (`predicted == oracle_loss_code`); **top1_span**",
        "(membership in injection span); **distance_error** `|predicted − oracle_loss_code|`.",
        "Legacy column `top1_vs_loss` aliases **top1_span**. Never score vs marked reject/use alone.",
        "",
        "SC = bpfix SourceComment heuristic port on mutant source. "
        "VS = last source-mapped line in the **captured verifier log** "
        "(does not load object BTF; consumes log text only).",
        "",
        "| Obligation | case_id | loss_span | SC line | SC top1_line | SC top1_span | VS line | VS top1_line | VS top1_span | lab reject | disagree (span) |",
        "| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- |",
    ]

    def yn(v: bool | None) -> str:
        if v is True:
            return "yes"
        if v is False:
            return "no"
        return "n/a"

    for r in rows:
        span = r["oracle_loss_span"]
        span_s = ",".join(str(x) for x in span) if span else "—"
        lines.append(
            f"| {r['obligation']} | `{r['case_id']}` | {span_s} | "
            f"{r['sc_reported_line'] or '—'} | {yn(r['sc_top1_line'])} | {yn(r['sc_top1_span'])} | "
            f"{r['vs_reported_line'] or '—'} | {yn(r['vs_top1_line'])} | {yn(r['vs_top1_span'])} | "
            f"{yn(r['lab_rejected'])} | {yn(r['disagreement'])} |"
        )

    # Focus summaries
    lines += ["", "## PointerProvenance + ScalarRange", ""]
    lines.append("| case_id | SC line/span | VS line/span | note |")
    lines.append("| --- | --- | --- | --- |")
    for r in rows:
        if r["obligation"] not in ("PointerProvenance", "ScalarRange"):
            continue
        note = r["sc_note"] if r["sc_top1_span"] is False else r["vs_note"]
        if r["obligation"] == "PointerProvenance" and r["vs_top1_span"]:
            note = (
                "Terminal verifier report maps to XOR wash (coincides with author "
                "injection span), not the later marked use — not a semantic proof-loss claim"
            )
        if r["obligation"] == "ScalarRange" and r["vs_top1_span"] is False:
            note = "VS near-reject (stack load); SC has no scalar-guard → both miss loss"
        lines.append(
            f"| `{r['case_id']}` | {yn(r['sc_top1_line'])}/{yn(r['sc_top1_span'])} | "
            f"{yn(r['vs_top1_line'])}/{yn(r['vs_top1_span'])} | {note} |"
        )

    lines += ["", "## Summary by obligation (rejecting cases only)", ""]
    lines.append(
        "| Obligation | n_reject | SC top1_line | SC top1_span | VS top1_line | VS top1_span | span disagree |"
    )
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["obligation"], []).append(r)
    for ob, rs in sorted(by.items()):
        rej = [r for r in rs if r["lab_rejected"]]
        sc_l = sum(1 for r in rej if r["sc_top1_line"] is True)
        sc_s = sum(1 for r in rej if r["sc_top1_span"] is True)
        vs_l = sum(1 for r in rej if r["vs_top1_line"] is True)
        vs_s = sum(1 for r in rej if r["vs_top1_span"] is True)
        dis = sum(1 for r in rej if r["disagreement"] is True)
        lines.append(
            f"| {ob} | {len(rej)} | {sc_l}/{len(rej)} | {sc_s}/{len(rej)} | "
            f"{vs_l}/{len(rej)} | {vs_s}/{len(rej)} | {dis}/{len(rej)} |"
        )

    lines += [
        "",
        "## Takeaways",
        "",
        "- **PP:** SC has no provenance heuristic (systematic miss). VS **top1_span** hits "
        "the XOR wash (coincides with author injection span; **top1_line** may miss if "
        "the map is not the first executable line) — not a semantic proof-loss claim.",
        "- **SR:** SC finds no scalar guard on unbound-index templates (miss). VS reports "
        "the stack load (reject/use), not the unbound `idx` assignment (loss).",
        "- **PB:** SC **top1_line** hits the under-check; VS hits the wide load (reject).",
        "- **NP-nocheck:** SC reports lookup (before injection); VS reports reject deref — "
        "both miss line and span; still the RQ4 separation seed.",
        "- Accepting NP-with-check rows: VS score n/a (no reject); SC rename story unchanged.",
        "",
        f"Artifacts: `{out_json.relative_to(ROOT).as_posix()}` · `{out_md.relative_to(ROOT).as_posix()}`",
        "",
    ]
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"rows={len(rows)}")


if __name__ == "__main__":
    main()

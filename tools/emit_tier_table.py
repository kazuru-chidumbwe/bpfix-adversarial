#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""SourceComment vs VerifierState disagreement table."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.heuristics import looks_like_null_check  # noqa: E402
from bpfix_adversarial.logparse import parse_verifier_log, sourcecomment_events  # noqa: E402
from bpfix_adversarial.model import ProofEventEvidence, ProofEventRole  # noqa: E402


CASES = [
    {
        "case_id": "NP-idiomatic-pad8",
        "log": "fixtures/logs/synthetic/NP-idiomatic-pad8.log",
        "verifier_state_loss_line": 14,  # asserted by the fixture annotation
        "notes": "Rename breaks SourceComment establish",
    },
    {
        "case_id": "NP-brittle-pad8",
        "log": "fixtures/logs/synthetic/NP-brittle-pad8.log",
        "verifier_state_loss_line": 14,  # asserted by the fixture annotation
        "notes": "SourceComment recognizes !ptr",
    },
    {
        "case_id": "PB-pad0",
        "log": "fixtures/logs/synthetic/PB-pad0.log",
        "verifier_state_loss_line": 10,  # asserted by the fixture annotation
        "notes": "Packet under-check: SourceComment sees data_end",
    },
]


def fixture_oracle(text: str) -> int:
    """Oracle loss line as the fixture itself declares it."""
    m = re.search(r"ORACLE_LOSS_LINE=(\d+)", text)
    if not m:
        raise SystemExit("fixture carries no ORACLE_LOSS_LINE annotation")
    return int(m.group(1))


def analyze(case: dict) -> dict:
    path = ROOT / case["log"]
    log = parse_verifier_log(path.read_text(encoding="utf-8"))
    events = sourcecomment_events(log)
    sc_establish = [
        e
        for e in events
        if e.evidence == ProofEventEvidence.SOURCE_COMMENT
        and e.role == ProofEventRole.PROOF_ESTABLISHED
    ]
    sc_loss = [
        e
        for e in events
        if e.evidence == ProofEventEvidence.SOURCE_COMMENT
        and e.role == ProofEventRole.PROOF_LOST
    ]
    null_lines = [
        loc
        for loc in log.source_locations
        if loc.text.strip().startswith("if ")
    ]
    sc_null_ok = any(looks_like_null_check(loc.text) for loc in null_lines)
    # VerifierState tier: asserted by the fixture annotation, not measured from
    # the log. It is an input to this inset, so it is reported but never scored
    # against the oracle; doing so would restate the input.
    vs_line = case["verifier_state_loss_line"]
    oracle_loss_line = fixture_oracle(path.read_text(encoding="utf-8"))
    sc_reported = (
        sc_establish[-1].source.line
        if sc_establish and sc_establish[-1].source
        else (sc_loss[-1].source.line if sc_loss and sc_loss[-1].source else None)
    )
    sc_correct = sc_reported == oracle_loss_line if sc_reported else False
    return {
        **case,
        "oracle_loss_line": oracle_loss_line,
        "sourcecomment_null_check_recognized": sc_null_ok,
        "sourcecomment_reported_line": sc_reported,
        "verifier_state_asserted_line": vs_line,
        "sourcecomment_correct_vs_oracle": sc_correct,
    }


def markdown(rows: list[dict]) -> str:
    lines = [
        "# SourceComment vs VerifierState",
        "",
        "| case | SC null-check? | SC line | VS line (asserted) | SC matches oracle |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['case_id']} | "
            f"{'yes' if r['sourcecomment_null_check_recognized'] else 'no'} | "
            f"{r['sourcecomment_reported_line']} | {r['verifier_state_asserted_line']} | "
            f"{'yes' if r['sourcecomment_correct_vs_oracle'] else 'no'} |"
        )
    lines.append("")
    lines.append(
        "Lead example: **NP-idiomatic-pad8**. SourceComment misses the "
        "`if (!entry)` establish under rename."
    )
    lines.append("")
    lines.append(
        "Illustration of the tier contract on synthetic fixture logs, not an "
        "empirical finding. The VS line is carried by each fixture's annotation "
        "rather than measured from the log, so it is reported for context and is "
        "not scored against the oracle. On the lab captures VS behaves differently: "
        "for PacketBounds it stops at the wide load, not the check (VS top1_line 0/3). "
        "Lab-derived SourceComment and VerifierState outcomes are in `sc_vs_honesty.*`."
    )
    return "\n".join(lines)


def main() -> None:
    rows = [analyze(c) for c in CASES]
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"cases": rows}
    (out_dir / "tier_disagreement.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    md = markdown(rows)
    (out_dir / "tier_disagreement.md").write_text(md + "\n", encoding="utf-8", newline="\n")
    print(md)
    print(f"Wrote {out_dir / 'tier_disagreement.json'}")
    print(f"Wrote {out_dir / 'tier_disagreement.md'}")


if __name__ == "__main__":
    main()

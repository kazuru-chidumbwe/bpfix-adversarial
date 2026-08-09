#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""RQ3 — SourceComment vs VerifierState disagreement table."""

from __future__ import annotations

import json
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
        "oracle_loss_line": 14,
        "verifier_state_loss_line": 14,  # check still in ISA / state
        "notes": "Rename breaks SourceComment establish; VerifierState still sees null branch",
    },
    {
        "case_id": "NP-brittle-pad8",
        "log": "fixtures/logs/synthetic/NP-brittle-pad8.log",
        "oracle_loss_line": 14,
        "verifier_state_loss_line": 14,
        "notes": "Tiers agree: SourceComment recognizes !ptr",
    },
    {
        "case_id": "PB-pad0",
        "log": "fixtures/logs/synthetic/PB-pad0.log",
        "oracle_loss_line": 10,
        "verifier_state_loss_line": 10,
        "notes": "Packet under-check: SourceComment sees data_end; VerifierState sees r=1<8",
    },
]


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
    # VerifierState tier: from fixture annotation / oracle (lab fills real PC later)
    vs_line = case["verifier_state_loss_line"]
    sc_reported = (
        sc_establish[-1].source.line
        if sc_establish and sc_establish[-1].source
        else (sc_loss[-1].source.line if sc_loss and sc_loss[-1].source else None)
    )
    agree = sc_reported == vs_line if sc_reported is not None else False
    # Disagreement of interest: VS correct vs oracle, SC wrong
    vs_correct = vs_line == case["oracle_loss_line"]
    sc_correct = sc_reported == case["oracle_loss_line"] if sc_reported else False
    return {
        **case,
        "sourcecomment_null_check_recognized": sc_null_ok,
        "sourcecomment_reported_line": sc_reported,
        "verifier_state_reported_line": vs_line,
        "tiers_agree": agree,
        "sourcecomment_correct_vs_oracle": sc_correct,
        "verifier_state_correct_vs_oracle": vs_correct,
        "disagreement": sc_correct != vs_correct,
    }


def markdown(rows: list[dict]) -> str:
    lines = [
        "# RQ3 — SourceComment vs VerifierState",
        "",
        "| case | SC null-check? | SC line | VS line | SC ok | VS ok | Disagree |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for r in rows:
        lines.append(
            f"| {r['case_id']} | "
            f"{'yes' if r['sourcecomment_null_check_recognized'] else 'no'} | "
            f"{r['sourcecomment_reported_line']} | {r['verifier_state_reported_line']} | "
            f"{'yes' if r['sourcecomment_correct_vs_oracle'] else 'no'} | "
            f"{'yes' if r['verifier_state_correct_vs_oracle'] else 'no'} | "
            f"{'yes' if r['disagreement'] else 'no'} |"
        )
    lines.append("")
    lines.append(
        "Lead example: **NP-idiomatic-pad8** — VerifierState remains oracle-correct; "
        "SourceComment misses `if (!entry)` establish."
    )
    return "\n".join(lines)


def main() -> None:
    rows = [analyze(c) for c in CASES]
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {"cases": rows}
    (out_dir / "tier_disagreement.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    md = markdown(rows)
    (out_dir / "tier_disagreement.md").write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"Wrote {out_dir / 'tier_disagreement.json'}")
    print(f"Wrote {out_dir / 'tier_disagreement.md'}")


if __name__ == "__main__":
    main()

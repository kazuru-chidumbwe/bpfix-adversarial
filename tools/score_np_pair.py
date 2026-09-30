#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score the NullablePointer fixture pair (brittle vs idiomatic).

Both inputs are synthetic fixture logs with their own line numbering, not
captures of the committed mutants. The oracle is read from each fixture's own
ORACLE_* annotation rather than hardcoded, so the scored oracle and the log can
not drift apart.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.heuristics import looks_like_null_check  # noqa: E402
from bpfix_adversarial.logparse import (  # noqa: E402
    parse_verifier_log,
    reported_loss_from_events,
    sourcecomment_events,
)
from bpfix_adversarial.model import ProofEventRole  # noqa: E402
from bpfix_adversarial.score import score_honesty  # noqa: E402


def fixture_oracle(text: str) -> tuple[int, int]:
    """Read ORACLE_LOSS_LINE / ORACLE_REJECT_LINE from the fixture itself."""
    m = re.search(r"ORACLE_LOSS_LINE=(\d+)\s+ORACLE_REJECT_LINE=(\d+)", text)
    if not m:
        raise SystemExit("fixture carries no ORACLE_* annotation")
    return int(m.group(1)), int(m.group(2))


def score_fixture(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    oracle_loss, oracle_reject = fixture_oracle(text)
    log = parse_verifier_log(text)
    events = sourcecomment_events(log)
    # For NullablePointer honesty of *establish* recognition:
    established = [
        e
        for e in events
        if e.role == ProofEventRole.PROOF_ESTABLISHED
        and e.source
        and looks_like_null_check(e.source.text)
    ]
    check_recognized = bool(established)
    # Diagnostic that trusts SourceComment establish → reports check line as loss/establish
    reported = (
        established[-1].source.line
        if established and established[-1].source
        else reported_loss_from_events(events)
    )
    honesty = score_honesty(
        oracle_loss_code=oracle_loss,
        oracle_reject_line=oracle_reject,
        reported_loss_line=reported,
    )
    return {
        "fixture": path.relative_to(ROOT).as_posix(),
        "check_recognized_sourcecomment": check_recognized,
        "n_sourcecomment_events": len(events),
        "events": [e.to_dict() for e in events],
        "scores": honesty,
        "null_check_lines": [
            {"line": loc.line, "text": loc.text, "matched": looks_like_null_check(loc.text)}
            for loc in log.source_locations
            if loc.text.startswith("if ")
        ],
    }


def main() -> None:
    fixtures = ROOT / "fixtures" / "logs" / "synthetic"
    results = [
        score_fixture(fixtures / "NP-brittle-pad8.log"),
        score_fixture(fixtures / "NP-idiomatic-pad8.log"),
    ]
    out = {
        "figure": "NP rename pair end-to-end (fixture logs + SourceComment port)",
        "basis": (
            "Synthetic fixture logs with their own line numbering. Oracle read from "
            "each fixture's ORACLE_* annotation. Not a capture of the committed "
            "mutants and not comparable to results/sc_vs_honesty.json line numbers."
        ),
        "results": results,
        "paper_takeaway": (
            "Brittle `if (!ptr)` is recognized as ProofEstablished; "
            "idiomatic `if (!entry)` is not. SourceComment recognition breaks under rename."
        ),
    }
    out_path = ROOT / "results" / "np_pair_score.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

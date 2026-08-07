#!/usr/bin/env python3
"""Score NullablePointer fixture pair (brittle vs idiomatic) for paper Figure 1."""

from __future__ import annotations

import json
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


def score_fixture(path: Path, *, oracle_loss: int, oracle_reject: int) -> dict:
    text = path.read_text(encoding="utf-8")
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
        oracle_loss_line=oracle_loss,
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
        score_fixture(
            fixtures / "NP-brittle-pad8.log", oracle_loss=14, oracle_reject=24
        ),
        score_fixture(
            fixtures / "NP-idiomatic-pad8.log", oracle_loss=14, oracle_reject=24
        ),
    ]
    out = {
        "figure": "NP rename pair end-to-end (fixture logs + SourceComment port)",
        "results": results,
        "paper_takeaway": (
            "Brittle `if (!ptr)` is recognized as ProofEstablished; "
            "idiomatic `if (!entry)` is not — SourceComment honesty break under rename."
        ),
    }
    out_path = ROOT / "results" / "np_pair_score.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

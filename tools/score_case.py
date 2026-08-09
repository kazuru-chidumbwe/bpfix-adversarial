#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Score one adversarial case result against its oracle (stub)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def score(case: dict, reported_loss: int | None) -> dict:
    oracle = case["oracle"]
    d_true = oracle["reject_insn"] - oracle["loss_insn"]
    if reported_loss is None:
        return {
            "top1_loss_match": False,
            "distance_true": d_true,
            "distance_reported": None,
            "distance_error": None,
        }
    d_rep = oracle["reject_insn"] - reported_loss
    return {
        "top1_loss_match": reported_loss == oracle["loss_insn"],
        "distance_true": d_true,
        "distance_reported": d_rep,
        "distance_error": abs(d_rep - d_true),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("case_json", type=Path)
    p.add_argument("--reported-loss", type=int, default=None)
    args = p.parse_args()
    case = json.loads(args.case_json.read_text(encoding="utf-8"))
    print(json.dumps(score(case, args.reported_loss), indent=2))


if __name__ == "__main__":
    main()

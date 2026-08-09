# SPDX-License-Identifier: MIT
"""CLI for bpfix-adversarial."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import UPSTREAM_BPFIX, __version__
from .analyze import analyze_file, analyze_text_line
from .heuristics import classify_line
from .rename_attack import generate_rename_cases, summary


def _print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, sort_keys=True))


def cmd_heuristics(args: argparse.Namespace) -> int:
    hits = {k: v.to_dict() for k, v in classify_line(args.text).items()}
    _print_json({"text": args.text, "heuristics": hits, "upstream": UPSTREAM_BPFIX})
    return 0


def cmd_rename_demo(args: argparse.Namespace) -> int:
    cases = generate_rename_cases()
    if args.breaks_only:
        cases = [c for c in cases if c.honesty_break]
    payload = {
        "summary": summary(generate_rename_cases()),
        "cases": [c.to_dict() for c in cases],
        "upstream": UPSTREAM_BPFIX,
    }
    if args.limit is not None:
        payload["cases"] = payload["cases"][: args.limit]
    _print_json(payload)
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    if args.text is not None:
        _print_json(analyze_text_line(args.text))
        return 0
    path = Path(args.file)
    rows = analyze_file(path)
    if args.hits_only:
        rows = [
            r
            for r in rows
            if any(h["matched"] for h in r["heuristics"].values())
        ]
    _print_json({"file": str(path), "n": len(rows), "lines": rows})
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    _print_json({"bpfix_adversarial": __version__, "upstream": UPSTREAM_BPFIX})
    return 0


def cmd_score_log(args: argparse.Namespace) -> int:
    from .logparse import parse_verifier_log, reported_loss_from_events, sourcecomment_events
    from .score import score_honesty

    text = Path(args.log).read_text(encoding="utf-8")
    log = parse_verifier_log(text)
    events = sourcecomment_events(log)
    reported = reported_loss_from_events(events)
    scores = None
    if args.oracle_loss is not None and args.oracle_reject is not None:
        scores = score_honesty(
            oracle_loss_code=args.oracle_loss,
            oracle_reject_line=args.oracle_reject,
            reported_loss_line=reported,
        )
    _print_json(
        {
            "log": args.log,
            "terminal_error": log.terminal_error,
            "events": [e.to_dict() for e in events],
            "reported_loss_line": reported,
            "scores": scores,
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bpfix-adversarial",
        description=(
            "Controlled stress testing of eBPF diagnostic localization "
            "(injection-site agreement; SourceComment heuristics from eunomia-bpf/bpfix)."
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("heuristics", help="Classify one source line")
    h.add_argument("--text", required=True)
    h.set_defaults(func=cmd_heuristics)

    r = sub.add_parser(
        "rename-demo",
        help="Demonstrate looks_like_null_check rename brittleness",
    )
    r.add_argument("--breaks-only", action="store_true")
    r.add_argument("--limit", type=int, default=None)
    r.set_defaults(func=cmd_rename_demo)

    a = sub.add_parser("analyze", help="Analyze a C file or one --text line")
    a.add_argument("file", nargs="?", default=None)
    a.add_argument("--text", default=None)
    a.add_argument("--hits-only", action="store_true")
    a.set_defaults(func=cmd_analyze)

    s = sub.add_parser(
        "score-log",
        help="Parse verifier log fixture and score injection-site agreement",
    )
    s.add_argument("log")
    s.add_argument("--oracle-loss", type=int, default=None)
    s.add_argument("--oracle-reject", type=int, default=None)
    s.set_defaults(func=cmd_score_log)

    v = sub.add_parser("version")
    v.set_defaults(func=cmd_version)
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "analyze" and args.text is None and args.file is None:
        parser.error("analyze requires a file path or --text")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Emit RQ2 rename-honesty table (JSON + Markdown) for the paper inset."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.rename_attack import generate_rename_cases, summary  # noqa: E402


def markdown_table(cases) -> str:
    breaks = [c for c in cases if c.honesty_break]
    lines = [
        "| Original check | Renamed check | `looks_like_null_check` before | after | Honesty break |",
        "| --- | --- | --- | --- | --- |",
    ]
    # Compact inset: one row per brittle name → first safe rename that breaks
    seen = set()
    for c in breaks:
        if c.original_var in seen:
            continue
        seen.add(c.original_var)
        lines.append(
            f"| `{c.original_line}` | `{c.renamed_line}` | "
            f"{'yes' if c.original_null_check else 'no'} | "
            f"{'yes' if c.renamed_null_check else 'no'} | "
            f"{'yes' if c.honesty_break else 'no'} |"
        )
    lines.append("")
    lines.append(
        f"Full combinatorial matrix: **{len(breaks)}/{len(cases)}** "
        f"({100.0 * len(breaks) / len(cases):.1f}%) honesty breaks "
        f"(SourceComment null-check flips under idiomatic rename)."
    )
    lines.append("")
    lines.append(
        "Helper-anchored control: `bpf_map_lookup_elem` remains recognized "
        "under identifier rename (rename-insensitive)."
    )
    return "\n".join(lines)


def main() -> None:
    cases = generate_rename_cases()
    s = summary(cases)
    out_dir = ROOT / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": s,
        "cases": [c.to_dict() for c in cases],
        "upstream": {
            "repo": "https://github.com/eunomia-bpf/bpfix",
            "commit": "81d97e4a528456e0082a77f4fb6edd13fa092b7b",
            "predicate": "looks_like_null_check",
            "name_shaped": ["!tmp", "!val", "!ptr", "!value"],
        },
    }
    (out_dir / "rename_honesty.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    md = "# RQ2 inset — rename honesty of `looks_like_null_check`\n\n" + markdown_table(
        cases
    )
    (out_dir / "rename_honesty.md").write_text(md + "\n", encoding="utf-8")
    print(md)
    print(f"\nWrote {out_dir / 'rename_honesty.json'}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Metamorphic variants of the vendored upstream bpfix-bench cases (campaign v2).

For each fixtures/upstream/bpfix-bench-cases/<id>/buggy.bpf.c writes
campaigns/v2/upstream/<id>/:

  orig.bpf.c       unchanged copy (recaptured on the same host as the variants)
  pad8.bpf.c       8 volatile pad lines inserted immediately before the anchor
  pad32.bpf.c      32 volatile pad lines inserted immediately before the anchor
  rename.bpf.c     one local identifier used in an `if (!x)` check renamed, flipping
                   it across upstream's looks_like_null_check name list (only when
                   such an identifier exists and the rename is safe)
  transform.json   anchor, line shift, rename map, and the repair-site oracle
                   (bpfix_adversarial.repair_site) mapped into each variant's lines

Anchor = bpfix's committed `-->` line for the case (the rejected statement), or
its first snippet line when `-->` is 0. Padding goes between everything above the
use and the use itself. A case is skipped for padding when the anchor is not a
safe statement boundary (previous code line must end in ; { or }, and the
anchor must not start with } else case default #).
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.bpfix_output import parse_bpfix  # noqa: E402
from bpfix_adversarial.oracle import code_line_mask  # noqa: E402
from bpfix_adversarial.repair_site import diff_hunks, repair_sites  # noqa: E402

CASES = ROOT / "fixtures" / "upstream" / "bpfix-bench-cases"
OUT = ROOT / "campaigns" / "v2" / "upstream"
PADS = (8, 32)
BRITTLE = ("tmp", "val", "ptr", "value")
IDIOMATIC_TARGET = "entry_rn"  # not on upstream's list; unlikely to collide
BRITTLE_TARGET = "ptr"
CHECK_RE = re.compile(r"^\s*if\s*\(\s*!\s*([A-Za-z_]\w*)\s*\)")
NO_PAD_START = ("}", "else", "case ", "default", "#", "{")


def pad_block(n: int, indent: str) -> list[str]:
    out = [f"{indent}/* bpfix-adversarial v2 distance pad (volatile): {n} ops */",
           f"{indent}volatile __u64 __bpfix_pad = 0;"]
    out += [f"{indent}__bpfix_pad += {i + 1};" for i in range(n)]
    return out


def anchor_line(diag) -> int | None:
    if diag.primary:
        return diag.primary
    return diag.label_lines[0] if diag.label_lines else None


def pad_safe(lines: list[str], anchor: int) -> tuple[bool, str]:
    mask = code_line_mask(lines)
    if not (1 <= anchor <= len(lines)) or not mask[anchor - 1]:
        return False, "anchor is not a code line"
    text = lines[anchor - 1].strip()
    if text.startswith(NO_PAD_START):
        return False, f"anchor starts with {text.split()[0]!r}"
    prev = next((lines[i - 1].rstrip() for i in range(anchor - 1, 0, -1) if mask[i - 1]), "")
    if not prev.endswith((";", "{", "}")):
        return False, "previous code line is not a statement boundary"
    return True, ""


def rename_plan(text: str, lines: list[str], anchor: int | None) -> dict | None:
    """Pick one `if (!x)` identifier before the anchor and its rename target."""
    for i, ln in enumerate(lines, 1):
        if anchor is not None and i >= anchor:
            break
        m = CHECK_RE.match(ln)
        if not m:
            continue
        ident = m.group(1)
        if re.search(rf"#\s*define\s+{ident}\b", text) or re.search(rf"\b{ident}\s*\(", text):
            continue  # macro or function, not a local
        if not re.search(rf"[\w\s\*]\b{ident}\s*(=|;|,|\))", text):
            continue
        target = IDIOMATIC_TARGET if ident in BRITTLE else BRITTLE_TARGET
        if re.search(rf"\b{target}\b", text):
            continue
        return {"from": ident, "to": target, "check_line": i,
                "direction": "listed->idiomatic" if ident in BRITTLE else "idiomatic->listed"}
    return None


def apply_rename(text: str, old: str, new: str) -> str:
    # Not after '.' or '->' (struct members), whole word only.
    return re.sub(rf"(?<![\w.>])(?<!->){old}\b", new, text)


def main(out: Path = OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    summary = []
    for case in sorted(p for p in CASES.iterdir() if p.is_dir()):
        text = (case / "buggy.bpf.c").read_text(encoding="utf-8").replace("\r\n", "\n")
        fixed = (case / "fixed.bpf.c").read_text(encoding="utf-8").replace("\r\n", "\n")
        diag = parse_bpfix((case / "diagnostic.txt").read_text(encoding="utf-8"))
        lines = text.splitlines()
        sites = repair_sites(diff_hunks(text, fixed))
        anchor = anchor_line(diag)
        dest = out / case.name
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True)
        (dest / "orig.bpf.c").write_text(text, encoding="utf-8", newline="\n")
        variants: dict[str, dict] = {"orig": {"shift_from": None, "shift": 0, "repair_sites": sites}}

        ok, why = pad_safe(lines, anchor) if anchor else (False, "no anchor")
        if ok:
            indent = re.match(r"\s*", lines[anchor - 1]).group(0)
            for n in PADS:
                block = pad_block(n, indent)
                new = lines[: anchor - 1] + block + lines[anchor - 1 :]
                (dest / f"pad{n}.bpf.c").write_text("\n".join(new) + "\n", encoding="utf-8", newline="\n")
                k = len(block)
                variants[f"pad{n}"] = {
                    "shift_from": anchor,
                    "shift": k,
                    "repair_sites": [s + k if s >= anchor else s for s in sites],
                    "anchor_in_variant": anchor + k,
                }
        plan = rename_plan(text, lines, anchor)
        if plan:
            renamed = apply_rename(text, plan["from"], plan["to"])
            (dest / "rename.bpf.c").write_text(renamed, encoding="utf-8", newline="\n")
            variants["rename"] = {"shift_from": None, "shift": 0, "repair_sites": sites, **plan}
        meta = {
            "case_id": case.name,
            "error_id": diag.error_id,
            "anchor": anchor,
            "anchor_source": "primary" if diag.primary else "first_snippet_line",
            "pad_skipped": None if ok else why,
            "variants": variants,
        }
        (dest / "transform.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8", newline="\n")
        summary.append((case.name, sorted(variants), meta["pad_skipped"]))
    for name, vs, skip in summary:
        print(f"{name:40} {','.join(vs):28} {('pad skipped: ' + skip) if skip else ''}")


if __name__ == "__main__":
    main()

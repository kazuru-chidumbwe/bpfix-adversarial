#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verifier-level check that padding and renaming leave the loaded program unchanged.

Reads the SoftwareX-stamp captures and compares, across pads 0/8/32 for each
rejecting template and within each NullablePointer brittle/idiomatic rename
pair: verdict, processed-instruction count, reject message, and the sequence of
verifier-listed instructions. The only value masked is the kernel address that
the loader patches into ld_imm64 map references (0xffff...), which changes from
one load to the next.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.score_sc_vs_honesty import lab_rejected  # noqa: E402

CAP = ROOT / "fixtures" / "logs" / "captured"
STAMP = "20260801T181331Z"
OUT_JSON = ROOT / "results" / "pad_rename_invariance.json"
OUT_MD = ROOT / "results" / "pad_rename_invariance.md"

INSN_RE = re.compile(r"^\s*(\d+): \(([0-9a-f]{2})\)\s*(.*?)\s*(?:;.*)?$")
PROCESSED_RE = re.compile(r"^processed (\d+) insns")
KADDR_RE = re.compile(r"0xffff[0-9a-f]{12}")
PADS = (0, 8, 32)


def load_facts(case_id: str) -> dict:
    path = CAP / f"{case_id}.{STAMP}.log"
    text = path.read_text(encoding="utf-8", errors="replace")
    body = text.split("BEGIN PROG LOAD LOG", 1)[1].split("END PROG LOAD LOG", 1)[0]
    lines = body.splitlines()
    insns = []
    for ln in lines:
        m = INSN_RE.match(ln)
        if m:
            operands = KADDR_RE.sub("0xKADDR", " ".join(m.group(3).split()))
            insns.append(f"{m.group(1)}:{m.group(2)}:{operands}")
    processed = next(int(m.group(1)) for ln in lines if (m := PROCESSED_RE.match(ln)))
    rejected = lab_rejected(text)
    reject_message = None
    if rejected:
        vt = next(i for i, ln in enumerate(lines) if ln.startswith("verification time"))
        reject_message = lines[vt - 1].strip()
    return {
        "case_id": case_id,
        "log": str(path.relative_to(ROOT)).replace("\\", "/"),
        "verdict": "REJECT" if rejected else "ACCEPT",
        "processed_insns": processed,
        "reject_message": reject_message,
        "insn_lines": len(insns),
        "insn_sequence_sha256": hashlib.sha256("\n".join(insns).encode()).hexdigest(),
    }


def same(rows: list[dict], keys: tuple[str, ...]) -> bool:
    return all(all(r[k] == rows[0][k] for k in keys) for r in rows)


def main() -> None:
    keys = ("verdict", "processed_insns", "reject_message", "insn_sequence_sha256")
    pad_groups = []
    for prefix, family in (("PB", "PacketBounds"), ("PP", "PointerProvenance"), ("SR", "ScalarRange")):
        rows = [load_facts(f"{prefix}-pad{p}") for p in PADS]
        pad_groups.append({"family": family, "identical": same(rows, keys), "rows": rows})
    rename_pairs = []
    for p in PADS:
        rows = [load_facts(f"NP-brittle-pad{p}"), load_facts(f"NP-idiomatic-pad{p}")]
        rename_pairs.append({"pad": p, "identical": same(rows, keys), "rows": rows})

    payload = {
        "stamp": STAMP,
        "compared": list(keys),
        "masked": "kernel address patched into ld_imm64 map references (0xffff...)",
        "pad_invariance": pad_groups,
        "rename_invariance": rename_pairs,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")

    lines = [
        "# Pad and rename invariance at the verifier",
        "",
        f"SoftwareX-stamp captures `{STAMP}`. Compared: verdict, processed-instruction "
        "count, reject message, and the verifier-listed instruction sequence (the "
        "load-time kernel address in `ld_imm64` map references is masked).",
        "",
        "## Padding (pads 0 / 8 / 32)",
        "",
        "| Family | Verdict | Processed insns | Reject message | Identical across pads |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for g in pad_groups:
        r = g["rows"][0]
        lines.append(
            f"| {g['family']} | {r['verdict']} | {r['processed_insns']} | "
            f"{r['reject_message']} | {'yes' if g['identical'] else 'no'} |"
        )
    lines += [
        "",
        "## Renaming (NullablePointer `ptr` vs `entry`)",
        "",
        "| Pad | Verdict | Processed insns | Identical within pair |",
        "| ---: | --- | ---: | --- |",
    ]
    for pr in rename_pairs:
        r = pr["rows"][0]
        lines.append(
            f"| {pr['pad']} | {r['verdict']} | {r['processed_insns']} | "
            f"{'yes' if pr['identical'] else 'no'} |"
        )
    lines += [
        "",
        "This shows the verifier processes the same program before and after each "
        "transformation on this pin. It is not a proof of semantic equivalence.",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"Wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

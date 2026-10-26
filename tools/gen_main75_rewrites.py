#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate the verifier-visible rewrites of docs/MAIN75-PIN-PROTOCOL.md Section 7.

For each main75 case, every rewrite (VPAD, MACRO, INLINE, REORDER, SPLIT) is
applied to both buggy.bpf.c and fixed.bpf.c where its precondition holds. The
anchor is bpfix's primary line in the pin capture of buggy. Writes
``campaigns/n3/<case>/<ID>.buggy.bpf.c`` / ``<ID>.fixed.bpf.c`` and
``campaigns/n3/rewrites.json`` (applied or the reason it was not).

Usage: python tools/gen_main75_rewrites.py --run campaigns/main75/lab/<run>
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.bpfix_output import parse_bpfix  # noqa: E402
from bpfix_adversarial.oracle import code_line_mask  # noqa: E402

CASES = ROOT / "fixtures" / "upstream" / "bpfix-bench-cases"
OUT = ROOT / "campaigns" / "n3"
REWRITES = ("VPAD", "VPADC", "MACRO", "INLINE", "REORDER", "SPLIT")
PAD = "{ volatile __u32 __adv_pad = 0; __adv_pad++; }"
NPAD = 8

TYPE_WORDS = {
    "int", "long", "short", "char", "unsigned", "signed", "const", "volatile", "struct", "void", "bool",
    "size_t", "static", "__always_inline", "inline",
} | {f"{p}{n}" for p in ("__u", "__s", "u", "s", "__be", "__le") for n in (8, 16, 32, 64)}
KEYWORDS = TYPE_WORDS | {"if", "else", "return", "for", "while", "do", "break", "continue", "goto", "sizeof",
                         "switch", "case", "default", "NULL", "true", "false"}
SIMPLE_TYPE = r"(?:const\s+)?(?:struct\s+\w+|unsigned\s+\w+|__[us]\d+|[us]\d+|__be\d+|__le\d+|int|long|char|void|bool|size_t)"
DECL_RE = re.compile(rf"^\s*({SIMPLE_TYPE})\s*(\**)\s*(\w+)\s*(=|;)")
DECL_START = re.compile(rf"^\s*{SIMPLE_TYPE}[\s\*]+\w+\s*(=|;|\[)")
IDENT = re.compile(r"[A-Za-z_]\w*")


def code_mask(lines: list[str]) -> list[bool]:
    return code_line_mask([ln.rstrip() for ln in lines])


def find_once(lines: list[str], text: str) -> int | None:
    hits = [i for i, ln in enumerate(lines) if ln.strip() == text]
    return hits[0] if len(hits) == 1 else None


def prev_code(lines: list[str], i: int) -> int | None:
    mask = code_mask(lines)
    for j in range(i - 1, -1, -1):
        if mask[j]:
            return j
    return None


def next_code(lines: list[str], i: int) -> int | None:
    mask = code_mask(lines)
    for j in range(i + 1, len(lines)):
        if mask[j]:
            return j
    return None


def indent(s: str) -> str:
    return s[: len(s) - len(s.lstrip())]


def func_start(lines: list[str], i: int) -> int | None:
    """Index of the first line of the function containing line i (SEC() line if present)."""
    for j in range(i, -1, -1):
        ln = lines[j]
        if ln and not ln[0].isspace() and ln.strip() not in ("{", "}") and "(" in ln \
                and not ln.lstrip().startswith(("#", "//", "/*", "*")) and not ln.rstrip().endswith(";"):
            k = j
            if k > 0 and lines[k - 1].startswith("SEC("):
                k -= 1
            return k
    return None


def idents(s: str) -> set[str]:
    out = set()
    for m in IDENT.finditer(s):
        before = s[max(0, m.start() - 2): m.start()]
        if before.endswith("->") or before.endswith("."):
            continue  # member name
        out.add(m.group(0))
    return out - KEYWORDS


def has_call(s: str) -> bool:
    for m in re.finditer(r"([A-Za-z_]\w*)\s*\(", s):
        if m.group(1) not in KEYWORDS:
            return True
    return False


def if_condition(line: str) -> tuple[int, int] | None:
    """(start, end) indices of the condition of a leading ``if (`` on this line."""
    m = re.match(r"^\s*if\s*\(", line)
    if not m:
        return None
    depth, start = 1, m.end()
    for k in range(start, len(line)):
        if line[k] == "(":
            depth += 1
        elif line[k] == ")":
            depth -= 1
            if depth == 0:
                return start, k
    return None


def top_level_split(cond: str, op: str) -> list[str] | None:
    parts, depth, cur, k = [], 0, "", 0
    while k < len(cond):
        c = cond[k]
        depth += c == "("
        depth -= c == ")"
        if depth == 0 and cond.startswith(op, k):
            parts.append(cur.strip())
            cur, k = "", k + len(op)
            continue
        cur += c
        k += 1
    parts.append(cur.strip())
    return parts if len(parts) > 1 else None


# --- the five rewrites: each returns (new_lines, None) or (None, reason) ------------

def vpad(lines: list[str], a: int):
    p = prev_code(lines, a)
    if p is None or not lines[p].rstrip().endswith((";", "{", "}")):
        return None, "previous code line does not end a statement"
    ind = indent(lines[a])
    return lines[:a] + [ind + PAD] * NPAD + lines[a:], None


def macro(lines: list[str], a: int):
    s = lines[a].strip()
    if not s.endswith(";") or s.count(";") != 1:
        return None, "anchor is not one statement ending in ';'"
    if re.match(r"^(return|break|continue)\b", s) or DECL_START.match(s):
        return None, "anchor is a declaration, return, break or continue"
    inc = [i for i, ln in enumerate(lines) if ln.lstrip().startswith("#include")]
    if not inc:
        return None, "no #include to place the macro after"
    new = list(lines)
    new[a] = indent(lines[a]) + f"ADV_STMT({s[:-1]});"
    at = inc[-1] + 1
    return new[:at] + ["#define ADV_STMT(...) \\", "\t__VA_ARGS__"] + new[at:], None


def nearest_if(lines: list[str], a: int, f0: int):
    for j in range(a - 1, f0, -1):
        if if_condition(lines[j]):
            return j
    return None


def inline(lines: list[str], a: int):
    f0 = func_start(lines, a)
    if f0 is None:
        return None, "function start not found"
    j = nearest_if(lines, a, f0)
    if j is None:
        return None, "no if above the anchor in this function"
    s, e = if_condition(lines[j])
    cond = lines[j][s:e]
    if re.search(r"(?<![=!<>])=(?!=)", cond) or has_call(cond) or "sizeof" in cond:
        return None, "condition has an assignment, call or sizeof"
    names = sorted(n for n in idents(cond) if not n.isupper())
    if not names:
        return None, "condition has no local identifier"
    header_end = next((k for k in range(f0, a) if "{" in lines[k] or lines[k].rstrip().endswith(")")), f0)
    header = " ".join(lines[f0: header_end + 1])
    params: list[str] = []
    for n in names:
        decl = None
        for k in range(f0, j):
            m = DECL_RE.match(lines[k])
            if m and m.group(3) == n:
                decl = f"{m.group(1)} {m.group(2)}{n}"
        if decl is None:
            m = re.search(rf"({SIMPLE_TYPE})\s*(\**)\s*{n}\s*[,)]", header)
            decl = f"{m.group(1)} {m.group(2)}{n}" if m else None
        if decl is None:
            return None, f"no simple one-line declaration for '{n}'"
        params.append(decl)
    helper = f"static __always_inline int __adv_guard({', '.join(params)}) {{ return ({cond}); }}"
    new = list(lines)
    new[j] = lines[j][:s] + f"__adv_guard({', '.join(names)})" + lines[j][e:]
    return new[:f0] + [helper, ""] + new[f0:], None


def reorder(lines: list[str], a: int):
    p = prev_code(lines, a)
    if p is None:
        return None, "no previous code line"
    x, y = lines[p].strip(), lines[a].strip()
    for s in (x, y):
        if not s.endswith(";") or s.count(";") != 1:
            return None, "a statement is not single-line ending in ';'"
        if has_call(s) or re.match(r"^return\b", s) or re.match(r"^\w+\s*:", s) or "{" in s or "}" in s:
            return None, "a statement has a call, return, label or brace"
    if idents(x) & idents(y):
        return None, "the statements share an identifier"
    new = list(lines)
    new[p], new[a] = indent(lines[p]) + y, indent(lines[a]) + x
    return new, None


def split(lines: list[str], a: int):
    f0 = func_start(lines, a)
    if f0 is None:
        return None, "function start not found"
    for j in range(a - 1, f0, -1):
        c = if_condition(lines[j])
        if not c:
            continue
        s, e = c
        cond, rest = lines[j][s:e], lines[j][e + 1:]
        ands, ors = top_level_split(cond, "&&"), top_level_split(cond, "||")
        if ands and ors:
            continue
        nx = next_code(lines, j)
        if rest.strip().endswith("{"):
            depth, k = 0, j
            while k < len(lines):
                depth += lines[k].count("{") - lines[k].count("}")
                if depth == 0 and k > j:
                    break
                k += 1
            nx = next_code(lines, k) if k < len(lines) else None
        if nx is not None and lines[nx].strip().startswith("else"):
            continue
        ind = indent(lines[j])
        if ands:
            new = list(lines)
            new[j] = ind + " ".join(f"if ({p})" for p in ands) + rest
            return new, None
        if ors and re.match(r"^\s*return\b[^;]*;\s*$", rest):
            new = list(lines)
            new[j] = ind + " ".join(f"if ({p}){rest}" for p in ors).replace("  ", " ")
            return new, None
    return None, "no splittable one-line if above the anchor"


FUNCS = {"VPAD": vpad, "VPADC": vpad, "MACRO": macro, "INLINE": inline, "REORDER": reorder, "SPLIT": split}


def counterpart(buggy: list[str], fixed: list[str], a: int) -> int | None:
    """Line of fixed that buggy line a corresponds to in the buggy -> fixed diff.

    Equal blocks map one to one; a replaced block maps its first line to the
    first line of the replacement; a deleted line has no counterpart.
    """
    import difflib

    sm = difflib.SequenceMatcher(a=[s.rstrip() for s in buggy], b=[s.rstrip() for s in fixed], autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if i1 <= a < i2:
            if tag == "equal":
                return j1 + (a - i1)
            if tag == "replace":
                return j1 + min(a - i1, j2 - j1 - 1)
            return None
    return None


def apply_both(rid: str, buggy: list[str], fixed: list[str], a: int):
    anchor = buggy[a].strip()
    if rid == "VPAD":
        fa = find_once(fixed, anchor)
        if find_once(buggy, anchor) is None or fa is None:
            return None, None, "anchor line not found exactly once in both files"
    else:
        fa = counterpart(buggy, fixed, a)
        if fa is None:
            return None, None, "anchor deleted by the fix (no counterpart in fixed)"
    nb, why = FUNCS[rid](buggy, a)
    if nb is None:
        return None, None, why
    nf, why = FUNCS[rid](fixed, fa)
    if nf is None:
        return None, None, f"fixed: {why}"
    return nb, nf, None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    args = ap.parse_args(argv)
    run = args.run if args.run.is_absolute() else ROOT / args.run

    if OUT.exists():
        shutil.rmtree(OUT)
    table: dict = {}
    for cdir in sorted(p for p in CASES.iterdir() if p.is_dir()):
        cid = cdir.name
        bp = sorted((run / "buggy").glob(f"{cid}__buggy.*.bpfix.txt"))
        primary = parse_bpfix(bp[-1].read_text(encoding="utf-8", errors="replace")).primary if bp else None
        row: dict = {"anchor": primary}
        buggy = cdir.joinpath("buggy.bpf.c").read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
        fixed = cdir.joinpath("fixed.bpf.c").read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
        for rid in REWRITES:
            if not primary or primary > len(buggy):
                row[rid] = {"applied": False, "reason": "no bpfix primary line"}
                continue
            nb, nf, why = apply_both(rid, buggy, fixed, primary - 1)
            if why:
                row[rid] = {"applied": False, "reason": why}
                continue
            d = OUT / cid
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{rid}.buggy.bpf.c").write_text("\n".join(nb), encoding="utf-8", newline="\n")
            (d / f"{rid}.fixed.bpf.c").write_text("\n".join(nf), encoding="utf-8", newline="\n")
            row[rid] = {"applied": True}
        table[cid] = row
    counts = {rid: sum(1 for r in table.values() if r[rid]["applied"]) for rid in REWRITES}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "rewrites.json").write_text(json.dumps({"generator": "tools/gen_main75_rewrites.py",
                                                    "anchor_run": run.relative_to(ROOT).as_posix(),
                                                    "applied": counts, "cases": table}, indent=1) + "\n",
                                       encoding="utf-8", newline="\n")
    print(json.dumps(counts))
    return 0


if __name__ == "__main__":
    sys.exit(main())

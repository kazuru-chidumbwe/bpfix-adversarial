#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus pass 3: build and load each pass-2 survivor on the cite pin.

Implements "Pass 3 procedure" in docs/WILD-CORPUS-PROTOCOL.md. Runs ON the lab
host (needs git, clang, sudo for loading, and a built tools/wildload). In
screening order, for every candidate that passed pass 2 and has no row yet in
fixtures/wild/pass3.jsonl: build parent and fix, load the objects that depend
on a changed file, decide, and append one row. Stops at 30 included cases or
after the stop date. Included cases are stored under fixtures/wild/cases/.

Environment: WILD_WORK (default ~/wild: repos/, tmp/, wildload binary),
WILDLOAD (loader path), WILD_TIMEBOX (seconds per candidate, default 7200).

Usage: python3 tools/wild_pass3.py [--max-candidates N]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.logparse import verifier_error_block  # noqa: E402

WILD = ROOT / "fixtures" / "wild"
OUT = WILD / "pass3.jsonl"
CASES = WILD / "cases"
WORK = Path(os.environ.get("WILD_WORK", "~/wild")).expanduser()
WILDLOAD = os.environ.get("WILDLOAD", str(WORK / "wildload"))
TIMEBOX = int(os.environ.get("WILD_TIMEBOX", "7200"))
PIN_ROOT = "/sys/fs/bpf/wildload"
STOP_DATE = dt.date(2026, 11, 8)
MAX_INCLUDED = 30
MAKE_BPF = {"cilium/tetragon", "cilium/cilium"}

COMPLEXITY = re.compile(r"too large|1000001|BPF program is too large|combined stack size|jump sequence of|"
                        r"back-edge|infinite loop|loop is not bounded|insns? limit", re.I)
ENVIRONMENT = re.compile(r"unknown func|invalid func|cannot use helper|helper call is not allowed|kfunc|"
                         r"attach_btf|attach to|not supported|unsupported|missing btf|BTF is required|"
                         r"invalid btf|tail_calls are not allowed|cannot call GPL-restricted|unknown opcode|"
                         r"Invalid argument$", re.I)


class TimeBox(Exception):
    pass


def run(cmd, cwd=None, timeout=None, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace",
                          timeout=timeout, env=env, shell=isinstance(cmd, str))


def left(deadline: float) -> float:
    t = deadline - time.time()
    if t <= 0:
        raise TimeBox()
    return t


def ensure_repo(repo: str) -> Path:
    d = WORK / "repos" / repo.replace("/", "_")
    if not (d / ".git").exists() and not (d / "HEAD").exists():
        d.parent.mkdir(parents=True, exist_ok=True)
        p = run(["git", "clone", "-q", "--filter=blob:none", "--no-checkout", f"https://github.com/{repo}", str(d)],
                timeout=3600)
        if p.returncode:
            raise RuntimeError(f"clone failed: {p.stderr.strip()[-300:]}")
    return d


def worktree(repo_dir: Path, rev: str, dest: Path, deadline: float) -> None:
    if dest.exists():
        run(["git", "-C", str(repo_dir), "worktree", "remove", "--force", str(dest)])
        shutil.rmtree(dest, ignore_errors=True)
    run(["git", "-C", str(repo_dir), "worktree", "prune"])
    p = run(["git", "-C", str(repo_dir), "worktree", "add", "-q", "-f", "--detach", str(dest), rev],
            timeout=left(deadline))
    if p.returncode:
        raise RuntimeError(f"worktree {rev[:8]}: {p.stderr.strip()[-300:]}")


def drop_worktree(repo_dir: Path, dest: Path) -> None:
    run(["git", "-C", str(repo_dir), "worktree", "remove", "--force", str(dest)])
    shutil.rmtree(dest, ignore_errors=True)


def parse_compile_cmds(log: str, base: Path) -> list[dict]:
    """clang -c commands from a verbose make log, with the directory each ran in."""
    cmds, cwd = [], base
    for line in log.splitlines():
        m = re.search(r"Entering directory '([^']+)'", line)
        if m:
            cwd = Path(m.group(1))
            continue
        if "clang" not in line or " -c " not in line or " -o " not in line:
            continue
        clang_part = line.split("|")[0].strip()
        try:
            toks = shlex.split(clang_part)
        except ValueError:
            continue
        if not any("bpf" in t for t in toks):
            continue
        src = toks[toks.index("-c") + 1] if "-c" in toks else None
        try:
            obj_toks = shlex.split(line.split("|")[-1]) if "|" in line else toks
        except ValueError:
            continue
        o_idx = [i for i, t in enumerate(obj_toks) if t == "-o"]
        obj = obj_toks[o_idx[-1] + 1] if o_idx and o_idx[-1] + 1 < len(obj_toks) else None
        if src and obj and obj != "-":
            cmds.append({"cwd": str(cwd), "clang": toks, "src": src, "obj": obj, "line": line.strip()})
    return cmds


def deps_of(cmd: dict, deadline: float) -> list[str]:
    toks = [t for t in cmd["clang"] if t not in ("-c", "-emit-llvm")]
    out = []
    skip = False
    for t in toks:
        if skip:
            skip = False
            continue
        if t == "-o":
            skip = True
            continue
        if t == cmd["src"]:
            continue
        out.append(t)
    p = run(out + ["-MM", cmd["src"]], cwd=cmd["cwd"], timeout=min(300, left(deadline)))
    text = p.stdout.replace("\\\n", " ")
    return [str((Path(cmd["cwd"]) / d).resolve()) for d in text.split()[1:]] if p.returncode == 0 else []


def build_make(wt: Path, deadline: float) -> tuple[list[dict], str]:
    p = run(["make", "-C", "bpf", "-j4", "V=1"], cwd=wt, timeout=left(deadline))
    if p.returncode:
        raise RuntimeError("make failed: " + (p.stdout + p.stderr).strip()[-600:])
    return parse_compile_cmds(p.stdout + p.stderr, wt / "bpf"), "project build"


def include_dirs(wt: Path, unit: Path) -> list[str]:
    dirs, d = [], unit.parent
    while True:
        dirs.append(d)
        for name in ("include", "headers", "libbpf", "x86", "arch/x86", "vmlinux", "bpf"):
            if (d / name).is_dir():
                dirs.append(d / name)
        if d == wt:
            break
        d = d.parent
    seen, out = set(), []
    for x in dirs:
        if x not in seen:
            seen.add(x)
            out.append(str(x))
    return out


def build_direct(wt: Path, changed: list[str], vmlinux_dir: str, objdir: Path, deadline: float):
    units: set[Path] = set()
    for rel in changed:
        f = wt / rel
        if not f.is_file():
            continue
        if rel.endswith(".c") and "SEC(" in f.read_text(errors="replace"):
            units.add(f)
        elif rel.endswith(".h"):
            name = re.escape(Path(rel).name)
            g = run(f"grep -rlE '#include.*[\"</]{name}[\">]' --include='*.c' .", cwd=wt, timeout=min(300, left(deadline)))
            for hit in g.stdout.split():
                h = (wt / hit).resolve()
                if "SEC(" in h.read_text(errors="replace"):
                    units.add(h)
    cmds, errors = [], []
    objdir.mkdir(parents=True, exist_ok=True)
    for u in sorted(units)[:40]:
        obj = objdir / (u.relative_to(wt).as_posix().replace("/", "__") + ".o")
        inc = sum((["-I", d] for d in include_dirs(wt, u)), [])
        clang = ["clang", "-g", "-O2", "-target", "bpf", "-D__TARGET_ARCH_x86", *inc, "-I", vmlinux_dir,
                 "-I", "/usr/include", "-c", str(u), "-o", str(obj)]
        p = run(clang, cwd=u.parent, timeout=min(600, left(deadline)))
        if p.returncode == 0:
            cmds.append({"cwd": str(u.parent), "clang": clang, "src": str(u), "obj": str(obj), "line": shlex.join(clang)})
        else:
            errors.append(f"{u.relative_to(wt)}: {p.stderr.strip()[-200:]}")
    if not cmds:
        raise RuntimeError("direct compile failed: " + (" | ".join(errors) or "no compilation unit found"))
    return cmds, "direct compile"


def load(obj: Path, outdir: Path, tag: str, deadline: float) -> dict[str, dict]:
    outdir.mkdir(parents=True, exist_ok=True)
    pin = f"{PIN_ROOT}/{tag}"
    run(["sudo", "-n", "mkdir", "-p", pin])
    p = run(["sudo", "-n", "env", f"WILDLOAD_PIN_ROOT={pin}", WILDLOAD, str(obj), str(outdir)],
            timeout=min(1800, left(deadline)))
    run(["sudo", "-n", "rm", "-rf", pin])
    run(["sudo", "-n", "chown", "-R", f"{os.getuid()}:{os.getgid()}", str(outdir)])
    res: dict[str, dict] = {}
    for line in p.stdout.splitlines():
        parts = line.split(" ", 4)
        if len(parts) >= 4 and parts[0] == "PROG":
            res[parts[1]] = {"verdict": parts[2], "errno": int(parts[3]), "section": parts[4] if len(parts) > 4 else "",
                             "log": str(outdir / f"{parts[1]}.log")}
    return res


def reject_kind(log_path: str) -> str:
    text = Path(log_path).read_text(errors="replace") if Path(log_path).is_file() else ""
    lines = text.splitlines()
    block = verifier_error_block(lines)
    msg = " ".join(block[1]) if block else ""
    if not msg:
        return "environment"
    if COMPLEXITY.search(msg):
        return "complexity"
    if ENVIRONMENT.search(msg):
        return "environment"
    return "safety"


def git_show(repo_dir: Path, rev: str, path: str) -> str | None:
    p = run(["git", "-C", str(repo_dir), "show", f"{rev}:{path}"])
    return p.stdout if p.returncode == 0 else None


GUARD_LINE = re.compile(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)")
MAX_DEFINES = 12


def positive_macros(kind: str, cond: str) -> set[str]:
    """Macros that must be defined (non-zero) for a branch to be taken."""
    cond = cond.split("//")[0].split("/*")[0].strip()
    if kind == "ifdef":
        return {cond.split()[0]} if cond else set()
    if kind != "if":
        return set()  # ifndef / else: enabling a macro would not take the branch
    names = {m.group(2) for m in re.finditer(r"(!\s*)?defined\s*\(?\s*([A-Za-z_]\w*)", cond) if not m.group(1)}
    rest = re.sub(r"!?\s*defined\s*\(?\s*[A-Za-z_]\w*\s*\)?", " ", cond)
    names |= {m.group(2) for m in re.finditer(r"(!\s*)?\b([A-Z_][A-Z0-9_]{2,})\b", rest) if not m.group(1)}
    return names


def guards(text: str, changed: set[int]) -> set[str]:
    stack: list[tuple[str, str]] = []
    out: set[str] = set()
    for i, line in enumerate(text.splitlines(), 1):
        m = GUARD_LINE.match(line)
        if m:
            kind, cond = m.group(1), m.group(2).strip()
            if kind in ("if", "ifdef", "ifndef"):
                stack.append((kind, cond))
            elif kind == "elif" and stack:
                stack[-1] = ("if", cond)
            elif kind == "else" and stack:
                stack[-1] = ("else", stack[-1][1])
            elif kind == "endif" and stack:
                stack.pop()
            continue
        if i in changed:
            for k, cnd in stack:
                out |= positive_macros(k, cnd)
    return out


def feature_macros(repo_dir: Path, parent: str, fix: str, files: list[str]) -> list[str]:
    import difflib

    found: set[str] = set()
    for rel in files:
        a, b = git_show(repo_dir, parent, rel), git_show(repo_dir, fix, rel)
        if a is None or b is None:
            continue
        al, bl = a.splitlines(), b.splitlines()
        changed: set[int] = set()
        for tag, i1, i2, _j1, _j2 in difflib.SequenceMatcher(a=al, b=bl, autojunk=False).get_opcodes():
            if tag == "equal":
                continue
            changed |= set(range(i1 + 1, i2 + 1)) if i2 > i1 else {i1, i1 + 1}
        found |= guards(a, changed)
    return sorted(found)[:MAX_DEFINES]


def with_defines(cmd: dict, defines: list[str], out: Path) -> str:
    defs = " ".join(f"-D{d}=1" for d in defines)
    line = re.sub(r"(^|\s)(\S*clang\S*)(\s)", lambda m: f"{m.group(1)}{m.group(2)} {defs}{m.group(3)}", cmd["line"], count=1)
    i = line.rfind(" -o ")
    tail = line[i + 4:].split(None, 1)
    return line[:i] + f" -o {shlex.quote(str(out))}" + (" " + tail[1] if len(tail) > 1 else "")


def load_objects(selected: list[dict], tmp: Path, side: str, rank: int, deadline: float,
                 defines: list[str] | None = None) -> dict:
    objs = {}
    for cmd in selected:
        obj = (Path(cmd["cwd"]) / cmd["obj"]).resolve()
        tag = "feat" if defines else "keep"
        stash = tmp / f"{side}-{tag}" / obj.name
        stash.parent.mkdir(parents=True, exist_ok=True)
        line = cmd["line"]
        if defines:
            line = with_defines(cmd, defines, stash)
            p = run(line, cwd=cmd["cwd"], timeout=min(900, left(deadline)))
            if p.returncode or not stash.is_file():
                continue
        else:
            if not obj.is_file():
                continue
            shutil.copy2(obj, stash)
        key = Path(cmd["src"]).name + "::" + obj.name
        objs[key] = {"obj": str(stash), "cmd": line,
                     "progs": load(stash, tmp / f"{side}-{tag}-logs" / obj.stem, f"{rank}-{side}-{tag}", deadline)}
    return objs


def decide(par: dict, fix: dict) -> tuple[str, list, list]:
    flips, rejects = [], []
    for key in sorted(par):
        for prog, r in sorted(par[key]["progs"].items()):
            if r["verdict"] != "REJECT":
                continue
            kind = reject_kind(r["log"])
            rejects.append({"object": key, "program": prog, "kind": kind})
            f = fix.get(key, {}).get("progs", {}).get(prog)
            if kind == "safety" and f and f["verdict"] == "ACCEPT":
                flips.append({"object": key, "program": prog, "section": r["section"]})
    if flips:
        return "included", flips, rejects
    if not rejects:
        return "E4", flips, rejects
    if any(x["kind"] == "safety" for x in rejects):
        return "I3", flips, rejects
    return ("C" if all(x["kind"] == "complexity" for x in rejects) else "I4"), flips, rejects


def screen(c: dict, files: list[str], vmlinux_dir: str) -> dict:
    deadline = time.time() + TIMEBOX
    rank = c["screen_rank"]
    row = {"screen_rank": rank, "repo": c["repo"], "commit": c["commit"], "started": dt.datetime.utcnow().isoformat() + "Z"}
    tmp = WORK / "tmp" / f"{rank:03d}"
    repo_dir = ensure_repo(c["repo"])
    if run(["git", "-C", str(repo_dir), "cat-file", "-e", c["commit"]]).returncode:
        run(["git", "-C", str(repo_dir), "fetch", "-q", "origin", c["commit"]], timeout=left(deadline))
    parent = run(["git", "-C", str(repo_dir), "rev-parse", f"{c['commit']}^"]).stdout.strip()
    row["parent"] = parent
    selected: dict[str, list[dict]] = {}
    try:
        for side, rev in (("parent", parent), ("fix", c["commit"])):
            wt = tmp / side
            worktree(repo_dir, rev, wt, deadline)
            try:
                if c["repo"] in MAKE_BPF:
                    cmds, btype = build_make(wt, deadline)
                else:
                    cmds, btype = build_direct(wt, files, vmlinux_dir, tmp / f"{side}-objs", deadline)
            except RuntimeError as e:
                row.update(outcome="E5", note=f"{side}: {e}"[:800])
                return row
            row["build_type"] = btype
            changed_abs = {str((wt / f).resolve()) for f in files}
            selected[side] = [cmd for cmd in cmds
                              if btype == "direct compile" or changed_abs & set(deps_of(cmd, deadline))]
        par = load_objects(selected["parent"], tmp, "parent", rank, deadline)
        fix = load_objects(selected["fix"], tmp, "fix", rank, deadline)
        outcome, flips, rejects = decide(par, fix)
        row.update(decided_by="default", n_objects={"parent": len(par), "fix": len(fix)})
        if outcome == "E4":
            defines = feature_macros(repo_dir, parent, c["commit"], files)
            row["feature_macros"] = defines
            if defines:
                par_f = load_objects(selected["parent"], tmp, "parent", rank, deadline, defines)
                fix_f = load_objects(selected["fix"], tmp, "fix", rank, deadline, defines)
                if par_f and fix_f:
                    outcome, flips, rejects = decide(par_f, fix_f)
                    par, fix = par_f, fix_f
                    row.update(decided_by="features", n_objects={"parent": len(par), "fix": len(fix)})
                else:
                    row["feature_build"] = "failed at one commit; default decision kept"
    except TimeBox:
        row.update(outcome="E5", note="2-hour time box")
        return row
    finally:
        for side in ("parent", "fix"):
            drop_worktree(repo_dir, tmp / side)

    row.update(outcome=outcome, parent_rejects=rejects, flips=flips)
    if outcome == "included":
        store(c, row, flips[0], par, fix, files, repo_dir, parent)
    shutil.rmtree(tmp, ignore_errors=True)
    return row


def store(c, row, flip, par, fix, files, repo_dir, parent) -> None:
    d = CASES / f"{c['screen_rank']:03d}"
    shutil.rmtree(d, ignore_errors=True)
    for side, rev in (("parent", parent), ("fix", c["commit"])):
        for rel in files:
            text = git_show(repo_dir, rev, rel)
            if text is not None:
                p = d / side / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding="utf-8", newline="\n")
    k, prog = flip["object"], flip["program"]
    shutil.copy2(par[k]["progs"][prog]["log"], d / "buggy.log")
    shutil.copy2(fix[k]["progs"][prog]["log"], d / "fixed.log")
    shutil.copy2(par[k]["obj"], d / "buggy.o")
    shutil.copy2(fix[k]["obj"], d / "fixed.o")
    meta = {k2: row.get(k2) for k2 in ("screen_rank", "repo", "commit", "parent", "build_type", "flips",
                                         "decided_by", "feature_macros")}
    meta.update(object=k, program=prog, section=flip["section"], parent_cmd=par[k]["cmd"], fix_cmd=fix[k]["cmd"],
                changed_files=files)
    (d / "meta.json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-candidates", type=int, default=0)
    args = ap.parse_args(argv)
    cands = {c["screen_rank"]: c for c in json.loads((WILD / "candidates.json").read_text(encoding="utf-8"))["candidates"]}
    files = {json.loads(l)["screen_rank"]: json.loads(l)["bpf_c_files"]
             for l in (WILD / "screen_files.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()}
    survivors = [int(r["rank"]) for r in csv.DictReader((WILD / "pass2_decisions.tsv").open(encoding="utf-8"), delimiter="\t")
                 if r["decision"] == "pass"]
    done = {}
    if OUT.is_file():
        done = {json.loads(l)["screen_rank"]: json.loads(l) for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()}
    vmlinux_dir = str(ROOT / ".cache" / f"vmlinux-{os.uname().release}")
    if not (Path(vmlinux_dir) / "vmlinux.h").is_file():
        raise SystemExit(f"missing {vmlinux_dir}/vmlinux.h")
    n = 0
    for rank in sorted(survivors):
        included = sum(1 for r in done.values() if r.get("outcome") == "included")
        if included >= MAX_INCLUDED or dt.date.today() > STOP_DATE:
            print(f"stop: included={included}, date={dt.date.today()}")
            break
        if rank in done:
            continue
        if args.max_candidates and n >= args.max_candidates:
            break
        t0 = time.time()
        try:
            row = screen(cands[rank], files[rank], vmlinux_dir)
        except Exception as e:  # noqa: BLE001 - recorded, screening continues
            row = {"screen_rank": rank, "repo": cands[rank]["repo"], "commit": cands[rank]["commit"],
                   "outcome": "E5", "note": f"driver error: {e}"[:800]}
        row["seconds"] = round(time.time() - t0)
        with OUT.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")
        done[rank] = row
        n += 1
        status = (f"{dt.datetime.utcnow():%Y-%m-%d %H:%M}Z rank {rank} {row['outcome']} "
                  f"({row['seconds']}s); screened {len(done)}/{len(survivors)}; "
                  f"included {sum(1 for r in done.values() if r.get('outcome') == 'included')}")
        (WORK / "pass3.status").write_text(status + "\n")
        print(status, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

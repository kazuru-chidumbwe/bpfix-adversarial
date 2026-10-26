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


def screen(c: dict, files: list[str], vmlinux_dir: str) -> dict:
    deadline = time.time() + TIMEBOX
    row = {"screen_rank": c["screen_rank"], "repo": c["repo"], "commit": c["commit"], "started": dt.datetime.utcnow().isoformat() + "Z"}
    tmp = WORK / "tmp" / f"{c['screen_rank']:03d}"
    repo_dir = ensure_repo(c["repo"])
    if run(["git", "-C", str(repo_dir), "cat-file", "-e", c["commit"]]).returncode:
        run(["git", "-C", str(repo_dir), "fetch", "-q", "origin", c["commit"]], timeout=left(deadline))
    parent = run(["git", "-C", str(repo_dir), "rev-parse", f"{c['commit']}^"]).stdout.strip()
    row["parent"] = parent
    sides: dict[str, dict] = {}
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
            changed_abs = {str((wt / f).resolve()) for f in files}
            selected = []
            for cmd in cmds:
                if btype == "direct compile" or changed_abs & set(deps_of(cmd, deadline)):
                    selected.append(cmd)
            objs = {}
            for cmd in selected:
                obj = (Path(cmd["cwd"]) / cmd["obj"]).resolve()
                if not obj.is_file():
                    continue
                key = Path(cmd["src"]).name + "::" + obj.name
                stash = tmp / f"{side}-keep" / obj.name
                stash.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(obj, stash)
                objs[key] = {"obj": str(stash), "cmd": cmd["line"],
                             "progs": load(stash, tmp / f"{side}-logs" / obj.stem, f"{c['screen_rank']}-{side}", deadline)}
            sides[side] = {"build_type": btype, "objects": objs}
            row["build_type"] = btype
    except TimeBox:
        row.update(outcome="E5", note="2-hour time box")
        return row
    finally:
        for side in ("parent", "fix"):
            drop_worktree(repo_dir, tmp / side)

    par, fix = sides["parent"]["objects"], sides["fix"]["objects"]
    row["n_objects"] = {"parent": len(par), "fix": len(fix)}
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
    row["parent_rejects"] = rejects
    row["flips"] = flips
    if flips:
        row["outcome"] = "included"
        store(c, row, flips[0], par, fix, files, repo_dir, parent)
    elif not rejects:
        row["outcome"] = "E4"
    elif any(x["kind"] == "safety" for x in rejects):
        row["outcome"] = "I3"
    else:
        row["outcome"] = "C" if all(x["kind"] == "complexity" for x in rejects) else "I4"
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
    meta = {k2: row[k2] for k2 in ("screen_rank", "repo", "commit", "parent", "build_type", "flips")}
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

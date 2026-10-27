#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus pass 4: rebuild the pass-3 build failures with the build-environment fixes.

Implements the 27 Oct 2026 entry of "Changes after the freeze" in
docs/WILD-CORPUS-PROTOCOL.md. Runs ON the lab host, like pass 3, and reuses its
worktrees, loading, decision rule, feature build and case store. The retry set
is every pass-3 E5 and every pass-3 E4. Rows go to
fixtures/wild/pass4.jsonl; status to $WILD_WORK/pass4.status.

Usage: python3 tools/wild_pass4.py [--max-candidates N] [--ranks 11,14]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shlex
import stat
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import wild_pass3 as p3  # noqa: E402

OUT = p3.WILD / "pass4.jsonl"
MULTIARCH = "/usr/include/x86_64-linux-gnu"
KREL = "6.12.86+deb13"
KARCH = Path(f"/usr/src/linux-headers-{KREL}-amd64")
KCOMMON = Path(f"/usr/src/linux-headers-{KREL}-common")
MAX_ROUNDS = 8
LIBBPF_INC = Path("/usr/include/bpf")
UNIT_MARK = re.compile(r"\bSEC\(|\b__(?:bpf_)?section\(|__attribute__\s*\(\(\s*section")
# Batch 2 (protocol, batch 2 item 8): a .c file that includes a changed header holding the programs is a unit.
HEADER_MARK_COUNTS = False
MISSING = re.compile(r"fatal error: '([^']+)' file not found")
KBUILD_WARN = ["-Wno-unused-value", "-Wno-pointer-sign", "-Wno-compare-distinct-pointer-types",
               "-Wno-gnu-variable-sized-type-not-at-end", "-Wno-address-of-packed-member",
               "-Wno-tautological-compare", "-Wno-unknown-warning-option"]


def install_clang_wrapper(work: Path) -> Path:
    """`clang` first on PATH: the pin's clang plus -Wno-error and the multiarch dir searched last."""
    d = work / "p4bin"
    d.mkdir(parents=True, exist_ok=True)
    w = d / "clang"
    w.write_text(f'#!/bin/sh\nexec /usr/bin/clang "$@" -Wno-error -idirafter {MULTIARCH}\n', encoding="utf-8")
    w.chmod(w.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    os.environ["PATH"] = f"{d}:{os.environ['PATH']}"
    return w


def kernel_includes() -> list[str]:
    inc = [KCOMMON / "arch/x86/include", KARCH / "arch/x86/include/generated", KCOMMON / "include",
           KARCH / "include", KCOMMON / "arch/x86/include/uapi", KARCH / "arch/x86/include/generated/uapi",
           KCOMMON / "include/uapi", KARCH / "include/generated/uapi"]
    return sum((["-I", str(x)] for x in inc), []) + ["-include", str(KCOMMON / "include/linux/kconfig.h")]


def in_kernel_headers(name: str) -> bool:
    roots = [KCOMMON / "include", KARCH / "include", KCOMMON / "arch/x86/include", KCOMMON / "include/uapi",
             KCOMMON / "arch/x86/include/uapi", KARCH / "include/generated", KARCH / "arch/x86/include/generated"]
    return any((r / name).is_file() for r in roots)


def repo_dir_for(wt: Path, name: str, index: list[str]) -> str | None:
    """Shortest repository path ending in /name; the include dir is that path minus name."""
    suffix = "/" + name.lstrip("./")
    hits = sorted((p for p in index if ("/" + p).endswith(suffix)), key=lambda p: (len(p), p))
    if not hits:
        return None
    rel = hits[0][: len(hits[0]) - len(suffix) + 1].rstrip("/")
    return str(wt / rel) if rel else str(wt)


def compile_cmd(mode: str, u: Path, obj: Path, inc: list[str], vmlinux_dir: str) -> tuple[list[str], str]:
    if mode == "vmlinux":
        clang = ["clang", "-g", "-O2", "-target", "bpf", "-D__TARGET_ARCH_x86", *inc, "-I", vmlinux_dir,
                 "-I", "/usr/include", "-c", str(u), "-o", str(obj)]
        return clang, shlex.join(clang)
    clang = ["clang", "-g", "-O2", "-D__KERNEL__", "-D__BPF_TRACING__", "-D__TARGET_ARCH_x86", "-fno-stack-protector",
             *KBUILD_WARN, *inc, *kernel_includes(), "-emit-llvm", "-c", str(u), "-o", str(obj) + ".bc"]
    llc = ["llc", "-march=bpf", "-filetype=obj", str(obj) + ".bc", "-o", str(obj)]
    return clang, shlex.join(clang) + " && " + shlex.join(llc)  # not a pipe: a clang failure must fail the step


def compile_unit(wt: Path, u: Path, obj: Path, vmlinux_dir: str, index: list[str], deadline: float):
    extra: list[str] = []
    mode = "vmlinux"
    err = ""
    for _ in range(MAX_ROUNDS + 1):
        inc = sum((["-I", d] for d in extra + p3.include_dirs(wt, u)), [])
        clang, line = compile_cmd(mode, u, obj, inc, vmlinux_dir)
        obj.unlink(missing_ok=True)
        p = p3.run(line, cwd=u.parent, timeout=min(600, p3.left(deadline)))
        if p.returncode == 0 and obj.is_file() and obj.stat().st_size:
            return {"cwd": str(u.parent), "clang": clang, "src": str(u), "obj": str(obj), "line": line,
                    "compile_mode": mode, "extra_includes": [str(Path(x).relative_to(wt)) if Path(x).is_relative_to(wt) else x for x in extra]}, ""
        err = p.stderr.strip()[-200:]
        m = MISSING.search(p.stderr)
        if not m:
            break
        name = m.group(1)
        d = repo_dir_for(wt, name, index)
        if d is None and (LIBBPF_INC / name).is_file():
            d = str(LIBBPF_INC)  # libbpf's own headers, included without the bpf/ prefix
        if d and d not in extra:
            extra.append(d)
            continue
        if mode == "vmlinux" and in_kernel_headers(name):
            mode = "kbuild"
            continue
        break
    return None, f"{u.relative_to(wt)}: {err}"


def build_direct(wt: Path, changed: list[str], vmlinux_dir: str, objdir: Path, deadline: float):
    index = p3.run(["git", "-C", str(wt), "ls-files"]).stdout.split()
    units: set[Path] = set()
    for rel in changed:
        f = wt / rel
        if not f.is_file():
            continue
        if rel.endswith(".c") and UNIT_MARK.search(f.read_text(errors="replace")):
            units.add(f)
        elif rel.endswith(".h"):
            name = re.escape(Path(rel).name)
            g = p3.run(f"grep -rlE '#include.*[\"</]{name}[\">]' --include='*.c' .", cwd=wt,
                       timeout=min(300, p3.left(deadline)))
            header_marked = HEADER_MARK_COUNTS and bool(UNIT_MARK.search(f.read_text(errors="replace")))
            for hit in g.stdout.split():
                h = (wt / hit).resolve()
                if header_marked or UNIT_MARK.search(h.read_text(errors="replace")):
                    units.add(h)
    cmds, errors = [], []
    objdir.mkdir(parents=True, exist_ok=True)
    for u in sorted(units)[:40]:
        obj = objdir / (u.relative_to(wt).as_posix().replace("/", "__") + ".o")
        cmd, err = compile_unit(wt, u, obj, vmlinux_dir, index, deadline)
        if cmd:
            cmds.append(cmd)
        else:
            errors.append(err)
    if not cmds:
        raise RuntimeError("direct compile failed: " + (" | ".join(errors) or "no compilation unit found"))
    return cmds, "direct compile"


def llc_steps(log: str) -> dict[str, tuple[str, str]]:
    """IR file -> (llc command line, object it writes), from a verbose make log."""
    out: dict[str, tuple[str, str]] = {}
    for line in log.splitlines():
        try:
            toks = shlex.split(line.strip())
        except ValueError:
            continue
        if not toks or not Path(toks[0]).name.startswith("llc") or "-o" not in toks:
            continue
        obj = toks[toks.index("-o") + 1]
        for t in toks[1:]:
            if t.endswith(".ll") and t != obj:
                out[Path(t).name] = (line.strip(), obj)
    return out


def build_make(wt: Path, deadline: float) -> tuple[list[dict], str]:
    """Pass-3 project build, but an IR output (`-o x.ll`) is followed to the object llc makes from it."""
    p = p3.run(["make", "-C", "bpf", "-j4", "V=1"], cwd=wt, timeout=p3.left(deadline))
    if p.returncode:
        raise RuntimeError("make failed: " + (p.stdout + p.stderr).strip()[-600:])
    log = p.stdout + p.stderr
    steps = llc_steps(log)
    cmds = []
    for cmd in p3.parse_compile_cmds(log, wt / "bpf"):
        if cmd["obj"].endswith(".ll") and "|" not in cmd["line"]:
            step = steps.get(Path(cmd["obj"]).name)
            if step is None:
                continue
            cmd = {**cmd, "obj": step[1], "line": cmd["line"] + " && " + step[0]}
        cmds.append(cmd)
    return cmds, "project build"


OPEN_ERRORS: list[str] = []
LEGACY_LOADED: list[str] = []
LEGACY = Path(os.environ.get("WILDLOAD_LEGACY", str(p3.WORK / "wildload-legacy")))
# Old cilium patches per-endpoint constants into the object at load time (its own ELF loader);
# loaded raw, the placeholder address of a .data value is shifted and the verifier refuses it.
TEMPLATED = re.compile(r"pointer arithmetic with \S+ operator prohibited|invalid size of register spill|leaks addr|"
                       r"partial copy of pointer|pointer comparison prohibited|bitwise operator \S+ on pointer prohibited")
PLACEHOLDER = re.compile(r"\(18\) r\d+ = 0x[0-9a-f]+\s+; R\d+_w=map_value\(map=\S*\.data,")
PLACEHOLDER_WINDOW = 6  # instructions before the failing one


def install_legacy_wrappers(work: Path) -> dict[str, str]:
    """One wrapper per default program type, since sudo passes only the pin-root variable through."""
    out = {}
    for t in ("sched_cls", "xdp"):
        w = work / "p4bin" / f"wildload-legacy-{t}"
        w.parent.mkdir(parents=True, exist_ok=True)
        w.write_text(f'#!/bin/sh\nWILDLOAD_DEFAULT_TYPE={t} exec {LEGACY} "$@"\n', encoding="utf-8")
        w.chmod(w.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        out[t] = str(w)
    return out


LEGACY_WRAPPERS: dict[str, str] = {}


def load(obj: Path, outdir: Path, tag: str, deadline: float) -> dict[str, dict]:
    """Pass-3 load; an object libbpf 1.5 refuses for its legacy `maps` section (OPEN_ERROR 95) is loaded
    with the libbpf 0.8.3 build instead. An object that still yields no program is recorded."""
    res = P3_LOAD(obj, outdir, tag, deadline)
    if not res and OPEN_CODE.get(str(obj)) == "OPEN_ERROR 95" and LEGACY_WRAPPERS:
        kind = "xdp" if "xdp" in Path(obj).name else "sched_cls"
        saved, p3.WILDLOAD = p3.WILDLOAD, LEGACY_WRAPPERS[kind]
        try:
            res = P3_LOAD(obj, outdir, tag, deadline)
        finally:
            p3.WILDLOAD = saved
        if res:
            LEGACY_LOADED.append(f"{tag}:{Path(obj).name}:{kind}")
    if not res:
        code = OPEN_CODE.get(str(obj), "no program")
        OPEN_ERRORS.append(f"{tag}:{Path(obj).name}:{code}")
    return res


P3_REJECT_KIND = p3.reject_kind


def reject_kind(log_path: str) -> str:
    kind = P3_REJECT_KIND(log_path)
    if kind == "safety":
        lines = Path(log_path).read_text(errors="replace").splitlines() if Path(log_path).is_file() else []
        block = p3.verifier_error_block(lines)
        msg = " ".join(block[1]) if block else ""
        at = next((i for i, ln in enumerate(lines) if TEMPLATED.search(ln)), None)
        if TEMPLATED.search(msg) and at is not None:
            insns = [ln for ln in lines[:at] if re.match(r"\d+: \(", ln)][-PLACEHOLDER_WINDOW:]
            if any(PLACEHOLDER.search(ln) for ln in insns):
                return "environment"
    return kind


OPEN_CODE: dict[str, str] = {}
P3_RUN = p3.run


def run(cmd, cwd=None, timeout=None, env=None):
    """p3.run, keeping the loader's OPEN_ERROR code per object (95 = legacy `maps` section)."""
    p = P3_RUN(cmd, cwd=cwd, timeout=timeout, env=env)
    if isinstance(cmd, list) and any(Path(c).name == "wildload" for c in cmd[:6]) and "OPEN_ERROR" in p.stdout:
        obj = next((c for c in cmd if c.endswith(".o")), None)
        m = re.search(r"OPEN_ERROR (-?\d+)", p.stdout)
        if obj and m:
            OPEN_CODE[obj] = f"OPEN_ERROR {m.group(1)}"
    return p


P3_LOAD = p3.load


def final_outcome(row: dict) -> str:
    """Outcome from the recorded fields (protocol, correction to item 6). Only an object that failed to
    open blocks the decision; objects that open with no program do not, unless the deciding build's parent
    side loaded no program at all."""
    if row.get("decided_outcome") is None:
        return row["outcome"]
    errs = row.get("open_errors") or []
    if any(not e.endswith(":no program") for e in errs):
        return "E5"
    tag = "feat" if row.get("decided_by") == "features" else "keep"
    empty = {e.split(":")[1] for e in errs if e.split(":")[0].endswith(f"parent-{tag}")}
    if len(empty) >= (row.get("n_objects") or {}).get("parent", 0):
        return "E5"
    return row["decided_outcome"]


def retry_set() -> list[int]:
    """Every pass-3 E5 and every pass-3 E4: pass 3 could not tell an object it failed to open from one that loaded."""
    rows = [json.loads(ln) for ln in (p3.WILD / "pass3.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()]
    return sorted(r["screen_rank"] for r in rows if r["outcome"] in ("E5", "E4"))


def included_so_far() -> int:
    n = 0
    for path in (p3.WILD / "pass3.jsonl", OUT):
        if path.is_file():
            n += sum(1 for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and
                     json.loads(ln).get("outcome") == "included")
    return n


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-candidates", type=int, default=0)
    ap.add_argument("--ranks", default="", help="comma-separated subset of the retry set")
    args = ap.parse_args(argv)
    for d in (KARCH, KCOMMON):
        if not d.is_dir():
            raise SystemExit(f"missing pin kernel headers: {d}")
    install_clang_wrapper(p3.WORK)
    p3.build_direct, p3.build_make, p3.load, p3.run = build_direct, build_make, load, run
    p3.reject_kind = reject_kind
    if LEGACY.is_file():
        LEGACY_WRAPPERS.update(install_legacy_wrappers(p3.WORK))
    else:
        raise SystemExit(f"missing legacy loader {LEGACY}")
    cands = {c["screen_rank"]: c for c in json.loads((p3.WILD / "candidates.json").read_text(encoding="utf-8"))["candidates"]}
    files = {json.loads(ln)["screen_rank"]: json.loads(ln)["bpf_c_files"]
             for ln in (p3.WILD / "screen_files.jsonl").read_text(encoding="utf-8").splitlines() if ln.strip()}
    todo = retry_set()
    if args.ranks:
        todo = [r for r in todo if r in {int(x) for x in args.ranks.split(",")}]
    done = {}
    if OUT.is_file():
        done = {json.loads(ln)["screen_rank"]: json.loads(ln) for ln in OUT.read_text(encoding="utf-8").splitlines() if ln.strip()}
    vmlinux_dir = str(ROOT / ".cache" / f"vmlinux-{os.uname().release}")
    if not (Path(vmlinux_dir) / "vmlinux.h").is_file():
        raise SystemExit(f"missing {vmlinux_dir}/vmlinux.h")
    n = 0
    for rank in todo:
        included = included_so_far()
        if included >= p3.MAX_INCLUDED or dt.date.today() > p3.STOP_DATE:
            print(f"stop: included={included}, date={dt.date.today()}")
            break
        if rank in done:
            continue
        if args.max_candidates and n >= args.max_candidates:
            break
        p3.shutil.rmtree(p3.WORK / "tmp" / f"{rank:03d}", ignore_errors=True)
        t0 = time.time()
        OPEN_ERRORS.clear()
        LEGACY_LOADED.clear()
        try:
            row = p3.screen(cands[rank], files[rank], vmlinux_dir)
        except Exception as e:  # noqa: BLE001 - recorded, screening continues
            row = {"screen_rank": rank, "repo": cands[rank]["repo"], "commit": cands[rank]["commit"],
                   "outcome": "E5", "note": f"driver error: {e}"[:800]}
        if OPEN_ERRORS:
            row["open_errors"] = sorted(set(OPEN_ERRORS))
        if LEGACY_LOADED:
            row["legacy_loaded"] = sorted(set(LEGACY_LOADED))
        if row.get("outcome") == "E4" and not any((row.get("n_objects") or {}).values()):
            row.update(outcome="E5", note="no built object depends on a changed file")
        elif row.get("outcome") in ("E4", "I3", "I4", "C") and OPEN_ERRORS:
            row["decided_outcome"] = row["outcome"]
            row["outcome"] = final_outcome(row)
            if row["outcome"] == "E5":
                row["note"] = "no program loaded from: " + ", ".join(sorted(set(OPEN_ERRORS)))[:700]
        row["pass"] = 4
        row["seconds"] = round(time.time() - t0)
        with OUT.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")
        done[rank] = row
        n += 1
        status = (f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M}Z rank {rank} {row['outcome']} "
                  f"({row['seconds']}s); retried {len(done)}/{len(todo)}; included (passes 3+4) {included_so_far()}")
        (p3.WORK / "pass4.status").write_text(status + "\n")
        print(status, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())

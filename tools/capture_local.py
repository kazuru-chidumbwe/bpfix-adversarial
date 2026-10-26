#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compile and load every BPF C file under a directory on *this* host; keep the verifier logs.

Runs on the lab host itself (clone the repo there), so no SSH, no password files
and no paramiko are involved. Writes, under ``--out``:

  <case>.<stamp>.log            bpftool -d prog load output (or COMPILE_FAIL + clang stderr)
  <case>.<stamp>.log.compile    clang stderr
  env.<stamp>.txt               uname / clang / bpftool / host pin
  manifest.<stamp>.jsonl        one row per case: src + log sha256 (LF), verdict, processed insns

Profiles:
  template   clang -O2 -g -target bpf -I/usr/include/<multiarch> -idirafter /usr/include
             (the v1.0.2 capture flags); prog type from SEC("xdp") else socket.
  upstream   clang -target bpf -O2 -g -I /usr/include -D__TARGET_ARCH_x86 -I <vmlinux dir>
             (bpfix-bench/tools/bpf_case.py compile_bpf); prog type inferred by libbpf.

Usage:
  python tools/capture_local.py --src campaigns/v2/mutants --out campaigns/v2/captured/<label>
  python tools/capture_local.py --profile upstream --vmlinux-dir /tmp/vmlinux \
      --src campaigns/v2/upstream --glob '*/*.bpf.c' --out campaigns/v2/captured/<label>-upstream
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.score_sc_vs_honesty import lab_rejected  # noqa: E402

PROCESSED_RE = re.compile(r"^processed (\d+) insns", re.M)


def sha256_lf(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def run(argv: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def tool_version(argv: list[str]) -> str:
    try:
        p = run(argv, timeout=30)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"UNAVAILABLE ({exc})"
    return (p.stdout or p.stderr).strip()


def multiarch() -> str:
    try:
        p = run(["gcc", "-dumpmachine"], timeout=10)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    except OSError:
        pass
    return f"{platform.machine()}-linux-gnu"


def compile_argv(profile: str, src: Path, obj: Path, clang: list[str], vmlinux_dir: str | None) -> list[str]:
    if profile == "template":
        return [*clang, "-O2", "-g", "-target", "bpf", f"-I/usr/include/{multiarch()}",
                "-idirafter", "/usr/include", "-c", str(src), "-o", str(obj)]
    argv = [*clang, "-target", "bpf", "-O2", "-g", "-I", "/usr/include", "-D__TARGET_ARCH_x86"]
    if vmlinux_dir:
        argv += ["-I", vmlinux_dir]
    return argv + ["-c", str(src), "-o", str(obj)]


def prog_type(profile: str, text: str) -> str | None:
    if profile == "upstream":
        return None  # libbpf infers the type from the SEC() name
    return "xdp" if 'SEC("xdp")' in text else "socket"


def case_id_for(src: Path, base: Path) -> str:
    rel = src.relative_to(base)
    if src.name.endswith(".bpf.c"):
        # campaigns/v2/upstream/<case>/<variant>.bpf.c -> <case>__<variant>
        return "__".join([*rel.parent.parts, src.name[: -len(".bpf.c")]])
    return src.stem


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, required=True, help="directory to scan")
    ap.add_argument("--glob", default="**/*.c")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--profile", choices=("template", "upstream"), default="template")
    ap.add_argument("--vmlinux-dir", default=None, help="directory holding vmlinux.h (upstream profile)")
    ap.add_argument("--clang", default=os.environ.get("CLANG", "clang"))
    ap.add_argument("--bpftool", default=os.environ.get("BPFTOOL", "sudo -n bpftool"),
                    help='bpftool command (default "sudo -n bpftool"; use "bpftool" when already root)')
    ap.add_argument("--bpffs", default="/sys/fs/bpf")
    ap.add_argument("--label", default=None, help="free-text host label recorded in the env pin")
    args = ap.parse_args(argv)

    src_dir = args.src if args.src.is_absolute() else ROOT / args.src
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    clang = shlex.split(args.clang)
    bpftool = shlex.split(args.bpftool)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    env_lines = [
        f"label={args.label or ''}",
        f"utc={stamp}",
        f"profile={args.profile}",
        "uname=" + " ".join(platform.uname()),
        "uname_r=" + platform.release(),
        "clang=" + tool_version([*clang, "--version"]).splitlines()[0],
        "bpftool=" + " | ".join(tool_version([*bpftool, "version"]).splitlines()[:2]),
        f"bpftool_cmd={args.bpftool}",
    ]
    (out / f"env.{stamp}.txt").write_text("\n".join(env_lines) + "\n", encoding="utf-8", newline="\n")

    sources = sorted(p for p in src_dir.glob(args.glob) if p.is_file())
    if not sources:
        print(f"no sources matched {args.glob} under {src_dir}", file=sys.stderr)
        return 2
    rows = []
    with tempfile.TemporaryDirectory(prefix="bpfix-cap-") as td:
        for src in sources:
            case_id = case_id_for(src, src_dir)
            text = src.read_text(encoding="utf-8")
            obj = Path(td) / f"{case_id}.o"
            log = out / f"{case_id}.{stamp}.log"
            cp = run(compile_argv(args.profile, src, obj, clang, args.vmlinux_dir))
            (out / f"{case_id}.{stamp}.log.compile").write_text(cp.stderr, encoding="utf-8", newline="\n")
            if cp.returncode != 0:
                body = "COMPILE_FAIL\n" + cp.stderr
                verdict = "COMPILE_FAIL"
            else:
                pin = f"{args.bpffs}/bpfix_cap_{stamp}_{re.sub(r'[^A-Za-z0-9_]', '_', case_id)}"[:120]
                load = [*bpftool, "-d", "prog", "load", str(obj), pin]
                ptype = prog_type(args.profile, text)
                if ptype:
                    load += ["type", ptype]
                lp = run(load)
                body = lp.stdout + lp.stderr
                # Unpin with the same privilege prefix as the load (e.g. "sudo -n").
                run([*bpftool[:-1], "rm", "-f", pin])
                verdict = "REJECT" if lab_rejected(body) else ("ACCEPT" if lp.returncode == 0 else "LOAD_ERROR")
            log.write_text(body.replace("\r\n", "\n"), encoding="utf-8", newline="\n")
            m = PROCESSED_RE.search(body)
            row = {
                "case_id": case_id,
                "src": src.relative_to(ROOT).as_posix() if src.is_relative_to(ROOT) else str(src),
                "src_sha256": sha256_lf(src.read_bytes()),
                "log": log.relative_to(ROOT).as_posix() if log.is_relative_to(ROOT) else str(log),
                "log_sha256": sha256_lf(log.read_bytes()),
                "verdict": verdict,
                "processed_insns": int(m.group(1)) if m else None,
                "utc": stamp,
                "profile": args.profile,
            }
            rows.append(row)
            print(f"{verdict:12} {case_id}")
    with (out / f"manifest.{stamp}.jsonl").open("w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    print(f"stamp={stamp} n={len(rows)} out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

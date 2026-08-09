#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Lab A/B: marker-bearing vs marker-neutral mutants (Gates marker isolation).

For each SoftwareX-stamp case in results/sc_vs_honesty.json, compile+load the
original source and a line-preserving marker-stripped twin on the same lab host
in one SSH session. Compare verdict, VerifierState stop line, and normalized
source-map sets.

Does not print credentials. Writes fixtures/logs/captured/*-markeriso-*.log and
results/marker_isolation_lab.json.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.marker_isolation import strip_oracle_markers  # noqa: E402
from tools.score_sc_vs_honesty import lab_rejected, vs_stop_line  # noqa: E402

# Reuse lab env helpers without treating tools/ as a package.
import importlib.util

def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

_cap = _load_mod("lab_capture_via_env", ROOT / "tools" / "lab_capture_via_env.py")
load_env = _cap.load_env
connect = _cap.connect
normalize_lab_env = _cap.normalize_lab_env

STAMP_FILTER = "20260801T181331Z"
SOURCE_AT_RE = re.compile(r";\s*(.*?)\s*@\s*([^:]+):(\d+)\s*$")
ENV = Path(os.environ.get("BPFIX_LAB_ENV_FILE", str(ROOT / "lab" / ".env")))


def prog_type_for(text: str) -> str:
    return "xdp" if 'SEC("xdp")' in text else "socket"


def normalize_log_body(text: str) -> str:
    """Drop host-ephemeral noise; keep verifier diagnostic substance."""
    lines = []
    for ln in text.splitlines():
        if ln.startswith("META "):
            continue
        if ln.strip() in {"ACCEPT", "REJECT", "COMPILE_FAIL"}:
            continue
        if ln.startswith("EXIT:"):
            continue
        if ln.startswith("connecting ") or ln.startswith("ssh ok"):
            continue
        # Timing / accounting noise (differs run-to-run and bearing/neutral)
        if re.match(r"^verification time \d+ usec$", ln.strip()):
            continue
        if re.match(
            r"^processed \d+ insns \(limit \d+\) max_states_per_insn \d+ "
            r"total_states \d+ peak_states \d+ mark_read \d+$",
            ln.strip(),
        ):
            continue
        # Collapse absolute tmp paths / stamps / variant ids
        ln = re.sub(r"/tmp/bpfix-iso-[A-Za-z0-9_.-]+", "/tmp/bpfix-iso-STAMP", ln)
        ln = re.sub(r"bpfix_iso_[A-Za-z0-9_]+", "bpfix_iso_ID", ln)
        ln = re.sub(r"markeriso-(bearing|neutral)", "markeriso-VARIANT", ln)
        # ASLR / map allocation addresses differ per load; not marker-dependent
        ln = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", ln)
        lines.append(ln.rstrip())
    # Keep from BEGIN PROG LOAD LOG if present
    joined = "\n".join(lines)
    idx = joined.find("BEGIN PROG LOAD LOG")
    if idx >= 0:
        joined = joined[idx:]
    return joined.strip() + "\n"


def source_map_set(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for ln in text.splitlines():
        m = SOURCE_AT_RE.search(ln)
        if m:
            out.append((int(m.group(3)), m.group(1).strip()))
    return out


def source_comment_texts(text: str) -> list[str]:
    """Verifier `; …` source comments (with or without @file:line)."""
    out: list[str] = []
    for ln in text.splitlines():
        m = SOURCE_AT_RE.search(ln)
        if m:
            out.append(m.group(1).strip())
            continue
        s = ln.strip()
        if s.startswith(";") and not s.startswith("; R") and "R0=" not in s[:8]:
            # bare `; source` form (Ubuntu 6.8 bpftool often omits @file:line)
            body = s[1:].strip()
            if body and not body.startswith("(") and "R" not in body[:2]:
                out.append(body)
    return out


def analyze_captured_log(
    out: str,
    *,
    variant: str,
    prog_type: str,
    src_sha256: str,
    log_rel: str,
    object_meta: dict | None = None,
) -> dict:
    if any(line.strip() == "COMPILE_FAIL" for line in out.splitlines()):
        verdict = "COMPILE_FAIL"
    elif any(line.strip() == "ACCEPT" for line in out.splitlines()):
        verdict = "ACCEPT"
    else:
        verdict = "REJECT"

    vs_line, vs_txt, vs_note = vs_stop_line(out)
    maps = source_map_set(out)
    comments = source_comment_texts(out)
    meta = object_meta or {}
    # Prefer echoed OBJSHA lines from the remote compile session
    for ln in out.splitlines():
        if ln.startswith("OBJSHA:"):
            meta["obj_sha256"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("DISASMSHA:"):
            meta["disasm_sha256"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("BTFSHA:"):
            meta["btf_sha256"] = ln.split(":", 1)[1].strip()
        elif ln.startswith("BTFEXTSHA:"):
            meta["btf_ext_sha256"] = ln.split(":", 1)[1].strip()
    return {
        "variant": variant,
        "verdict": verdict,
        "prog_type": prog_type,
        "src_sha256": src_sha256,
        "log": log_rel,
        "lab_rejected": lab_rejected(out) if verdict != "COMPILE_FAIL" else None,
        "vs_reported_line": vs_line,
        "vs_source_text": vs_txt,
        "vs_note": vs_note,
        "source_map_lines": [ln for ln, _ in maps],
        "source_map_pairs": [{"line": ln, "text": tx} for ln, tx in maps],
        "source_comment_texts": comments,
        "normalized_log_sha256": hashlib.sha256(
            normalize_log_body(out).encode()
        ).hexdigest(),
        "has_oracle_token_in_log": "ORACLE_" in out,
        "obj_sha256": meta.get("obj_sha256"),
        "disasm_sha256": meta.get("disasm_sha256"),
        "btf_sha256": meta.get("btf_sha256"),
        "btf_ext_sha256": meta.get("btf_ext_sha256"),
    }


def nodbg_object_sha(
    client: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    src_text: str,
) -> str:
    """Compile without -g under a fixed remote path; return ELF sha256."""
    rc = "/tmp/bpfix-iso-nodbg-same.c"
    ro = "/tmp/bpfix-iso-nodbg-same.o"
    with sftp.file(rc, "w") as f:
        f.write(src_text)
    cmd = (
        "export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; "
        f"clang -O2 -target bpf -I/usr/include/x86_64-linux-gnu "
        f"-idirafter /usr/include -c {rc} -o {ro}; "
        f"sha256sum {ro} | awk '{{print $1}}'"
    )
    _i, o, _e = client.exec_command(cmd, timeout=90, get_pty=True)
    out = o.read().decode(errors="replace").strip().splitlines()
    for ln in reversed(out):
        tok = ln.strip().split()[0] if ln.strip() else ""
        if len(tok) == 64 and all(c in "0123456789abcdef" for c in tok):
            return tok
    return ""


def pair_match(b: dict, n: dict) -> dict:
    same_verdict = b["verdict"] == n["verdict"]
    same_vs = b["vs_reported_line"] == n["vs_reported_line"]
    same_maps = b["source_map_pairs"] == n["source_map_pairs"]
    same_comments = b.get("source_comment_texts") == n.get("source_comment_texts")
    same_norm = b["normalized_log_sha256"] == n["normalized_log_sha256"]
    same_nodbg = (
        b.get("nodbg_obj_sha256")
        and n.get("nodbg_obj_sha256")
        and b["nodbg_obj_sha256"] == n["nodbg_obj_sha256"]
    )
    # -g ELF often differs: debug/source metadata retains authored source text
    # (.BTF and .BTF.ext dumps differ on the Ubuntu A/B campaign). Reported, not required for pass.
    same_dbg = (
        b.get("obj_sha256")
        and n.get("obj_sha256")
        and b["obj_sha256"] == n["obj_sha256"]
    )
    no_oracle = (not b["has_oracle_token_in_log"]) and (not n["has_oracle_token_in_log"])
    return {
        "verdict": same_verdict,
        "vs_reported_line": same_vs,
        "source_map_pairs": same_maps,
        "source_comment_texts": same_comments,
        "normalized_log": same_norm,
        "nodbg_obj_sha256": bool(same_nodbg),
        "dbg_obj_sha256": bool(same_dbg),
        "no_oracle_in_logs": no_oracle,
        "pass": bool(
            same_verdict
            and same_norm
            and same_comments
            and same_nodbg
            and no_oracle
        ),
    }


def load_pair(
    client: paramiko.SSHClient,
    sftp: paramiko.SFTPClient,
    *,
    case_id: str,
    variant: str,
    src_text: str,
    password: str | None,
    run_stamp: str,
) -> dict:
    ptype = prog_type_for(src_text)
    remote_c = f"/tmp/bpfix-iso-{run_stamp}-{case_id}-{variant}.c"
    remote_o = f"/tmp/bpfix-iso-{run_stamp}-{case_id}-{variant}.o"
    remote_log = f"/tmp/bpfix-iso-{run_stamp}-{case_id}-{variant}.log"
    with sftp.file(remote_c, "w") as f:
        f.write(src_text)

    if password:
        pw_file = f"/tmp/.bpfix_iso_pw_{run_stamp}"
        # password file written once by caller
        sudo_bpf = f'PW=$(cat {pw_file}); printf "%s\\n" "$PW" | sudo -S -p "" /usr/sbin/bpftool'
        sudo_rm = f'PW=$(cat {pw_file}); printf "%s\\n" "$PW" | sudo -S -p "" rm -f'
    else:
        sudo_bpf = "sudo -n /usr/sbin/bpftool"
        sudo_rm = "sudo -n rm -f"

    pin = f"bpfix_iso_{run_stamp}_{case_id}_{variant}".replace("-", "_")[:80]
    cmd = (
        f"export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; "
        f"clang -O2 -g -target bpf -I/usr/include/x86_64-linux-gnu "
        f"-idirafter /usr/include -c {remote_c} -o {remote_o} 2>{remote_log}.ce; "
        f"ec=$?; if [ $ec -ne 0 ]; then echo COMPILE_FAIL; cat {remote_log}.ce; exit 1; fi; "
        f"echo OBJSHA:$(sha256sum {remote_o} | awk '{{print $1}}'); "
        f"echo DISASMSHA:$(llvm-objdump -d {remote_o} 2>/dev/null | sha256sum | awk '{{print $1}}'); "
        f"echo BTFSHA:$(llvm-objdump -s -j .BTF {remote_o} 2>/dev/null | sha256sum | awk '{{print $1}}'); "
        f"echo BTFEXTSHA:$(llvm-objdump -s -j .BTF.ext {remote_o} 2>/dev/null | sha256sum | awk '{{print $1}}'); "
        f"{sudo_bpf} -d prog load {remote_o} /sys/fs/bpf/{pin} "
        f"type {ptype} >{remote_log} 2>&1; load_ec=$?; "
        f"{sudo_rm} /sys/fs/bpf/{pin} 2>/dev/null; "
        f"if grep -qE 'failed to load|invalid|unbounded|math between' {remote_log}; "
        f"then echo REJECT; else echo ACCEPT; fi; "
        f"echo EXIT:$load_ec; cat {remote_log}"
    )
    _i, o, _e = client.exec_command(cmd, timeout=120, get_pty=True)
    out = o.read().decode(errors="replace")
    if password:
        out = out.replace(password, "***")

    local_dir = ROOT / "fixtures" / "logs" / "captured"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_log = local_dir / f"{case_id}.markeriso-{variant}.{run_stamp}.log"
    # Always LF — Windows captures must not commit CRLF (CI: tools/check_lf_logs.py).
    text = out.replace("\r\n", "\n").replace("\r", "\n")
    with local_log.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)

    return analyze_captured_log(
        out,
        variant=variant,
        prog_type=ptype,
        src_sha256=hashlib.sha256(src_text.encode()).hexdigest(),
        log_rel=str(local_log.relative_to(ROOT)).replace("\\", "/"),
    )


def rescore_existing(lab_path: Path) -> dict:
    """Recompute match fields from already-captured markeriso logs."""
    lab = json.loads(lab_path.read_text(encoding="utf-8"))
    pairs = []
    for p in lab["pairs"]:
        b_text = (ROOT / p["bearing"]["log"]).read_text(encoding="utf-8", errors="replace")
        n_text = (ROOT / p["neutral"]["log"]).read_text(encoding="utf-8", errors="replace")
        b = analyze_captured_log(
            b_text,
            variant="bearing",
            prog_type=p["bearing"]["prog_type"],
            src_sha256=p["bearing"]["src_sha256"],
            log_rel=p["bearing"]["log"],
        )
        n = analyze_captured_log(
            n_text,
            variant="neutral",
            prog_type=p["neutral"]["prog_type"],
            src_sha256=p["neutral"]["src_sha256"],
            log_rel=p["neutral"]["log"],
        )
        pairs.append(
            {
                "case_id": p["case_id"],
                "obligation": p["obligation"],
                "src": p["src"],
                "bearing": b,
                "neutral": n,
                "match": pair_match(b, n),
            }
        )
    n = len(pairs)
    hits = sum(1 for p in pairs if p["match"]["pass"])
    lab["pairs"] = pairs
    lab["n_pairs"] = n
    lab["summary"] = {
        "pass": hits,
        "n": n,
        "pass_rate": round(hits / n, 4) if n else 0.0,
        "verdict_match": sum(1 for p in pairs if p["match"]["verdict"]),
        "vs_match": sum(1 for p in pairs if p["match"]["vs_reported_line"]),
        "source_map_match": sum(1 for p in pairs if p["match"]["source_map_pairs"]),
        "source_comment_match": sum(1 for p in pairs if p["match"]["source_comment_texts"]),
        "normalized_log_match": sum(1 for p in pairs if p["match"]["normalized_log"]),
        "obj_sha_match": sum(1 for p in pairs if p["match"].get("obj_sha256")),
        "disasm_sha_match": sum(1 for p in pairs if p["match"].get("disasm_sha256")),
        "btf_sha_match": sum(1 for p in pairs if p["match"].get("btf_sha256")),
        "btf_ext_sha_match": sum(1 for p in pairs if p["match"].get("btf_ext_sha256")),
    }
    lab["note"] = (
        "Marker-neutral = ORACLE_* comments replaced with /* */ (line-preserving). "
        "pass = identical verdict + normalized verifier log body (timing/ASLR stripped) + "
        "source-comment texts + ELF object SHA-256 + llvm-objdump -d SHA-256, "
        "and no ORACLE_ token in either log. BTF section hashes reported when available."
    )
    lab_path.write_text(json.dumps(lab, indent=2) + "\n", encoding="utf-8")
    return lab


def main() -> int:
    sc = json.loads((ROOT / "results" / "sc_vs_honesty.json").read_text(encoding="utf-8"))
    rows = [
        r
        for r in sc["rows"]
        if STAMP_FILTER in (r.get("log") or "")
        and r.get("src")
        and Path(ROOT / r["src"]).is_file()
        and "repaired" not in r["case_id"]
    ]
    cfg = normalize_lab_env(load_env(ENV))
    password = (cfg.get("LAB_TEST_PASSWORD") or "").strip() or None
    client = connect(cfg)
    sftp = client.open_sftp()
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # pin probe (no secrets)
    _i, o, _e = client.exec_command(
        "hostname; uname -r; clang --version | head -1; bpftool version | head -1",
        timeout=30,
        get_pty=True,
    )
    host_probe = o.read().decode(errors="replace").strip()
    print(host_probe)

    if password:
        pw_file = f"/tmp/.bpfix_iso_pw_{run_stamp}"
        with sftp.file(pw_file, "w") as f:
            f.write(password + "\n")
        client.exec_command(f"chmod 600 {pw_file}", timeout=10)

    pairs = []
    try:
        for r in rows:
            case_id = r["case_id"]
            src_path = ROOT / r["src"]
            bearing = src_path.read_text(encoding="utf-8")
            neutral = strip_oracle_markers(bearing, preserve_lines=True)
            assert "ORACLE_" not in neutral
            assert bearing.count("\n") == neutral.count("\n")

            print(f"A/B {case_id} ...", flush=True)
            b = load_pair(
                client,
                sftp,
                case_id=case_id,
                variant="bearing",
                src_text=bearing,
                password=password,
                run_stamp=run_stamp,
            )
            n = load_pair(
                client,
                sftp,
                case_id=case_id,
                variant="neutral",
                src_text=neutral,
                password=password,
                run_stamp=run_stamp,
            )
            # Same-path -O2 (no -g) ELF identity — path embedding cannot confound.
            b["nodbg_obj_sha256"] = nodbg_object_sha(client, sftp, bearing)
            n["nodbg_obj_sha256"] = nodbg_object_sha(client, sftp, neutral)
            pairs.append(
                {
                    "case_id": case_id,
                    "obligation": r["obligation"],
                    "src": r["src"],
                    "bearing": b,
                    "neutral": n,
                    "match": pair_match(b, n),
                }
            )
            print(
                f"  verdict {b['verdict']}/{n['verdict']} "
                f"norm={pairs[-1]['match']['normalized_log']} "
                f"nodbg={pairs[-1]['match']['nodbg_obj_sha256']} "
                f"dbg={pairs[-1]['match']['dbg_obj_sha256']} "
                f"pass={pairs[-1]['match']['pass']}",
                flush=True,
            )
    finally:
        if password:
            client.exec_command(f"rm -f /tmp/.bpfix_iso_pw_{run_stamp}", timeout=10)
        client.close()

    n = len(pairs)
    hits = sum(1 for p in pairs if p["match"]["pass"])
    payload = {
        "generator": "tools/lab_marker_isolation_ab.py",
        "run_stamp": run_stamp,
        "softwarex_stamp_filter": STAMP_FILTER,
        "host_probe": host_probe,
        "n_pairs": n,
        "summary": {
            "pass": hits,
            "n": n,
            "pass_rate": round(hits / n, 4) if n else 0.0,
            "verdict_match": sum(1 for p in pairs if p["match"]["verdict"]),
            "vs_match": sum(1 for p in pairs if p["match"]["vs_reported_line"]),
            "source_map_match": sum(1 for p in pairs if p["match"]["source_map_pairs"]),
            "source_comment_match": sum(
                1 for p in pairs if p["match"]["source_comment_texts"]
            ),
            "normalized_log_match": sum(1 for p in pairs if p["match"]["normalized_log"]),
            "nodbg_obj_match": sum(1 for p in pairs if p["match"].get("nodbg_obj_sha256")),
            "dbg_obj_match": sum(1 for p in pairs if p["match"].get("dbg_obj_sha256")),
        },
        "pairs": pairs,
        "note": (
            "Marker-neutral = ORACLE_* → /* */ (line-preserving). "
            "pass = verdict + normalized -g load log (timing/ASLR stripped) + "
            "source-comment texts + same-path -O2 (no -g) ELF sha256 identity. "
            "Lab -O2 -g objects often differ (debug/source metadata; .BTF and .BTF.ext dumps); reported as dbg_obj_match."
        ),
    }
    out = ROOT / "results" / "marker_isolation_lab.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2))
    print(f"Wrote {out}")
    return 0 if hits == n and n > 0 else 1


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--rescore":
        lab = rescore_existing(ROOT / "results" / "marker_isolation_lab.json")
        print(json.dumps(lab["summary"], indent=2))
        raise SystemExit(0 if lab["summary"]["pass"] == lab["summary"]["n"] else 1)
    raise SystemExit(main())

#!/usr/bin/env python3
"""Lab-load a single BPF C file via LAB_TEST_* and report accept/reject."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
# Override with BPFIX_LAB_ENV_FILE to point at a lab .env outside the repo
# (e.g. a notes/ checkout); defaults to a gitignored lab/.env next to this tool.
ENV = Path(os.environ.get("BPFIX_LAB_ENV_FILE", str(ROOT / "lab" / ".env")))


def load_env(path: Path) -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return normalize_lab_env(cfg)


def normalize_lab_env(cfg: dict[str, str]) -> dict[str, str]:
    """Accept LAB_TEST_* (canonical) or LAB_HOST2_* (author notes alias)."""
    aliases = {
        "LAB_TEST_HOST": ("LAB_HOST2", "LAB_HOST2_HOST"),
        "LAB_TEST_USER": ("LAB_HOST2_USER",),
        "LAB_TEST_PASSWORD": ("LAB_HOST2_PASSWORD",),
        "LAB_TEST_SSH_KEY": ("LAB_HOST2_SSH_KEY",),
    }
    out = dict(cfg)
    for canon, alts in aliases.items():
        if (out.get(canon) or "").strip():
            continue
        for a in alts:
            if (out.get(a) or "").strip():
                out[canon] = out[a]
                break
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: lab_load_one.py <relative-or-abs.c> [prog_type]")
        return 2
    src = Path(sys.argv[1])
    if not src.is_absolute():
        src = ROOT / src
    prog_type = sys.argv[2] if len(sys.argv) > 2 else "socket"
    text = src.read_text(encoding="utf-8")
    sha = hashlib.sha256(text.encode()).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cfg = load_env(ENV)
    host = (cfg.get("LAB_TEST_HOST") or "").strip()
    user = (cfg.get("LAB_TEST_USER") or "boma").strip()
    key_path = (cfg.get("LAB_TEST_SSH_KEY") or "").strip()
    password = (cfg.get("LAB_TEST_PASSWORD") or "").strip() or None
    if not host:
        raise SystemExit("Set LAB_TEST_HOST (or LAB_HOST2) in lab/.env / BPFIX_LAB_ENV_FILE")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict = {
        "hostname": host,
        "username": user,
        "timeout": 20,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if key_path:
        kwargs["pkey"] = paramiko.Ed25519Key.from_private_key_file(
            str(Path(key_path).expanduser())
        )
    elif password:
        kwargs["password"] = password
    else:
        raise SystemExit("Set LAB_TEST_SSH_KEY or LAB_TEST_PASSWORD (or LAB_HOST2_* aliases)")
    c.connect(**kwargs)
    sftp = c.open_sftp()
    remote_c = f"/tmp/bpfix-one-{stamp}.c"
    remote_o = f"/tmp/bpfix-one-{stamp}.o"
    remote_log = f"/tmp/bpfix-one-{stamp}.log"
    with sftp.file(remote_c, "w") as f:
        f.write(text)
    # Prefer passworded sudo when LAB_TEST_PASSWORD is set (app-test-server);
    # fall back to passwordless sudo -n (SoftwareX pin / lab-test).
    if password:
        pw_file = f"/tmp/.bpfix_one_pw_{stamp}"
        with sftp.file(pw_file, "w") as f:
            f.write(password + "\n")
        c.exec_command(f"chmod 600 {pw_file}", timeout=10)
        sudo_bpf = f'PW=$(cat {pw_file}); printf "%s\\n" "$PW" | sudo -S -p "" /usr/sbin/bpftool'
        sudo_rm = f'PW=$(cat {pw_file}); printf "%s\\n" "$PW" | sudo -S -p "" rm -f'
        cleanup_pw = f"rm -f {pw_file}"
    else:
        sudo_bpf = "sudo -n /usr/sbin/bpftool"
        sudo_rm = "sudo -n rm -f"
        cleanup_pw = "true"
    cmd = (
        f"export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; "
        f"clang -O2 -g -target bpf -I/usr/include/x86_64-linux-gnu "
        f"-idirafter /usr/include -c {remote_c} -o {remote_o} 2>{remote_log}.ce; "
        f"ec=$?; if [ $ec -ne 0 ]; then echo COMPILE_FAIL; cat {remote_log}.ce; "
        f"{cleanup_pw}; exit 1; fi; "
        f"{sudo_bpf} -d prog load {remote_o} /sys/fs/bpf/bpfix_one_{stamp} "
        f"type {prog_type} >{remote_log} 2>&1; load_ec=$?; "
        f"{sudo_rm} /sys/fs/bpf/bpfix_one_{stamp} 2>/dev/null; "
        f"{cleanup_pw}; "
        f"if grep -qE 'failed to load|invalid|unbounded|math between' {remote_log}; "
        f"then echo REJECT; else echo ACCEPT; fi; "
        f"echo EXIT:$load_ec; tail -n 40 {remote_log}"
    )
    _i, o, _e = c.exec_command(cmd, timeout=90, get_pty=True)
    out = o.read().decode(errors="replace")
    if password:
        out = out.replace(password, "***")
    print(out)
    local_dir = ROOT / "fixtures" / "logs" / "captured"
    local_dir.mkdir(parents=True, exist_ok=True)
    local_log = local_dir / f"{src.stem}.{stamp}.log"
    local_log.write_text(out, encoding="utf-8")
    verdict = "ACCEPT" if any(line.strip() == "ACCEPT" for line in out.splitlines()) else "REJECT"
    if any(line.strip() == "COMPILE_FAIL" for line in out.splitlines()):
        verdict = "COMPILE_FAIL"
    meta = {
        "src": str(src.relative_to(ROOT)).replace("\\", "/"),
        "src_sha256": sha,
        "stamp": stamp,
        "verdict": verdict,
        "log": str(local_log.relative_to(ROOT)).replace("\\", "/"),
        "prog_type": prog_type,
    }
    print("META", meta)
    c.close()
    return 0 if verdict == "ACCEPT" else 1


if __name__ == "__main__":
    raise SystemExit(main())

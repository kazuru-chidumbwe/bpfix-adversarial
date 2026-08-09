# SPDX-License-Identifier: MIT
"""Lab capture via LAB_TEST_* (.env). Prefer key; sudo password from LAB_TEST_PASSWORD."""

from __future__ import annotations

import os
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import paramiko

ROOT = Path(__file__).resolve().parents[1]
# Override with BPFIX_LAB_ENV_FILE to point at a lab .env outside the repo
# (e.g. a notes/ checkout); defaults to a gitignored lab/.env next to this tool.
ENV = Path(os.environ.get("BPFIX_LAB_ENV_FILE", str(ROOT / "lab" / ".env")))
LOCAL_CAP = ROOT / "fixtures" / "logs" / "captured"
LOCAL_META = ROOT / "results" / "env_pins"


def load_env(path: Path) -> dict[str, str]:
    cfg: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
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


def connect(cfg: dict[str, str]) -> paramiko.SSHClient:
    host = (cfg.get("LAB_TEST_HOST") or "").strip()
    user = (cfg.get("LAB_TEST_USER") or "boma").strip()
    password = (cfg.get("LAB_TEST_PASSWORD") or "").strip() or None
    key_path = (cfg.get("LAB_TEST_SSH_KEY") or "").strip()
    if not host:
        raise SystemExit("Set LAB_TEST_HOST (or LAB_HOST2) in lab/.env (or BPFIX_LAB_ENV_FILE)")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    kwargs: dict = {
        "hostname": host,
        "username": user,
        "timeout": 25,
        "allow_agent": False,
        "look_for_keys": False,
    }
    if key_path:
        kp = Path(key_path).expanduser()
        kwargs["pkey"] = paramiko.Ed25519Key.from_private_key_file(str(kp))
        print(f"connecting {user}@{host} with key ...")
    elif password:
        kwargs["password"] = password
        print(f"connecting {user}@{host} with password ...")
    else:
        raise SystemExit("Set LAB_TEST_SSH_KEY or LAB_TEST_PASSWORD (or LAB_HOST2_* aliases)")
    client.connect(**kwargs)
    print("ssh ok")
    return client


def main() -> None:
    LOCAL_CAP.mkdir(parents=True, exist_ok=True)
    LOCAL_META.mkdir(parents=True, exist_ok=True)
    cfg = load_env(ENV)
    sudo_pw = (cfg.get("LAB_TEST_PASSWORD") or "").strip()
    # Empty password → assume passwordless sudo (sysadmin on lab-test)

    client = connect(cfg)

    def run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
        _stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
        out = stdout.read().decode("utf-8", errors="replace")
        err = stderr.read().decode("utf-8", errors="replace")
        return stdout.channel.recv_exit_status(), out, err

    _rc, out, err = run(
        "hostname; whoami; uname -r; clang --version | head -1; bpftool version | head -1"
    )
    print((out or err).strip())

    pack = Path(tempfile.gettempdir()) / "bpfix-adv-lab.tgz"
    with tarfile.open(pack, "w:gz") as tar:
        for rel in (
            "mutants",
            "lab",
            "bpfix_adversarial",
            "tools",
            "fixtures/logs/synthetic",
            "pyproject.toml",
            "README.md",
        ):
            p = ROOT / rel
            if p.exists():
                tar.add(p, arcname=rel)

    sftp = client.open_sftp()
    home = f"/home/{cfg.get('LAB_TEST_USER', 'boma').strip()}"
    sftp.put(str(pack), f"{home}/bpfix-adv-lab.tgz")
    print(f"uploaded {pack.name} ({pack.stat().st_size} bytes)")

    _rc, out, err = run(
        f"rm -rf {home}/bpfix-adversarial-work && mkdir -p {home}/bpfix-adversarial-work && "
        f"tar -xzf {home}/bpfix-adv-lab.tgz -C {home}/bpfix-adversarial-work && "
        f"cd {home}/bpfix-adversarial-work && mkdir -p fixtures/logs/captured results/env_pins && "
        "ls mutants/*/*.c | wc -l"
    )
    print("extract:", (out or err).strip())

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if sudo_pw:
        with sftp.file(f"{home}/.bpfix_sudo_pw", "w") as f:
            f.write(sudo_pw + "\n")
        run(f"chmod 600 {home}/.bpfix_sudo_pw")
        sudo_bpf = 'printf \'%s\\n\' "$PW" | sudo -S bpftool'
        sudo_rm = 'printf \'%s\\n\' "$PW" | sudo -S rm -f'
        pw_line = "PW=$(cat ~/.bpfix_sudo_pw)"
        cleanup_pw = "rm -f ~/.bpfix_sudo_pw"
    else:
        sudo_bpf = "sudo -n /usr/sbin/bpftool"
        sudo_rm = "sudo -n rm -f"
        pw_line = "PW="
        cleanup_pw = "true"

    remote_script = f"""#!/usr/bin/env bash
set -euo pipefail
cd ~/bpfix-adversarial-work
STAMP={stamp}
OUT_DIR=fixtures/logs/captured
META_DIR=results/env_pins
OBJ_DIR=/tmp/bpfix-adv-objs
export PATH="/usr/sbin:/usr/bin:$PATH"
{pw_line}
# Always drop the sudo password file on exit (success or failure).
trap '{cleanup_pw}' EXIT
mkdir -p "$OUT_DIR" "$META_DIR" "$OBJ_DIR"
{{
  echo host=$(hostname)
  echo user=$(whoami)
  echo utc=$STAMP
  uname -a
  clang --version | head -2 || echo NO_CLANG
  /usr/sbin/bpftool version || echo NO_BPFTOOL
}} | tee "$META_DIR/lab-test.$STAMP.env.txt"
MANIFEST="$META_DIR/capture-manifest.$STAMP.jsonl"
: > "$MANIFEST"
for src in $(find mutants -name '*.c' | sort); do
  case_id=$(basename "$src" .c)
  obj="$OBJ_DIR/${{case_id}}.o"
  log="$OUT_DIR/${{case_id}}.$STAMP.log"
  pin="/sys/fs/bpf/bpfix_adv_${{case_id}}"
  if grep -q 'SEC("xdp")' "$src"; then ptype=xdp; else ptype=socket; fi
  echo "=== CAPTURE $case_id type=$ptype ==="
  if ! clang -O2 -g -target bpf \\
      -I/usr/include/x86_64-linux-gnu \\
      -idirafter /usr/include \\
      -c "$src" -o "$obj" 2>"$log.compile"; then
    echo COMPILE_FAIL > "$log"
    cat "$log.compile" >> "$log" || true
  else
    # bpftool 7.5: verifier/debug log via -d (no log_level keyword)
    {sudo_bpf} -d prog load "$obj" "$pin" type "$ptype" >"$log" 2>&1 || true
    {sudo_rm} "$pin" 2>/dev/null || true
  fi
  src_hash=$(sha256sum "$src" | awk '{{print $1}}')
  log_hash=$(sha256sum "$log" | awk '{{print $1}}')
  printf '%s\\n' "{{\\"case_id\\":\\"$case_id\\",\\"src\\":\\"$src\\",\\"src_sha256\\":\\"$src_hash\\",\\"log\\":\\"$log\\",\\"log_sha256\\":\\"$log_hash\\",\\"utc\\":\\"$STAMP\\",\\"prog_type\\":\\"$ptype\\"}}" >> "$MANIFEST"
  echo "$case_id $log_hash"
  tail -n 12 "$log" || true
done
echo DONE stamp=$STAMP
wc -l "$MANIFEST"
"""
    # Note: cleanup_pw runs via trap EXIT (not duplicated at end).
    with sftp.file(f"{home}/run_bpfix_capture.sh", "w") as f:
        f.write(remote_script.replace("\r\n", "\n"))
    run("chmod +x ~/run_bpfix_capture.sh")
    print("running batch capture...")
    rc, out, err = run("bash ~/run_bpfix_capture.sh", timeout=600)
    print(out[-6000:] if len(out) > 6000 else out)
    if err.strip():
        print("stderr_tail:", err[-1500:])
    print("rc=", rc)

    remote_root = f"{home}/bpfix-adversarial-work"
    for name in sftp.listdir(f"{remote_root}/fixtures/logs/captured"):
        if stamp in name:
            sftp.get(
                f"{remote_root}/fixtures/logs/captured/{name}",
                str(LOCAL_CAP / name),
            )
            print("got log", name)
    for name in sftp.listdir(f"{remote_root}/results/env_pins"):
        if stamp in name:
            sftp.get(
                f"{remote_root}/results/env_pins/{name}",
                str(LOCAL_META / name),
            )
            print("got meta", name)

    sftp.close()
    client.close()
    print("stamp=", stamp)
    print("local_logs=", len(list(LOCAL_CAP.glob(f"*{stamp}*"))))


if __name__ == "__main__":
    main()

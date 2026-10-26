#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check that a downloaded Zenodo zip holds exactly the files of a git tag.

docs/ZENODO.md states the v1.0.2 record is
``git archive --format=zip --prefix=bpfix-adversarial-v1.0.2/ v1.0.2``. The note
also dates the mint to 15 Sep 2026 while the tag's commit is dated 30 Sep 2026,
so the archive may predate the final tag. Zip bytes differ with timestamps, so
this compares member names and file contents.

Usage:
  curl -L -o /tmp/z.zip "https://zenodo.org/records/22763331/files/<file>.zip?download=1"
  python tools/check_zenodo_archive.py --zip /tmp/z.zip --tag v1.0.2
Exit 0 when identical, 1 otherwise (differences printed).
"""

from __future__ import annotations

import argparse
import hashlib
import io
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest_members(zf: zipfile.ZipFile) -> dict[str, str]:
    out = {}
    for info in zf.infolist():
        if info.is_dir():
            continue
        name = info.filename.split("/", 1)[1] if "/" in info.filename else info.filename
        out[name] = hashlib.sha256(zf.read(info)).hexdigest()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--tag", default="v1.0.2")
    args = ap.parse_args(argv)

    git = subprocess.run(
        ["git", "-C", str(ROOT), "archive", "--format=zip", f"--prefix=bpfix-adversarial-{args.tag}/", args.tag],
        capture_output=True, check=True,
    )
    tag_files = digest_members(zipfile.ZipFile(io.BytesIO(git.stdout)))
    zen_files = digest_members(zipfile.ZipFile(args.zip))
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-list", "-n1", args.tag],
                            capture_output=True, text=True, check=True).stdout.strip()

    only_tag = sorted(set(tag_files) - set(zen_files))
    only_zen = sorted(set(zen_files) - set(tag_files))
    changed = sorted(n for n in set(tag_files) & set(zen_files) if tag_files[n] != zen_files[n])
    print(f"tag {args.tag} -> {commit}: {len(tag_files)} files; zip: {len(zen_files)} files")
    for label, names in (("only in tag", only_tag), ("only in zip", only_zen), ("content differs", changed)):
        for n in names:
            print(f"  {label}: {n}")
    ok = not (only_tag or only_zen or changed)
    print("IDENTICAL" if ok else "DIFFERENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

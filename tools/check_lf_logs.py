#!/usr/bin/env python3
"""Fail if any fixtures/**/*.log (or given paths) contain CRLF bytes.

CI / pre-push hygiene: .gitattributes declares eol=lf, but Windows captures
can still be committed with CRLF unless renormalized.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        paths = sorted((ROOT / "fixtures").rglob("*.log"))
    bad: list[str] = []
    for p in paths:
        if not p.is_file():
            continue
        data = p.read_bytes()
        if b"\r\n" in data or (b"\r" in data and b"\n" in data):
            # bare CR without LF also counts as non-LF
            bad.append(str(p.relative_to(ROOT)).replace("\\", "/"))
    if bad:
        print("CRLF (or CR) found in log files — run: git add --renormalize fixtures/")
        for b in bad:
            print(f"  {b}")
        return 1
    print(f"OK: {len(paths)} log file(s) are LF-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

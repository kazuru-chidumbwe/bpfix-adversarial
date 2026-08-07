#!/usr/bin/env python3
"""Fail unless package __version__ matches pyproject.toml [project].version."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'(?m)^version\s*=\s*"([^"]+)"', pyproject)
    if not m:
        print("ERROR: no version in pyproject.toml")
        return 1
    expected = m.group(1)
    sys.path.insert(0, str(ROOT))
    import bpfix_adversarial as pkg  # noqa: E402

    got = pkg.__version__
    if got != expected:
        print(f"ERROR: bpfix_adversarial.__version__={got!r} != pyproject={expected!r}")
        return 1
    print(f"OK: version {got}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

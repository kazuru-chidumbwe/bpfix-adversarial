#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Fail unless the version and release date agree across the files that state them.

docs/TAGS.md lists what this check covers, so it covers exactly that: the package
__version__, pyproject.toml, CITATION.cff, codemeta.json and code-metadata row C1
(CODE_METADATA.md) must agree on the version, and CITATION.cff date-released must
match codemeta.json dateModified.

Checking only pyproject against the package left the other two files free to
drift.
"""

from __future__ import annotations

import json
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

    cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    m_cff = re.search(r'(?m)^version:\s*"?([^"\s]+)"?\s*$', cff)
    if not m_cff:
        print("ERROR: CITATION.cff has no version")
        return 1
    if m_cff.group(1).strip().lstrip("v") != expected:
        print(f"ERROR: CITATION.cff version={m_cff.group(1)!r} != pyproject={expected!r}")
        return 1

    meta = json.loads((ROOT / "codemeta.json").read_text(encoding="utf-8"))
    if str(meta.get("version", "")).lstrip("v") != expected:
        print(f"ERROR: codemeta.json version={meta.get('version')!r} != pyproject={expected!r}")
        return 1

    code_meta = (ROOT / "CODE_METADATA.md").read_text(encoding="utf-8")
    m_c1 = re.search(r"(?m)^\|\s*C1\s*\|[^|]*\|\s*`?v?([^`|\s]+)`?\s*\|", code_meta)
    if not m_c1:
        print("ERROR: CODE_METADATA.md has no C1 row")
        return 1
    if m_c1.group(1) != expected:
        print(f"ERROR: CODE_METADATA.md C1={m_c1.group(1)!r} != pyproject={expected!r}")
        return 1

    m_date = re.search(r'(?m)^date-released:\s*"?(\d{4}-\d{2}-\d{2})"?', cff)
    if not m_date:
        print("ERROR: CITATION.cff has no date-released")
        return 1
    released = m_date.group(1)
    if meta.get("dateModified") != released:
        print(
            f"ERROR: codemeta.json dateModified={meta.get('dateModified')!r} != "
            f"CITATION.cff date-released={released!r}"
        )
        return 1

    print(f"OK: version {got} across pyproject, package, CITATION.cff, codemeta and C1")
    print(f"OK: release date {released} consistent across CITATION.cff and codemeta")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

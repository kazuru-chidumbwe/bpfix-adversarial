#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate campaign v2 mutants into campaigns/v2/mutants/ (see campaigns/v2/README.md).

The cited v1.0.2 mutants under mutants/ are not touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.gen_v2 import write_v2_mutants  # noqa: E402

OUT = ROOT / "campaigns" / "v2" / "mutants"


def main() -> None:
    paths = write_v2_mutants(OUT)
    print(f"Wrote {len(paths)} v2 mutants under {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()

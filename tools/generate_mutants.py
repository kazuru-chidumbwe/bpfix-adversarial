#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate all mutant C sources into mutants/."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bpfix_adversarial.gen_nullable import write_nullable_pair  # noqa: E402
from bpfix_adversarial.gen_obligations import write_obligation_templates  # noqa: E402


def main() -> None:
    mut = ROOT / "mutants"
    np_paths = []
    for pad in (0, 8, 32):
        np_paths.extend(write_nullable_pair(mut / "NullablePointer", pad=pad))
    other = write_obligation_templates(mut, pads=[0, 8, 32])
    print(f"Wrote {len(np_paths)} NullablePointer + {len(other)} other mutants under {mut}")


if __name__ == "__main__":
    main()

# SPDX-License-Identifier: MIT
"""Rename adversaries targeting looks_like_null_check name substrings."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from .heuristics import looks_like_null_check, looks_like_nullable_return, null_check_match_detail


# Names that *do* trip the bang-prefixed substrings in bpfix.
BRITTLE_NAMES = ("tmp", "val", "ptr", "value")

# Idiomatic C/eBPF names that do *not* contain those substrings.
SAFE_RENAMES = ("entry", "rec", "slot", "item", "elem", "obj", "node", "sk_ref")


@dataclass(frozen=True)
class RenameCase:
    case_id: str
    original_line: str
    renamed_line: str
    original_var: str
    renamed_var: str
    original_null_check: bool
    renamed_null_check: bool
    helper_line: str
    helper_anchored_stable: bool

    @property
    def honesty_break(self) -> bool:
        """True when rename flips SourceComment null-check recognition."""
        return self.original_null_check and not self.renamed_null_check

    def to_dict(self) -> dict:
        d = asdict(self)
        d["honesty_break"] = self.honesty_break
        d["original_detail"] = null_check_match_detail(self.original_line).to_dict()
        d["renamed_detail"] = null_check_match_detail(self.renamed_line).to_dict()
        return d


def _check_line(var: str) -> str:
    return f"if (!{var})"


def _helper_line() -> str:
    return "entry = bpf_map_lookup_elem(&m, &key);"


def generate_rename_cases(
    brittle: Iterable[str] = BRITTLE_NAMES,
    safe: Iterable[str] = SAFE_RENAMES,
) -> list[RenameCase]:
    """Pair each brittle name with each safe rename; measure heuristic flip."""
    helper = _helper_line()
    helper_ok = looks_like_nullable_return(helper)
    cases: list[RenameCase] = []
    for i, orig in enumerate(brittle):
        for j, new in enumerate(safe):
            if new == orig:
                continue
            o_line = _check_line(orig)
            n_line = _check_line(new)
            cases.append(
                RenameCase(
                    case_id=f"rename-null-{orig}-to-{new}-{i:02d}{j:02d}",
                    original_line=o_line,
                    renamed_line=n_line,
                    original_var=orig,
                    renamed_var=new,
                    original_null_check=looks_like_null_check(o_line),
                    renamed_null_check=looks_like_null_check(n_line),
                    helper_line=helper,
                    helper_anchored_stable=helper_ok,
                )
            )
    return cases


def summary(cases: list[RenameCase] | None = None) -> dict:
    cases = cases or generate_rename_cases()
    breaks = [c for c in cases if c.honesty_break]
    return {
        "n_cases": len(cases),
        "n_honesty_breaks": len(breaks),
        "break_rate": (len(breaks) / len(cases)) if cases else 0.0,
        "brittle_names": list(BRITTLE_NAMES),
        "safe_renames": list(SAFE_RENAMES),
        "note": (
            "looks_like_null_check flips under idiomatic rename of !tmp/!val/!ptr/!value; "
            "looks_like_nullable_return stays helper-anchored"
        ),
    }

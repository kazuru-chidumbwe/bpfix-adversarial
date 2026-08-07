"""Faithful Python port of bpfix SourceComment heuristics.

Pinned to eunomia-bpf/bpfix commit 81d97e4a528456e0082a77f4fb6edd13fa092b7b
(`crates/bpfix/src/source.rs`). Do not "improve" these predicates here —
the harness measures *their* honesty under adversarial renaming / distance.
"""

from __future__ import annotations

from .model import HeuristicHit

# Name-shaped substrings inside looks_like_null_check (sponsor: rename-brittle).
# Upstream uses bang-prefixed forms: !tmp, !val, !ptr, !value.
NULL_CHECK_NAME_SUBSTRINGS = ("!tmp", "!val", "!ptr", "!value")

# Structural alternatives that still fire without those names.
NULL_CHECK_STRUCTURAL = ("null", "== 0", "!= 0", "== null", "!= null")


def looks_like_scalar_guard(text: str) -> bool:
    return text.startswith("if ") and any(
        op in text for op in ("<", ">", "<=", ">=", "!=", "==")
    )


def looks_like_packet_bounds_check(text: str) -> bool:
    return text.startswith("if ") and "data_end" in text


def looks_like_null_check(text: str) -> bool:
    """Exact predicate shape from bpfix `looks_like_null_check`."""
    lower = text.lower()
    if not lower.startswith("if "):
        return False
    return any(
        p in lower
        for p in (
            "null",
            "!tmp",
            "!val",
            "!ptr",
            "!value",
            "== 0",
            "!= 0",
            "== null",
            "!= null",
        )
    )


def looks_like_nullable_return(text: str) -> bool:
    """Helper-anchored — rename-insensitive (contrast with looks_like_null_check)."""
    return any(
        h in text
        for h in (
            "bpf_map_lookup_elem",
            "bpf_ringbuf_reserve",
            "bpf_sk_lookup",
            "bpf_skc_lookup",
        )
    )


def looks_like_stack_initialization(text: str) -> bool:
    return "=" in text and ("0" in text or "memset" in text)


def looks_like_reference_acquire(text: str) -> bool:
    return any(
        h in text
        for h in ("bpf_ringbuf_reserve", "bpf_sk_lookup", "bpf_skc_lookup")
    )


def looks_like_reference_release(text: str) -> bool:
    return any(
        h in text
        for h in ("bpf_ringbuf_discard", "bpf_ringbuf_submit", "bpf_sk_release")
    )


def null_check_match_detail(text: str) -> HeuristicHit:
    lower = text.lower()
    matched_patterns: list[str] = []
    if lower.startswith("if "):
        for p in NULL_CHECK_NAME_SUBSTRINGS + NULL_CHECK_STRUCTURAL:
            if p in lower:
                matched_patterns.append(p)
    matched = looks_like_null_check(text)
    name_only = bool(set(matched_patterns) & set(NULL_CHECK_NAME_SUBSTRINGS)) and not (
        set(matched_patterns) & set(NULL_CHECK_STRUCTURAL)
    )
    notes = ""
    if matched and name_only:
        notes = "matched only via name substrings — brittle under idiomatic rename"
    elif matched:
        notes = "matched (structural and/or name patterns)"
    elif lower.startswith("if ") and "!" in lower:
        notes = "idiomatic null-ish check not recognized by bpfix heuristic"
    return HeuristicHit(
        name="looks_like_null_check",
        matched=matched,
        text=text,
        notes=notes,
        matched_patterns=matched_patterns,
    )


def classify_line(text: str) -> dict[str, HeuristicHit]:
    return {
        "looks_like_null_check": null_check_match_detail(text),
        "looks_like_nullable_return": HeuristicHit(
            name="looks_like_nullable_return",
            matched=looks_like_nullable_return(text),
            text=text,
            notes="helper-anchored; rename-insensitive",
        ),
        "looks_like_packet_bounds_check": HeuristicHit(
            name="looks_like_packet_bounds_check",
            matched=looks_like_packet_bounds_check(text),
            text=text,
        ),
        "looks_like_scalar_guard": HeuristicHit(
            name="looks_like_scalar_guard",
            matched=looks_like_scalar_guard(text),
            text=text,
        ),
    }

# SPDX-License-Identifier: MIT
"""Port-fidelity checks against vendored upstream source.rs at SoftwarX pin."""

from __future__ import annotations

import unittest
from pathlib import Path

from bpfix_adversarial.heuristics import (
    looks_like_null_check,
    looks_like_nullable_return,
    looks_like_packet_bounds_check,
    looks_like_reference_acquire,
    looks_like_reference_release,
    looks_like_scalar_guard,
    looks_like_stack_initialization,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RS = ROOT / "fixtures" / "upstream" / "bpfix-source-rs-pin" / "source.rs"
PIN = "81d97e4a528456e0082a77f4fb6edd13fa092b7b"

# Character-faithful twin of the seven Rust predicates (pin source.rs).
def rust_looks_like_scalar_guard(text: str) -> bool:
    return text.startswith("if ") and any(
        op in text for op in ("<", ">", "<=", ">=", "!=", "==")
    )


def rust_looks_like_packet_bounds_check(text: str) -> bool:
    return text.startswith("if ") and "data_end" in text


def rust_looks_like_null_check(text: str) -> bool:
    lower = text.lower()
    return lower.startswith("if ") and any(
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


def rust_looks_like_nullable_return(text: str) -> bool:
    return any(
        h in text
        for h in (
            "bpf_map_lookup_elem",
            "bpf_ringbuf_reserve",
            "bpf_sk_lookup",
            "bpf_skc_lookup",
        )
    )


def rust_looks_like_stack_initialization(text: str) -> bool:
    return "=" in text and ("0" in text or "memset" in text)


def rust_looks_like_reference_acquire(text: str) -> bool:
    return any(
        h in text
        for h in ("bpf_ringbuf_reserve", "bpf_sk_lookup", "bpf_skc_lookup")
    )


def rust_looks_like_reference_release(text: str) -> bool:
    return any(
        h in text
        for h in ("bpf_ringbuf_discard", "bpf_ringbuf_submit", "bpf_sk_release")
    )


CASES = [
    "if (!tmp)",
    "if (!entry)",
    "if (idx < 8)",
    "if (data + 8 > data_end)",
    "entry = bpf_map_lookup_elem(&m, &key);",
    "bpf_ringbuf_reserve(&rb, 8, 0);",
    "bpf_ringbuf_submit(e, 0);",
    "memset(buf, 0, sizeof(buf));",
    "x = 0;",
    "not a match",
]


class TestPortFidelity(unittest.TestCase):
    def test_vendored_source_rs_present(self) -> None:
        self.assertTrue(SOURCE_RS.is_file(), f"missing {SOURCE_RS}")
        text = SOURCE_RS.read_text(encoding="utf-8")
        for name in (
            "looks_like_scalar_guard",
            "looks_like_packet_bounds_check",
            "looks_like_null_check",
            "looks_like_nullable_return",
            "looks_like_stack_initialization",
            "looks_like_reference_acquire",
            "looks_like_reference_release",
        ):
            self.assertIn(f"fn {name}", text)
        # Pin literals that SoftwarX cites for the null-check brittleness story.
        for lit in ("!tmp", "!val", "!ptr", "!value", "bpf_map_lookup_elem"):
            self.assertIn(lit, text)
        readme = (SOURCE_RS.parent / "README.md").read_text(encoding="utf-8")
        self.assertIn(PIN, readme)

    def test_python_matches_rust_twin(self) -> None:
        pairs = [
            (looks_like_scalar_guard, rust_looks_like_scalar_guard),
            (looks_like_packet_bounds_check, rust_looks_like_packet_bounds_check),
            (looks_like_null_check, rust_looks_like_null_check),
            (looks_like_nullable_return, rust_looks_like_nullable_return),
            (looks_like_stack_initialization, rust_looks_like_stack_initialization),
            (looks_like_reference_acquire, rust_looks_like_reference_acquire),
            (looks_like_reference_release, rust_looks_like_reference_release),
        ]
        for py_fn, rust_fn in pairs:
            for case in CASES:
                self.assertEqual(
                    py_fn(case),
                    rust_fn(case),
                    msg=f"{py_fn.__name__} diverged on {case!r}",
                )


if __name__ == "__main__":
    unittest.main()

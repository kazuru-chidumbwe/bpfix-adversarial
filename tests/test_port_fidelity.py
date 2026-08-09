# SPDX-License-Identifier: MIT
"""Port-fidelity checks: Python predicates vs vendored upstream source.rs literals."""

from __future__ import annotations

import hashlib
import re
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
# SHA-256 of upstream crates/bpfix/src/source.rs @ PIN (verified round-2 review).
SOURCE_RS_SHA256 = "f86f884583491f7c0606772ba4ec56e4468437f6d986e26412931820cbf73e52"

FN_NAMES = (
    "looks_like_scalar_guard",
    "looks_like_packet_bounds_check",
    "looks_like_null_check",
    "looks_like_nullable_return",
    "looks_like_stack_initialization",
    "looks_like_reference_acquire",
    "looks_like_reference_release",
)

# Expected string literals from each Rust fn body (order-insensitive sets).
EXPECTED_LITERALS: dict[str, set[str]] = {
    "looks_like_scalar_guard": {"if ", "<", ">", "<=", ">=", "!=", "=="},
    "looks_like_packet_bounds_check": {"if ", "data_end"},
    "looks_like_null_check": {
        "if ",
        "null",
        "!tmp",
        "!val",
        "!ptr",
        "!value",
        "== 0",
        "!= 0",
        "== null",
        "!= null",
    },
    "looks_like_nullable_return": {
        "bpf_map_lookup_elem",
        "bpf_ringbuf_reserve",
        "bpf_sk_lookup",
        "bpf_skc_lookup",
    },
    "looks_like_stack_initialization": {"=", "0", "memset"},
    "looks_like_reference_acquire": {
        "bpf_ringbuf_reserve",
        "bpf_sk_lookup",
        "bpf_skc_lookup",
    },
    "looks_like_reference_release": {
        "bpf_ringbuf_discard",
        "bpf_ringbuf_submit",
        "bpf_sk_release",
    },
}

CASES = [
    "if (!tmp)",
    "if (!entry)",
    "if (idx < 8)",
    "if (data + 8 > data_end)",
    "entry = bpf_map_lookup_elem(&m, &key);",
    "bpf_ringbuf_reserve(&rb, 8, 0);",
    "bpf_ringbuf_submit(e, 0);",
    "bpf_sk_release(sk);",
    "x = bpf_skc_lookup_tcp(&skb, &tuple, sizeof(tuple), BPF_F_CURRENT_NETNS, 0);",
    "memset(buf, 0, sizeof(buf));",
    "x = 0;",
    "if (p == null)",
    "if (p != 0)",
    "if (X == NULL)",
    "not a match",
]


def _extract_fn_body(src: str, name: str) -> str:
    m = re.search(
        rf"pub\(crate\) fn {name}\(text: &str\) -> bool \{{(.*?)\n\}}",
        src,
        flags=re.S,
    )
    if not m:
        raise AssertionError(f"missing fn {name} in vendored source.rs")
    return m.group(1)


def _string_literals(body: str) -> set[str]:
    # Rust char literals '<' and string literals "…"
    out: set[str] = set()
    out.update(re.findall(r'"([^"]*)"', body))
    out.update(re.findall(r"'([^']*)'", body))
    return out


class TestPortFidelity(unittest.TestCase):
    def test_vendored_sha256_matches_upstream_pin(self) -> None:
        self.assertTrue(SOURCE_RS.is_file(), f"missing {SOURCE_RS}")
        digest = hashlib.sha256(SOURCE_RS.read_bytes()).hexdigest()
        self.assertEqual(digest, SOURCE_RS_SHA256)
        readme = (SOURCE_RS.parent / "README.md").read_text(encoding="utf-8")
        self.assertIn(PIN, readme)
        self.assertIn(SOURCE_RS_SHA256, readme)

    def test_rust_literals_match_expected_sets(self) -> None:
        src = SOURCE_RS.read_text(encoding="utf-8")
        for name in FN_NAMES:
            body = _extract_fn_body(src, name)
            got = _string_literals(body)
            self.assertEqual(
                got,
                EXPECTED_LITERALS[name],
                msg=f"{name}: Rust literals {got} != expected {EXPECTED_LITERALS[name]}",
            )

    def test_python_predicates_agree_on_cases(self) -> None:
        # Ground behavioural check against the same literal rules as Rust.
        for case in CASES:
            lower = case.lower()  # C identifiers; matches Rust to_ascii_lowercase for ASCII
            self.assertEqual(
                looks_like_null_check(case),
                lower.startswith("if ")
                and any(
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
                ),
                msg=case,
            )
            self.assertEqual(
                looks_like_packet_bounds_check(case),
                case.startswith("if ") and "data_end" in case,
                msg=case,
            )
            self.assertEqual(
                looks_like_nullable_return(case),
                any(
                    h in case
                    for h in (
                        "bpf_map_lookup_elem",
                        "bpf_ringbuf_reserve",
                        "bpf_sk_lookup",
                        "bpf_skc_lookup",
                    )
                ),
                msg=case,
            )
            self.assertEqual(
                looks_like_reference_release(case),
                any(
                    h in case
                    for h in (
                        "bpf_ringbuf_discard",
                        "bpf_ringbuf_submit",
                        "bpf_sk_release",
                    )
                ),
                msg=case,
            )
            _ = looks_like_scalar_guard(case)
            _ = looks_like_stack_initialization(case)
            _ = looks_like_reference_acquire(case)


if __name__ == "__main__":
    unittest.main()

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

PREDICATES = (
    looks_like_scalar_guard,
    looks_like_packet_bounds_check,
    looks_like_null_check,
    looks_like_nullable_return,
    looks_like_stack_initialization,
    looks_like_reference_acquire,
    looks_like_reference_release,
)

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

# Outputs of the seven upstream predicates, recorded by compiling
# fixtures/upstream/bpfix-source-rs-pin/source.rs lines 80-129 unchanged and
# running them on each string (rustc 1.95, 2026-09-25). Bit order follows
# PREDICATES below. This is Rust output, not a Python restatement.
RUST_TRUTH: list[tuple[str, str]] = [
    ('if (!tmp)', "0010000"),
    ('if (!entry)', "0000000"),
    ('if (idx < 8)', "1000000"),
    ('if (data + 8 > data_end)', "1100000"),
    ('entry = bpf_map_lookup_elem(&m, &key);', "0001000"),
    ('bpf_ringbuf_reserve(&rb, 8, 0);', "0001010"),
    ('bpf_ringbuf_submit(e, 0);', "0000001"),
    ('bpf_sk_release(sk);', "0000001"),
    ('x = bpf_skc_lookup_tcp(&skb, &tuple, sizeof(tuple), BPF_F_CURRENT_NETNS, 0);', "0001110"),
    ('memset(buf, 0, sizeof(buf));', "0000000"),
    ('x = 0;', "0000100"),
    ('if (p == null)', "1010000"),
    ('if (p != 0)', "1010100"),
    ('if (X == NULL)', "1010000"),
    ('not a match', "0000000"),
    ('  if (!ptr)', "0000000"),
    ('IF (!PTR)', "0010000"),
    ('if(!ptr)', "0000000"),
    ('if (a >= b)', "1000000"),
    ('cookie ^= bpf_get_prandom_u32();', "0000000"),
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

    def test_python_predicates_match_rust_outputs(self) -> None:
        for text, bits in RUST_TRUTH:
            got = "".join(str(int(fn(text))) for fn in PREDICATES)
            self.assertEqual(got, bits, msg=repr(text))


if __name__ == "__main__":
    unittest.main()

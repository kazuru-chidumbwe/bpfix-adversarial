# SPDX-License-Identifier: MIT
"""Committed results hashes must match live mutants and captured logs."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _mutant_for(case_id: str) -> Path:
    hits = list(ROOT.joinpath("mutants").rglob(f"{case_id}.c"))
    if not hits:
        raise FileNotFoundError(case_id)
    return hits[0]


class TestResultHashes(unittest.TestCase):
    def _check_src(self, rel: str) -> None:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for row in data["rows"]:
            cid = row["case_id"]
            live = _sha(_mutant_for(cid))
            self.assertEqual(
                live,
                row["src_sha256"],
                f"{rel} case {cid}: src_sha256 does not match mutants/**/{cid}.c",
            )

    def _check_logs(self, rel: str) -> None:
        data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        for row in data["rows"]:
            path = row.get("log_path")
            sha = row.get("log_sha256")
            if not path or not sha:
                continue
            p = ROOT / path
            self.assertTrue(p.is_file(), f"{rel} case {row['case_id']}: missing {path}")
            live = _sha(p)
            self.assertEqual(
                live,
                sha,
                f"{rel} case {row['case_id']}: log_sha256 does not match {path}",
            )

    def test_four_obligation_src_sha256(self) -> None:
        self._check_src("results/four_obligation_matrix.json")

    def test_sc_vs_honesty_src_sha256(self) -> None:
        self._check_src("results/sc_vs_honesty.json")

    def test_four_obligation_log_sha256(self) -> None:
        self._check_logs("results/four_obligation_matrix.json")

    def test_sc_vs_honesty_log_sha256(self) -> None:
        self._check_logs("results/sc_vs_honesty.json")


if __name__ == "__main__":
    unittest.main()

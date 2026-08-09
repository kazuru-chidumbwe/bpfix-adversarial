# SPDX-License-Identifier: MIT
"""Schemas must stay parseable JSON (optional interchange; not runtime-gated)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


class TestSchemas(unittest.TestCase):
    def test_case_schema_loads(self) -> None:
        data = json.loads((SCHEMAS / "case.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(data.get("title"), "BpfixAdversarialCase")
        self.assertIn("case_id", data["required"])

    def test_result_schema_loads(self) -> None:
        data = json.loads((SCHEMAS / "result.schema.json").read_text(encoding="utf-8"))
        self.assertIn("properties", data)


if __name__ == "__main__":
    unittest.main()

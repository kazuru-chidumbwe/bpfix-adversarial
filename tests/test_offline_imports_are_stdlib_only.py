#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""The offline paths must import on a stdlib-only install.

README and docs/DEPENDENCIES.md both promise that `pip install -e .` is enough
for the offline workflow. A module-scope `import paramiko` breaks that promise
the moment anything offline touches the module, and it breaks it at import time,
before the code that actually needs SSH is ever reached.

That regression shipped once: the freshness check began running
`lab_marker_isolation_ab.py --rescore`, which needs no SSH, but the module
imported paramiko at the top. Both documented offline entry points, the venv
quick start and the Docker image, failed identically. It was invisible in any
environment that happened to have the `[lab]` extra installed.

This test encodes the invariant directly rather than relying on the test runner
happening to lack the optional dependency.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPTIONAL = {"paramiko"}


def module_scope_imports(path: Path) -> set[str]:
    """Top-level import names, ignoring those guarded by TYPE_CHECKING or a function."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            found.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.add(node.module.split(".")[0])
    return found


class TestOfflineImportsAreStdlibOnly(unittest.TestCase):
    def test_no_optional_dependency_at_module_scope(self) -> None:
        offenders = []
        for path in sorted((ROOT / "tools").glob("*.py")) + sorted(
            (ROOT / "bpfix_adversarial").glob("*.py")
        ):
            hit = module_scope_imports(path) & OPTIONAL
            if hit:
                offenders.append(f"{path.relative_to(ROOT).as_posix()}: {sorted(hit)}")
        self.assertEqual(
            offenders,
            [],
            "optional dependencies must be imported inside the code paths that need "
            "them, not at module scope:\n  " + "\n  ".join(offenders),
        )

    def test_rescore_entry_point_imports_without_ssh_support(self) -> None:
        """The rescore path is reachable without the [lab] extra."""
        path = ROOT / "tools" / "lab_marker_isolation_ab.py"
        self.assertNotIn("paramiko", module_scope_imports(path))
        source = path.read_text(encoding="utf-8")
        self.assertIn("--rescore", source)


if __name__ == "__main__":
    unittest.main()

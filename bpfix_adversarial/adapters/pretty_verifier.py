# SPDX-License-Identifier: MIT
"""Adapter for Pretty Verifier (Rizza et al., netgroup-polito/pretty-verifier).

Pretty Verifier reads the verifier log, the C source and the compiled object
and prints a source-level error. It takes the line just before
``processed N insns`` as the verifier's error, which is the layout of the plain
(level 1) log that a failed load prints. Captures made with ``bpftool -d``
also carry the statistics lines ``verification time`` and ``stack depth``
there, so ``replay`` passes the program-load log with those two lines removed
and nothing else changed.

Environment: ``PRETTY_VERIFIER`` (CLI path, default ``pretty-verifier``),
``PRETTY_VERIFIER_SRC`` (source checkout, for the commit in provenance).
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
from pathlib import Path

from ..reporters import CaseContext, Prediction

ANSI = re.compile(r"\x1b\[[0-9;]*m")
BANNER = "Prettier Verifier"
NUMBERED = re.compile(r"^\s*(\d+) \| ")
IN_FILE = re.compile(r"^\s*\| in file (.+?)\s*$")
STATS = re.compile(r"^(verification time|stack depth) ")


def plain_log(capture: str) -> str:
    lines = capture.splitlines()
    begin = next((i for i, ln in enumerate(lines) if "-- BEGIN PROG LOAD LOG --" in ln), None)
    end = next((i for i, ln in enumerate(lines) if "-- END PROG LOAD LOG --" in ln), None)
    body = lines[begin + 1 : end] if begin is not None and end is not None else lines
    return "\n".join(ln for ln in body if not STATS.match(ln)) + "\n"


class PrettyVerifier:
    name = "PrettyVerifier"
    needs_artifact = ".prettyverifier.txt"

    def __init__(self) -> None:
        self.cli = os.environ.get("PRETTY_VERIFIER", "pretty-verifier")
        self.src = os.environ.get("PRETTY_VERIFIER_SRC")

    def provenance(self) -> dict:
        commit = None
        if self.src:
            p = subprocess.run(["git", "-C", self.src, "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
            commit = p.stdout.strip() or None
        return {"cli": self.cli, "source_commit": commit,
                "input": "program-load log without 'verification time' and 'stack depth' lines"}

    def replay(self, ctx: CaseContext, obj: Path) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".log", delete=False, encoding="utf-8") as f:
            f.write(plain_log(ctx.log_text()))
            tmp = f.name
        try:
            p = subprocess.run([self.cli, "-l", tmp, "-c", str(ctx.source), "-o", str(obj)],
                               capture_output=True, text=True, timeout=300, check=False)
        finally:
            os.unlink(tmp)
        text = ANSI.sub("", p.stdout + p.stderr)
        i = text.find(BANNER)
        return text[i:] if i >= 0 else "NO_PRETTY_VERIFIER_OUTPUT\n" + text[-2000:]

    def predict(self, ctx: CaseContext) -> Prediction:
        p = ctx.artifact(self.needs_artifact)
        if p is None:
            return Prediction(None, [], "PrettyVerifier output missing")
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines or not lines[0].startswith(BANNER):
            return Prediction(None, [], lines[0] if lines else "empty")
        if any("Error not managed" in ln for ln in lines):
            return Prediction(None, [], "error not managed")
        found: list[int] = []
        for i, ln in enumerate(lines):
            m = NUMBERED.match(ln)
            if not m:
                continue
            nxt = IN_FILE.match(lines[i + 1]) if i + 1 < len(lines) else None
            if nxt and Path(nxt.group(1)).name != ctx.source.name:
                continue  # a location in another file (e.g. a header)
            found.append(int(m.group(1)))
        if not found:
            return Prediction(None, [], "no source location")
        return Prediction(found[0], found, "")

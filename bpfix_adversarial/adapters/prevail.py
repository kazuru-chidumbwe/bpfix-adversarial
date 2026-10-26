# SPDX-License-Identifier: MIT
"""Adapter for PREVAIL (Gershuni et al., vbpf/prevail), an independent eBPF verifier.

PREVAIL does not read the kernel's log: it analyses the compiled object with
its own abstract interpreter and, with ``--line-info``, prints the source
location of the first failed assertion as ``; <path>:<line>``. Its verdict can therefore differ from
the kernel's; a program PREVAIL accepts scores as a miss and is noted.

Environment: ``PREVAIL`` (binary path, default ``prevail``), ``PREVAIL_SRC``
(source checkout, for the commit in provenance).
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from ..reporters import CaseContext, Prediction

LOC = re.compile(r"^; (.+):(\d+)\s*$")
HEADER = "PREVAIL"


class Prevail:
    name = "PREVAIL"
    needs_artifact = ".prevail.txt"

    def __init__(self) -> None:
        self.bin = os.environ.get("PREVAIL", "prevail")
        self.src = os.environ.get("PREVAIL_SRC")

    def provenance(self) -> dict:
        version = subprocess.run([self.bin, "--version"], capture_output=True, text=True, check=False).stdout.strip()
        commit = None
        if self.src:
            p = subprocess.run(["git", "-C", self.src, "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
            commit = p.stdout.strip() or None
        return {"binary": self.bin, "version": version, "source_commit": commit,
                "input": "compiled object only; the kernel log is not read"}

    def _run(self, args: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run([self.bin, *args, "--line-info"], capture_output=True, text=True, timeout=600,
                              check=False)

    def replay(self, ctx: CaseContext, obj: Path) -> str:
        p = self._run([str(obj)])
        out = p.stdout + p.stderr
        if "please specify a program" in out:
            # Several programs in the object: analyse the one the kernel failed to load.
            progs = re.findall(r"section=(\S+) function=(\S+)", out)
            failed = re.search(r"prog '([^']+)': BPF program load failed", ctx.log_text())
            pick = next((sf for sf in progs if failed and sf[1] == failed.group(1)), None) or \
                next((sf for sf in progs if sf[0] != ".text"), None)
            if pick:
                p = self._run([str(obj), pick[0], pick[1]])
                out = f"(program {pick[0]}/{pick[1]})\n{p.stdout}{p.stderr}"
        return f"{HEADER} exit={p.returncode}\n{out}"

    def predict(self, ctx: CaseContext) -> Prediction:
        p = ctx.artifact(self.needs_artifact)
        if p is None:
            return Prediction(None, [], "PREVAIL output missing")
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines or not lines[0].startswith(HEADER):
            return Prediction(None, [], lines[0] if lines else "empty")
        verdict = "FAIL" if any(ln.startswith("FAIL") for ln in lines) else (
            "PASS" if any(ln.startswith("PASS") for ln in lines) else "other")
        found = [int(m.group(2)) for ln in lines if (m := LOC.match(ln)) and Path(m.group(1)).name == ctx.source.name]
        if not found:
            return Prediction(None, [], f"PREVAIL {verdict}, no source location")
        return Prediction(found[0], [], f"PREVAIL {verdict}")

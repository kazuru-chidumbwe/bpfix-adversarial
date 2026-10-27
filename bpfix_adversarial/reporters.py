# SPDX-License-Identifier: MIT
"""Reporter registry: every diagnostic the scorers compare goes through here.

A reporter maps one captured case to a :class:`Prediction` (a primary source
line and, optionally, further labelled lines). Built-in reporters read the
captured verifier log or the case source. A reporter backed by an external
tool reads that tool's output, which a replay step stored next to the log as
``<case>.<stamp><suffix>`` (as ``tools/replay_bpfix_dir.py`` does for bpfix).

Adding a reporter: write a module with a class that has ``name``,
``needs_artifact`` and ``predict(ctx)``, and add one line to ``ADAPTERS`` in
``bpfix_adversarial/adapters/__init__.py``. An external tool's adapter also
has ``replay(ctx, obj) -> str`` (run the tool on one case, given the compiled
object) and ``provenance() -> dict``; ``tools/replay_reporter.py`` calls them
on the lab host. The scorers iterate the registry, so they need no change.
See docs/ADDING-A-REPORTER.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol


@dataclass(frozen=True)
class CaseContext:
    case_id: str
    source: Path  # the C file that was compiled and loaded
    log_path: Path  # captured bpftool -d output for that file
    obligation: Optional[str] = None  # upstream classifier label, when known

    def artifact(self, suffix: str) -> Optional[Path]:
        """Output of an external reporter stored beside the log, if present."""
        name = self.log_path.name
        stem = name[: -len(".log")] if name.endswith(".log") else name
        p = self.log_path.with_name(stem + suffix)
        return p if p.is_file() else None

    def log_text(self) -> str:
        return self.log_path.read_text(encoding="utf-8", errors="replace")


@dataclass
class Prediction:
    primary: Optional[int]
    labels: list[int] = field(default_factory=list)
    note: str = ""
    file: Optional[str] = None  # file the reporter names for primary, when it names one; else ctx.source


class Reporter(Protocol):
    name: str
    needs_artifact: Optional[str]  # file suffix of the external output, or None

    def predict(self, ctx: CaseContext) -> Prediction: ...


class _Bpfix:
    name = "bpfix"
    needs_artifact = ".bpfix.txt"

    def predict(self, ctx: CaseContext) -> Prediction:
        from .bpfix_output import parse_bpfix

        p = ctx.artifact(self.needs_artifact)
        if p is None:
            return Prediction(None, [], "bpfix output missing")
        d = parse_bpfix(p.read_text(encoding="utf-8", errors="replace"))
        return Prediction(d.primary, d.label_lines, d.error_id or "", d.path)


class _VerifierState:
    name = "VerifierState"
    needs_artifact = None

    def predict(self, ctx: CaseContext) -> Prediction:
        from tools.score_sc_vs_honesty import vs_stop_loc

        line, _txt, note, file = vs_stop_loc(ctx.log_text())
        return Prediction(line, [], note, file)


class _SourceComment:
    name = "SourceComment"
    needs_artifact = None

    def predict(self, ctx: CaseContext) -> Prediction:
        from tools.score_sc_vs_honesty import sc_report

        if not ctx.obligation:
            return Prediction(None, [], "SC: no obligation label")
        line, note = sc_report(ctx.source, ctx.obligation, ctx.case_id)
        return Prediction(line, [], note)


BUILTIN: tuple[Reporter, ...] = (_Bpfix(), _VerifierState(), _SourceComment())


def registry() -> dict[str, Reporter]:
    from .adapters import ADAPTERS

    out: dict[str, Reporter] = {}
    for rep in (*BUILTIN, *(make() for make in ADAPTERS)):
        if rep.name in out:
            raise ValueError(f"duplicate reporter name {rep.name!r}")
        out[rep.name] = rep
    return out


AdapterFactory = Callable[[], Reporter]

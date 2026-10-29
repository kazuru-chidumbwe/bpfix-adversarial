# SPDX-License-Identifier: MIT
"""Parse rendered upstream bpfix CLI diagnostics (rustc-style) into labels.

Format (bpfix 0.1.9)::

    error[BPFIX-E001]: headline
      --> PB-pad8.c:26
       |
    12 | if (data + 1 > data_end)
       | ------------------------ secondary label message
    26 | return *(__u64 *)data;
       | ^^^^^^^^^^^^^^^^^^^^^^ rejected here: primary label message

``primary`` is the ``-->`` line. ``labels`` are every snippet line with its
underline kind (``^`` primary, ``-`` secondary) and message. A ``-->`` line of
0 (seen upstream when the rejected instruction has no line record) is kept as
``primary_raw`` and reported as ``primary = None``.

When the verifier log carries no source locations (kernels before 6.9 print
``; <source>`` without `` @ file:line``), bpfix points into the log itself
(``--> <verifier-log>:26``). That number is a log line, not a source line, so
it is kept as ``primary_raw`` and reported as ``primary = None`` with no labels.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field

RE_ERR = re.compile(r"^error\[BPFIX-(E\d+)\]:\s*(.*)$", re.M)
RE_ARROW = re.compile(r"^\s*-->\s+(\S+?):(\d+)(?::\d+)?\s*$", re.M)
RE_SNIP = re.compile(r"^\s*(\d+)\s+\|\s?(.*)$")
RE_UNDER = re.compile(r"^\s*\|\s*([\^-]+)\s*(.*)$")
RE_NEXT = re.compile(r"^\s*=\s*next action:\s*(.*)$", re.M)
RE_PC = re.compile(r"nearest BPF instruction pc\s+(\d+)")
LOG_PATH = "<verifier-log>"


@dataclass(frozen=True)
class Label:
    line: int
    source: str
    kind: str  # "primary" ('^') or "secondary" ('-') or "plain" (no underline)
    message: str


@dataclass
class BpfixDiagnostic:
    error_id: str | None
    headline: str | None
    path: str | None
    primary_raw: int | None
    primary: int | None
    next_action: str | None
    nearest_pc: int | None
    labels: list[Label] = field(default_factory=list)

    @property
    def label_lines(self) -> list[int]:
        return [lab.line for lab in self.labels]

    @property
    def secondary_lines(self) -> list[int]:
        return [lab.line for lab in self.labels if lab.kind == "secondary"]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["label_lines"] = self.label_lines
        d["secondary_lines"] = self.secondary_lines
        return d


def parse_bpfix(text: str) -> BpfixDiagnostic:
    err = RE_ERR.search(text)
    arrow = RE_ARROW.search(text)
    nxt = RE_NEXT.search(text)
    pc = RE_PC.search(text)
    raw = int(arrow.group(2)) if arrow else None
    labels: list[Label] = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = RE_SNIP.match(ln)
        if not m:
            continue
        kind, msg = "plain", ""
        if i + 1 < len(lines):
            u = RE_UNDER.match(lines[i + 1])
            if u:
                kind = "primary" if u.group(1).startswith("^") else "secondary"
                msg = u.group(2).strip()
        labels.append(Label(line=int(m.group(1)), source=m.group(2).strip(), kind=kind, message=msg))
    in_log = bool(arrow) and arrow.group(1) == LOG_PATH
    if in_log:
        labels = []
    return BpfixDiagnostic(
        error_id=err.group(1) if err else None,
        headline=err.group(2).strip() if err else None,
        path=arrow.group(1) if arrow else None,
        primary_raw=raw,
        primary=raw if raw and not in_log else None,
        next_action=nxt.group(1).strip() if nxt else None,
        nearest_pc=int(pc.group(1)) if pc else None,
        labels=labels,
    )


def structure_key(d: BpfixDiagnostic) -> dict:
    """Identifier-free shape of a diagnostic, for comparing rename pairs.

    Source text and file names are dropped; what remains is what a rename
    should not change if the diagnostic is rename-stable.
    """
    return {
        "error_id": d.error_id,
        "primary": d.primary_raw,
        "labels": [(lab.line, lab.kind, lab.message) for lab in d.labels],
        "next_action": d.next_action,
    }

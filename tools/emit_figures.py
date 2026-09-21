#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Emit three the paper's figure SVGs from committed results/*.json (stdlib only).

File names match the paper's figure numbers: fig3-sc-vs-honesty.svg,
fig4-lab-distance.svg and fig5-scoring-modes-cli.svg are Figs. 3, 4 and 5.
Figs. 1 and 2 are author-drawn and are not generated here.
Paper Figs. 1 (architecture) and 2 (synthetic/rename) are hand-authored outside
this emitter, so the paper has one more figure than this emitter produces.
Rename boundary is prose-only (no rate figure).
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures"
RESULTS = ROOT / "results"


def svg_header(w: int, h: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">',
        f"<title>{title}</title>",
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<text x="24" y="28" font-family="Segoe UI, Arial, sans-serif" '
        f'font-size="16" font-weight="600">{title}</text>',
    ]


def bar_chart(
    title: str,
    labels: list[str],
    series: list[tuple[str, list[float | None], str]],
    outfile: Path,
    *,
    ymax: float | None = None,
) -> None:
    w, h = 720, 360
    left, bottom, top, right = 70, 60, 50, 24
    plot_w = w - left - right
    plot_h = h - top - bottom
    mx = ymax if ymax is not None else max(
        (v for _, vals, _ in series for v in vals if v is not None), default=1.0
    )
    mx = max(mx, 1e-6)
    n = max(len(labels), 1)
    group_w = plot_w / n
    bar_w = group_w / (len(series) + 1)
    lines = svg_header(w, h, title)
    lines.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" '
        f'stroke="#333" stroke-width="1"/>'
    )
    lines.append(
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" '
        f'stroke="#333" stroke-width="1"/>'
    )
    for i, lab in enumerate(labels):
        gx = left + i * group_w
        for j, (_name, vals, color) in enumerate(series):
            if i >= len(vals):
                continue
            v = vals[i]
            x = gx + (j + 0.5) * bar_w
            if v is None:
                lines.append(
                    f'<text x="{x + bar_w*0.425:.1f}" y="{top+plot_h-6}" text-anchor="middle" '
                    f'font-family="Segoe UI, Arial, sans-serif" font-size="11" '
                    f'fill="{color}">N/A</text>'
                )
                continue
            bh = (v / mx) * plot_h
            y = top + plot_h - bh
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w*0.85:.1f}" '
                f'height="{bh:.1f}" fill="{color}"/>'
            )
        lines.append(
            f'<text x="{gx + group_w/2:.1f}" y="{h-28}" text-anchor="middle" '
            f'font-family="Segoe UI, Arial, sans-serif" font-size="11">{lab}</text>'
        )
    lx = left
    for name, _, color in series:
        lines.append(f'<rect x="{lx}" y="{h-18}" width="12" height="12" fill="{color}"/>')
        lines.append(
            f'<text x="{lx+16}" y="{h-8}" font-family="Segoe UI, Arial, sans-serif" '
            f'font-size="11">{name}</text>'
        )
        lx += 18 + 8 * len(name)
    lines.append("</svg>")
    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def emit_fig3_sc_vs() -> None:
    data = json.loads((RESULTS / "sc_vs_honesty.json").read_text(encoding="utf-8"))
    fams = ["PacketBounds", "PointerProvenance", "ScalarRange"]
    sc_line, vs_span = [], []
    for fam in fams:
        rows = [
            r
            for r in data["rows"]
            if r["obligation"] == fam and r.get("lab_rejected")
        ]
        n = len(rows) or 1
        if fam == "PointerProvenance":
            sc_line.append(None)  # no upstream PointerProvenance predicate
        else:
            sc_line.append(sum(1 for r in rows if r.get("sc_top1_line") is True) / n)
        vs_span.append(sum(1 for r in rows if r.get("vs_top1_span") is True) / n)
    bar_chart(
        "SC top1_line vs VS top1_span (rejecting templates)",
        ["PB", "PP", "SR"],
        [
            ("SC top1_line", sc_line, "#2a6f97"),
            ("VS top1_span", vs_span, "#ee6c4d"),
        ],
        OUT / "fig3-sc-vs-honesty.svg",
        ymax=1.0,
    )


def emit_fig4_lab_distance() -> None:
    data = json.loads((RESULTS / "rq1_lab_distance.json").read_text(encoding="utf-8"))
    pb = sorted(
        (r for r in data["rows"] if r["obligation"] == "PacketBounds"),
        key=lambda r: r["pad"],
    )
    labels = [str(r["pad"]) for r in pb]
    sc_d = [float(r["sc_distance_error"] or 0) for r in pb]
    vs_d = [float(r["vs_distance_error"] or 0) for r in pb]
    bar_chart(
        "PB lab distance vs pad (SC stays 0; VS grows with pad)",
        labels,
        [
            ("SC d", sc_d, "#2a9d8f"),
            ("VS d", vs_d, "#e76f51"),
        ],
        OUT / "fig4-lab-distance.svg",
    )


def emit_fig5_set_recall() -> None:
    data = json.loads((RESULTS / "rq1_bpfix_cli.json").read_text(encoding="utf-8"))
    rows = sorted(
        (r for r in data["rows"] if r.get("obligation") == "PacketBounds"),
        key=lambda r: r.get("pad", 0),
    )
    labels = [r["case_id"] for r in rows]
    top1 = [
        1.0 if r.get("bpfix_primary_src") == r.get("oracle_loss_code") else 0.0
        for r in rows
    ]
    recall = [1.0 if r.get("bpfix_loss_mentioned") else 0.0 for r in rows]
    bar_chart(
        "PacketBounds CLI: top1_line vs set_recall_message",
        labels,
        [
            ("top1_line", top1, "#264653"),
            ("set_recall_message", recall, "#f4a261"),
        ],
        OUT / "fig5-scoring-modes-cli.svg",
        ymax=1.0,
    )


FIGURE_OUTPUTS = (
    "figures/fig3-sc-vs-honesty.svg",
    "figures/fig4-lab-distance.svg",
    "figures/fig5-scoring-modes-cli.svg",
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    emit_fig3_sc_vs()
    emit_fig4_lab_distance()
    emit_fig5_set_recall()
    print(f"Wrote SVGs under {OUT}")


if __name__ == "__main__":
    main()

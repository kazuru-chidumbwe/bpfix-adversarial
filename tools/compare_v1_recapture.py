#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Compare a fresh capture of the v1.0.2 mutants with the committed cite-pin logs.

On the cite-pin host this answers "does the pin still reproduce the published
logs?". Both logs are reduced to the verifier's program-load log (between
BEGIN/END PROG LOAD LOG) with run-to-run noise removed by the same rules as
the marker A/B (tools/lab_marker_isolation_ab.py::normalize_log_body: hex
addresses, timing and accounting trailers, tmp paths). Writes
``v1_recapture_compare.json`` into the recapture directory.

Usage: python tools/compare_v1_recapture.py --recaptured campaigns/v2/lab/<run>/v1-recapture
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.lab_marker_isolation_ab import normalize_log_body  # noqa: E402

COMMITTED = ROOT / "fixtures" / "logs" / "captured"
STAMP = "20260801T181331Z"


def prog_log(text: str) -> str:
    body = normalize_log_body(text)
    end = body.find("-- END PROG LOAD LOG --")
    return body[: end] if end >= 0 else body


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recaptured", type=Path, required=True)
    args = ap.parse_args(argv)
    rec = args.recaptured if args.recaptured.is_absolute() else ROOT / args.recaptured
    manifest = sorted(rec.glob("manifest.*.jsonl"))[-1]
    rows = [json.loads(ln) for ln in manifest.read_text(encoding="utf-8").splitlines() if ln.strip()]
    out = []
    for r in rows:
        old = COMMITTED / f"{r['case_id']}.{STAMP}.log"
        new = rec / Path(r["log"]).name
        if not old.is_file():
            out.append({"case_id": r["case_id"], "status": "no committed log"})
            continue
        a = prog_log(old.read_text(encoding="utf-8"))
        b = prog_log(new.read_text(encoding="utf-8"))
        out.append({
            "case_id": r["case_id"],
            "status": "identical" if a == b else "different",
            "committed_sha256": hashlib.sha256(a.encode()).hexdigest(),
            "recaptured_sha256": hashlib.sha256(b.encode()).hexdigest(),
            "src_sha256_lf": r["src_sha256"],
        })
    n_same = sum(1 for o in out if o["status"] == "identical")
    payload = {"manifest": manifest.name, "committed_stamp": STAMP, "identical": n_same, "n": len(out), "rows": out}
    (rec / "v1_recapture_compare.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    for o in out:
        print(f"{o['status']:16} {o['case_id']}")
    print(f"identical {n_same}/{len(out)} (normalized program-load logs vs committed {STAMP})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

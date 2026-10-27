#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Wild corpus batch 2: wider sources, screened by the batch-1 rules.

Implements the 27 Oct 2026 "Batch 2" entry of "Changes after the freeze" in
docs/WILD-CORPUS-PROTOCOL.md. Files live under fixtures/wild/batch2/.

  select    sources by rule          -> repos.json              (home)
  collect   GitHub commit search (gh CLI) -> candidates.json        (home)
  files     pass 1, changed-file lists     -> screen_files.jsonl     (home)
  review    pass 2 input, message + BPF C diff -> review/*.txt (home; used after the build)
  build     pass 4 build, load and decide  -> build.jsonl            (lab host)

Usage: python3 tools/wild_batch2.py {select,collect,files,review,build} [--max-candidates N]
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import wild_collect_candidates as wc  # noqa: E402
from tools import wild_screen_files as wf  # noqa: E402

B2 = ROOT / "fixtures" / "wild" / "batch2"
CANDS = B2 / "candidates.json"
FILES = B2 / "screen_files.jsonl"
REVIEW = B2 / "review"
DECISIONS = B2 / "pass2_decisions.tsv"
OUT = B2 / "build.jsonl"
WINDOW = "2024-01-01..2026-10-25"
SEED = 20261027
RANK_BASE = 1000

REPOS_FILE = B2 / "repos.json"
TOPICS = ("ebpf", "bpf", "xdp", "libbpf")
REPO_QUERY = "topic:{topic} stars:>=200 pushed:>=2026-01-01 archived:false fork:false"

BPF_DIR2 = re.compile(r"(^|/)(kernel|bpf[-_][^/]*|[^/]*cprog)(/|$)", re.I)


def is_bpf_c(path: str) -> bool:
    """Batch-1 rule plus the directory names of the batch-2 projects (protocol, batch 2 item 4)."""
    if wf.is_bpf_c(path):
        return True
    p = path.lower()
    return p.endswith((".c", ".h")) and "/" in p and bool(BPF_DIR2.search(p.rsplit("/", 1)[0]))


def gh_json(args: list[str]):
    for _ in range(5):
        res = wc.subprocess.run(["gh", "api", *args], capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0:
            return json.loads(res.stdout)
        if "rate limit" in (res.stdout + res.stderr).lower():
            time.sleep(65)
            continue
        return None
    raise RuntimeError(f"rate limit not cleared for {args!r}")


def select() -> int:
    """Sources by rule (protocol, batch 2 item 1): topic search, then BPF C in the default branch."""
    found: dict[str, dict] = {}
    for topic in TOPICS:
        q = REPO_QUERY.format(topic=topic)
        for page in range(1, 11):
            d = gh_json(["-X", "GET", "search/repositories", "-f", f"q={q}", "-f", "per_page=100", "-f", f"page={page}"])
            items = d["items"]
            for it in items:
                r = found.setdefault(it["full_name"], {"repo": it["full_name"], "stars": it["stargazers_count"],
                                                       "default_branch": it["default_branch"], "topics_matched": []})
                r["topics_matched"].append(topic)
            time.sleep(2.1)
            if len(items) < 100:
                break
    batch1 = {r.lower() for r in wc.REPOS}
    rows = []
    for name in sorted(found, key=str.lower):
        r = found[name]
        if name.lower() in batch1:
            r["selected"], r["reason"] = False, "in batch 1"
        else:
            t = gh_json([f"repos/{name}/git/trees/{r['default_branch']}?recursive=1"]) or {}
            r["bpf_c_files"] = sum(1 for x in t.get("tree", []) if x["type"] == "blob" and is_bpf_c(x["path"]))
            r["tree_truncated"] = bool(t.get("truncated"))
            r["selected"] = r["bpf_c_files"] > 0
            r["reason"] = "BPF C in default branch" if r["selected"] else "no BPF C file by the pass-1 rule"
        rows.append(r)
    B2.mkdir(parents=True, exist_ok=True)
    REPOS_FILE.write_text(json.dumps({"queried": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                      "query": REPO_QUERY, "topics": list(TOPICS), "n_found": len(rows),
                                      "n_selected": sum(r["selected"] for r in rows), "repos": rows},
                                     indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {REPOS_FILE} found={len(rows)} selected={sum(r['selected'] for r in rows)}")
    return 0


def repos() -> list[str]:
    return [r["repo"] for r in json.loads(REPOS_FILE.read_text(encoding="utf-8"))["repos"] if r["selected"]]


def search(repo: str, phrase: str) -> list[dict]:
    q = f'"{phrase}" repo:{repo} committer-date:{WINDOW}'
    items: list[dict] = []
    for page in range(1, 11):
        cmd = ["gh", "api", "-X", "GET", "search/commits", "-f", f"q={q}", "-f", "per_page=100", "-f", f"page={page}"]
        for _ in range(30):
            res = wc.subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if res.returncode == 0:
                break
            if "rate limit" in (res.stdout + res.stderr).lower() or "error connecting" in res.stderr.lower():
                time.sleep(65)  # rate limit, or the network dropped: wait and retry the same request
                continue
            raise RuntimeError(f"gh failed for {q!r}: {res.stderr.strip()}")
        else:
            raise RuntimeError(f"rate limit not cleared for {q!r}")
        batch = json.loads(res.stdout).get("items", [])
        items.extend(batch)
        time.sleep(2.1)
        if len(batch) < 100:
            break
    return items


def collect() -> int:
    by_commit: dict[str, dict] = {}
    sources = repos()
    for repo in sources:
        for phrase in wc.PHRASES:
            for it in search(repo, phrase):
                row = by_commit.setdefault(it["sha"], {
                    "repo": repo, "commit": it["sha"], "parents": [p["sha"] for p in it.get("parents", [])],
                    "title": it["commit"]["message"].split("\n", 1)[0],
                    "committer_date": it["commit"]["committer"]["date"], "html_url": it["html_url"], "matched": []})
                if phrase not in row["matched"]:
                    row["matched"].append(phrase)
            print(f"{repo:50s} {phrase!r:28s} total={len(by_commit)}", flush=True)
    rows = sorted(by_commit.values(), key=lambda r: (r["repo"], r["commit"]))
    order = [r["commit"] for r in rows]
    random.Random(SEED).shuffle(order)
    rank = {c: RANK_BASE + i for i, c in enumerate(order)}
    for r in rows:
        r["screen_rank"] = rank[r["commit"]]
    rows.sort(key=lambda r: r["screen_rank"])
    B2.mkdir(parents=True, exist_ok=True)
    CANDS.write_text(json.dumps({"protocol": "docs/WILD-CORPUS-PROTOCOL.md (batch 2)", "window": WINDOW, "seed": SEED,
                                 "rank_base": RANK_BASE, "repos": sources, "phrases": list(wc.PHRASES),
                                 "n": len(rows), "candidates": rows}, indent=1, ensure_ascii=False) + "\n",
                     encoding="utf-8", newline="\n")
    print(f"wrote {CANDS} n={len(rows)}")
    return 0


def files_of(repo: str, sha: str) -> list[dict]:
    """wf.files_of, retried when the network drops."""
    for _ in range(30):
        try:
            return wf.files_of(repo, sha)
        except RuntimeError as e:
            if "error connecting" not in str(e).lower():
                raise
            time.sleep(65)
    raise RuntimeError(f"{repo}@{sha}: network not back")


def files() -> int:
    cands = json.loads(CANDS.read_text(encoding="utf-8"))["candidates"]
    done = set()
    if FILES.is_file():
        done = {json.loads(ln)["commit"] for ln in FILES.read_text(encoding="utf-8").splitlines() if ln.strip()}
    with FILES.open("a", encoding="utf-8", newline="\n") as f:
        for c in cands:
            if c["commit"] in done:
                continue
            fl = files_of(c["repo"], c["commit"])
            bpf = [x["filename"] for x in fl if is_bpf_c(x["filename"])]
            f.write(json.dumps({"screen_rank": c["screen_rank"], "repo": c["repo"], "commit": c["commit"],
                                "n_files": len(fl), "bpf_c_files": bpf,
                                "pass1": "bpf-c" if bpf else "E2-no-bpf-c"}) + "\n")
            f.flush()
            time.sleep(0.3)
    rows = [json.loads(ln) for ln in FILES.read_text(encoding="utf-8").splitlines() if ln.strip()]
    print(f"screened {len(rows)}; bpf-c {sum(r['pass1'] == 'bpf-c' for r in rows)}")
    return 0


def review() -> int:
    from tools import wild_dump_for_review as wd

    wd.PASS1, wd.OUT = FILES, REVIEW
    return wd.main([])


def pass1_survivors() -> set[int]:
    return {json.loads(ln)["screen_rank"] for ln in FILES.read_text(encoding="utf-8").splitlines()
            if ln.strip() and json.loads(ln)["pass1"] == "bpf-c"}


def build(argv: list[str]) -> int:
    from tools import wild_pass4 as p4

    p3 = p4.p3
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-candidates", type=int, default=0)
    args = ap.parse_args(argv)
    for d in (p4.KARCH, p4.KCOMMON):
        if not d.is_dir():
            raise SystemExit(f"missing pin kernel headers: {d}")
    if not p4.LEGACY.is_file():
        raise SystemExit(f"missing legacy loader {p4.LEGACY}")
    p4.install_clang_wrapper(p3.WORK)
    p3.build_direct, p3.build_make, p3.load, p3.run = p4.build_direct, p4.build_make, p4.load, p4.run
    p3.reject_kind = p4.reject_kind
    p4.LEGACY_WRAPPERS.update(p4.install_legacy_wrappers(p3.WORK))
    p3.MAKE_BPF = set()  # batch 2: every candidate is a direct compile (item 6)

    cands = {c["screen_rank"]: c for c in json.loads(CANDS.read_text(encoding="utf-8"))["candidates"]}
    fl = {json.loads(ln)["screen_rank"]: json.loads(ln)["bpf_c_files"]
          for ln in FILES.read_text(encoding="utf-8").splitlines() if ln.strip()}
    todo = sorted(r for r in fl if r in pass1_survivors())  # item 5: pass 2 comes after the build
    done = {}
    if OUT.is_file():
        done = {json.loads(ln)["screen_rank"]: json.loads(ln) for ln in OUT.read_text(encoding="utf-8").splitlines() if ln.strip()}
    vmlinux_dir = str(ROOT / ".cache" / f"vmlinux-{os.uname().release}")
    if not (Path(vmlinux_dir) / "vmlinux.h").is_file():
        raise SystemExit(f"missing {vmlinux_dir}/vmlinux.h")

    def included() -> int:
        return p4.included_so_far() + sum(1 for r in done.values() if r.get("outcome") == "included")

    n = 0
    for rank in todo:
        if included() >= p3.MAX_INCLUDED or dt.date.today() > p3.STOP_DATE:
            print(f"stop: included={included()}, date={dt.date.today()}")
            break
        if rank in done:
            continue
        if args.max_candidates and n >= args.max_candidates:
            break
        p3.shutil.rmtree(p3.WORK / "tmp" / f"{rank:03d}", ignore_errors=True)
        t0 = time.time()
        p4.OPEN_ERRORS.clear()
        p4.LEGACY_LOADED.clear()
        try:
            row = p3.screen(cands[rank], fl[rank], vmlinux_dir)
        except Exception as e:  # noqa: BLE001 - recorded, screening continues
            row = {"screen_rank": rank, "repo": cands[rank]["repo"], "commit": cands[rank]["commit"],
                   "outcome": "E5", "note": f"driver error: {e}"[:800]}
        if p4.OPEN_ERRORS:
            row["open_errors"] = sorted(set(p4.OPEN_ERRORS))
        if p4.LEGACY_LOADED:
            row["legacy_loaded"] = sorted(set(p4.LEGACY_LOADED))
        if row.get("outcome") == "E4" and not any((row.get("n_objects") or {}).values()):
            row.update(outcome="E5", note="no built object depends on a changed file")
        elif row.get("outcome") in ("E4", "I3", "I4", "C") and p4.OPEN_ERRORS:
            row["decided_outcome"] = row["outcome"]
            row["outcome"] = p4.final_outcome(row)
            if row["outcome"] == "E5":
                row["note"] = "no program loaded from: " + ", ".join(sorted(set(p4.OPEN_ERRORS)))[:700]
        row["batch"] = 2
        row["seconds"] = round(time.time() - t0)
        with OUT.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(row) + "\n")
        done[rank] = row
        n += 1
        status = (f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M}Z rank {rank} {row['outcome']} "
                  f"({row['seconds']}s); screened {len(done)}/{len(todo)}; included (both batches) {included()}")
        (p3.WORK / "batch2.status").write_text(status + "\n")
        print(status, flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("select", "collect", "files", "review", "build"):
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    return {"select": select, "collect": collect, "files": files, "review": review}.get(cmd, lambda: build(rest))()


if __name__ == "__main__":
    sys.exit(main())

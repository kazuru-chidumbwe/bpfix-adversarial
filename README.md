# bpfix-adversarial

Does an eBPF reject log still point at the line where a fault was injected after padding and renaming?

When the verifier rejects a program, the stop site in the log is often not where the missing check belongs. This tree builds small failing programs with known injection markers, captures verifier logs on a pinned lab host, and scores whether a diagnostic still names that marker. Scoring covers bpfix SourceComment heuristics, thin baselines, and upstream CLI replay.

Target: [bpfix](https://github.com/eunomia-bpf/bpfix) / Zheng et al. ([arXiv:2607.02748](https://arxiv.org/abs/2607.02748)). Not a verifier-soundness, bypass, or CVE study.

[![CI](https://github.com/kazuru-chidumbwe/bpfix-adversarial/actions/workflows/ci.yml/badge.svg)](https://github.com/kazuru-chidumbwe/bpfix-adversarial/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Frozen tree for published numbers:** [`v1.0.2`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.2). Metadata: [CODE_METADATA.md](CODE_METADATA.md), [CITATION.cff](CITATION.cff), [codemeta.json](codemeta.json). Prefer that tag over floating `master`. Upstream bpfix pin: `81d97e4a528456e0082a77f4fb6edd13fa092b7b`.

## Offline insets (no lab SSH)

```bash
git clone https://github.com/kazuru-chidumbwe/bpfix-adversarial.git
cd bpfix-adversarial
git checkout v1.0.2
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -U pip && pip install -e .   # stdlib-only core; optional: pip install -e ".[lab,openai]"
make smoke                   # version + unittest + rename-demo
python tools/emit_rename_table.py
python tools/emit_four_obligation_matrix.py
python tools/score_sc_vs_honesty.py
make figures                 # regenerate Figs 2–5 SVGs from results/*.json
```

One-command offline path (Python tooling only; does not emulate the verifier; containers share the host kernel):

```bash
docker build -t bpfix-adversarial:offline .
docker run --rm bpfix-adversarial:offline
```

Committed tables: [`results/`](results/). Docs index: [`docs/README.md`](docs/README.md).

## What it does

| Capability | Role |
| --- | --- |
| Mutant generators | Obligation-scoped C under `mutants/` with `ORACLE_LOSS_LINE` / `ORACLE_REJECT_LINE` |
| Lab capture | clang + `bpftool -d` on a pinned Debian 13 host (`tools/lab_*.py`) |
| Scoring | SourceComment port + VerifierState + upstream bpfix CLI replay; top-1 / set-recall |
| Paper insets | Committed tables under `results/` |

Four stress families. NullablePointer, PointerProvenance, ScalarRange, PacketBounds.

## Install

Requires Python 3.10+.

```bash
git clone https://github.com/kazuru-chidumbwe/bpfix-adversarial.git
cd bpfix-adversarial
git checkout v1.0.2
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -U pip
pip install -e .
```

Optional. The OpenAI separation path needs `OPENAI_API_KEY`.
The paper separation demonstration used **Ollama** with `--backend ollama`. No cloud key.
Model digest and seed are pinned. See `tools/rq4_llm_repair.py` and `results/rq4_ollama/`.
Lab SSH helpers need `paramiko` and a `lab/.env`. See [`docs/LAB-PIN.md`](docs/LAB-PIN.md) and [`docs/TAGS.md`](docs/TAGS.md).
To add a reporter: map a log to a primary line, then call `bpfix_adversarial.score.score_honesty` (see `docs/METRICS.md`).

## Minimal demo

After install, show that bpfix-style null-check name lists break under idiomatic rename
while helper-anchored recognition stays stable.

```bash
python -c "import bpfix_adversarial as m; print(m.__version__)"
# → 1.0.2 on the v1.0.2 pin

python -m bpfix_adversarial rename-demo --breaks-only --limit 2
```

Example excerpt.

```json
{
  "summary": { "n_honesty_breaks": 32, "break_rate": 1.0 },
  "cases": [
    {
      "original_line": "if (!tmp)",
      "renamed_line": "if (!entry)",
      "honesty_break": true,
      "helper_anchored_stable": true
    }
  ]
}
```

Full combinatorial **4x8** matrix of brittle x idiomatic name pairs: all 32 pairs flip
the SourceComment null-check predicate. This draws the recognition boundary of a
name-list heuristic; it is **not** scored as `top1_line` and is **not** an empirical
localization rate over n=32. Helper-anchored `bpf_map_lookup_elem` recognition is
rename-insensitive by construction. See `results/rename_honesty.md`.

## Tests

```bash
make smoke          # version + unittest + rename-demo
# or: python -m unittest discover -s tests -v
```

CI runs the same suite on Python 3.10 and 3.12. See `.github/workflows/ci.yml`.

## Reproduce paper insets

Committed paper-facing tables live in [`results/`](results/). Offline emitters
need no lab for most runs.

```bash
python tools/emit_rename_table.py            # rename metamorphic matrix
python tools/emit_distance_sweep.py          # synthetic distance (pads 0–64)
python tools/emit_tier_table.py              # SC vs VS (fixtures)
python tools/score_np_pair.py                # NP brittle/idiomatic fixture pair
python tools/emit_four_obligation_matrix.py  # four-obligation coverage
python tools/score_sc_vs_honesty.py          # SC/VS on lab-captured logs
python tools/emit_rq1_lab_distance.py        # lab pad distance (0/8/32)
python tools/emit_depth21_selection.py       # depth-21 curated join table (unscored)
# Optional lab / CLI:
#   python tools/lab_capture_via_env.py
#   tools/run_rq1_bpfix_cli.sh && python tools/emit_rq1_bpfix_cli.py
#   python tools/rq4_llm_repair.py --backend ollama   # separation demonstration
#   python tools/rq4_llm_repair.py --backend openai   # optional; needs OPENAI_API_KEY
#   # Do not use tools/honesty_utility_rq4.py to regenerate cite insets (legacy; refuses by default).
```

| Campaign | Focus | Primary inset |
| --- | --- | --- |
| Distance | Injection-site distance under padding | `distance_sweep.*`, `rq1_lab_distance.*`, `rq1_bpfix_cli.*` |
| Rename | Null-check name-list brittleness | `rename_honesty.*` |
| Tiers | SourceComment vs VerifierState | `tier_disagreement.*`, `sc_vs_honesty.*` |
| Separation | Localization is not repair. n=1 demo | `honesty_utility_rq4.*` via `rq4_llm_repair.py --backend ollama` |

## Layout

```
bpfix_adversarial/   heuristic port, generators, logparse, score
mutants/              NP + PP/SR/PB C templates (+ repaired seeds)
fixtures/logs/        synthetic/ + captured/ (lab bpftool logs)
fixtures/upstream/    depth-21 sparse bpfix-bench cases (curated target)
lab/                  Linux capture helpers
tools/                emit tables, lab capture, generate mutants
results/              committed paper insets (md/json)
docs/                 metrics, lab pin, deps, upstream, tags (see docs/README.md)
schemas/              optional JSON Schema contracts
tests/                unittest suite
Makefile              smoke / insets
CODE_METADATA.md      code-metadata table (C1–C8)
```

## Scope note

Validated paper evidence is the **template** four-obligation reject-oracles,
SC/VS injection-site agreement, and the upstream bpfix CLI primary-arrow table
on the Debian pin. Depth-21 under `fixtures/upstream/` is a **curated validation
target**, not independently scored results. Cite tag `v1.0.2` records the Ollama
separation demonstration with n=1. The scored construct is injection-site
agreement. It is not a verified semantic proof-loss oracle. See [`docs/METRICS.md`](docs/METRICS.md).

## License

MIT. See [`LICENSE`](LICENSE).

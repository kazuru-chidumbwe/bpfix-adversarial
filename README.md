# bpfix-adversarial

Check whether eBPF reject diagnostics still name the line where a fault was
injected after pad and rename stress.

When the verifier rejects a program, the stop site in the log is often not where
the missing check belongs. This repo builds small failing programs with known
injection markers. It captures verifier logs on a pinned lab. It scores whether
a diagnostic still points at that marker. Scoring covers bpfix SourceComment
heuristics, thin baselines, and upstream CLI replay.

Object under test is [bpfix](https://github.com/eunomia-bpf/bpfix) and Zheng et al.
See [arXiv:2607.02748](https://arxiv.org/abs/2607.02748).
This does **not** test verifier soundness, bypasses, or kernel CVEs.

[![CI](https://github.com/kazuru-chidumbwe/bpfix-adversarial/actions/workflows/ci.yml/badge.svg)](https://github.com/kazuru-chidumbwe/bpfix-adversarial/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Cite pin [`v1.0.0`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.0).
Permanent archive: [doi:10.5281/zenodo.21859727](https://doi.org/10.5281/zenodo.21859727).
See [CODE_METADATA.md](CODE_METADATA.md), [CITATION.cff](CITATION.cff), and [codemeta.json](codemeta.json).
Cite the release tag / Zenodo version, not floating `master`.
Upstream bpfix pin is `81d97e4a528456e0082a77f4fb6edd13fa092b7b`.

## Quick Start (offline insets)

No lab SSH required. After install:

```bash
git clone https://github.com/kazuru-chidumbwe/bpfix-adversarial.git
cd bpfix-adversarial
git checkout v1.0.0
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -U pip && pip install -e .
make smoke                   # version + unittest + rename-demo
python tools/emit_rename_table.py
python tools/emit_four_obligation_matrix.py
python tools/score_sc_vs_honesty.py
```

Or one-command offline smoke plus inset emitters. This path is Python tooling only.
It does **not** pin or emulate the eBPF verifier. Containers share the host kernel.

```bash
docker build -t bpfix-adversarial:offline .
docker run --rm bpfix-adversarial:offline
```

Committed paper tables live under [`results/`](results/).
Docs index: [`docs/README.md`](docs/README.md) (metrics, lab pin, deps, upstream, tags, Zenodo).

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
git checkout v1.0.0          # package cite pin
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
# → 1.0.0 on the v1.0.0 pin

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

Full combinatorial matrix. **32/32** top-1 breaks for the SourceComment name-list
heuristic. See `results/rename_honesty.md`.

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
docs/                 metrics, lab pin, deps, upstream, tags, Zenodo (see docs/README.md)
schemas/              optional JSON Schema contracts
tests/                unittest suite
Makefile              smoke / insets (peer-harness shape)
CODE_METADATA.md      SoftwareX C1–C8 table
```

## Scope note

Validated paper evidence is the **template** four-obligation reject-oracles,
SC/VS injection-site agreement, and the upstream bpfix CLI primary-arrow table
on the Debian pin. Depth-21 under `fixtures/upstream/` is a **curated validation
target**, not independently scored results. Cite tag `v1.0.0` records the Ollama
separation demonstration with n=1. The scored construct is injection-site
agreement. It is not a verified semantic proof-loss oracle. See [`docs/METRICS.md`](docs/METRICS.md).

## License

MIT. See [`LICENSE`](LICENSE).

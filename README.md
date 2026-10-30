# bpfix-adversarial

Where do eBPF verifier diagnostics point, relative to the lines developers change to fix the rejected program, and does that answer survive rewrites that the verifier sees?

When the verifier rejects a program, it stops at the instruction where its safety argument breaks, but the line a developer has to change is often elsewhere. This harness captures each rejection on a pinned laboratory kernel, runs every registered diagnostic tool (a reporter) on the same capture, and scores the source line each one names against the developer's own fix, under three rules for what counts as the repair site. A second oracle, read from the verifier's state, never sees the fix. Verifier-checked rewrites and a control reporter measure whether a reporter's answer is stable.

Reporters: upstream [bpfix](https://github.com/eunomia-bpf/bpfix) CLI replay (Zheng et al., [arXiv:2607.02748](https://arxiv.org/abs/2607.02748)), VerifierState, SourceComment (a port of bpfix's source heuristics), and two external tools added as adapters, [Pretty Verifier](https://github.com/netgroup-polito/pretty-verifier) and [PREVAIL](https://github.com/vbpf/prevail). Baselines: a uniformly random executable line and a control that repeats a fixed line number.

[![CI](https://github.com/kazuru-chidumbwe/bpfix-adversarial/actions/workflows/ci.yml/badge.svg)](https://github.com/kazuru-chidumbwe/bpfix-adversarial/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Release: `v1.1.0`. Metadata: [CODE_METADATA.md](CODE_METADATA.md), [CITATION.cff](CITATION.cff), [codemeta.json](codemeta.json). Upstream bpfix pin: `81d97e4a528456e0082a77f4fb6edd13fa092b7b`.

## Quick start (offline)

The offline workflow rescores every corpus from the committed captures and needs only the Python 3.10+ standard library.

```bash
git clone https://github.com/kazuru-chidumbwe/bpfix-adversarial.git
cd bpfix-adversarial
git checkout v1.1.0
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -U pip && pip install -e .
make smoke                   # version, unit tests, rename demo
make natural                 # rescore main75, rewrites, developer-fixed cases, second configuration, state oracle
python tools/check_results_fresh.py   # rebuild every committed result and fail on any difference
```

In a container (Python tooling only; it does not emulate the verifier):

```bash
docker build -t bpfix-adversarial:offline .
docker run --rm bpfix-adversarial:offline
```

On Windows, tracked paths reach 149 characters below the clone directory; if the clone sits deep enough to pass the 260-character limit, run `git config --global core.longpaths true` before cloning.

## Corpora

| Corpus | What it is | Where |
| --- | --- | --- |
| main75 | The 75 cases of upstream bpfix's main split, buggy and fixed, vendored at the pinned commit; 74 have a fix that changes code and are scored | `fixtures/upstream/`, captures in `campaigns/main75/lab/` |
| Rewrites | Padding and renaming (`campaigns/v2/upstream/`), and VPAD, VPADC, MACRO, INLINE, SPLIT and REORDER of both programs (`campaigns/n3/`); a pair is scored only if the rewritten buggy program REJECTS and the rewritten fixed one ACCEPTS | as listed |
| Developer-fixed | Verifier rejections fixed by developers in public eBPF projects, collected under a fixed protocol | `fixtures/wild/` (`docs/WILD-CORPUS-PROTOCOL.md`) |
| Templates | Hand-written programs for four obligation families with construction-time markers, kept as regression fixtures | `mutants/`, `campaigns/v2/mutants/` |

Each capture directory holds the verifier log of every program and a manifest row with its verdict, processed-instruction count and the SHA-256 of source and log. The rules for main75, the rewrites and the second configuration are in `docs/MAIN75-PIN-PROTOCOL.md`, with each change and its date.

## Results

| Result | File |
| --- | --- |
| main75 on the laboratory pin (Testbed A) | `results/main75_pin.md` |
| Rewrites of main75 | `results/main75_rewrites.md` |
| Second configuration (Testbed B) and its comparison with the pin | `results/main75_pin.testbed-b.md`, `results/cross_config.md` |
| Developer-fixed cases | `results/wild.md` |
| State oracle | `results/state_oracle.md` (`docs/STATE-ORACLE.md`) |
| Pretty Verifier line lookup | `results/pv_lookup.md` |
| Template campaigns | `results/rq1_bpfix_cli.md`, `results/rename_honesty.md`, `results/distance_sweep.md` and the other template results (`make insets`) |

Every result is JSON plus Markdown, written by the emitter named in `tools/check_results_fresh.py`. In template-era file and function names, "honesty" means agreement with the injection site (for example `rename_honesty`, `score_honesty`).

## Laboratory capture

Capture needs Linux with eBPF support, Clang and bpftool; the pin is documented in `docs/LAB-PIN.md`.

| Run | Command |
| --- | --- |
| main75, buggy and fixed, with bpfix replay | `lab/run_main75_pin.sh` |
| Rewrites of main75 | `lab/run_n3_pin.sh` |
| Replay of an adapter on a capture directory | `python tools/replay_reporter.py --reporter <name> --captured <dir>` |
| Developer-fixed cases: search, build, load, decide | `tools/wild_batch3.py`, `tools/wild_replay.py`, `tools/score_wild.py` (`docs/LAB-RUN-WILD.md`) |
| Second configuration | `ALLOW_OTHER_KERNEL=1 LABEL=<name> lab/run_main75_pin.sh`, then `python tools/score_main75_pin.py --run <dir> --tag <name>` and `python tools/compare_configs.py --tag <name>` |

## Adding a reporter

A reporter is one module and one line in `bpfix_adversarial/reporters.py`: a class that replays the tool on a captured case, records its provenance and parses its stored output into a primary line and labels. Every scorer then includes it in every table, under every repair-site rule and on every rewrite. The Pretty Verifier and PREVAIL adapters are worked examples; `docs/ADDING-A-REPORTER.md` walks through the first.

## Tests

```bash
python -m unittest discover -s tests
python tools/measure_coverage.py     # statement and branch coverage, with and without tools/
```

CI runs the tests, the version-sync, line-ending and freshness checks, and `make natural` followed by a check that no committed result changed, on Python 3.10 and 3.12 on Linux and on Python 3.12 on Windows (`.github/workflows/ci.yml`).

## Layout

```
bpfix_adversarial/   core package: reporters, parsers, repair-site and state oracles, scoring
tools/               capture, replay, scoring, emitters, developer-fixed pipeline
lab/                 laboratory run scripts
fixtures/upstream/   vendored main75 cases
fixtures/wild/       developer-fixed candidates, decisions and cases
campaigns/           captures: main75, rewrites (n3), template campaign v2
mutants/             template programs
results/             committed results (JSON and Markdown)
docs/                protocols, metrics, lab pin, adapters, upstream issues
tests/               unittest suite
```

## License

MIT. See [`LICENSE`](LICENSE).

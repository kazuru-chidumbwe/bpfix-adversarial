# Architecture — bpfix-adversarial

Research instrument for measuring **injection-site agreement** of eBPF
verifier diagnostics under controlled pad/rename stress. Not a verifier, not a
bypass tool, not a CVE finder.

## Pipeline

```text
Obligation templates          Lab host (pinned)           Scorers
(mutants/ NP·PP·SR·PB)   →   clang + bpftool -d     →   SourceComment / VS / CLI
   ORACLE_* markers            fixtures/logs/captured/      results/*.md|json
                               results/env_pins/
```

| Stage | Responsibility |
| --- | --- |
| **Mutant generators** | Obligation-scoped C with construction-time injection markers |
| **Lab capture** | Compile + load on a pinned host; stamp verifier logs + env pin |
| **Log parse** | Extract reported stop sites from `bpftool` / verifier text |
| **Scoring** | Top-1 / set-recall vs injection markers; pad and rename stress |
| **Emitters** | Committed SoftwareX insets under `results/` (offline replay) |

## Package map (extension without reverse-engineering tools/)

| Module | Role |
| --- | --- |
| `bpfix_adversarial/heuristics.py` | SourceComment `looks_like_*` port |
| `bpfix_adversarial/logparse.py` | Verifier-log → source locations / events |
| `bpfix_adversarial/oracle.py` | `ORACLE_*` marker + injection-span extraction |
| `bpfix_adversarial/score.py` | `score_honesty` (top-1 + distance) |
| `bpfix_adversarial/cli.py` | Small CLI entry points |
| `tools/*.py` | Thin emitters / lab SSH helpers / SoftwareX table writers |

**Add a new reporter:** implement a function `log_text → primary_line (+ optional message)`, then call `score_honesty(...)` (and optionally `oracle_sites` for markers). Prefer extending the package modules; keep `tools/` as I/O wrappers.

Lab SSH helpers intentionally live under `tools/lab_*.py` (host credentials via gitignored `lab/.env`) — see [`LAB-PIN.md`](LAB-PIN.md).

## Stress families

| Family | Short | Failure mode under test |
| --- | --- | --- |
| NullablePointer | NP | Null-check rename / pad distance |
| PointerProvenance | PP | Provenance loss vs reported site |
| ScalarRange | SR | Scalar bounds vs reported site |
| PacketBounds | PB | Packet bounds vs reported site |

## What is / is not under test

| Under test | Not under test |
| --- | --- |
| Injection-site agreement of SC / VS / upstream bpfix CLI on templates | Verifier soundness |
| Stability under pad and idiomatic rename | Kernel CVE / exploit paths |
| Localization–repair separation demonstration (n=1) | Full upstream bpfix-bench scoring as primary claim |
| Semantic verifier-state proof-loss oracle | Cross-kernel census |

Object under test: [bpfix](https://github.com/eunomia-bpf/bpfix) @ `81d97e4a528456e0082a77f4fb6edd13fa092b7b`.

## Determinism and cite policy

- SoftwareX tables cite an annotated release tag (see [`TAGS.md`](TAGS.md)) and stamp family `20260801T181331Z` (template oracles); separation load used Ollama `llama3.2:3b` + alternate-host pin `app-test-server.20260807T112233Z`.
- Depth-21 under `fixtures/upstream/` is a **curated validation target**, not independently scored results.
- Prefer offline emitters / Docker offline image over re-running lab capture when reproducing published insets.

See also: [THREAT-MODEL.md](THREAT-MODEL.md), [METRICS.md](METRICS.md), [TAGS.md](TAGS.md), [LAB-PIN.md](LAB-PIN.md).

# Code metadata (SoftwareX)

Mandatory SoftwareX metadata for **bpfix-adversarial** `v1.0.2`.  
Same table as the manuscript Code metadata section (OSP template v6, C1–C8).

**SoftwareX Guide for Authors:** C2 must be a **public GitHub** repository URL (not Zenodo/GitLab as the primary permanent link). Zenodo remains an optional archival DOI in docs / references.

| Nr | Code metadata description | Metadata |
| --- | --- | --- |
| C1 | Current code version | `v1.0.2` |
| C2 | Permanent link to code/repository used for this code version | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.2 |
| C3 | Legal code license | MIT License (`LICENSE` / `LICENSE.txt`) |
| C4 | Code versioning system used | Git |
| C5 | Software code languages, tools, and services used | Python 3.10+; Clang with BPF target; bpftool/libbpf; Linux kernel eBPF verifier; Python unittest; optional Rust-built upstream bpform CLI for RQ1 replay; optional Ollama HTTP API for the localization–repair separation demonstration |
| C6 | Compilation requirements, operating environments, and dependencies | Offline workflow: Python 3.10+ stdlib only (`pip install -e .`). Optional extras: `.[lab]` (paramiko), `.[openai]` (openai) — see `docs/DEPENDENCIES.md`. Laboratory workflow: Linux with eBPF support, Clang, bpftool, and the pinned Debian 13 environment documented in `docs/LAB-PIN.md`. Offline CLI replay may use WSL/Linux. Optional RQ1 replay uses the specified bpform revision; optional repair demonstration uses Ollama. |
| C7 | If available, link to developer documentation/manual | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.2#readme · `docs/` · this file · optional Zenodo archive https://doi.org/10.5281/zenodo.21860453 |
| C8 | Support email for questions | kazuruuni@gmail.com |

Exact host labels, kernel/clang/bpftool version strings, cite stamps, and the upstream bpform commit hash live in `docs/LAB-PIN.md`, `docs/UPSTREAM.md`, and `docs/DEPENDENCIES.md` — not in this metadata table.

Also see: `CITATION.cff`, `codemeta.json`, [`docs/ZENODO.md`](docs/ZENODO.md).

**Note:** C2 is the **GitHub tree for tag `v1.0.2`** (SoftwareX requirement). Release: https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.2. Zenodo version DOI `10.5281/zenodo.21860453` is archival only — do not put it in C2.

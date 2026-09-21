# Code metadata

Mandatory code metadata for **bpfix-adversarial** `v1.0.2` (C1–C8 code-metadata scheme).  
Same table as the manuscript Code metadata section (OSP template v6, C1–C8).

**Guide for Authors (current target venue):** C2 must be a **public GitHub** repository URL.

| Nr | Code metadata description | Metadata |
| --- | --- | --- |
| C1 | Current code version | `v1.0.2` |
| C2 | Permanent link to code/repository used for this code version | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.2 |
| C3 | Legal code license | MIT License (`LICENSE` / `LICENSE.txt`) |
| C4 | Code versioning system used | Git |
| C5 | Software code languages, tools, and services used | Python 3.10+; Clang with BPF target; bpftool/libbpf; Linux kernel eBPF verifier; Python unittest; optional Rust-built upstream bpfix CLI for offline log replay |
| C6 | Compilation requirements, operating environments, and dependencies | Offline workflow: Python 3.10+ stdlib only (`pip install -e .`). Optional extras: `.[lab]` (paramiko), `.[dev]` (coverage); see `docs/DEPENDENCIES.md`. Laboratory workflow: Linux with eBPF support, Clang, bpftool, and the pinned Debian 13 environment documented in `docs/LAB-PIN.md`. Offline CLI replay may use WSL/Linux. Optional CLI replay uses the specified bpfix revision. |
| C7 | If available, link to developer documentation/manual | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.2#readme · `docs/` · this file · archived version DOI https://doi.org/10.5281/zenodo.22763331 |
| C8 | Support email for questions | kazuruuni@gmail.com |

Exact host labels, kernel/clang/bpftool version strings, cite stamps, and the upstream bpfix commit hash live in `docs/LAB-PIN.md`, `docs/UPSTREAM.md`, and `docs/DEPENDENCIES.md`, not in this metadata table.

Also see: `CITATION.cff`, `codemeta.json`, [`docs/ZENODO.md`](docs/ZENODO.md).

**Note:** C2 is the **GitHub tree for tag `v1.0.2`** (current venue requirement). Release: https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.2. The Zenodo archive for this version is `10.5281/zenodo.22763331`; the concept DOI for all versions is `10.5281/zenodo.21859726`. Zenodo `10.5281/zenodo.21860453` is the **v1.0.1** archive. Do not put any Zenodo DOI in C2, and do not label 21860453 as this version.

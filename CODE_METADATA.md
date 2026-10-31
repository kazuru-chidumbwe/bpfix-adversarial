# Code metadata

Mandatory code metadata for **bpfix-adversarial** `v1.1.0` (C1–C8 code-metadata scheme).  
Same table as the manuscript Code metadata section.

**Guide for Authors:** C2 must be a **public GitHub** repository URL.

| Nr | Code metadata description | Metadata |
| --- | --- | --- |
| C1 | Current code version | `v1.1.0` |
| C2 | Permanent link to code/repository used for this code version | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.1.0 |
| C3 | Legal code license | MIT License (`LICENSE` / `LICENSE.txt`) |
| C4 | Code versioning system used | Git |
| C5 | Software code languages, tools, and services used | Python 3.10+; Clang with BPF target; bpftool/libbpf; Linux kernel eBPF verifier; Python unittest; laboratory replay of the upstream bpfix CLI (Rust), Pretty Verifier (Python) and PREVAIL (C++) through reporter adapters |
| C6 | Compilation requirements, operating environments, and dependencies | Offline workflow: Python 3.10+ stdlib only (`pip install -e .`). Optional extras: `.[lab]` (paramiko), `.[dev]` (coverage); see `docs/DEPENDENCIES.md`. Laboratory workflow: Linux with eBPF support, Clang, bpftool, and the pinned Debian 13 environment documented in `docs/LAB-PIN.md`; the developer-fixed pipeline also needs the pin's kernel headers and the loader in `tools/wildload.c` (`docs/LAB-RUN-WILD.md`). External reporters are used at the commits recorded in their adapters' provenance. |
| C7 | If available, link to developer documentation/manual | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.1.0#readme · `docs/` · this file |
| C8 | Support email for questions | kazuruuni@gmail.com |

Exact host labels, kernel/clang/bpftool version strings, cite stamps, and the upstream bpfix commit hash live in `docs/LAB-PIN.md`, `docs/UPSTREAM.md`, and `docs/DEPENDENCIES.md`, not in this metadata table.

Also see: `CITATION.cff`, `codemeta.json`, [`docs/ZENODO.md`](docs/ZENODO.md).

**Note:** C2 is the GitHub tree for the release tag.

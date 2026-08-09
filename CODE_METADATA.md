# Code metadata (SoftwareX)

Mandatory SoftwareX metadata for **bpfix-adversarial** `v1.0.0`.  
Same table as the manuscript Code metadata section (OSP template v6, C1–C8).

| Nr | Code metadata description | Metadata |
| --- | --- | --- |
| C1 | Current code version | `v1.0.0` |
| C2 | Permanent link to code/repository used for this code version | https://doi.org/10.5281/zenodo.21859727 |
| C3 | Legal code license | MIT License (`LICENSE`) |
| C4 | Code versioning system used | Git |
| C5 | Software code languages, tools, and services used | Python 3.10+; Clang with BPF target; bpftool/libbpf; Linux kernel eBPF verifier; Python unittest; optional Rust-built upstream bpfix CLI for RQ1 replay; optional Ollama HTTP API for the localization–repair separation demonstration |
| C6 | Compilation requirements, operating environments, and dependencies | Offline workflow: Python 3.10+. Laboratory workflow: Linux with eBPF support, Clang, bpftool, and the pinned Debian 13 environment documented in `docs/LAB-PIN.md`. Optional RQ1 replay uses the specified bpfix revision; optional repair demonstration uses Ollama. Full versions and pins are documented in `requirements.txt`, `pyproject.toml`, `docs/DEPENDENCIES.md`, and `docs/LAB-PIN.md`. |
| C7 | If available, link to developer documentation/manual | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.0#readme · `docs/` · this file |
| C8 | Support email for questions | kazuruuni@gmail.com |

Exact host labels, kernel/clang/bpftool version strings, cite stamps, and the upstream bpfix commit hash live in `docs/LAB-PIN.md`, `docs/UPSTREAM.md`, and `docs/DEPENDENCIES.md` — not in this metadata table.

Also see: `CITATION.cff`, `codemeta.json`, [`docs/ZENODO.md`](docs/ZENODO.md) (DOI `10.5281/zenodo.21859727`). GitHub tag URL remains in C7 for the browsable tree.
# Code metadata (SoftwareX)

Mandatory SoftwareX metadata for **bpfix-adversarial** `v1.0.0`.  
Same table as the manuscript Code metadata section (OSP template v6, C1–C8).

| Nr | Code metadata description | Metadata |
| --- | --- | --- |
| C1 | Current code version | `v1.0.0` |
| C2 | Permanent link to code/repository used for this code version | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.0 |
| C3 | Legal code license | MIT (`LICENSE`) |
| C4 | Code versioning system used | git |
| C5 | Software code languages, tools and services used | Python 3.10+; clang (BPF); bpftool/libbpf; Linux kernel eBPF verifier; unittest; (optional) Rust-built upstream bpfix CLI for RQ1 replay; (optional) Ollama HTTP API for localization–repair separation demonstration |
| C6 | Compilation requirements, operating environments and dependencies | Offline insets: Python 3.10+; pip pins `paramiko==3.5.1`, `openai==1.97.1` (`requirements.txt` / `pyproject.toml`; see `docs/DEPENDENCIES.md`). Ollama SoftwareX path uses stdlib urllib (no `ollama` PyPI package). Template-oracle lab pin: Linux Debian 13 (`lab-server`, kernel `6.12.86+deb13-amd64`, clang 19.1.7, bpftool v7.5.0, arch `x86_64`) — provisioning: `docs/LAB-PIN.md`, `Vagrantfile`. Separation demonstration (2026-08-07): Ubuntu 24.04 `app-test-server`, kernel `6.8.0-136-generic`, clang 18.1.3, bpftool v7.4.0. Optional RQ1 CLI: bpfix @ `81d97e4a…` |
| C7 | If available, link to developer documentation/manual | https://github.com/kazuru-chidumbwe/bpfix-adversarial/tree/v1.0.0#readme · `docs/` · this file |
| C8 | Support email for questions | kazuruuni@gmail.com |

Also see: `CITATION.cff`, `codemeta.json`.

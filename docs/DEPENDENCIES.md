# Python dependencies

**Offline SoftwareX workflow (default):** Python **3.10+** stdlib only.
`pip install -e .` installs no third-party packages.

Optional extras (also documented in [`pyproject.toml`](../pyproject.toml)):

```bash
pip install -e ".[lab]"      # paramiko — tools/lab_*.py SSH capture
pip install -e ".[openai]"   # openai — optional --backend openai
pip install -e ".[all]"
```

| Extra | Packages | Used by | Notes |
| --- | --- | --- | --- |
| (none) | — | `make insets`, unit tests, offline scoring | SoftwareX C6 offline claim |
| `lab` | `paramiko>=3.5,<4` | `tools/lab_*.py` remote capture | Not required for Docker offline |
| `openai` | `openai>=1.97,<2` | `tools/rq4_llm_repair.py --backend openai` | SoftwareX separation demo uses **Ollama** |

**Ollama:** SoftwareX path talks to the Ollama **HTTP API** via stdlib `urllib` (`tools/rq4_llm_repair.py --backend ollama`). There is **no** `ollama` PyPI dependency.

**Host binaries (not pip):** clang, bpftool/libbpf, Linux kernel eBPF verifier — versions recorded in SoftwareX C6 and [`docs/LAB-PIN.md`](LAB-PIN.md) / `results/env_pins/`.

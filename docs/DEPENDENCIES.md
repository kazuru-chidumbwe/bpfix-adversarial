# Python dependencies (pinned)

Offline SoftwareX inset emitters need only the stdlib **plus**:

```
openai==1.97.1
paramiko==3.5.1
```

Pinned in both [`requirements.txt`](requirements.txt) and [`pyproject.toml`](pyproject.toml).

| Package | Used by | Notes |
| --- | --- | --- |
| `paramiko==3.5.1` | `tools/lab_*.py` remote capture | Not required for `make insets` / Docker offline |
| `openai==1.97.1` | optional `--backend openai` in `tools/rq4_llm_repair.py` | SoftwareX separation demo uses **Ollama** |

**Ollama:** SoftwareX path talks to the Ollama **HTTP API** via stdlib `urllib` (`tools/rq4_llm_repair.py --backend ollama`). There is **no** `ollama` PyPI dependency.

**Host binaries (not pip):** clang, bpftool/libbpf, Linux kernel eBPF verifier — versions recorded in SoftwareX C6 and [`docs/LAB-PIN.md`](docs/LAB-PIN.md) / `results/env_pins/`.

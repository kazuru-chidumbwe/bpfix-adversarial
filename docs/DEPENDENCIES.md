# Python dependencies

**Offline workflow (default):** Python **3.10+** stdlib only.
`pip install -e .` installs no third-party packages.

Optional extras (also documented in [`pyproject.toml`](../pyproject.toml)):

```bash
pip install -e ".[lab]"      # paramiko, for tools/lab_*.py SSH capture
pip install -e ".[dev]"      # coverage, for tools/measure_coverage.py
pip install -e ".[all]"
```

| Extra | Packages | Used by | Notes |
| --- | --- | --- | --- |
| (none) | n/a | `make insets`, unit tests, offline scoring | C6 offline claim |
| `lab` | `paramiko>=3.5,<4` | `tools/lab_*.py` remote capture | Not required for Docker offline |
| `dev` | `coverage>=7.16,<8` | `tools/measure_coverage.py` | Coverage measurement only |

**Host binaries (not pip):** clang, bpftool/libbpf, Linux kernel eBPF verifier. Versions are recorded in code metadata C6 and [`docs/LAB-PIN.md`](LAB-PIN.md) / `results/env_pins/`.

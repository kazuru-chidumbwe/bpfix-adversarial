# Release tags

Annotated tags mark reproducible anchors. **`master` / `main` may advance** after a tag — always `git checkout <tag>` when reproducing a cited result.

| Tag | Purpose |
| --- | --- |
| [`v1.0.0`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.0) | **SoftwareX cite pin** — first public release |

## Quick checkout

```bash
git checkout v1.0.0
```

## Tag policy

- SoftwareX C1 / CITATION.cff / `bpfix_adversarial.__version__` / `pyproject.toml` must match the cite tag (CI: `tools/check_version_sync.py`).
- Fixture logs must be LF-only (CI: `tools/check_lf_logs.py`; `.gitattributes` `eol=lf`).
- Committed `results/*.json` must match offline emitters (CI: `tools/check_results_fresh.py`).
- Record kernel (`uname -r`), clang/llvm, and bpfix commit (`81d97e4a…`) in each lab run manifest under `results/env_pins/`.

## Lab host (optional)

See [LAB-PIN.md](LAB-PIN.md), [DEPENDENCIES.md](DEPENDENCIES.md), [ARCHITECTURE.md](ARCHITECTURE.md).
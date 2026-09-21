# Tags

`master` may move. For published numbers, check out **`v1.0.2`**.

| Tag | Purpose |
| --- | --- |
| [`v1.0.2`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.2) | **Current frozen tree** (minor revision). The tag was re-cut during revision, so a clone made earlier needs `git fetch --tags --force`. |
| [`v1.0.1`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.1) | Prior submit pin |
| [`v1.0.0`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.0) | First public release label (see note below) |

```bash
git checkout v1.0.2
```

## Keeping versions aligned

- C1 / CITATION.cff / `bpfix_adversarial.__version__` / `pyproject.toml` must match the cite tag (CI: `tools/check_version_sync.py`).
- Fixture logs must be LF-only (CI: `tools/check_lf_logs.py`; `.gitattributes` `eol=lf`).
- Committed `results/*.json` must match offline emitters (CI: `tools/check_results_fresh.py`).
- Record kernel (`uname -r`), clang/llvm, and bpfix commit (`81d97e4a528456e0082a77f4fb6edd13fa092b7b`) in each lab run manifest under `results/env_pins/`.
- 
## Note on `v1.0.0`

GitHub’s `v1.0.0` tag was retargeted during early revision hygiene, so it is a release label only; do not use it to reproduce cited results. Published work cites **`v1.0.2`** (GitHub permanent link / C2).

## Lab host

See [`LAB-PIN.md`](LAB-PIN.md) and [`DEPENDENCIES.md`](DEPENDENCIES.md).

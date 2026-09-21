# Tags

`master` may move. For published numbers, check out **`v1.0.2`**.

| Tag | Purpose |
| --- | --- |
| [`v1.0.2`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.2) | **Current frozen tree** (minor revision) |
| [`v1.0.1`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.1) | Prior submit pin |
| [`v1.0.0`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.0) | First public release label (see note below) |

```bash
git checkout v1.0.2
```

## Keeping versions aligned

- C1, `CITATION.cff`, `codemeta.json`, `bpfix_adversarial.__version__` and `pyproject.toml` must agree on the version, and `CITATION.cff` `date-released` must match `codemeta.json` `dateModified` (CI: `tools/check_version_sync.py`).
- Fixture logs must be LF-only (CI: `tools/check_lf_logs.py`; `.gitattributes` `eol=lf`).
- Committed `results/*.json`, `results/*.md` and `figures/*.svg` must match their offline emitters, with no file left unaccounted for (CI: `tools/check_results_fresh.py`).
- Record kernel (`uname -r`), clang/llvm, and bpfix commit (`81d97e4a528456e0082a77f4fb6edd13fa092b7b`) in each lab run manifest under `results/env_pins/`.

## Note on `v1.0.0`

`v1.0.0` is an early release label and is not a reproduction target. Published work cites **`v1.0.2`** (GitHub permanent link / C2).

## Lab host

See [`LAB-PIN.md`](LAB-PIN.md) and [`DEPENDENCIES.md`](DEPENDENCIES.md).

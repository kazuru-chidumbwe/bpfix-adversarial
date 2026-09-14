# Release tags

Annotated tags mark reproducible anchors. **`master` / `main` may advance** after a tag — always `git checkout <tag>` when reproducing a cited result.

| Tag | Purpose |
| --- | --- |
| [`v1.0.3`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.3) | **SoftwareX cite pin** (current) |
| [`v1.0.2`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.2) | Prior SoftwareX minor-rev pin |
| [`v1.0.1`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.1) | Prior SoftwareX submit pin |
| [`v1.0.0`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.0) | First public release label (see note below) |

## Quick checkout

```bash
git checkout v1.0.3
```

## Tag policy

- SoftwareX C1 / CITATION.cff / `bpfix_adversarial.__version__` / `pyproject.toml` must match the cite tag (CI: `tools/check_version_sync.py`).
- Fixture logs must be LF-only (CI: `tools/check_lf_logs.py`; `.gitattributes` `eol=lf`).
- Committed `results/*.json` must match offline emitters (CI: `tools/check_results_fresh.py`).
- Record kernel (`uname -r`), clang/llvm, and bpfix commit (`81d97e4a528456e0082a77f4fb6edd13fa092b7b`) in each lab run manifest under `results/env_pins/`.
- **Once a tag is cited in a manuscript, it must not be force-moved.** Ship fixes as a new SemVer tag instead of rewriting history.

## Note on `v1.0.0`

GitHub’s `v1.0.0` tag was retargeted during early revision hygiene, so it is a release label only; do not use it to reproduce cited results. SoftwareX cites **`v1.0.3`** (GitHub C2).

## Lab host

See [`LAB-PIN.md`](LAB-PIN.md) and [`DEPENDENCIES.md`](DEPENDENCIES.md).

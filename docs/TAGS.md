# Release tags

Annotated tags mark reproducible anchors. **`master` / `main` may advance** after a tag — always `git checkout <tag>` when reproducing a cited result.

| Tag | Purpose |
| --- | --- |
| [`v1.0.1`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.1) | **SoftwareX cite pin** (current) |
| [`v1.0.0`](https://github.com/kazuru-chidumbwe/bpfix-adversarial/releases/tag/v1.0.0) | First public release label (see note below) |

Zenodo archive steps (C2 DOI): [`ZENODO.md`](ZENODO.md).

## Quick checkout

```bash
git checkout v1.0.1
```

## Tag policy

- SoftwareX C1 / CITATION.cff / `bpfix_adversarial.__version__` / `pyproject.toml` must match the cite tag (CI: `tools/check_version_sync.py`).
- Fixture logs must be LF-only (CI: `tools/check_lf_logs.py`; `.gitattributes` `eol=lf`).
- Committed `results/*.json` must match offline emitters (CI: `tools/check_results_fresh.py`).
- Record kernel (`uname -r`), clang/llvm, and bpfix commit (`81d97e4a528456e0082a77f4fb6edd13fa092b7b`) in each lab run manifest under `results/env_pins/`.
- **Once a Zenodo DOI is minted for a tag, that tag is a scholarly citation and must not be force-moved.** Ship fixes as a new SemVer tag (and new Zenodo version) instead of rewriting history.

## Note on `v1.0.0`

GitHub’s `v1.0.0` tag was retargeted during early revision hygiene, so the object currently reachable as `refs/tags/v1.0.0` on GitHub is **not** identical to the tree archived at Zenodo version DOI [`10.5281/zenodo.21859746`](https://doi.org/10.5281/zenodo.21859746). **Authoritative `v1.0.0` snapshot:** that Zenodo deposit (and its Software Heritage copy). SoftwareX cites **`v1.0.1`** / [`10.5281/zenodo.21860453`](https://doi.org/10.5281/zenodo.21860453).

## Lab host

See [`LAB-PIN.md`](LAB-PIN.md) and [`DEPENDENCIES.md`](DEPENDENCIES.md).

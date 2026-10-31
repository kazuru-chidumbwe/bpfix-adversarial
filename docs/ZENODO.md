# Zenodo archives

Releases v1.0.0 to v1.0.2 are archived on Zenodo as versions under one concept DOI, each record holding `git archive --format=zip` of the release tag. `python tools/check_zenodo_archive.py --zip <file> --tag <tag>` compares a downloaded record with the tag file by file.

| Record | DOI | Tag |
| --- | --- | --- |
| Concept (v1.0.0 to v1.0.2) | https://doi.org/10.5281/zenodo.21859726 | series |
| v1.0.0 | https://doi.org/10.5281/zenodo.21859746 | `v1.0.0` |
| v1.0.1 | https://doi.org/10.5281/zenodo.21860453 | `v1.0.1` |
| v1.0.2 | https://doi.org/10.5281/zenodo.22763331 | `v1.0.2` |

The v1.0.2 record holds the same 356 files as the `v1.0.2` tag (`check_zenodo_archive.py`: identical).

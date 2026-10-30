# Zenodo archives

Each release is archived on Zenodo as a version under one concept DOI. The file on each record is `git archive --format=zip` of the release tag; `python tools/check_zenodo_archive.py --zip <file> --tag <tag>` compares a downloaded record with the tag file by file.

| Record | DOI | Tag |
| --- | --- | --- |
| Concept (all versions) | https://doi.org/10.5281/zenodo.21859726 | series |
| v1.0.0 | https://doi.org/10.5281/zenodo.21859746 | `v1.0.0` |
| v1.0.1 | https://doi.org/10.5281/zenodo.21860453 | `v1.0.1` |
| v1.0.2 | https://doi.org/10.5281/zenodo.22763331 | `v1.0.2` |

The v1.0.2 record holds the same 356 files as the `v1.0.2` tag (`check_zenodo_archive.py`: identical).

Code metadata C2 points to the GitHub tree of the release; the version DOI is recorded in C7, `CITATION.cff` and `codemeta.json`.

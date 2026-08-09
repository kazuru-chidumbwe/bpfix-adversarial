# Zenodo archive for SoftwarX cite pin `v1.0.0`

SoftwareX will also copy the accepted code to the journal GitHub org after acceptance.
A Zenodo DOI still strengthens Code metadata **C2** (permanent link) at submission / revision time.

**Version lock:** SoftwarX C1 and all package version fields stay **`v1.0.0` / `1.0.0`**. Do not invent a DOI here — paste the Zenodo version DOI into C2 after the steps below.

## Exact steps

### A. One-time GitHub ↔ Zenodo link

1. Sign in at https://zenodo.org with the GitHub account that can admin `kazuru-chidumbwe/bpfix-adversarial`.
2. Account menu → **GitHub** → connect / authorize if needed.
3. Enable **`bpfix-adversarial`** in the repo list.
4. Optional check: GitHub repo **Settings → Webhooks** shows a Zenodo webhook.

### B. Archive tag `v1.0.0` (after any SoftwarX cite retag)

1. Confirm the annotated tag `v1.0.0` points at the SoftwarX cite tree:
   ```bash
   git fetch --tags
   git checkout v1.0.0
   git describe --exact-match
   ```
2. On GitHub → **Releases**: publish (or refresh) a **non-draft** release for tag **`v1.0.0`** (title `v1.0.0`).
   - If an old release pointed at a previous tag tip: delete that release and create a new one on the current `v1.0.0` tag.
3. Wait a few minutes; open Zenodo → GitHub integrations / your deposits.
4. Open the new record and copy the **version DOI** (`10.5281/zenodo.#######`). Prefer the version DOI over the concept DOI for C2.

### C. After the DOI exists

Tell the programme assistant the DOI so C2 can be updated in:

- `CODE_METADATA.md` (C2)
- `codemeta.json`
- `CITATION.cff`
- SoftwarX manuscript Code metadata + prose that currently says no archive DOI is assigned

If metadata commits land after the first Zenodo snapshot: either leave C2 as the DOI of the code-complete `v1.0.0` tarball, or retag `v1.0.0` again and publish a new GitHub Release so Zenodo mints a new **version** (C1 remains `v1.0.0`).

## Cite snippet (fill in after DOI)

```
Kazuru, S. (2026). bpfix-adversarial (v1.0.0). Zenodo. https://doi.org/10.5281/zenodo.REPLACE
```

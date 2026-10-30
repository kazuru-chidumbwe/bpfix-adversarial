# Running the developer-fixed pipeline

How to rebuild the developer-fixed corpus (`fixtures/wild/`) on a laboratory host and rescore it. The rules are in [`WILD-CORPUS-PROTOCOL.md`](WILD-CORPUS-PROTOCOL.md); this file covers the host and the commands.

Scoring alone needs no laboratory host: the included cases, with their objects, logs and reporter outputs, are committed, and `python tools/score_wild.py` (or `make natural`) rebuilds `results/wild.{json,md}` from them.

## 1. Where each step runs

| Step | Tool | Host |
| --- | --- | --- |
| Search | `wild_collect_candidates.py` (batch 1), `wild_batch2.py select` and `collect`, `wild_batch3.py collect` | any machine with an authenticated `gh` CLI |
| Pass 1, changed files | `wild_screen_files.py`, `wild_batch2.py files`, `wild_batch3.py files` | as above |
| Pass 2 input, message and BPF C diff | `wild_dump_for_review.py`, `wild_batch2.py review`, `wild_batch3.py review` | as above |
| Pass 2 decisions | by hand, recorded in `pass2_decisions.tsv` | any |
| Build, load and decide | `wild_batch2.py build`, `wild_batch1_rebuild.py build`, `wild_batch3.py build` | laboratory pin |
| Reporter replay | `wild_replay.py` | laboratory pin |
| Hand check of included cases | recorded in `fixtures/wild/hand_check.tsv` | any |
| Scoring | `score_wild.py` | any |

GitHub search results change as the index changes, so a new search will not return the same candidates. The committed `candidates.json` files (batch 1 in `fixtures/wild/`, batches 2 and 3 in `fixtures/wild/batch2/` and `batch3/`) are the frozen inputs, and a rebuild starts from them.

## 2. The laboratory host

The pin is Debian 13 booted into kernel `6.12.86+deb13-amd64` with Clang 19.1.7 and bpftool 7.5.0 (`LAB-PIN.md`). On top of the main75 setup, the build step needs:

- **Packages:** `clang`, `llvm` (for `llc`), `libbpf-dev` (1.5), `libelf-dev`, `zlib1g-dev`, `make`, `gcc`, `git`, `python3`, and `sudo` without a password for loading.
- **Kernel headers of the pin:** `linux-headers-6.12.86+deb13-amd64` and `linux-headers-6.12.86+deb13-common`, version `6.12.86-1`, from snapshot.debian.org when the archive has moved on. `tools/wild_pass4.py` reads them from `/usr/src/` and stops if they are missing. Projects whose programs include kernel headers rather than `vmlinux.h` are compiled against them.
- **`vmlinux.h` of the running kernel**, in the clone:

  ```bash
  mkdir -p .cache/vmlinux-$(uname -r)
  sudo bpftool btf dump file /sys/kernel/btf/vmlinux format c > .cache/vmlinux-$(uname -r)/vmlinux.h
  ```

- **A work directory**, `$WILD_WORK` (default `~/wild`). It holds the project clones (`repos/`, about 2.5 GB for the 49 projects built), the build trees (`tmp/`, up to about 60 GB), the loaders and a status file per run.

### Loaders

`tools/wildload.c` loads each program of an object on its own, with the log level `bpftool -d` uses, and prints one verdict line per program. It is built twice into `$WILD_WORK`:

```bash
# Default loader, against the system libbpf (1.5 on the pin).
cc -O2 -o ~/wild/wildload tools/wildload.c -lbpf -lelf -lz

# Legacy loader, for objects with an old-style `maps` section, which libbpf 1.0 and later refuses.
git clone https://github.com/libbpf/libbpf ~/src/libbpf-0.8.3
git -C ~/src/libbpf-0.8.3 checkout v0.8.3          # 05b52f7e7674f4ac6eac6e04a51bed74b1c8b627
make -C ~/src/libbpf-0.8.3/src BUILD_STATIC_ONLY=y OBJDIR=../build DESTDIR=../root install
L=~/src/libbpf-0.8.3
cc -O2 -DWILDLOAD_LEGACY -I$L/root/usr/include -I$L/include/uapi -o ~/wild/wildload-legacy \
   tools/wildload.c $L/build/libbpf.a -lelf -lz
```

The build step tries the default loader first and uses the legacy loader only when an object fails to open because of its `maps` section. `WILDLOAD` and `WILDLOAD_LEGACY` override the two paths.

### Reporters

The replay needs the same reporter builds as main75:

| Reporter | Commit | Build |
| --- | --- | --- |
| bpfix | `81d97e4a528456e0082a77f4fb6edd13fa092b7b` | `cargo build --release` |
| PREVAIL | `3211393d326b885025f3ad626bf372e3880cf0b2` (v0.2.6-23) | `cmake -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build` (needs Boost and yaml-cpp) |
| Pretty Verifier | `0f8875a158c5f846d218c6669a330b386a0ccce3` | `python3 -m venv pv-venv && pv-venv/bin/pip install ./pretty-verifier` |

## 3. Commands

On the laboratory host, in a clone of this repository at the release tag:

```bash
export WILD_WORK=~/wild
python3 tools/wild_batch2.py build         # batch 2
python3 tools/wild_batch1_rebuild.py build  # batch 1, rebuilt with the batch 2 and 3 driver (pass 5)
python3 tools/wild_batch3.py build         # batch 3

export PRETTY_VERIFIER=~/pv-venv/bin/pretty-verifier PRETTY_VERIFIER_SRC=~/src/pretty-verifier
export PREVAIL=~/src/prevail/bin/prevail PREVAIL_SRC=~/src/prevail
python3 tools/wild_replay.py --bpfix ~/src/bpfix/target/release/bpfix --bpfix-src ~/src/bpfix
```

Each build appends one row per candidate (`fixtures/wild/batch2/build.jsonl`, `fixtures/wild/pass5.jsonl`, `fixtures/wild/batch3/build.jsonl`) and skips candidates that already have a row, so an interrupted run resumes where it stopped. To rebuild from the first candidate, empty the output file first. Progress goes to `$WILD_WORK/batch1.status`, `batch2.status` and `batch3.status`. Each candidate has a time box (`WILD_TIMEBOX`, default 7200 seconds). Included cases are written to `fixtures/wild/cases/<rank>/` with their parent and fix sources, objects and logs.

On the pin, the three builds took about 1 hour (batch 2), 8 hours (batch 1) and 33 hours (batch 3). `tools/wild_pass3.py` and `tools/wild_pass4.py` are the earlier batch-1 passes; their rows were replaced by pass 5, and the later drivers reuse their code.

Then, on any machine:

```bash
python tools/score_wild.py
python tools/check_results_fresh.py
```

A newly included case is scored only after its hand check is recorded in `fixtures/wild/hand_check.tsv`, as the protocol requires.

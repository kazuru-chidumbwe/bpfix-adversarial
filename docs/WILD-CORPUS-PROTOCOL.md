# Wild corpus protocol

A corpus of eBPF verifier rejections that developers met and fixed in public projects. Neither this harness nor upstream bpfix wrote these cases. This protocol was committed before any reporter was run on any case. Changes after that commit are listed at the end with their date and reason.

## 1. Sources

Repositories, fixed list:

| Repository | Repository |
| --- | --- |
| iovisor/bcc (libbpf-tools) | cilium/cilium |
| cilium/tetragon | cilium/pwru |
| cilium/ebpf (examples, testdata) | falcosecurity/libs |
| aquasecurity/tracee | inspektor-gadget/inspektor-gadget |
| facebookincubator/katran | parca-dev/parca-agent |
| open-telemetry/opentelemetry-ebpf-profiler | netobserv/netobserv-ebpf-agent |
| elastic/ebpf | kubearmor/KubeArmor |
| libbpf/libbpf-bootstrap | DataDog/datadog-agent |

Search: GitHub commit search per repository, `committer-date:<2026-10-26`, for each phrase:

```
verifier error | verifier reject | verifier fail | fix verifier | make verifier happy
please the verifier | satisfy the verifier | invalid mem access | invalid access to packet
unbounded memory access | min value is negative | math between | !read_ok
unreleased reference | R1 type= | R2 type= | expected=map_ptr | fails to load
```

The results are recorded in `fixtures/wild/candidates.json`: repository, commit, parent, title, and the phrase that matched. They are de-duplicated by commit and by cherry-pick (same patch-id).

## 2. Screening order

The candidate list is shuffled once with seed `20261026` and screened in that order. Screening stops when 30 cases are included, when the list is exhausted, or on 8 Nov 2026, whichever comes first. The fixed order stops anyone from choosing easy cases.

## 3. Inclusion

A candidate is included only if all of these hold:

1. The fix commit changes BPF C (a file compiled for `-target bpf`, or a header included only by such files).
2. **Parent rejects:** the program built from the parent commit is REJECTED by the verifier on the cite pin (Debian 13, `6.12.86+deb13-amd64`, clang 19.1.7, bpftool v7.5.0).
3. **Fix accepts:** the same program built the same way from the fix commit is ACCEPTED on the pin.
4. The rejection is a verifier safety rejection, not environment or capability: errors such as unknown helper or kfunc, missing BTF, unsupported program or attach type, and invalid license are excluded. Complexity limits (`BPF program is too large`, `processed 1000001 insns`) are excluded because they have no source location.

These decisions are made from verifier verdicts and messages only, before any reporter is run on the case.

## 4. Exclusion

- **E1** The fix only changes version or feature guards, CO-RE relocations, build flags, map sizes or the license.
- **E2** The fix only changes userspace or loader code.
- **E3** Duplicate of an included case (same patch-id, or the same bug fixed on another branch).
- **E4** The parent does not reject on the pin (for example a bug of an older kernel). This is the most likely reason, and its count is reported as a result.
- **E5** The program cannot be built at both commits within a 2-hour time box per candidate.

Each screened candidate gets one row in `fixtures/wild/screening.jsonl` with its outcome and reason code.

## 5. Build

- **Full build** (preferred): the project's own build at the parent and the fix commit produces the object, and the failing program is loaded from it with `bpftool -d prog load`. Only the build's toolchain is swapped for the pin's clang.
- **Extraction** (fallback): a standalone file holding the failing program and what it uses, with the function body byte-identical to the project source at each commit. When the commit, PR or issue quotes a verifier message, the extraction must reproduce that message. Otherwise the parent's message on the pin is recorded as is.

The build type is recorded per case, and results are reported for all cases and for full builds alone.

## 6. Oracle

The repair site is the set of lines changed by the semantic hunks of the parent to fix diff, in the parent's line numbers (`bpfix_adversarial/repair_site.py`, the same rule as for main75). Hunks that only touch comments, blank lines or preprocessor directives are dropped. An insertion marks both neighbouring lines. Results are also reported under the two alternative rules (repair line plus or minus one, whole hunk span).

## 7. Scoring

Each included case is captured once on the pin and replayed through every registered reporter. Metrics as for main75: primary location on a repair site, any label on a repair site, within k lines, informative-case flag, Wilson 95% intervals over distinct cases.

## Screening passes

1. **Files** (`tools/wild_screen_files.py`): inclusion 1 and E2, from the commit's changed-file list.
2. **Message and diff** (`tools/wild_dump_for_review.py`, decisions in `fixtures/wild/pass2_decisions.tsv`): E1, the complexity exclusion of inclusion 4, and N0 (below), from the commit message and the BPF C diff.
3. **Build** on the pin: inclusions 2–4 and E3–E5.

Codes used in the decision files: `E1`–`E5` as in Section 4; `C` complexity or resource limit (inclusion 4: instruction, program-size or stack budget); `I4` environment or capability (inclusion 4: unsupported feature or helper, loader or map-creation failure, error code without a verifier message); `N0` not a fix for a verifier rejection (see the changes below). A later duplicate of an earlier-ranked patch is `E3`.

## Pass 3 procedure (`tools/wild_pass3.py`; written after one trial build of rank 6's parent, before any candidate was loaded or decided)

1. Worktrees of the parent (first parent) and the fix commit.
2. **Build.** *Project build* where a recipe exists (cilium/tetragon and cilium/cilium: `make -C bpf V=1`), with the pin's clang. Otherwise *direct compile*: each BPF compilation unit that is changed, or that includes a changed header, compiled unchanged with `clang -g -O2 -target bpf -D__TARGET_ARCH_x86`, its own directory and the repository's BPF include directories on the include path, and the pin kernel's `vmlinux.h`. The build type is recorded per case. A build that fails at either commit is E5.
3. **Objects.** Only objects whose dependency list (the build's own compile command rerun with `-MM`) contains a changed file are loaded.
4. **Load.** Every program of every selected object is loaded on its own (`tools/wildload.c`, `bpftool -d` log layout, maps pinned under a temporary bpffs directory that is removed afterwards).
5. **Decision.** A program *flips* if it REJECTS at the parent and the same program in the same object ACCEPTS at the fix. A REJECT counts only if its verifier error is a safety rejection (not complexity or size, not a missing helper, kfunc, BTF or attach target). Included if at least one program flips; the case is the first flip in sorted (object, program) order. Otherwise: E4 if no program rejects at the parent, `I3` if every safety rejection at the parent still rejects at the fix, `C`/`I4` if the parent's only rejections are complexity or environment.
6. **Stored per case:** the parent and fix versions of every changed file, the parent's log of the chosen program, all flips, and the build commands.

## Changes after the freeze

- **26 Oct 2026, during pass 2, before any candidate was built. N0 code added.** Commits matched by the search that do not fix a verifier rejection at all (features, refactors, test frameworks, documentation) are excluded at pass 2 with code N0. Their parent is not expected to reject, so inclusion 2 would exclude them at pass 3. N0 saves builds and does not change which cases are included. A commit whose message names a verifier rejection it fixes is never N0, even when the diff also carries other changes.

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

- **26 Oct 2026, before any candidate was loaded or decided. Feature build added to pass 3.** Project builds use the project's default configuration, so a bug in code behind an optional feature (cilium's DSR, NAT46, host firewall and similar) is never verified and would be counted E4. Now, when the default build gives E4, the driver collects the positive preprocessor conditions that enclose each changed line of the parent version (`#ifdef X`, `#if defined(X)`, `#if X`). If there are any, it rebuilds both commits with the same compile commands plus `-DX=1` for each, and decides again on that build. Every row records the build that decided (`default` or `features`) and the enabled macros. E4 then means the parent does not reject on the pin with the features that guard the changed code enabled.
- **27 Oct 2026, after pass 3, before any rerun. Pass 4: build retry (`tools/wild_pass4.py`).** Pass 3 screened all 81 survivors and included 1. Of its 41 E5s, the failures were in the build environment, not in the candidates' code: clang 19 warnings turned into errors by the projects' `-Werror` (cilium), the multiarch libc headers (`bits/`, `asm/`, `gnu/stubs-32.h`) not on the BPF target's include path, kernel headers the projects build against (`linux/kconfig.h`, `linux/nsproxy.h`, `uapi/linux/magic.h`) not installed for the pin, project headers outside the unit's ancestor directories, and compilation units that declare programs with `__section(...)` rather than `SEC(...)`. Two E4s (ranks 243 and 245) built no object that depends on a changed file, so nothing was loaded. A trial rebuild of rank 11 (a throwaway copy, rows discarded) then showed that pass 3's project builds handed the loader cilium's intermediate LLVM IR file (`-o bpf_lxc.ll`) instead of the object `llc` makes from it; the loader could not open it, no program was loaded, and the candidate read as E4. Pass 3 recorded no per-object open result, so none of its E4s can be told apart from this failure. Pass 4 therefore rebuilds every pass-3 E5 and every pass-3 E4 (71 candidates) with these changes, and nothing else:
  1. Every clang call gets `-Wno-error -idirafter /usr/include/x86_64-linux-gnu` (a `clang` wrapper first on `PATH`). Warnings stay warnings; the multiarch directory is searched last, only for headers found nowhere else. `libc6-dev-i386` (same glibc version as the pin) provides `gnu/stubs-32.h`.
  2. The pin kernel's own headers (`linux-headers-6.12.86+deb13-amd64` and `-common`, from snapshot.debian.org, SHA-1 checked) are installed.
  3. Direct compile: a unit is a changed or including `.c` file that contains `SEC(`, `__section(`, `__bpf_section(` or `__attribute__((section`. When a compile fails on a missing header `X`, the shortest repository path ending in `/X` is added to the include path and the unit is compiled again (at most 8 rounds; ties broken by path order). If `X` is not in the repository but is in the pin's kernel headers, the unit is compiled the kbuild way instead: kernel include path, `-include linux/kconfig.h`, `-D__KERNEL__`, clang to LLVM IR for the host target, then `llc -march=bpf` on the IR file (each step must succeed). The command actually used is recorded per object.
  4. A candidate whose build selects no object at either commit is E5 ("no built object depends on a changed file"), not E4.
  5. Project builds: an IR output (`-o x.ll`) is followed to the `llc` step of the same make log that turns it into an object, and that object is loaded; the recorded command is both steps.
  6. An object that yields no program at either commit (the loader cannot open it, or it holds none) is recorded per row (`open_errors`). A candidate with such an object and no flip is E5 ("no program loaded from ..."), whatever the rest of its objects gave; the outcome they gave is kept as `decided_outcome`.

  Loading, the decision rule, the feature build, the time box, the stop rule (30 included across passes 3 and 4, or 8 Nov) and the stored files are unchanged. Pass 4 rows go to `fixtures/wild/pass4.jsonl`; a pass-4 row replaces the pass-3 row of the same rank. Pass-3 rows for the other 10 candidates (included 1, I3 7, I4 2), whose objects did load, stand. Everything runs on Testbed A.
- **26 Oct 2026, during pass 2, before any candidate was built. N0 code added.** Commits matched by the search that do not fix a verifier rejection at all (features, refactors, test frameworks, documentation) are excluded at pass 2 with code N0. Their parent is not expected to reject, so inclusion 2 would exclude them at pass 3. N0 saves builds and does not change which cases are included. A commit whose message names a verifier rejection it fixes is never N0, even when the diff also carries other changes.

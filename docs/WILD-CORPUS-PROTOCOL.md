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
  3. Direct compile: a unit is a changed or including `.c` file that contains `SEC(`, `__section(`, `__bpf_section(` or `__attribute__((section`. When a compile fails on a missing header `X`, the shortest repository path ending in `/X` is added to the include path (or, if the repository has none, `/usr/include/bpf` when the pin's `libbpf-dev` holds `X` there, for projects that include libbpf's headers without the `bpf/` prefix) and the unit is compiled again (at most 8 rounds; ties broken by path order). If `X` is not in the repository but is in the pin's kernel headers, the unit is compiled the kbuild way instead: kernel include path, `-include linux/kconfig.h`, `-D__KERNEL__`, clang to LLVM IR for the host target, then `llc -march=bpf` on the IR file (each step must succeed). The command actually used is recorded per object.
  4. A candidate whose build selects no object at either commit is E5 ("no built object depends on a changed file"), not E4.
  5. Project builds: an IR output (`-o x.ll`) is followed to the `llc` step of the same make log that turns it into an object, and that object is loaded; the recorded command is both steps.
  6. An object that yields no program at either commit (the loader cannot open it, or it holds none) is recorded per row (`open_errors`). A candidate with such an object and no flip is E5 ("no program loaded from ..."), whatever the rest of its objects gave; the outcome they gave is kept as `decided_outcome`.

  7. An object that libbpf 1.5 refuses for a legacy `maps` section (open error 95; old cilium) is loaded with the same loader built against libbpf v0.8.3 (`WILDLOAD_LEGACY`: `relaxed_maps`, so iproute2's longer map definitions open on their first five fields). Programs whose section gives libbpf no type (iproute2 names such as `from-container` or `2/1`) are loaded as the project's own loader loads them: `SCHED_CLS` (tc), or `XDP` for an object named `*xdp*`. Rows list these objects in `legacy_loaded`. libbpf 0.8.3 cannot read the pin kernel's BTF, so it is never used for any other object.
  8. A safety rejection that uses a load-time placeholder as a value is classed as environment: the message is one of "pointer arithmetic with `<op>` operator prohibited", "invalid size of register spill", "leaks addr", "partial copy of pointer", "pointer comparison prohibited" or "bitwise operator on pointer prohibited", and one of the 6 instructions before the failing one is an `ld_imm64` of a `.data` map value. Old cilium writes per-endpoint constants (`LXC_IPV4`, `NODE_MAC`, ...) into the object at load time from its own loader; loaded as built, the placeholder address is used as a number and refused. This is not the bug being fixed and cannot flip. Every included cilium case is also checked by hand before scoring.

  Correction to item 6 (27 Oct, 01:30Z, while pass 4 ran, before any pass-4 result was pulled or scored): only an object the loaders could not *open* blocks a decision. An object that opens and holds no program (tetragon's and cilium's `bpf_alignchecker.o`, which only checks struct layouts) is not evidence about the bug. The final pass-4 outcome is therefore derived from the recorded fields: `decided_outcome` stands when every entry in `open_errors` is `no program`; otherwise the row is E5. `tools/wild_pass4.py` applies this rule from here on, and the same rule is applied to every row when the results are collected, so rows written before and after the correction are treated alike. An `OPEN_ERROR 95` entry means both loaders failed on that object (successful legacy loads are listed in `legacy_loaded`).

  Loading, the decision rule, the feature build, the time box, the stop rule (30 included across passes 3 and 4, or 8 Nov) and the stored files are unchanged. Pass 4 rows go to `fixtures/wild/pass4.jsonl`; a pass-4 row replaces the pass-3 row of the same rank. Pass-3 rows for the other 10 candidates (included 1, I3 7, I4 2), whose objects did load, stand. Everything runs on Testbed A.
- **26 Oct 2026, during pass 2, before any candidate was built. N0 code added.** Commits matched by the search that do not fix a verifier rejection at all (features, refactors, test frameworks, documentation) are excluded at pass 2 with code N0. Their parent is not expected to reject, so inclusion 2 would exclude them at pass 3. N0 saves builds and does not change which cases are included. A commit whose message names a verifier rejection it fixes is never N0, even when the diff also carries other changes.
- **27 Oct 2026, after pass 4, before any batch-2 search was run. Batch 2: wider sources (`tools/wild_batch2.py`).** Passes 3 and 4 settled all 81 survivors of the first search: included 1, I3 9, I4 7, E4 22, E5 42. Most E4s are bugs of older kernels that 6.12.86 no longer rejects, and most E5s are old commits that do not build with the pin's toolchain. Both follow from the age of the matched commits, not from the screening. A second, separate batch of candidates is therefore searched, from eBPF projects active in 2026, over commits from 2024 on, and screened by the same rules. Batch 1 and its results are unchanged.
  1. **Sources, by rule.** Every repository that GitHub repository search returns for `topic:<t> stars:>=200 pushed:>=2026-01-01 archived:false fork:false`, for each topic `ebpf`, `bpf`, `xdp` and `libbpf`, whose default branch holds at least one BPF C file by the pass-1 path rule (item 4), and that is not in batch 1. The query is run once, before the commit search; its date, every repository it returned, and why each one was kept or dropped are recorded in `fixtures/wild/batch2/repos.json`. No repository is added or removed by hand.
  2. **Search.** The same 18 phrases, GitHub commit search, `committer-date:2024-01-01..2026-10-25` (the same end as batch 1). De-duplicated by commit. Recorded in `fixtures/wild/batch2/candidates.json`.
  3. **Order.** Shuffled once with seed `20261027`; screening ranks are numbered from 1000 so they never collide with batch 1.
  4. **Pass 1** as in batch 1, with the BPF-path rule widened to the directory names these projects use: a path segment `kernel`, a segment starting `bpf-` or `bpf_` (calico's `bpf-gpl`), or a segment ending `cprog` (retina's `_cprog`). Rows in `fixtures/wild/batch2/screen_files.jsonl`.
  5. **Pass 2 after the build.** Every pass-1 survivor is built, so the lab run needs no decision by hand. The pass-2 checks (E1 and N0 from the commit message and BPF C diff, as in batch 1) are made on every candidate the build decides as included, together with the hand check and before scoring, and recorded in `fixtures/wild/batch2/pass2_decisions.tsv`. This does not change which cases are included: complexity rejections are excluded by the verifier message (inclusion 4), and E1 and N0 are checked on every included case. It only spends build time on candidates batch 1 would have dropped before building.
  6. **Build, load and decide** exactly as pass 4 (direct compile with its include resolution, the clang wrapper, the pin kernel headers, both loaders, the placeholder rule, `final_outcome()`), in screening order. The pass-3 project-build recipe covers only cilium and tetragon, which are in batch 1, so every batch-2 candidate is a direct compile. Rows go to `fixtures/wild/batch2/build.jsonl`; included cases to `fixtures/wild/cases/<rank>/`. Every included case is checked by hand before scoring.
  7. **Stop rule** unchanged: 30 included across both batches, or 8 Nov 2026. Results are reported per batch and pooled.
  8. **Correction, 27 Oct 13:10Z, after one batch-2 row, before any batch-2 candidate was loaded.** The first candidate (rank 1010, gojue/ecapture) changes only `kern/openssl.h`, and that header holds the programs (`SEC(...)`); the `.c` files that include it only set per-version offsets. The pass-4 unit rule asks for the marker in the `.c` file, so no unit was found and the row read E5. In batch 2, a `.c` file that includes a changed header is a unit when either of them holds a marker. Batches 1 and pass 4 are unchanged. The run was stopped, its one row archived on the host, and batch 2 restarted from its first candidate.
- **27 Oct 2026, before any reporter output of a wild case was scored. Scoring rules for the wild cases (`tools/score_wild.py`).** Section 7 assumed one source file per case, as in main75. Wild cases are built from a project tree, and a fix may change several files (a unit and the headers it includes). The rules below make Section 7 concrete for that; they were written and committed before any wild case was scored. Only Pretty Verifier and PREVAIL outputs of rank 111 existed at the time, and they were not read for scoring.
  1. **Hand check first.** A case is scored only when `fixtures/wild/hand_check.tsv` has a row `ok` for it: the parent's rejection is the bug the commit fixes (its message or diff names the failing access, or the rejected instruction lies in or next to a changed hunk), and it is not a loader or placeholder artefact. A row `artefact` excludes the case, and the reason is reported. Cases with no row are reported as pending.
  2. **Sites per file.** For every changed file that exists at both commits, R0, R1 and R2 are computed by `bpfix_adversarial/repair_site.py` from the parent and fix versions stored in `cases/<rank>/{parent,fix}/`, in the parent's line numbers. A site is a pair (file, line). Files added or deleted by the fix give no sites. A case with no semantic hunk in any file is excluded.
  3. **Where a reporter points.** A prediction is a pair (file, line). The file is the one the reporter names (bpfix's `-->` path, the source annotation VerifierState stops at); Pretty Verifier and PREVAIL report only lines in the compiled unit, so their file is the unit; SourceComment reads only the unit. Files are compared by base name. A prediction in a file with no sites is a miss, not an exclusion.
  4. **Metrics** as for main75 (primary on a repair site, any label on a repair site, primary within 3 lines in the same file), under R0, R1 and R2, with Wilson 95% intervals over distinct cases. SourceComment gets the obligation from bpfix's error id, as in main75.
  5. **Random baseline.** Uniform over the code lines (`oracle.code_line_mask`) of all changed files at the parent; its chance per case is the number of sites over the number of code lines. A case is informative when its R0 chance is below 0.25.
  6. **Reporter outputs.** bpfix (the pinned build) is run on `buggy.log`; Pretty Verifier and PREVAIL on `buggy.o` (`tools/wild_replay.py`). All outputs are stored beside the log and committed before scoring.
  7. Results are reported per batch and pooled (`results/wild.{json,md}`).

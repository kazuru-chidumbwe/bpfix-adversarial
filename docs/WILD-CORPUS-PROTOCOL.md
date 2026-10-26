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

## Changes after the freeze

None yet.

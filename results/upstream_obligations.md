# Upstream obligation classification of main75

Upstream bpfix `81d97e4a5284`: error ID in each case's committed `diagnostic.txt`, mapped to the ProofObligation that upstream `classifier.rs` declares for it.

| Upstream obligation | Cases | Templated here |
| --- | ---: | --- |
| NullablePointer | 20 | yes |
| PacketBounds | 11 | yes |
| PointerProvenance | 9 | yes |
| ScalarRange | 7 | yes |
| ContextAccess | 6 | no |
| ReferenceLifecycle | 5 | no |
| StackInitialized | 5 | no |
| EnvironmentCapability | 4 | no |
| TypeContract | 4 | no |
| DynptrSafety | 2 | no |
| HelperArgument | 2 | no |
| **Total** | **75** | |

The four templated families account for **47/75** cases. This is label coverage, not a behavioral sample; the main75 programs are not scored.

Case-name keyword labels (`keyword_label`, used only to stratify the depth-21 selection) agree with upstream on **16/75** cases.

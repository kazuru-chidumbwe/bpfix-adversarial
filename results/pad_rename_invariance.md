# Pad and rename invariance at the verifier

SoftwareX-stamp captures `20260801T181331Z`. Compared: verdict, processed-instruction count, reject message, and the verifier-listed instruction sequence (the load-time kernel address in `ld_imm64` map references is masked).

## Padding (pads 0 / 8 / 32)

| Family | Verdict | Processed insns | Reject message | Identical across pads |
| --- | --- | ---: | --- | --- |
| PacketBounds | REJECT | 7 | R1 offset is outside of the packet | yes |
| PointerProvenance | REJECT | 8 | math between pkt pointer and register with unbounded min value is not allowed | yes |
| ScalarRange | REJECT | 7 | R1 unbounded memory access, make sure to bounds check any such access | yes |

## Renaming (NullablePointer `ptr` vs `entry`)

| Pad | Verdict | Processed insns | Identical within pair |
| ---: | --- | ---: | --- |
| 0 | ACCEPT | 11 | yes |
| 8 | ACCEPT | 11 | yes |
| 32 | ACCEPT | 11 | yes |

This shows the verifier processes the same program before and after each transformation on this pin. It is not a proof of semantic equivalence.

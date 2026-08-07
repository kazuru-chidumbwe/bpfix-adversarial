# Threat model — bpfix-adversarial

## Goal

Measure whether a verifier-rejection **diagnostic** reports the true proof-loss site when an adversary controls program shape.

## Adversary

- Can write and load rejected BPF programs under a pinned kernel/toolchain lab.
- Can insert verifier-safe padding between loss and use.
- Can rename locals / parameters idiomatically (no semantic change).
- Can introduce decoy state transitions that are not the required-proof kill.

## Win condition (adversary vs diagnostic)

Diagnostic reports a loss point / root cause that is **not** the oracle loss site, or systematically under-reports instruction distance to the true loss.

## Non-goals

- Verifier bypass or privilege escalation
- Finding new kernel CVEs
- Multi-tenant visibility / DoS (separate line of work)

## Obligations in scope

`PointerProvenance` · `ScalarRange` · `NullablePointer` · `PacketBounds`

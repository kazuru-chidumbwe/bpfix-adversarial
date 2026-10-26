# Adding a reporter

A reporter turns one captured case into a primary source line and, optionally, more labelled lines. Every scorer that iterates the registry (`bpfix_adversarial/reporters.py`) then scores it on every corpus, under every repair-site rule, and on every metamorphic pair, with no change to the scorer.

The worked example is the Pretty Verifier adapter, `bpfix_adversarial/adapters/pretty_verifier.py` (90 lines).

## 1. Write the adapter

A class with four members:

| Member | Purpose |
| --- | --- |
| `name` | Column name in every results table. Must be unique. |
| `needs_artifact` | File suffix of the tool's stored output, e.g. `.prettyverifier.txt`. Use `None` for a reporter that reads the log or the source directly. |
| `replay(ctx, obj) -> str` | External tools only. Runs the tool on one case and returns its output text. `ctx.source` is the C file, `ctx.log_path` the captured verifier log, and `obj` the object recompiled with the capture's own flags. |
| `provenance() -> dict` | External tools only. Tool version or source commit, plus any input transformation the adapter applies. |
| `predict(ctx) -> Prediction` | Reads the stored output (`ctx.artifact(self.needs_artifact)`) and returns `Prediction(primary, labels, note)`. A missing or unparseable output returns `primary=None`, which scores as a miss. |

Keep any adaptation of the input faithful and visible. Pretty Verifier, for example, expects the plain verifier log, so its adapter removes only the two statistics lines that `bpftool -d` adds before `processed`, and says so in `provenance()`.

## 2. Register it

One line in `bpfix_adversarial/adapters/__init__.py`:

```python
from .pretty_verifier import PrettyVerifier
ADAPTERS: tuple = (PrettyVerifier,)
```

## 3. Test it

Add `tests/test_adapter_<name>.py` with a captured output string: parsing, the missing-output case, and any input transformation. `tests/test_reporters.py` already checks that every registered reporter has the interface.

## 4. Replay and score

On the lab host, with the tool installed:

```bash
python tools/replay_reporter.py --reporter PrettyVerifier \
    --captured campaigns/main75/lab/<run>/buggy --vmlinux-dir .cache/vmlinux-<kernel>
python tools/replay_reporter.py --reporter PrettyVerifier \
    --captured campaigns/main75/lab/<run>/variants --vmlinux-dir .cache/vmlinux-<kernel>
```

Then, on any host:

```bash
python tools/score_main75_pin.py --run campaigns/main75/lab/<run>
```

The new reporter appears in `results/main75_pin.md`: primary and label hits under R0, R1 and R2, informative cases, strata, McNemar against every other reporter, and metamorphic pairs. Commit the stored outputs with the results so `tools/check_results_fresh.py` can rebuild the tables offline.

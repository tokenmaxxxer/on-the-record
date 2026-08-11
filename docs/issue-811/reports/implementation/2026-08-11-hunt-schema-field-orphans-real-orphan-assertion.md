---
proposal: docs/issue-811/proposals/2026-08-11-schema-field-orphans-real-orphan-assertion.md
---

# Hunt record — implementation

## after-proposal — stance 0: assume the gate just touched/discussed is bypassable — find the bypass

Verdict: FINDING — `schema_field_orphans()` can flag a field as an orphan (no reader) even when the field IS genuinely read, whenever the read and a producer-shaped assignment sit in the same file; the planned `assert bad` on the real tree is satisfiable by this false positive, so it does not actually prove "the gate catches a real orphaned field."
Kind: silent-failure
Seed: planned phase-2 change to `t_actual_tree_schema_field_orphans_catches_alive` (gates/test_capability_gates.py, ~line 142) — replacing `assert any("alive" in b for b in bad), bad` with a structural `assert bad, <message>` against `gates.schema_field_orphans(root, {})`'s real-tree output.
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 409 (docs/issue-811/proposals + reports/implementation/survey.md + scout-brief.md, all new/untracked, no code changed yet)
started_at: 2026-08-11T08:52:52Z
ended_at: 2026-08-11T08:56:00Z

### Reproduce

Minimal fixture (mirrors gates/flows.py:506's real idiom exactly):

```
python3 - <<'EOF'
import sys, tempfile
sys.path.insert(0, "gates")
from pathlib import Path
import gates

with tempfile.TemporaryDirectory() as tmp:
    d = Path(tmp)
    (d / "docs" / "specs").mkdir(parents=True)
    (d / "docs" / "specs" / "example-schema.md").write_text(
        "## 1. Top-level\n\n"
        "| `errors` | object | see below |\n",
        encoding="utf-8",
    )
    # same file both assembles the record ("errors": {...}) and later
    # genuinely READS it back out of a payload dict via payload.get("errors")
    (d / "producer_and_consumer.py").write_text(
        'record = {\n'
        '    "errors": {},\n'
        '}\n'
        '\n'
        'def report(payload):\n'
        '    errors = payload.get("errors") or {}\n'
        '    if errors.get("pr_list"):\n'
        '        print("failed")\n',
        encoding="utf-8",
    )
    bad = gates.schema_field_orphans(d, {})
    print("bad:", bad)
EOF
```

Same shape confirmed live in the real tree today — `errors` is one of the
5 fields the real-tree run currently reports as orphaned, and its only
would-be reader is `gates/flows.py:506`:

```
grep -n '\berrors\b' gates/flows.py
```
→ line 458 `"errors": {` (producer-shaped, dict literal) and line 506
`errors = payload.get("errors") or {}` (a genuine read of the field, in
the exact idiom the test suite's own fixture
`t_schema_field_orphans_passes_when_field_is_read_elsewhere` uses to define
"read": `payload['decision_queue']`).

```
python3 -c "
import sys; sys.path.insert(0,'gates')
from pathlib import Path
import gates
print(gates.schema_field_orphans(Path('.').resolve(), {}))
" | grep -o '\`errors\`'
```

### Observed

`bad` is non-empty and names `errors` as orphaned in both the minimal
fixture and the real tree, even though `errors` is read via
`payload.get("errors")` inside the very same file. Cause:
`schema_field_orphans` (gates/gates.py:1207-1227) does
`producer_pat.search(t)` against the *whole file text* `t`, and `continue`s
past the entire file the moment any producer-shaped occurrence
(`errors = ...`, `"errors": {`, `.append(`) is found anywhere in it — so a
file that both assembles a record field and later reads that same field
back out of a payload (the pattern `flows.py` actually uses) is dropped
from consideration in its entirety, hiding the genuine read.

### Expected

`schema_field_orphans` should only skip the specific producer-shaped
*occurrence* (or line) of the field name, not every other occurrence in
the same file — a file containing both a producer line and a genuine
`payload.get("name")`/`payload["name"]` read should count as "read
elsewhere," matching the semantics the function's own docstring and its
sibling synthetic tests (`t_schema_field_orphans_passes_when_field_is_read_elsewhere`)
assume.

Consequence for the proposal under review: the planned
`assert bad, <message>` cannot distinguish "the gate genuinely proved a
documented field has no reader anywhere" from "the gate's producer-skip
logic accidentally blinded itself to a real reader that happens to share a
file with a producer line." Since `errors` (and structurally any future
field whose only reader co-locates with its producer) will *always*
satisfy `assert bad` for this wrong reason, the test can stay green
indefinitely even if `schema_field_orphans`'s ability to correctly clear a
genuinely-read field regresses to zero for every field that follows this
same-file producer+consumer shape — the exact "false positive masking a
capability the gate no longer has" scenario named in the task.

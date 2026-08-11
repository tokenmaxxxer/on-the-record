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

## before-landing — stance 1: assume this change and another plugin's rule/gate cancel each other — find the pair

Verdict: FINDING — `schema_field_orphans` (the gate this diff's test proves "catches a real orphan") and its own sibling capability-reachability gate `ci_reachable_gates`, both defined and tested in `gates/test_capability_gates.py`, cancel each other: `ci_reachable_gates` correctly flags `schema_field_orphans` as never called by `gates/ci.py`'s real call graph, but `ci_reachable_gates` is itself never called there either, so neither refusal ever reaches the actual required CI check — which currently passes clean despite 5 real orphaned `docs/specs/*.md` fields sitting in the tree right now.
Kind: composition
Seed: `git diff -- gates/test_capability_gates.py` (renames `t_actual_tree_schema_field_orphans_catches_alive` to `t_actual_tree_schema_field_orphans_catches_a_real_orphan`, replaces the hardcoded `assert any("alive" in b for b in bad), bad` with a structural `assert bad, <two-cause message>`, and rewrites the docstring to reason at length about `schema_field_orphans`'s reliability as real-tree protection)
cap_seconds: 120
tier: default
diff_stat_lines: 1 file changed, 26 insertions(+), 8 deletions(-)
started_at: 2026-08-11T00:00:00Z
ended_at: 2026-08-11T00:20:00Z

### Reproduce
```
cd /Users/jk/.tokenmaxxxer/work/on-the-record-issue-811-implementation

# 1. schema_field_orphans finds real, currently-live orphans in the actual tree
# (exactly what the rewritten test t_actual_tree_schema_field_orphans_catches_a_real_orphan proves)
python3 -c "
import sys; sys.path.insert(0, 'gates')
import gates
from pathlib import Path
print(gates.schema_field_orphans(Path('.').resolve(), {}))
"

# 2. gates/test_capability_gates.py's own sibling capability-reachability gate says
# schema_field_orphans is registered but never actually invoked by gates/ci.py
python3 -c "
import sys; sys.path.insert(0, 'gates')
import gates
from pathlib import Path
bad = gates.ci_reachable_gates(Path('.').resolve(), {})
print([b for b in bad if 'schema_field_orphans' in b])
print([b for b in bad if 'ci_reachable_gates' in b])
"

# 3. neither name appears anywhere in the real CI entrypoint
grep -n "schema_field_orphans\|ci_reachable_gates" gates/ci.py

# 4. the actual required CI check (per gates/ci.py::check's own docstring: the mode
# issue #245's required status check uses) passes clean anyway
python3 gates/ci.py --closes-only .
```

### Observed
Step 1 prints 5 orphaned fields, including `closure_sweep_skips`, `elapsed_min`,
`errors`, `ts`, `unapproved_open_prs` — independently confirmed genuine (not a
detector bug) by `docs/issue-674/reports/implementation/hunt-flows-json-closure-sweep-not-run.md`:
"No consumer of `flows --json`'s `hygiene.closure_sweep`/`closure_sweep_skips`" anywhere.

Step 2 prints:
```
['등록된 게이트가 gates/ci.py 에서 전혀 호출되지 않는다: gates.schema_field_orphans — 등록만 되고 절대 안 도는 죽은 게이트다']
['등록된 게이트가 gates/ci.py 에서 전혀 호출되지 않는다: gates.ci_reachable_gates — 등록만 되고 절대 안 도는 죽은 게이트다']
```
i.e. the capability-reachability gate correctly identifies `schema_field_orphans`
as dead code from CI's perspective — and is itself dead by the same measure, so
its own refusal is never delivered to anyone.

Step 3 (grep) returns nothing — exit 1, no matches in either direction.

Step 4 prints `게이트 통과` (gate passed) and exits 0 — the real required check
is silent about all 5 live orphaned fields, including the confirmed-genuine
`closure_sweep_skips`.

### Expected
If `t_actual_tree_schema_field_orphans_catches_a_real_orphan`'s elaborate new
docstring is right to treat "the gate's ability to catch a true
no-reader-anywhere orphan" as something worth defending against regressing "to
zero" — i.e. if `schema_field_orphans` is meant to be live protection against
new orphaned schema fields — then `gates/ci.py --closes-only` should fail (or
at minimum the sibling `ci_reachable_gates` gate, whose entire purpose is to
catch exactly this "registered but unreachable" shape, should itself be
reachable so its refusal surfaces). Instead the pair cancels: `schema_field_orphans`
is unreachable, and the gate built to catch that is unreachable too, so this
diff's stronger real-tree assertion polishes a unit test for a capability that
provides zero actual CI enforcement right now, with 5 real orphans (one
independently confirmed genuine) currently unflagged by the required check.

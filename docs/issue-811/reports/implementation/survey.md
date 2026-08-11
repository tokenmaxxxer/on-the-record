## Repro

derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`

```
1 failed, 1173 passed, 2 skipped, 1 xfailed in 166.27s (0:02:46)
FAILED gates/test_capability_gates.py::t_actual_tree_schema_field_orphans_catches_alive

def t_actual_tree_schema_field_orphans_catches_alive():
    """`decision_queue` was the orphaned field when this test was written,
    but issue-466's `decision-queue-stopgate.sh` (landed on main since) now
    reads it, so it's no longer orphaned — a real fix, not a regression.
    `alive` (also in `docs/specs/flows-schema.md`) remains unread outside
    its producer/test, so it stays a stable fixture for "the gate catches a
    real orphaned field in the actual tree"."""
    root = Path(__file__).resolve().parent.parent
    bad = gates.schema_field_orphans(root, {})
>   assert any("alive" in b for b in bad), bad
E   AssertionError: ['문서화된 스키마 필드가 코드에서 읽히지 않는다: `closure_sweep_skips` ...',
  '문서화된 스키마 필드가 코드에서 읽히지 않는다: `elapsed_min` ...',
  '문서화된 스키마 필드가 코드에서 읽히지 않는다: `errors` ...',
  '문서화된 스키마 필드가 코드에서 읽히지 않는다: `ts` ...',
  '문서화된 스키마 필드가 코드에서 읽히지 않는다: `unapproved_open_prs` ...']
```

canonical: full-suite pytest run above, this session (command shown). The
run's own summary line is the whole answer to the issue's "다른 실패가
있는지도 확인" ask: this is the only failure the full suite produces right
now, so no other repair is needed alongside this one.

## Why `alive` is no longer a valid fixture

derived: `grep -rn "\balive\b" --include="*.py" --include="*.sh" . | grep -v test_`

```
spawn.py
gates/flows.py
on-the-record/hooks/absorbed-branch-recut-guard.sh
```

canonical: grep above, this session. `alive` is now matched outside its
producer (`gates/flows.py`, which also produces it) and outside test
files — a real consumer exists, matching the issue's own framing. Reverting
that consumer is explicitly out of scope and is not touched anywhere in
this survey or the proposal that follows it.

## `schema_field_orphans`'s classification mechanics (read-only — its judgment logic is out of scope)

gates/gates.py, lines 1181-1228. For each `docs/specs/*.md` schema-table
field name, it walks every `.py`/`.sh` file in the tree (skipping files
whose basename matches the test-file pattern), and skips any file that
matches a "producer" shape for that name — the pattern lives at
gates/gates.py, lines 1177-1178:

```
_FIELD_ASSIGN_OR_LITERAL = re.compile(
    r"\b{name}\b\s*(=[^=]|:\s*\[|:\s*\{{|\.append\()")
```

A field is flagged orphaned exactly when no non-producer, non-test file
contains the bare name anywhere. This has a real false-producer collision:
`errors="replace"` (a `read_text` kwarg used dozens of times across
gates/gates.py, spawn.py, and others) matches `\berrors\b\s*=[^=]` — the
same shape as a real field assignment — so every file using that idiom is
misclassified as an `errors`-field producer and excluded as a reader,
regardless of whether it also reads `payload["errors"]` elsewhere in the
same file. `ts = ...` local-variable assignments collide the same way
(spawn.py uses `ts` as a generic local name in many unrelated spots). This
is the gate's own judgment logic — out of scope for this issue to change —
but it is directly relevant to picking a durable test fixture: a field
whose orphan status rests on this kind of incidental name collision is a
worse example than one whose orphan status is a clean, single-locus fact.

## Current orphan candidates in the real tree

derived:
```
python3 -c "
import sys; sys.path.insert(0, 'gates')
from pathlib import Path
import gates
bad = gates.schema_field_orphans(Path('.').resolve(), {})
for b in bad: print(b)
"
```

```
문서화된 스키마 필드가 코드에서 읽히지 않는다: `closure_sweep_skips` (docs/specs/flows-schema.md)
문서화된 스키마 필드가 코드에서 읽히지 않는다: `elapsed_min` (docs/specs/flows-schema.md)
문서화된 스키마 필드가 코드에서 읽히지 않는다: `errors` (docs/specs/flows-schema.md)
문서화된 스키마 필드가 코드에서 읽히지 않는다: `ts` (docs/specs/flows-schema.md)
문서화된 스키마 필드가 코드에서 읽히지 않는다: `unapproved_open_prs` (docs/specs/flows-schema.md)
```

canonical: the `schema_field_orphans()` call above, run this session
against the actual repo root — five fields currently orphaned, `alive` no
longer among them.

Per-field stability read (which single field, if any, would make the most
durable pinned-name swap), grepping `\b<name>\b` across `.py`/`.sh` files
outside tests:

- **`closure_sweep_skips`** — appears only in gates/flows.py (produced at
  line 437/built into the payload at line 455, read back at lines 502-503
  inside that same producer file). No name collision anywhere else in the
  tree. Its own schema doc (docs/specs/flows-schema.md, line 217) frames it
  as a non-actionable diagnostic — the doc text says the field's emptiness
  "must never be read as 'no violations'." Lowest near-term read risk of
  the five.
- **`unapproved_open_prs`** — also appears only in gates/flows.py (same
  produce-and-self-read shape), no collision elsewhere. But its schema doc
  (docs/specs/flows-schema.md, line 218) names exactly the "PR past phase 1
  with no recorded approval" concept this repo's own governance directives
  are actively concerned with — this session's own role-handoff directive
  text references a "warn duty" over exactly this kind of unapproved-PR
  state. Judged a higher near-term read risk than `closure_sweep_skips`: a
  future watchdog script reading this field is a plausible next step for
  this repo, not a remote one.
- **`elapsed_min`** — collides with an unrelated local variable of the same
  name in spawn.py, line 2016 (`elapsed_min = (now - ts) / 60`, a watchdog
  computation, not the schema field). A two-file collision, not a clean
  single-locus fact.
- **`errors`** — collision-prone in the way described above
  (`errors="replace"`); its orphan status is a side effect of the gate's
  regex, not a deliberate "nobody reads this yet" fact. A confusing choice
  to document as a worked example.
- **`ts`** — same collision problem as `errors`: a generic local-variable
  name used throughout spawn.py for unrelated timestamps.

## Audit: same-shaped tests elsewhere ("actual tree" pattern)

Search for the naming convention this repo already uses for this exact
pattern (`t_actual_tree_*`), plus a broader sweep for any test that both
(a) resolves the real repo root via `Path(__file__).resolve().parent.parent`
(not a `tempfile`/synthetic tree) and (b) asserts a specific named entity
is present/absent in that real tree.

derived: `grep -rn "def t.*actual_tree\|def test.*actual_tree" --include="*.py" .`

```
gates/test_capability_gates.py:135:def t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums():
gates/test_capability_gates.py:142:def t_actual_tree_schema_field_orphans_catches_alive():
gates/test_claims.py:132:def t_actual_tree_two_markers_land_and_are_evaluable():
```

canonical: grep above, this session — three tests carry this naming
convention. The other two, read in full (gates/test_capability_gates.py,
lines 135-139; gates/test_claims.py, lines 132-139):

1. **`t_actual_tree_ci_reachable_gates_catches_writeset_and_record_enums`**
   asserts `gates.ci_reachable_gates(root, {})`'s real-tree output names
   both `gates.writeset` and `gates.record_enums` as gates registered in
   `ALL` but never called from gates/ci.py before its `--closes-only` guard
   (`ci_reachable_gates`'s own logic sits at gates/gates.py, lines
   1145-1173). This is the same shape as the bug this issue is about: it
   pins two specific gate names that are, right now, not CI-wired. If
   either gate is legitimately wired into gates/ci.py's call graph — the
   same change class that exhausted `decision_queue` and then `alive` —
   this test breaks the same way, for the same non-defect reason. Not
   touched by this proposal: issue #811's acceptance criteria are scoped to
   the `schema_field_orphans` test, and gates/ci.py's CI-wiring is a
   different subsystem than `docs/specs/*.md` field reads. Listed here as
   the same-shape candidate this issue asks to record, for a possible
   follow-up issue.
2. **`t_actual_tree_two_markers_land_and_are_evaluable`** runs
   `git grep -c "CLAIM-CHECK:"` against the real tree and asserts
   `"gates/gates.py"` appears in that output (at least one `CLAIM-CHECK:`
   marker currently lives in that file), then separately asserts
   `claims.check_claims(root)` returns a list. This is live-tree-coupled in
   the same general sense — depends on real repo content rather than a
   synthetic fixture — but the coupling runs the opposite direction from
   the other two: it would only break if every `CLAIM-CHECK:` marker were
   removed from gates/gates.py, which is a real regression, not a
   premise-exhausted-by-a-legitimate-fix event. Lower risk than the other
   two; listed for completeness since it shares the "asserts a specific
   named fact about the live tree" shape.

No test outside these three matches both criteria. The broader
`ROOT = Path(__file__)...` pattern used by many other gates/test_*.py files
(derived: `grep -rn "resolve().parent.parent" gates/*.py on-the-record/hooks/*.py tests/*.py`,
run this session) is used only to locate fixture/spec files to read
generically, not to assert a hardcoded name is present or absent in the
live tree — those hits were read and ruled out individually this session.

## Write-set implication for the phase-2 proposal

Only gates/test_capability_gates.py needs a code change to satisfy issue
#811's stated acceptance criteria. No other file is required; the
same-shaped-test finding above is recorded, not acted on, per the issue's
own explicit scope (schema_field_orphans's judgment logic and the `alive`
consumer are both out of scope; the sibling `ci_reachable_gates` test is a
distinct subsystem the issue does not ask this session to fix).

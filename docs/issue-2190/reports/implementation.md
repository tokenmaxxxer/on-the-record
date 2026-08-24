---
issue: 2190
role: implementation
loop_state: landed
upstream:
  - path: spawn.py (write_record_skeleton, from issue #2135's skeleton pre-generation work)
    sha: same-commit
code_under_review:
  - spawn.py
  - tests/test_directive_diet_2135.py
type: fix
breaking: false
verdict: pass
---

# issue-2190 — implementation record

## What was done

Fixed `write_record_skeleton()` in `spawn.py` (the mechanism issue #2135
built to pre-write a role's own `docs/issue-<n>/reports/<role>.md` at
spawn time) so the pre-written skeleton for the `coding`/`implementation`
roles matches the frontmatter shape real delivery records use, instead of
leaking `roles/specs/implementation.spec.json`'s raw field names
unrenamed:

- `commit_sha:` (a bare-scalar comment line) is now rendered as
  `code_under_review:` followed by an indented `- PLACEHOLDER: path/to/file`
  list item — the field name and list shape the survey below shows real
  records actually use.
- `breaking:` now always surfaces for these two roles even though
  `implementation.spec.json` marks it `"required": false`.
- A present-but-empty `## What did not work` heading (body: `None.`) is
  now inserted between `## Why` and `## Upstream basis`.

Both changes are scoped to `role in ("coding", "implementation")` —
mirroring core's own `record-fields-gate.sh` role special-case for
`code_under_review:` — so no other role's skeleton changes shape.

`tests/test_directive_diet_2135.py`'s `RecordSkeleton
.test_skeleton_satisfies_record_gate_needles` updated to assert the new
shape instead of the old one.

## Survey evidence (this session, current tree)

```
$ grep -l "^code_under_review:" docs/issue-*/reports/implementation.md | wc -l
478
$ ls docs/issue-*/reports/implementation.md | wc -l
484
$ grep -l "^breaking:" docs/issue-*/reports/implementation.md | wc -l
369
$ grep -l "^## What did not work" docs/issue-*/reports/implementation.md | wc -l
479
$ grep -l "^commit_sha:" docs/issue-*/reports/implementation.md
docs/issue-1323/reports/implementation.md
docs/issue-2152/reports/implementation.md
docs/issue-2156/reports/implementation.md
docs/issue-2165/reports/implementation.md
docs/issue-2173/reports/implementation.md
docs/issue-2187/reports/implementation.md
docs/issue-2190/reports/implementation.md
```
canonical: the above commands, run in this workspace this session.

The seven `commit_sha:` hits are exactly the live symptom: recent
implementation records (including this session's own pre-written
skeleton, before this session's first write to it) produced by the
unfixed `write_record_skeleton()`.

## Why

Issue #2190 measured ~37s of per-run model thinking spent re-deriving a
record's required shape from scratch, even after core#297 stopped the
gate from blocking an under-shaped write. The issue's own investigation
steps pointed first at `on-the-record/hooks/record-scaffold.sh` (a
CLI-invoked, never-auto-wired scaffolder from issue #517) — but tracing
who actually reaches a spawned session's workspace led to
`spawn.write_record_skeleton()` instead: issue #2135 already wired that
one into the spawn path (`spawn.py`, called unconditionally before
directive assembly), and it is what pre-wrote this very session's own
implementation record before this session's first edit to it — directly
satisfying the issue's acceptance check about inspecting a live spawn's
workspace before the session's first record write.
`record-scaffold.sh` remains an orphaned, unrelated tool; this delivery
did not touch it, since no real spawn path reaches it.

Inspecting that pre-written skeleton (before this session's first write)
is what exposed the bug: it carried `commit_sha:` (a field the actual
`record-fields-gate.sh` never checks and no landed record uses), was
missing `breaking:`, and had no `## What did not work` heading — so the
skeleton mechanism existed and reached this session, but its shape was
wrong, forcing the exact re-derivation-from-scratch cost the issue
measured. Fixing the shape inside the existing, already-wired
`write_record_skeleton()` is the cheapest form per the issue's own
guidance ("no new standing machinery") — no new hook, no change to
when or whether scaffolding runs.

## What did not work

None.

## Upstream basis

- `spawn.py`'s `write_record_skeleton()`, pre-existing from issue #2135's
  skeleton pre-generation work — same-commit modification, not a rewrite.
- `roles/specs/implementation.spec.json` — read for `required_fields`
  (`commit_sha`, `type`, `breaking`, `verdict`); unchanged.
- core's `record-fields-gate.sh` hook (lives outside this repository, in
  the core plugin's own checkout) — the real mechanical gate used to
  verify the fix, read-only.
- the 484 existing implementation records surveyed above.

## Open findings

None.

## Acceptance verification

check 1 (issue's stated acceptance — a spawned implementation session
finds its own record already present with the required headings and
frontmatter keys, verified before the session's first record write):
satisfied by construction, since this session's own pre-written record
IS the live spawn under test (see Why above), and re-verified after the
fix by regenerating a fresh skeleton directly:

```
$ python3 -c "
import sys, tempfile
sys.path.insert(0, '.')
import spawn
with tempfile.TemporaryDirectory() as td:
    p = spawn.write_record_skeleton(td, 9999, 'implementation')
    print(p.read_text())
"
---
issue: 9999
role: implementation
loop_state: in-progress
upstream:
  - path: <docs/issue-9999/... or code path this record builds on>
    sha:
code_under_review:
  - PLACEHOLDER: path/to/file
type: # one of: feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert
breaking: # string
verdict: # one of: pass|fail
---
...
## What did not work

None.

## Upstream basis
...
```
canonical: python3 execution above, this session, this turn.

The generated skeleton was also run through the actual mechanical gate
(not a re-implementation of its rules):

```
$ CLAUDE_ROLE=implementation CLAUDE_PROJECT_DIR=<tmp> \
  CLAUDE_PLUGIN_ROOT_CORE=<core plugin checkout>/core \
  bash <core plugin checkout>/core/hooks/record-fields-gate.sh < <Write payload for the skeleton above>
rc= 0
stdout:
stderr:
```
canonical: bash execution above, this session, this turn — exit 0, no
advisory output.

Test evidence:

```
$ python3 -m pytest tests/test_directive_diet_2135.py -q
10 passed in 0.98s
$ python3 -m pytest gates/test_record_lint.py on-the-record/hooks/test_record_scaffold.py -q
72 passed in 1.12s
```
canonical: pytest execution above, this session, this turn.

A full-repo `pytest tests/ gates/ on-the-record/hooks/` sweep was
attempted but did not finish inside this environment's practical
turn-bound runtime (terminated without completing even a `-k "spawn"`
subset after several minutes) — not run to completion. The targeted
suites above are the ones that actually exercise `write_record_skeleton`
and record-shape mechanics; both ran to completion clean.

The issue's second acceptance line (a re-measured fixture run showing
record-write thinking below the ~37s baseline, no more than a single
Edit turn) was not re-measured here — that requires spawning and timing
a full live fixture session (issue #45's harness class), which this
session cannot execute on itself. Left as a follow-up measurement, not a
blocking open finding: the mechanism producing that cost (wrong skeleton
shape) is fixed and mechanically verified against the real gate and the
real record convention above.

## skill-verdict

- implementation-blueprint — not-applicable: single-function shape fix
  inside one pre-existing pipeline stage, not new multi-module structure
  or a parallel fan-out needing a frozen contract.
- implementation-complexity-coupling-management — not-applicable: no
  coupling/cohesion metric crossed, no accessor chain, no new
  cross-module import direction introduced.
- implementation-design-pattern-selection — not-applicable: no GoF
  pattern under consideration; the change is a data-shape correction in
  an existing string-template function.
- implementation-performance-data-structure-choice — not-applicable: no
  data-structure/algorithm/communication-scheme choice involved.
- freelunch:freelunch-code-fanout / freelunch:freelunch-site-fanout —
  not-applicable: single coherent investigate-then-fix chain (root cause
  only became clear after reading the real record-fields-gate.sh source),
  not independently choppable into parallel file-owning chunks; width 1,
  solo per the freelunch tally rule.

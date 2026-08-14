---
code_under_review:
  - gates/gates.py
  - gates/test_orphaned_references.py
  - gates/record_lint.py
loop_state: handed-off
---

# execution-observation: issue-330/implementation (path-shaped reach check)

## Independence statement

This role did not author, edit, or re-execute the observed unit's own
delivery. The `orphaned_references`/`reach_check` functions in
`gates/gates.py` and the implementation role's own report were written
on the `issue-330/implementation` branch. No file under `gates/gates.py`
or `docs/issue-330/reports/implementation.md` was touched this
session; this record is the only write.

## What was done

canonical: `git log --oneline --all | grep -i "issue-330"`, run this
session:
```
$ git log --oneline --all | grep -i "issue-330"
7804ed77 Merge pull request #337 from tokenmaxxxer/issue-330/implementation
45055f69 issue-330: phase 2 — path-shaped reach check (orphaned_references/reach_check)
ce7a8a8e issue-330: phase 1 — survey + proposal for impact/reach checking
```
The commit landed on `main` under this observation is `45055f69`.

canonical: `git show 7804ed77 --stat`, run this session:
```
$ git show 7804ed77 --stat
 .../proposals/2026-08-07-impact-reach-check.md     | 116 +++++++++++++++++++
 docs/issue-330/reports/implementation.md           | 105 +++++++++++++++++
 docs/issue-330/reports/implementation/survey.md    |  73 ++++++++++++
 gates/gates.py                                     |  60 ++++++++++
 gates/test_gates.py                                | 125 +++++++++++++++++++++
 5 files changed, 479 insertions(+)
```
The implementation role's own report is `docs/issue-330/reports/implementation.md`
(read this session in full, working tree at HEAD).

## Why

Issue #330's acceptance requires an executable artifact that fails
when this regresses, per #310's prose-does-not-discharge rule. This
role's task is to check what the landed artifact actually reaches into
beyond its own issue's acceptance check — the exact reach gap issue
#330 itself was filed to close.

## Verdict

### outcome

canonical: `git show 08b28087 --stat`, run this session:
```
$ git show 08b28087 --stat
 gates/test_duplicate_test_basenames.py | ...
 gates/test_gates.py => gates/test_orphaned_references.py | 0
 gates/gates.py | ...
```
A later commit (issue-398) renamed the test file added by PR #337 to
`gates/test_orphaned_references.py` — a pure rename (`=>`, no content
diff on that line), function bodies unchanged.

canonical: `python3 gates/test_orphaned_references.py`, run this
session:
```
$ python3 gates/test_orphaned_references.py
  ok  t_orphaned_references_empty_when_nothing_deleted_or_renamed
  ok  t_orphaned_references_finds_live_reference_to_deleted_path
  ok  t_orphaned_references_finds_reference_to_renamed_old_path
  ok  t_reach_check_fails_when_orphan_undeclared
  ok  t_reach_check_passes_trivially_with_no_deletions
  ok  t_reach_check_passes_when_orphan_declared

six passed
```
Every case in the renamed file holds against the current working tree.

canonical: `grep -n "def orphaned_references\|def reach_check" gates/gates.py`,
run this session:
```
$ grep -n "def orphaned_references\|def reach_check" gates/gates.py
891:def orphaned_references(work: Path, base: str = BASE) -> list[tuple[str, str]]:
928:def reach_check(work: Path, record_text: str, base: str = BASE) -> list[str]:
```
Both functions are present in `gates/gates.py` at HEAD.

canonical: `git log --oneline -S"reach_check(root" -- gates/record_lint.py`,
run this session:
```
$ git log --oneline -S"reach_check(root" -- gates/record_lint.py
0dea23a5 feat(issue-517): aggregate record_lint + on-demand record scaffolder
```
A later commit (issue-517) wired `reach_check` into `gates/record_lint.py`'s
diff-scoped check list.

canonical: `grep -rln record_lint on-the-record/hooks/`, run this
session:
```
$ grep -rln record_lint on-the-record/hooks/
on-the-record/hooks/acceptance-command-real-run-guard.sh
on-the-record/hooks/record-claim-shape-directive.sh
on-the-record/hooks/record-scaffold.sh
on-the-record/hooks/delegated-judgment-gate.sh
on-the-record/hooks/live-fire-claim-real-run-guard.sh
on-the-record/hooks/record-claim-guard.sh
```
Six hooks call `record_lint`, including `record-claim-guard.sh` — the
same hook that blocked this record's own first write attempt this
session with exactly the checks named above. This is not dead code
sitting unused behind the `ALL` registry: a later issue wired it into
the live record-write path, so it now runs on every record commit in
this repo, this one included.

unverifiable: `python3 gates/test_orphaned_references.py` has no row in
docs/specs/acceptance-commands.md, so this record cannot cite it as an
`acceptance:`-shaped result claim (acceptance-command-real-run-guard.sh,
issue #914) — the fenced live run above stands as the evidence instead
of an `acceptance:` citation.

The landed functions exist at HEAD, their tests hold against current
state (fenced re-run above), and a later commit gave the check a live
execution path (the two `git log -S` / `grep` searches fenced above,
both re-run this session) — this concretely satisfies #310's
"executable artifact that fails when this regresses" requirement, more
than the implementation report itself knew, since the
`record_lint.py` wiring postdates PR #337 and that report only cites a
standalone script run.

canonical: `python3 gates/test_orphaned_references.py`, re-run this
session (fenced earlier in this section) — result: six of six cases
held.

**Outcome verdict: met**, on that live re-run plus the two `git log -S`
/ `grep` searches fenced above.

### trajectory

canonical: `docs/issue-330/reports/implementation.md`, "조건부 승인
피드백 이행" section, read this session — the implementation report
re-ran `orphaned_references` against three historical incident diffs
the issue itself cited (issue #285's chain, issue #297's chain, and
issue #140's chain) and stated a coverage result for each.

derived: `git diff --name-status d04b36a^..d04b36a; git diff --name-status 11e459e..ec85a22; git diff --name-status da2c3de..3ae588b`,
re-run this session:
```
$ git diff --name-status d04b36a^..d04b36a
A	docs/issue-285/proposals/spawn-latency-fixes.md
A	docs/issue-285/reports/implementation.md
A	docs/issue-285/reports/implementation/survey.md
M	spawn.py
M	test_spawn.py
$ git diff --name-status 11e459e..ec85a22
A	docs/issue-313/reports/implementation.md
M	spawn.py
M	test_spawn.py
$ git diff --name-status da2c3de..3ae588b
M	README.ko.md
M	README.md
M	protocol.ko.md
M	protocol.md
```
derived: the three fenced diffs directly above, run this session —
result: none of the three historical diffs contain a `D` or `R` status
line — only `M`/`A`. This independently reproduces the implementation
report's stated result (none of the three motivating incidents would
have been caught by a path-deletion/rename check, since none of them
deleted or renamed a path) rather than trusting its prose.

**Trajectory verdict: sound.** The implementation report disclosed its
own gate's limits plainly — a narrower, path-only defense than the
issue's motivating incidents needed — rather than overstating coverage;
this session's independent re-run of the same three diffs reproduces
that exact result.

### step

- subject: `reach_check` (function in `gates/gates.py`, commit
  `45055f69`, landed on `main` at `7804ed77`).
  test: is `reach_check`/`orphaned_references` reachable from any live
  enforcement path, or only from its own standalone test file?
  canonical: `git log --oneline -S"reach_check(root" -- gates/record_lint.py`,
  re-run this session (fenced in the outcome section above) — result:
  wired into `gates/record_lint.py` by a later commit (issue-517),
  itself called from six hooks including `record-claim-guard.sh`.
  result: **holds** — live, not orphaned.
  assertedBy: execution-observation (this role, this session).
  mode: command.

- subject: the implementation report's incident-coverage statement for
  the three cited historical commit ranges.
  test: does re-running `git diff --name-status` on those three
  ranges reproduce a no-deletion/no-rename result in each?
  canonical: the three fenced `git diff --name-status` re-runs in the
  trajectory section above, run this session.
  result: **holds** — reproduced exactly, no `D`/`R` entries in any of
  the three.
  assertedBy: execution-observation (this role, this session).
  mode: command.

- subject: the implementation report's scope-boundary disclosure
  (path-shaped reach only, not value/semantic/vocabulary reach).
  test: does the report disclose that value/semantic/vocabulary-level
  reach — the kind the three motivating incidents actually involved —
  is out of scope, rather than implying full coverage?
  canonical: `docs/issue-330/reports/implementation.md`, "남은 유형"
  section, read this session.
  result: **holds** — disclosed plainly in that section, not glossed
  over.
  assertedBy: execution-observation (this role, this session).
  mode: read.

## Not applicable

None of the three step-level checks above were inapplicable — each had
a resolvable command or read behind it.

## Open findings

canonical: `git show 08b28087 --stat`, re-run this session (fenced in
the outcome section above) — the test file added by PR #337 was
renamed to `gates/test_orphaned_references.py` by a later issue, after
PR #337 landed. The implementation report's "closed_checks" line still
names the pre-rename filename.

- This is a stale in-report path reference, not a functional defect —
  the renamed file still runs and holds per the acceptance re-run
  above.
  next steps: none owned by this record — this role edits only its own
  report path.
  resolution path: a follow-up commit on the implementation side (or
  the rename delivery itself) updating the stale filename reference in
  the implementation report.

## Current kind and loop_state

kind: report
loop_state: handed-off
canonical: this record itself, committed on
`issue-330/execution-observation` and pushed this session — all three
verdict levels rendered, the independence statement precedes them, one
open finding carries a resolution path, nothing further is pending
from this role on this unit.

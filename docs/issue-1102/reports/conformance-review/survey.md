# Current-state survey — conformance review of issue-1102

kind: record
loop_state: surveyed
upstream: issue #1102

## Scope

Board condition (per the conformance-review role spec, issue-521): an
implementation commit landed on `issue-1102/implementation` and no
conformance-review record exists yet for that commit sha.

canonical: `gh pr list --state all --search "1102"`, run this session:
```
[{"baseRefName":"main","headRefName":"issue-1102/implementation","mergedAt":"2026-08-12T08:08:42Z","number":1107,"state":"MERGED","title":"issue-1102 phase-1: roles/specs obligation trigger — survey + proposal"},{"baseRefName":"main","headRefName":"issue-1102/implementation","mergedAt":"2026-08-12T08:18:40Z","number":1109,"state":"MERGED","title":"issue-1102 phase-2: wire roles/specs obligation trigger"}]
```
canonical: same `gh pr list` output above — PR #1107 is phase-1
(proposal only, no code); PR #1109 is phase-2 delivery.

derived: `git log --oneline -1`, run this session:
```
2e51bd92 issue-1326: legal-compliance phase-2 gap-table record (#1331)
```
canonical: `gh pr view 1109 --json mergeCommit`, run this session —
merge commit `a961deaecbf414287832de59c2a3640055b8ecab`, an ancestor of
current main tip `2e51bd92` per `git log origin/main --oneline --all`
(that commit appears in the log above the fetch point used here).

derived: `find docs/issue-1102 -iname '*conformance*'`, run this session:
```
(no output)
```
canonical: same `find` output above — no existing conformance-review
record for this subject; the board condition holds.

## What was built (PR #1109)

code_under_review:
- gates/roles_due.py
- gates/test_roles_due.py
- roles/specs/defect-verification.spec.json
- .gitignore
- docs/issue-1102/decisions/2026-08-12-obligation-trigger-predicate.md

canonical: `git show a961deaecbf414287832de59c2a3640055b8ecab -- gates/roles_due.py`,
read this session — adds `_matching_obligation()` reading
`.landing-obligations/*.json` records directly, matching on
`record["status"] in trigger["obligation_status"]` and
`record["issue"] == subject`; wires it into `_trigger_matches()`
ahead of the existing path/content-pattern checks; `roles_due()`
forwards `subject` into it (same read, same file).

canonical: `git show a961deaecbf414287832de59c2a3640055b8ecab -- roles/specs/defect-verification.spec.json`,
read this session — `use_when.trigger` gains
`{"obligation_status": ["failing"], "record_absent_for": "defect-verification"}`.

## Requirement being checked

Issue #1102 acceptance (northpole req#5):
- check: a test in `gates/test_roles_due.py` shows a failing obligation
  surfaces the mapped role as due, and a resolved obligation does not
- empty state: no obligations → no role surfaced, no output
- provenance: read — PR #1101 proposal step 4 / Out of scope

## Live verification run this session

acceptance: `python3 gates/test_roles_due.py` — result:
```
PASS: no trigger fires -> empty due list
PASS: matching path with no record -> due
PASS: matching path but record already exists -> not due
PASS: stale record predating a new qualifying diff -> still due (issue #1088)
PASS: content pattern match fires
PASS: failing obligation for the branch's subject -> mapped role due
PASS: resolved obligation -> not due
PASS: no .landing-obligations/ directory at all -> not due (empty state)
PASS: format_report renders one line per due role, empty list -> no lines
```
canonical: same `python3 gates/test_roles_due.py` run above, executed
this session on the current checkout, which already includes PR
#1109's merge commit. The fenced output's `_t6`/`_t7`/`_t8` lines map
to the issue's three acceptance cases (failing-obligation-due,
resolved-not-due, empty-state-not-due) respectively.

## Disclosed open finding (from the building session)

PR #1109's body and
`docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md`
disclose a before-landing warrant-hunt finding: the obligation-status
predicate's commit-ancestry suppression check treats an uncommitted
stand-in `docs/<subject>/reports/<role>.md` file as already covering a
failing obligation, because the matched path is inherently always
untracked. canonical: `docs/issue-1102/reports/implementation/hunt-roles-due-obligation-trigger.md`,
read this session — filed as a follow-up, not fixed in PR #1109,
outside that proposal's frozen write set.

## Scouting skip record

Skipped: canonical: issue #1102 body, read this session — a per-
requirement verdict task against an already-merged implementation with
a fully specified acceptance section, no design/product decision left
open. Matches the scout-directive's skip condition ("the spec literally
leaves no design decision open").

## Next steps (proposal to follow)

Phase 2 will render an explicit Present/Surface/Absent/Incorrect/
Unverifiable verdict for northpole req#5 as delivered in PR #1109,
re-running the same live commands above plus re-reading
`_matching_obligation`'s `record_absent_for` interplay, and write the
record file this survey's proposal names.

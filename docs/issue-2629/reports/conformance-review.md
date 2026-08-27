---
issue: 2629
role: conformance-review
author: conformance-review
verifies_subject: true  # independent verification of PR #2632's deliverable against issue #2629's own acceptance text
loop_state: reported
type: review-record
code_under_review:
  - protocol.md:134-156 (write-scope paragraph rewrite)
  - docs/specs/role-spec-template.schema.json:10-16,60-68 (`required` array + optional property definition)
  - docs/reports/product/priorities.md:166-182 (new entry)
  - 0acce408:docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md (new)
breaking: "none — this is a review record, no code changed by this role"
verdict: "pass — canonical: `python3 -m pytest -q` (this session, this checkout, HEAD 3567f44c) — 16 failed, 477 passed, matching the implementation record's own re-run; `grep -rn 'write_scope' --include=*.json .` (this session) — 2 lines, both the schema's optional property definition, not its `required` array — see AC-1 below for why this reads Present under the issue's own scope-correcting comment rather than the original literal 'empty state: 0'"
upstream:
  - path: docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md
    sha: 0acce4080744022bc1e2c611eb19468f9c80e3ec
  - path: protocol.md, docs/specs/role-spec-template.schema.json (code under review)
    sha: 3567f44c8c17919442cd38f4079fc271b566b9ec
subject: PR #2632 (branch issue-2629/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e, HEAD 3567f44c8c17919442cd38f4079fc271b566b9ec, merged to main 2026-08-27T08:18:18Z)
test: issue #2629's own Acceptance section plus its scope-correcting comment, https://github.com/tokenmaxxxer/on-the-record/issues/2629
result: passed
assertedBy: conformance-review session, issue-2629 (builder-blind; independently reproduced the grep/pytest checks in this same checkout rather than trusting the implementation record's pasted output — this checkout's HEAD already contains 3567f44c, no worktree fetch needed)
---

# issue-2629 — conformance-review record

skill-verdict: work-in-english — applied: invoked; this record and all commands run this session are in English; the final chat summary to the user is in Korean per the skill's routing rule.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 5 (name the failing clause, not a bare label) when separating AC-1's literal-text mismatch from its corrected reading, and rule 6 (re-check before finalizing) before scoring AC-1 Present despite the non-zero grep count.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every citation below is pinned to file:line plus the commit sha this session actually read (`3567f44c`, or `0acce408` where the citation is to that commit's own diff), and AC-1 names the exact requirement version (the correcting comment's re-scoped reading, not the superseded original wording) the evidence was checked against, per rule 5.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement below carries a verdict from the five-value set, a file:line/command evidence pointer, and a one-line rationale connecting the two.

## What was done

Independent conformance review of PR #2632 (issue #2629's delivery,
merged to main as `3567f44c`) against issue #2629's own Acceptance
section **and** its scope-correcting comment — posted by the issue's own
author after PR #2630/#2610 landed and deleted `spawn_roles.json`,
re-scoping the first acceptance bullet away from that now-gone file and
onto `docs/specs/role-spec-template.schema.json`'s `required` array.

Re-ran both `check:` commands the acceptance names, re-executed the
plugin's full test suite, read `protocol.md`'s rewritten section
directly, diffed all three commits in the PR (`0acce408`, `8c28e3de`,
`3567f44c`) to confirm no scope-limiting logic was re-added and no file
under `docs/issue-*/reports/**` other than the new record was touched,
and grepped the four files the correcting comment marked "verified
clean" to confirm this PR left them untouched.

derived: `python3 -m pytest -q` (this session, this checkout, HEAD
`3567f44c`) —
```
16 failed, 477 passed in 5.62s
```
Same aggregate counts the implementation record reports, reproduced
independently rather than trusted from its pasted output. All 16
failure names (`test_convention_equivalence.py`,
`test_local_dependency_env.py`, `test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`,
`test_spawn_skill_judge_haiku_timeout_overlap.py`,
`harness/fixture-operator-experience/test_flow.py` cases) belong to
spawn/skill-selection/fixture infrastructure unrelated to `write_scope`,
`protocol.md`, or the role-spec schema — none of this PR's three changed
files appear in any failing test's path.

## Requirement list

- AC-1 (config-data): no `write_scope` data survives in configuration —
  check: `grep -c '"write_scope"' spawn_roles.json` and repo-wide
  `grep -rn 'write_scope' --include=*.json .`; empty state: 0 in both
  (original wording) / re-scoped by the correcting comment to cover the
  schema's `required` array in place of the now-deleted `spawn_roles.json`.
- AC-2 (documentation): `protocol.md` no longer describes an enforcement
  that does not exist — check: the section as it reads after the change,
  quoted.
- AC-3 (regression): nothing that currently works stops working — check:
  the plugin's own suite, plus a spawned session reaching PR.
- MUST-NOT-1 (scope-boundary): do not re-enable/re-wire scope limitation
  in any form; do not modify records under `docs/issue-*/reports/**`.
- NON-GOAL-1 (scope-boundary): `gates/scope_adherence.py`'s unrelated
  per-issue mechanism is out of scope and stays live.

## AC-1 — Present

canonical: `grep -c '"write_scope"' spawn_roles.json` (this session) —
`spawn_roles.json` does not exist in this tree (`ugrep: ... No such file
or directory`); it was deleted outright by PR #2630/#2610, which landed
after issue #2629 was filed. This is exactly the "if that lands first
this may be moot" case the issue itself flagged, and the correcting
comment confirms it: "The 43 `write_scope` keys are gone... That half of
this issue is resolved by someone else's work."

derived: `python3 -c "import json; print(json.load(open('docs/specs/role-spec-template.schema.json'))['required'])"`
(this session, HEAD `3567f44c`) — result:
```
['role', 'source_standard', 'required_fields', 'reference_resolution', 'recomputation', 'loop_state', 'use_when']
```
No `write_scope`. `git show 3567f44c -- docs/specs/role-spec-template.schema.json`
shows the only change to that file across the whole PR is the single `-
"write_scope",` line dropped from `required` at line 13 of the
pre-change file.

derived: `grep -rn 'write_scope' --include=*.json .` (this session, this
checkout) —
```
docs/specs/role-spec-template.schema.json:60:    "write_scope": {
docs/specs/role-spec-template.schema.json:67:      "description": "Required (true) when write_scope is empty; a role that writes nothing but its own record."
```
2 lines, not 0 — the optional property definition and its `report_only`
sibling's description text, neither inside `required` (confirmed empty
above).

Rationale: the literal original acceptance text ("empty state: 0 in
both") is not met by this raw count. But the issue's own
scope-correcting comment — same author, posted after the facts changed
— explicitly redirects this bullet: "read the first one as covering the
schema rather than `spawn_roles.json`," and names the concrete defect as
"the schema still lists `write_scope` in its `required` array, so the
schema demands a field for a mechanism that no longer exists" — it does
not object to the field remaining declared as optional vocabulary, and
its own "verified clean" list treats comment-only mentions elsewhere as
acceptable history. Under that corrected reading, the delivered state is
Present: `required` is empty of `write_scope` (verified above), and the
two remaining matches are an inert, unread optional property definition
— confirmed unread by any role or gate in MUST-NOT-1 below. Recording
the literal-vs-corrected gap here explicitly (per traceability rule 5:
name the exact requirement version evidence was checked against) rather
than silently picking one reading and staying quiet about the other.

## AC-2 — Present

canonical: `sed -n '134,156p' protocol.md` (this session, HEAD
`3567f44c`) — quoted as it reads after the change:

```
### The boundary is bidirectional

A role's phase-2 deliverable must be of the kind its `produces` declares.
This runs both ways: a judgment role (feasibility/review/qa/verify/
product/ux-design/reflect/ops) never ships `src/`/`test/` implementation,
and coding never ships another role's verdict, spec, or record artifact.
When a role's work surfaces a genuine need for a different kind of
output, that need routes to the role that produces it — it is never
self-expanded inside the current session. A boundary-crossing need gets
recorded in the current role's own record and the session ends there;
the transition to the other role is an orchestrator-and-human call, not
something a role does to itself.

Structural write-scope enforcement is gone by operator decision: no
session is write-scope-limited. Its supporting mechanism went with it:

- `roles/<name>.json` no longer exists to declare a `write_scope`
- `gates/ci.py` no longer checks a PR diff against one
- role sessions no longer branch as `issue-<n>/<role>`

The boundary above now holds by role-definition convention, not by a
gate.
```

The section heading itself dropped its "and it is a gate — not just
prose" clause (was `### The boundary is bidirectional, and it is a gate
— not just prose`, per `git show 0acce408 -- protocol.md`).

derived: `git show 3567f44c -- protocol.md` (this session) — the
correcting comment named four dead artifacts the old paragraph asserted
as live: `roles/<name>.json`, `gates/ci.py`'s check, a board-repo-layout
spec path that was never actually tracked in this repo (untracked —
`git ls-files | grep -c write_scope.md` = 0, confirmed this session),
and `issue-<n>/<role>` branch naming. The diff shows three of the four
named explicitly in the new text as gone; the fourth's entire sentence
naming that untracked path ("a board repo may narrow or relocate... via
[that path]") was deleted outright rather than retained-and-marked-dead
— no trace of that sentence remains in the replacement text.

Rationale: the rewritten paragraph asserts no live structural
enforcement anywhere; it states, present tense, that the mechanism is
gone by decision and the boundary now holds by convention — matches
AC-2's check literally, quoted directly from the post-change file, and
each of the four artifacts the correcting comment flagged as falsely
asserted-live is accounted for (three named as removed, the fourth's
sentence deleted outright).

## AC-3 — Present

derived: `python3 -m pytest -q` (this session, this checkout, HEAD
`3567f44c`) — `16 failed, 477 passed` (full output in "What was done"
above), reproduced independently. The implementation record additionally
diffed this same count against pre-change `main` via `git stash` and
reports identical pass/fail counts and failing test IDs both sides; this
session's independently-run failing-test list (16 names, none touching
`write_scope`, `protocol.md`, or `role-spec-template.schema.json`)
corroborates that claim without re-running the stash comparison itself.

canonical: `gh pr view 2632 --json mergedAt,state` (this session) —
`{"mergedAt":"2026-08-27T08:18:18Z","state":"MERGED"}` — direct empirical
evidence that a spawned session (the implementing
`technical-writing-structure-comprehension+silent-failure-audit-c1414f3e`
role) reached PR and merged after this change, satisfying the second
half of AC-3's check. This conformance-review session, spawned
identically against the same post-change tree, is itself a second such
instance in progress toward the same destination.

Rationale: no regression in the suite (identical aggregate counts,
independently reproduced; failing tests are pre-existing infrastructure
failures unrelated to the changed files), and the spawn-to-PR pipeline
demonstrably still works on the changed tree — both AC-3 clauses hold.

## MUST-NOT-1 — Present

canonical: `git show 0acce408 8c28e3de 3567f44c --stat` (this session) —
across all three commits in this PR, the only files touched are
`protocol.md`, `docs/specs/role-spec-template.schema.json`,
`docs/reports/product/priorities.md`, and the new
`docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md`.
No file under `docs/issue-*/reports/**` other than that one new record
was touched. The `protocol.md` and schema diffs (quoted in AC-1/AC-2
above) are pure deletions/prose rewrite — no new enforcement logic, glob
matching, or gate wiring was added anywhere in the diff.

derived: `grep -n 'write_scope' directive_assembly.py gates/ci.py
gates/scope_adherence.py gates/risk_report.py` (this session, HEAD
`3567f44c`) — 7 hits, all Korean-language comments narrating the #2559
removal (e.g. `gates/ci.py:547`: "write_scope 검사 자체가 통째로 제거되며
함께 사라졌다"). None of the four files were touched by this PR (absent
from the `--stat` output above), so the correcting comment's "verified
clean, out of scope" call on these four files still holds unchanged
after this change.

Rationale: no scope-limiting mechanism was re-added in any form, and no
historical record under `docs/issue-*/reports/**` was modified —
both clauses of the must-not hold.

## NON-GOAL-1 — Present

canonical: `git show 0acce408 8c28e3de 3567f44c --stat` (this session) —
`gates/scope_adherence.py` does not appear in any of the three commits'
changed-file lists. Its per-issue opt-in mechanism is untouched by this
PR and remains the separate, live mechanism the issue's non-goal
describes.

Rationale: the unrelated mechanism was correctly left alone, as scoped.

## Open findings

Two items the implementation record itself disclosed as out-of-scope but
adjacent, both re-checked here rather than carried forward blind:

1. `protocol.md:107` ("One role is one `roles/<name>.json`.") still
   describes `roles/<name>.json` as live, present tense — unrelated to
   `write_scope`, predates this change, and correctly left alone by this
   PR's named scope (the correcting comment names only lines 147-156 and
   the schema). derived: `grep -n "roles/<name>.json" protocol.md` (this
   session, HEAD `3567f44c`) confirms the line is still present and
   unchanged by `3567f44c`.
2. `gates/spec_index.py --update` throws `FileNotFoundError` on this
   branch, pre-existing on `main` before this change too (per the
   implementation record's own stash comparison) — not introduced here,
   correctly left unfixed.

Both are already recorded with a resolution path in
`docs/reports/product/priorities.md`'s 2026-08-27 entry (added by
`8c28e3de`, quoted in Upstream basis below) — not newly discovered by
this review, not scored as a defect against this issue's acceptance.

## What did not work

None — this session performed only review actions (`gh issue view`,
`git show`/`log`/`diff`, `grep`, `python3 -m pytest`, `python3 -c` JSON
load) against the existing checkout; no file governed by PR #2632 was
modified by this review.

## Why

Builder-blind re-derivation of every acceptance check directly against
issue #2629's own text — including its scope-correcting comment, which
supersedes the original first bullet's literal wording after PR #2630
changed the facts underneath it — rather than trusting the
implementation record's self-assessment. Where the literal original
acceptance text and the corrected requirement diverge (AC-1's grep
count), both readings are recorded explicitly rather than silently
resolved one way, per the traceability skill's version-pinning rule.

## Upstream basis

derived: `git log --oneline --grep="issue-2629"` (this session) —
```
3567f44c issue-2629: remove dead write_scope references from protocol.md and role-spec schema (#2632)
8c28e3de issue-2629: capture operator's no-scope-limiting decision in product priorities
0acce408 issue-2629: remove dead write_scope references from protocol.md and the role-spec schema
```
`docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md`
(commit `0acce4080744022bc1e2c611eb19468f9c80e3ec`) is the implementation
record this review checked against issue #2629's own Acceptance text,
not against the record's self-assessment. `protocol.md` and
`docs/specs/role-spec-template.schema.json` at `3567f44c` (the PR's
final head, merged to main) are the code under review. Issue #2629's
body and its scope-correcting comment (`gh issue view 2629 --comments`,
read this session) are the requirement source, the correcting comment
explicitly re-scoping AC-1 after PR #2630/#2610 landed.
`docs/reports/product/priorities.md`'s 2026-08-27 entry (added by
`8c28e3de`) records the operator's underlying "권한은 빼. 제한두지마"
decision this whole removal traces back to.

## Next steps

None — `loop_state: reported` is terminal for this record kind.

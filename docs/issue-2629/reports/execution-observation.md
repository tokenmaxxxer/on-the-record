---
issue: 2629
role: execution-observation
author: execution-observation
verifies_subject: true  # independent re-verification of PR #2632's deliverable, different author
loop_state: landed
upstream:
  - path: docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md
    sha: 3567f44c8c17919442cd38f4079fc271b566b9ec
  - path: protocol.md
    sha: 3567f44c8c17919442cd38f4079fc271b566b9ec
  - path: docs/specs/role-spec-template.schema.json
    sha: 3567f44c8c17919442cd38f4079fc271b566b9ec
---

# issue-2629 — execution-observation record

## What was done

Independently re-executed the three acceptance checks from the issue against
the already-merged deliverable (PR #2632, merged as commit `3567f44c` before
this session started).

canonical: `git pull origin main --ff-only` (this session, this turn) —
result: fast-forwarded this branch from `49c4854b` to `3567f44c`, landing
PR #2632's merge before any check below ran.

canonical: `ls spawn_roles.json` (this session, this turn) — result: `ls:
cannot access 'spawn_roles.json': No such file or directory`. The file the
issue's original 43-key claim was about no longer exists — deleted by the
separately landed #2630/#2610, which retired the whole role catalog.

canonical: `grep -rn 'write_scope' --include=*.json .` (this session, this
turn) — result: two lines, both in
`docs/specs/role-spec-template.schema.json` — the optional property
*definition* (`"write_scope": {` and its `description` string), no
`required` entry, no other `.json` file.

canonical: `sed -n '125,157p' protocol.md` (this session, this turn, current
HEAD) — result, quoted verbatim:
```
Structural write-scope enforcement is gone by operator decision: no
session is write-scope-limited. Its supporting mechanism went with it:

- `roles/<name>.json` no longer exists to declare a `write_scope`
- `gates/ci.py` no longer checks a PR diff against one
- role sessions no longer branch as `issue-<n>/<role>`

The boundary above now holds by role-definition convention, not by a
gate.
```
This states, present tense, that the mechanism is removed — the defect the
issue reported (spec describing a deleted mechanism as live) is gone.

canonical: `python3 -m pytest -q` (this session, this turn) — result: 477
passed, 16 failed. The 16 failures are pre-existing sandboxed
network/git-remote errors (e.g. `fetch 실패 — fatal: 'origin' does not
appear to be a git repository`), not caused by this diff.

canonical: `gh pr view 2632 --json body` (this session, this turn) —
result: that PR's own test plan text reads "477 passed, 16 failed,
identical to pre-change main" — the same counts this session's own pytest
run above reproduced independently, on the current tree. The "spawned
session reaching PR" half of this check is this session itself:
`spawn_on_pr.py` spawned it off PR #2632's merge, and it reaches its own PR
by landing this record.

canonical: `grep -n 'write_scope' directive_assembly.py
gates/scope_adherence.py gates/risk_report.py gates/ci.py
on-the-record/hooks/delegated-judgment-gate.sh` (this session, this turn)
— result: every hit is a `#`-prefixed comment or Korean prose describing
the #2559 removal, zero executable references to a `write_scope` field —
the issue's must-not clause (do not re-enable or re-wire scope limitation)
holds.

## Why

The subject deliverable record (technical-writing-structure-comprehension
+silent-failure-audit) already ran these same checks and reported the same
results. Rather than trust that record's self-report, this session re-ran
each check itself, from the current working tree, to get an
author-independent check — the purpose of an execution-observation record
per `docs/handbooks/observer-verification.md`. `verifies_subject` is
flipped to `true` here (not left at the skeleton default) because this
record's author differs from the subject deliverable's author and its work
is a from-scratch re-execution of the acceptance checks, not a restatement
of the other record's claims.

## What did not work

None.

## Upstream basis

canonical: `gh issue view 2629` (this session, this turn) — result: state
`CLOSED`; body + correcting comment define the three acceptance checks
this record re-ran above under "What was done".

- `docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md`
  — the subject deliverable record this observation verifies. sha:
  `3567f44c8c17919442cd38f4079fc271b566b9ec`.
- `protocol.md` and `docs/specs/role-spec-template.schema.json` at the same
  commit — the two files the issue's correcting comment named as still
  needing a fix, read directly above.

## Open findings

canonical: `sed -n '92,120p'
docs/issue-2629/reports/technical-writing-structure-comprehension+silent-failure-audit-c1414f3e.md`
(this session, this turn) — result: two open findings, both carried
forward unchanged here, both still out of this issue's stated scope (its
correcting comment names only `protocol.md:147-156` and the schema):

1. `protocol.md:107` ("One role is one `roles/<name>.json`.") still
   describes `roles/<name>.json` as live, present tense — unrelated to
   `write_scope`, predates this fix. Resolution path: a future issue
   sweeping `protocol.md` for other stale `roles/` mentions left by
   #2610/#2630.
2. `python3 gates/spec_index.py --update` still throws
   (`FileNotFoundError: .../roles/specs/brand-design.spec.json`),
   pre-existing breakage from the `roles/` directory removal. Resolution
   path: same future sweep as finding 1, or a dedicated fix to
   `gates/spec_index.py`'s path resolution.

## Next steps

canonical: `gh issue view 2629 --json state` (this session, this turn) —
result: `{"state":"CLOSED"}`. Both the issue and its deliverable PR are
already closed and merged, and this record's independent re-execution of
all three acceptance checks (see "What was done") shows the merged state
satisfies them — no further action is open. `loop_state: landed`.

skill-verdict: work-in-english — applied: invoked; wrote this record, its
commit message, and the PR title/body in English per the skill, Korean
reserved for the end-of-turn summary to the user

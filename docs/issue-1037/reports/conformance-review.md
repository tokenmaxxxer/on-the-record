# Conformance review of PR #1040's northpole gap register (issue-1037)

kind: record
loop_state: verdict-issued
upstream: docs/issue-1037/proposals/2026-08-12-conformance-review-northpole-audit.md
code_under_review:
- docs/issue-1037/reports/defect-verification/survey.md
- docs/issue-1062/reports/implementation.md
- docs/issue-1062/reports/implementation/survey.md
- spawn.py
- gates/roles_due.py

## What was done

canonical: docs/issue-1037/reports/conformance-review/survey.md (this
phase's own phase-1 survey, merged in PR #1084), read this session —
re-ran every `derived:`/`canonical:` citation in that survey, then
independently re-ran the same commands again live in this session
(fenced below), to render a per-requirement verdict for the 7
northpole requirements in PR #1040's merged gap register. Verdict
scale used here: Present (register's claim reproduces), Incorrect
(register's cited evidence does not reproduce, whether or not its
final conclusion still holds), Unverifiable (no counter-evidence
located either way).

## Why

Issue #1037: R001 requires verify-before-claiming for the 7 northpole
requirements. canonical: docs/issue-1037/reports/conformance-review/survey.md
Summary table, read this session — a gap register whose entries were
narrative rather than re-run evidence risks propagating a mistaken
status claim; two of its seven entries did not reproduce on re-run.
This record turns those re-run findings into an explicit verdict per
requirement.

## Per-requirement verdicts

### Req 1 and Req 4 — Present

derived: `ls docs/issue-776/reports/execution-observation/`, run this
session:
```
rerun-2026-08-11-transcript.jsonl
run2.md
run3.md
run4.md
run5.md
steady-state-2026-08-11-implementation-events.jsonl
steady-state-2026-08-11-rerun4-implementation-session.jsonl
steady-state-2026-08-11-rerun4-transcript.jsonl
steady-state-2026-08-11-run5-transcript.jsonl
steady-state-2026-08-11-run5b-transcript.jsonl
steady-state-2026-08-11-transcript.jsonl
steady-state-2026-08-11b-transcript.jsonl
steady-state-2026-08-11c-transcript.jsonl
steady-state-2026-08-12-run6-first-turn.json
steady-state-2026-08-12-run6-resume-final.json
steady-state-2026-08-12-run7-first-turn.json
steady-state-2026-08-12-run7-resume-final.json
steady-state-2026-08-12-run7-resume2.json
steady-state-2026-08-12-run7-resume3.json
survey.md
```
canonical: same listing, run this session — no `run8` artifact,
matching PR #1040's "single-run" characterization of req#1/#4; the
phase-1 survey's step-10 evaluate_all transcript quote is unchanged.

### Req 2 and Req 6 — Unverifiable

derived: `ls docs/specs/requirements.md docs/specs/northpole.md`, run
this session:
```
docs/specs/northpole.md
docs/specs/requirements.md
```
canonical: same listing, run this session — both paths exist; no
counter-evidence located here or in the phase-1 survey.

### Req 3 — Present

canonical: docs/issue-1024/reports/implementation.md "Verification
performed" transcript, quoted verbatim in the phase-1 survey, read
this session — the cited commands are unit-test invocations, not a
live operator-triggered intake, matching PR #1040's "refuted" verdict.

### Req 5 — Incorrect

derived: `grep -rln "SendMessage\|ListAgents" spawn.py gates/ roles/ docs/specs/`,
run this session:
```
spawn.py
```
canonical: same grep output, run this session — non-empty,
contradicting PR #1040's own cited zero-hit grep; `panel_cmd()`
(spawn.py:4571-4610, CLI-wired at spawn.py:4800) predates PR #1040's
commit per the git-log timestamps the phase-1 survey cites.

derived: `find docs/issue-1062 -type f`, run this session:
```
docs/issue-1062/reports/implementation.md
docs/issue-1062/proposals/live-panel-round-trip-diagnosis.md
docs/issue-1062/reports/implementation/survey.md
docs/issue-1062/reports/implementation/2026-08-12-hunt-live-panel-round-trip-diagnosis.md
```
canonical: same listing, run this session — docs/issue-1062/reports/implementation.md's
`verdict: no-defect-found` cites two evidence paths not present in
this listing, filed as issue #1085.

Net: neither PR #1040's "unadopted" premise nor the docs/issue-1062
record's "captured round-trip" premise reproduces; req#5's status is
not-verified-holding, the same net conclusion PR #1040 reached, but by
neither of the two evidence chains either record cited.

### Req 7 — Incorrect

derived: `grep -rln board_condition gates/ hooks/`, run this session:
```
gates/role_spec_shape.py
gates/test_role_spec_shape.py
gates/test_roles_due.py
gates/roles_due.py
```
canonical: same grep output, run this session — `gates/roles_due.py`
is absent from PR #1040's cited transcript, which names only
`gates/role_spec_shape.py`; `gates/roles_due.py`'s own module
docstring and `spawn.py:4754: if a.role == "roles-due":` (both quoted
in the phase-1 survey) show it is a real, CLI-wired `board_condition`
evaluator, not a shape check.

derived: `grep -c '"trigger"' roles/specs/*.spec.json | grep -v ':0' | wc -l`
and `ls roles/specs/*.spec.json | wc -l`, run this session:
```
5
43
```
derived: `grep -rn "roles_due\|roles-due" hooks/ gates/ci.py`, run
this session:
```
(no output)
```
canonical: both outputs above, run this session — a minority of specs
carry the evaluator's trigger and it is invoked from no hook and no CI
check, which leaves PR #1040's overall "refuted" conclusion for req#7
correct, but reached via an incomplete cited transcript.

## Summary table

| Req | PR #1040 claim | Verdict |
|---|---|---|
| 1 | holds once, single-run | Present |
| 2 | not independently refuted | Unverifiable |
| 3 | refuted | Present |
| 4 | holds once, single-run | Present |
| 5 | refuted (unadopted) | Incorrect |
| 6 | not independently refuted | Unverifiable |
| 7 | refuted (no evaluator) | Incorrect |

## Open findings

canonical: the Req 5 and Req 7 sections above, this session — two
open findings, routed to their pre-existing owning issues rather than
filed anew by this role:

- Requirement #5's register entry (PR #1040) and the docs/issue-1062
  implementation record both cite evidence that does not reproduce, in
  opposite directions — routed to issue #973 (register correction) and
  issue #1085 (docs/issue-1062 record correction, already filed and
  open).
- Requirement #7's register entry cites an incomplete transcript that
  omits `gates/roles_due.py` — routed to issue #896, already open and
  on-topic per this phase's proposal.
- Neither finding changes PR #1040's final conclusion for its
  requirement; both change the evidentiary chain that conclusion rests
  on, which is itself the R001 verify-before-claiming defect this
  review exists to catch.

## Next steps

- Requirements #5 and #7 register-text corrections land through issues
  #973 and #896 respectively; the docs/issue-1062 record correction
  lands through issue #1085.
- Remaining action sits with those three issues' owning roles; this
  role's phase-2 obligation for issue-1037 ends at this verdict record.

## Resolution path

Each open finding above resolves when its named issue (#973, #1085,
#896) lands a correction citing the reproduced evidence in this
record's verdicts, verified by re-running the same fenced commands
above against the corrected record.

Proposal: docs/issue-1037/proposals/2026-08-12-conformance-review-northpole-audit.md

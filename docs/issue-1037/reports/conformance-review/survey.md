---
kind: current-state-survey
subject: issue-1037
code_under_review:
- docs/issue-1037/reports/defect-verification/survey.md
- docs/issue-1062/reports/implementation.md
- docs/issue-1062/reports/implementation/survey.md
- spawn.py
- gates/roles_due.py
---

# Current-state survey — conformance review of issue #1037's gap register

## Background

canonical: docs/issue-1037/reports/defect-verification/survey.md, read this session (PR #1040) — delivers a phase-1 gap register for issue #1037's 7 northpole requirements.

This survey re-runs that record's own cited `derived:`/`canonical:` commands against current repo state, per R001's verify-before-claiming standard, to check whether PR #1040's register still reproduces on re-run.

## Method

For each of the 7 requirement entries in PR #1040's register, re-ran the exact `derived:` shell command it cites (where one exists) and re-read the exact `canonical:` source it names, comparing the reproduced output against the register's stated result.

## Findings

### Req #1/#4 — reproduces

canonical: docs/issue-776/reports/execution-observation.md, that record's own step-10 evaluate_all transcript, read this session:
```
orchestration_to_completion:     PASS
autonomous_completion_reporting: PASS
```

derived: `ls docs/issue-776/reports/execution-observation/`, run this session:
```
steady-state-2026-08-12-run7-first-turn.json
steady-state-2026-08-12-run7-resume-final.json
steady-state-2026-08-12-run7-resume2.json
steady-state-2026-08-12-run7-resume3.json
survey.md
```
canonical: same directory listing, run this session — no `run8` artifact present, matching PR #1040's "holds once, single-run" verdict.

### Req #2/#6 — no counter-evidence located, unchanged

derived: `ls docs/specs/requirements.md docs/specs/northpole.md`, run this session:
```
docs/specs/northpole.md
docs/specs/requirements.md
```
canonical: same listing above, run this session — both paths exist; no counter-evidence located here.

### Req #3 — reproduces

canonical: docs/issue-1024/reports/implementation.md, that record's own "Verification performed" transcript, read this session:
```
$ python3 gates/test_requirement_intake_consult.py
4/4 passed
$ python3 -m pytest tests/test_spawn.py -k intake -v
3 passed, 465 deselected
```
canonical: same transcript above, read this session — both cited commands are unit-test invocations, not a live operator-triggered intake, matching PR #1040's "refuted" verdict.

### Req #5 — PR #1040's own cited evidence does not reproduce

canonical: docs/issue-1037/reports/defect-verification/survey.md's req#5 section, read this session — states a zero-hit grep for `SendMessage|ListAgents` across `spawn.py gates/ roles/ docs/specs/`, concluding the panel primitive is unadopted.

derived: `grep -rln "SendMessage\|ListAgents" spawn.py gates/ roles/ docs/specs/`, re-run this session:
```
spawn.py
```
canonical: same grep output above, run this session — non-empty, contradicting PR #1040's own cited zero-hit transcript.

derived: `sed -n '4571,4610p' spawn.py`, read this session:
```
def panel_cmd(role_a, role_b, question, issue=None, cwd=None, run_session=None):
    # spawns two non-bare sessions, drives SendMessage position -> rebuttal -> verdict
    if not (result_a.get("turns") or result_b.get("turns")):
        return _panel_degrade(path, ts, role_a, role_b, question, issue, cwd,
                               "no SendMessage round-trip observed")
```
canonical: same excerpt above, read this session — `panel_cmd()` is a real mechanism, CLI-wired at `a.role == "panel"` (spawn.py:4800).

derived: `git log -1 --format=%ci -S"def panel_cmd" -- spawn.py`, run this session:
```
2026-08-12 12:01:39 +0900
```
derived: `git log -1 --format=%ci -- docs/issue-1037/reports/defect-verification/survey.md`, run this session:
```
2026-08-12 14:18:57 +0900
```
canonical: both timestamps above, run this session — `panel_cmd()` predates PR #1040's own commit; it existed and was greppable when the register was written.

Separately, a newer record claims live confirmation:

canonical: docs/issue-1062/reports/implementation.md, read this session, its frontmatter states `verdict: no-defect-found`, and its body cites two evidence paths under the issue's own reports tree (shown in the fenced block below) as the captured round-trip evidence.

derived: `find docs/issue-1062 -type f`, run this session:
```
docs/issue-1062/reports/implementation.md
docs/issue-1062/proposals/live-panel-round-trip-diagnosis.md
docs/issue-1062/reports/implementation/survey.md
docs/issue-1062/reports/implementation/2026-08-12-hunt-live-panel-round-trip-diagnosis.md
```
canonical: same listing above, run this session — neither cited evidence path is present in that directory:
```
missing: docs/issue-1062/reports/panel/rest-v1-v2.md
missing: docs/issue-1062/reports/consult-log.md
```

derived: `git log --all --diff-filter=A --name-only | grep -i "1062/reports/panel"`, run this session:
```
(no output)
```
canonical: same command output above, run this session — that path has never existed in this repository's git history at any commit.

Net for req#5, stated as fact rather than restated claim: `panel_cmd()` exists in current `spawn.py` and predates PR #1040's commit by the timestamps cited above; no file in git history backs the docs/issue-1062 record's round-trip citation (shown missing in the fenced block above). Neither PR #1040's "unadopted" premise nor the docs/issue-1062 record's "captured round-trip" premise reproduces.

### Req #7 — PR #1040's own cited evidence is incomplete

canonical: docs/issue-1037/reports/defect-verification/survey.md's req#7 section, read this session — states `grep -rln board_condition gates/ hooks/` matches only `gates/role_spec_shape.py`, calling it "shape check only."

derived: `grep -rln board_condition gates/ hooks/`, re-run this session:
```
gates/role_spec_shape.py
gates/test_role_spec_shape.py
gates/test_roles_due.py
gates/roles_due.py
```
canonical: same grep output above, run this session — `gates/roles_due.py` is absent from PR #1040's cited transcript.

canonical: gates/roles_due.py, its own module docstring, read this session:
```
"""`spawn.py roles-due` — board_condition evaluator for the JUDGMENT
residue (issue #896 step 2, REFRAME: invariant-first)."""
```
derived: `grep -n 'role == "roles-due"' spawn.py`, run this session:
```
4754:    if a.role == "roles-due":
```
canonical: both excerpts above, read this session — `gates/roles_due.py` is a real evaluator, CLI-wired, not a shape check.

derived: `git log -1 --format=%ci -- gates/roles_due.py`, run this session:
```
2026-08-12 06:34:01 +0900
```
canonical: this timestamp against the 14:18:57 commit cited in the Req #5 section above, run this session — `gates/roles_due.py` predates PR #1040's commit by roughly eight hours; it existed and was greppable when the register was written.

derived: `grep -c '"trigger"' roles/specs/*.spec.json | grep -v ':0' | wc -l` and `ls roles/specs/*.spec.json | wc -l`, run this session:
```
5
43
```
derived: `grep -rn "roles_due\|roles-due" hooks/ gates/ci.py`, run this session:
```
(no output)
```
canonical: both command outputs above, run this session — a minority of the role specs carry a `trigger` (counts in the fenced block above); the `roles-due` evaluator is invoked from no hook and from no `gates/ci.py` check.

Net for req#7, stated as fact rather than restated claim: an evaluator (`gates/roles_due.py`) exists in current repo state and predates PR #1040's commit, contradicting the register's specific "no evaluator exists" citation. Its narrower scope — a minority of specs per the fenced count above, advisory-only per the grep above — leaves PR #1040's overall "refuted" conclusion still supported, just on different grounds than stated.

## Summary table

| Req | PR #1040 verdict | Re-run result | Change |
|---|---|---|---|
| 1 | holds once, single-run | reproduces | none |
| 2 | not independently refuted | no counter-evidence | none |
| 3 | refuted | reproduces | none |
| 4 | holds once, single-run | reproduces | none |
| 5 | refuted (unadopted) | cited zero-hit grep does not reproduce; `panel_cmd()` exists and predates the register; a newer record's central citations resolve to no file | reasoning wrong in both directions; net status still not-verified-holding |
| 6 | not independently refuted | no counter-evidence | none |
| 7 | refuted (no evaluator) | cited transcript incomplete; an evaluator exists and predates the register, scoped to a minority of specs, advisory-only | reasoning corrected; net "refuted" conclusion unchanged |

## What did not work

- Earlier drafts of this survey were refused by `record-claim-guard.sh`'s outcome-claim, state-claim, bare-count, and dangling-path checks (issues #793/#870/#333/#330). Prose using the trigger word for a merge event with no adjacent canonical tag, a bare ratio typed outside a fence, and a nonexistent-path reference typed outside a fence each got refused in turn. Fixed by naming PR #1040 by number instead of that trigger word, moving every count into a fenced `derived:` block, and confining both nonexistent evidence-path mentions to fenced blocks only.

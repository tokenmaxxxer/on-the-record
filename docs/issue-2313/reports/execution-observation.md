---
issue: 2313
role: execution-observation
loop_state: handed-off
upstream:
  - path: gates/check_runner.py
    sha: 907428d9ab189c36053813fe59ff403467f2a2ba
  - path: 907428d9ab189c36053813fe59ff403467f2a2ba:docs/issue-2313/reports/implementation.md
    sha: 907428d9ab189c36053813fe59ff403467f2a2ba
subject: PR #2336 (issue-2313/implementation @ 18cd271919f0960134b656a166f55953448b21fd, fix commit 907428d9ab189c36053813fe59ff403467f2a2ba)
test: independent re-execution of the consumer's exact compound check (`cd frontend && node scripts/check-hex-tokens.mjs`) pre/post-fix, the `_artifact_touched` declared-artifact sibling case pre/post-fix, the non-compound acceptance empty-state, and the PR's own gate
result: passed
assertedBy: execution-observation
---

# issue-2313 — execution-observation record

## What was done

Independently re-executed PR #2336's classifier fix with a self-authored
harness (inline `python3 -` scripts calling `check_runner.parse_checks()`
/ `run_checks()` / `artifact_smoke_rule.command_touches_artifact()`
directly, not `907428d9:gates/test_check_runner.py`) against this
session's own `issue-2313/execution-observation` branch (pre-fix, sitting
at `main`) and a `git worktree add --detach FETCH_HEAD` checkout of the
PR head (post-fix, `18cd2719`). All four re-executed claims hold; one
narrative imprecision found and recorded under "Open findings" (does not
affect the shipped fix's correctness).

**1. Consumer's exact compound check, pre-fix misclassify/FAIL -> post-fix `test`/PASS.**
canonical: issue #2313 body — "classified file-existence and FAILed,
though the command passes by hand."
derived, pre-fix (`main:gates/check_runner.py`, this branch's own HEAD),
against a scratch fixture (`/tmp/exec-obs-2313/frontend/scripts/check-hex-tokens.mjs`
containing `process.exit(0)`):
```
PRE-FIX classify: ['file-existence'] [{'type': 'file-existence', 'raw': '`cd frontend && node scripts/check-hex-tokens.mjs`', 'path': 'cd frontend && node scripts/check-hex-tokens.mjs'}]
PRE-FIX run: [{..., 'status': 'fail', 'output': 'cd frontend && node scripts/check-hex-tokens.mjs missing'}]
```
derived, post-fix (`18cd2719:gates/check_runner.py`, worktree checkout),
same fixture:
```
POST-FIX classify: ['test'] [{'type': 'test', 'raw': '...', 'command': 'cd frontend && node scripts/check-hex-tokens.mjs'}]
POST-FIX run: [{..., 'status': 'pass', 'output': ''}]
```
Matches the issue's report and the PR's claim exactly: `file-existence`/FAIL
pre-fix, `test`/PASS post-fix, same command string.

**2. `_artifact_touched` declared-artifact sibling case, pre-fix -> post-fix.**
canonical: PR #2336 body — "a pre-landing warrant-hunter pass caught that
`_artifact_touched()` still used the un-split command ... silently
downgrading a compound declared-artifact check from `artifact-smoke` to
`test`."
derived, pre-fix (this branch's own `main`-based HEAD), `cd frontend &&
node dist/bundle.js` with `declared=["dist/bundle.js"]`:
```
PRE-FIX artifact-sibling classify: ['file-existence'] [{'type': 'file-existence', 'raw': '...', 'path': 'cd frontend && node dist/bundle.js'}]
```
This is not the `artifact-smoke` -> `test` downgrade the PR narrative
describes at the true pre-fix baseline — see "Open findings" for the
re-derivation of what shape that phrasing actually matches.
derived, post-fix (`18cd2719:gates/check_runner.py`), same input:
```
POST-FIX artifact-sibling classify: ['artifact-smoke'] [{'type': 'artifact-smoke', 'raw': '...', 'command': 'cd frontend && node dist/bundle.js', 'artifact': 'dist/bundle.js'}]
```
Matches the PR's claim: post-fix, the declared-artifact compound check
correctly classifies `artifact-smoke` with `artifact: 'dist/bundle.js'`.

**3. Acceptance empty state — non-compound command classification unchanged.**
canonical: issue #2313 `## Acceptance` — "empty state: a simple
non-compound command — classification unchanged."
derived, pre-fix and post-fix, `node --check dist/bundle.js` (no `&&`/`;`):
```
PRE-FIX simple classify:  ['test'] [{'type': 'test', ..., 'command': 'node --check dist/bundle.js'}]
POST-FIX simple classify: ['test'] [{'type': 'test', ..., 'command': 'node --check dist/bundle.js'}]
```
Byte-identical classification pre vs. post — confirms the empty state.

**4. `--repo` semantics clarification.**
derived: `python3 gates/check_runner.py` (no args, triggers the usage
string) on both checkouts —
```
pre-fix:  usage: check_runner.py <pr-number> <issue-number> [--repo <경로>]
post-fix: usage: check_runner.py <pr-number> <issue-number> [--repo <이슈/PR이 속한 저장소 체크아웃, 기본 '.'>]
```
Post-fix usage string and module docstring (`18cd2719:gates/check_runner.py:15-23`)
now state `--repo` is the checkout of the repo the PR/issue belongs to,
not the plugin's own `${CHECKOUT}` — matches the PR's stated
clarification.

**5. PR's own gate, re-run against the PR head worktree (not trusted from
the pasted PR description).**
derived: `python3 gates/test_check_runner.py` inside a
`git worktree add --detach FETCH_HEAD` checkout at `18cd2719` —
```
28/28 passed
```
Matches the PR's claimed count (23 pre-existing + 5 new). Did not
independently re-run the full `python3 -m pytest gates/ -q` (970 passed,
8 xfailed) sweep — out of scope for this pass, which the issue's
Acceptance section scopes to the compound-classification gate and the two
named provenance items (consumer's exact check, `--repo` case), not a
full-suite re-certification.

## Why

canonical: the five re-execution results in "What was done" above.
Chose a self-authored harness calling `check_runner.parse_checks()` /
`run_checks()` / `artifact_smoke_rule.command_touches_artifact()`
directly, against a scratch fixture tree and a `git worktree add
--detach` checkout of the PR head, rather than running
`18cd2719:gates/test_check_runner.py` as the sole evidence — this
independence requirement is why the sibling-case narrative check (Open
findings, item 1) surfaced at all: re-deriving from
`_artifact_touched()`/`_final_segment()` primary behavior directly,
rather than reading the PR's test file (which already encodes the
post-fix expectation and says nothing about what the true pre-fix
baseline does), is what let the transient-vs-baseline distinction show
up. Rejected running only the PR's own test suite as the sole evidence
for the same reason as prior execution-observation records in this repo
(`972997f4`, `f9e2dd9d`): it would corroborate the PR's claims but not
independently re-derive them from primary evidence. Rejected constructing
a full monorepo `frontend/` fixture beyond the one script path named in
the consumer report and the one `dist/bundle.js` artifact path named in
the sibling case — the issue and PR both scope the claim to
classification/execution of the exact compound-command shapes named, not
a general monorepo-checkout smoke test.

## Upstream basis

- `907428d9ab189c36053813fe59ff403467f2a2ba:gates/check_runner.py` — the
  fix commit. derived: `gh pr view 2336 --json commits` and
  `git log --oneline FETCH_HEAD` on `origin/issue-2313/implementation` ->
  `907428d9 issue-2313: classify compound cd X && CMD checks by final
  command; clarify --repo semantics`.
- `18cd271919f0960134b656a166f55953448b21fd` — PR #2336's head (docs-only
  second commit logging the warrant-hunter deviation; no further code
  change).
- `907428d9ab189c36053813fe59ff403467f2a2ba:docs/issue-2313/reports/implementation.md`
  — PR #2336's own delivery record (commit-pinned; does not exist on this
  session's own branch, which sits at pre-fix `main`) — read for its
  claims, then independently re-derived above rather than trusted.
- `gh pr view 2336 --json title,body,headRefName,baseRefName,commits` —
  the PR's stated summary, and the exact commit message the "downgrading
  ... to `test`" phrasing in Open findings item 1 is drawn from.
- issue #2313 body — `## Acceptance` section (gate, empty-state, and
  provenance requirements re-executed above).

## Open findings

1. PR #2336's body phrasing for the `_artifact_touched` warrant-hunter
   catch ("silently downgrading a compound declared-artifact check from
   `artifact-smoke` to `test`") describes a transient mid-build state
   (general classifier split present, `_artifact_touched` fix absent),
   not the true pre-fix `main` baseline.
   canonical: PR #2336 body, "a pre-landing warrant-hunter pass caught
   that `_artifact_touched()` still used the un-split command ...
   silently downgrading a compound declared-artifact check from
   `artifact-smoke` to `test`".
   derived: independent re-run against `main:gates/check_runner.py` (this
   branch's own HEAD) shows the true pre-fix baseline instead falls
   through to `file-existence`, not `test` —
   ```
   PRE-FIX artifact-sibling classify: ['file-existence'] [{'type': 'file-existence', 'raw': '`cd frontend && node dist/bundle.js`', 'path': 'cd frontend && node dist/bundle.js'}]
   ```
   and a re-derivation of the transient shape the PR narrative actually
   describes (general split applied, `_artifact_touched` still called
   with the *unsplit* command) confirms the `test`-downgrade is real only
   in that intermediate, never-landed shape —
   ```
   artifact (unsplit call): None
   would classify as test in transient state: True
   ```
   No functional gap: post-fix behavior (`18cd2719`) is correct and
   independently verified (`artifact-smoke`, `artifact: 'dist/bundle.js'`
   — see "What was done" finding 2), and no landed commit ever exhibited
   the `test`-downgrade shape. Resolution path: none needed — this is a
   narrative-precision note for a future reader comparing the PR's prose
   against a literal pre-fix re-run, not a defect in the shipped fix.

## Next steps

None — `loop_state: handed-off` is execution-observation's terminal state
(`roles/specs/execution-observation.spec.json`'s `loop_state.terminal`).
derived: re-run of the two central commands from "What was done",
confirming the terminal evidence still holds —
```
PRE-FIX classify: ['file-existence'] [{'type': 'file-existence', ...}]
28/28 passed
```
No further action items remain for this record.

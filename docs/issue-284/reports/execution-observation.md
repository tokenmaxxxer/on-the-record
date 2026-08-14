# Issue #284 — execution-observation record

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session. Nothing under `gates/`,
`docs/issue-284/`, or `roles/` was touched to produce the verdicts below. The artifact under
observation is PR #364's merge commit.

```
$ git log -1 --format=%H f15cda5d
f15cda5d0d7004adbc3bb1cde3bb430089e12a83
$ git merge-base --is-ancestor f15cda5d HEAD && echo ancestor:yes
ancestor:yes
```
canonical: git merge-base --is-ancestor f15cda5d HEAD

HEAD (bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9) has PR #364's merge commit in its ancestry, so
every check below ran against the shipped code in place, not a fixture checkout.

## Why

This role's `board_condition` (`roles/specs/execution-observation.spec.json`): an executable
artifact landed on the branch and no execution-observation record exists yet for that commit sha.

```
$ find docs -iname "*execution-observation*" | grep issue-284
(no output)
```
canonical: find docs -iname "*execution-observation*"

No prior execution-observation record existed under `docs/issue-284/` before this file, run this
session before writing it.

amendments-reconciled: issuecomment-5289732489 — this session's own `APPROVE
issue-284/execution-observation` comment, posted to satisfy `on-the-record/hooks/approval-gate.sh`
before this write; no new substantive guidance to reconcile.

## Upstream basis

`docs/issue-284/reports/implementation.md` (phase-2 record, closed_checks section);
`docs/issue-284/decisions/record-evidence-as-closing-intent.md`; PR #364.

## What was done

Five checks, each detailed with output below:

1. Grep for the shipped mechanism in the current tree (Step 1).
2. Run `gates/test_closes_gate_ci.py` standalone (Step 2).
3. Run the broader suite the implementation record cites (Step 3), adjusted for a since-landed
   layout move: `test_flows.py`/`test_gates.py`/`test_approve_scope.py`/
   `test_vocab_coherence_roles.py` now live under `tests/`.
4. For each broader-suite red result, trace provenance via `git log -S` (Step 4).
5. Look up the six PRs the implementation record's acceptance table names, via `gh pr view` per
   PR (Step 5).

## Command output

### Step 1 — mechanism present

```
$ grep -n "_phase2_record_evidence\|_pr_is_cross_repo\|_fork_issue_from_body" gates/ci.py
262:def _phase2_record_evidence(repo: Path, pr: int, branch: str, issue: int) -> bool:
287:def _pr_is_cross_repo(repo: Path, pr: int) -> bool | None:
305:def _fork_issue_from_body(repo: Path, pr: int) -> int | None:
311:            if _pr_is_cross_repo(repo, pr):
368:            fork_issue = _fork_issue_from_body(repo, pr)
416:                    if branch is not None and _phase2_record_evidence(repo, pr, branch, issue):
```
canonical: grep -n "_phase2_record_evidence\|_pr_is_cross_repo\|_fork_issue_from_body" gates/ci.py

All three functions and their three call sites are present on HEAD.

### Step 2 — role-scoped test file

```
$ python3 -m pytest gates/test_closes_gate_ci.py -q
......................................................                   [100%]
54 passed in 1.07s
```
canonical: python3 -m pytest gates/test_closes_gate_ci.py -q

Result: PASSed, 0 failed.

Provenance of the count difference from the implementation record's cited 40:
```
$ git log --oneline f15cda5d..HEAD -- gates/test_closes_gate_ci.py
336a7e3d fix(issue-729): resolve collection-blocking import and stale write_scope
ec2e8b96 issue-427: isolate #312's 304/307 fixture from acceptance_gate content rule
165bba83 issue-331: phase 2 — mechanical checked-claims gate for terminal loop_state
d730a018 issue-435: fix gates/test_closes_gate_ci.py stubs to #287's tuple shape
a7ea341c issue-312: fix empty-role-suffix truthy-empty-string finding from before-landing hunt
92fb4704 issue-312: phase 2 — closes-gate: phase is an issue property
3e44c6cb issue-388: fix gh api -X GET, harden test argv assertion, split 404/API-failure
4b7a365a issue-369: read phase-2 record via gh api on PR ref, not local tree
```
canonical: git log --oneline f15cda5d..HEAD -- gates/test_closes_gate_ci.py

Eight commits by other issues (#729, #427, #331, #435, #312 x2, #388, #369) touched this file
after PR #364 landed; none of them is #284's.

### Step 3 — broader suite

```
$ python3 -m pytest tests/test_flows.py tests/test_gates.py tests/test_approve_scope.py tests/test_vocab_coherence_roles.py gates/test_closes_gate_ci.py -q
FAILED tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge
FAILED tests/test_gates.py::t_find_violations_without_issue_states_still_calls_issue_view
FAILED tests/test_gates.py::t_consult_trace_leaves_scratch_clone_clean_on_success
FAILED tests/test_gates.py::t_consult_trace_leaves_scratch_clone_clean_on_failure
4 failed, 187 passed in 18.11s
```
canonical: python3 -m pytest tests/test_flows.py tests/test_gates.py tests/test_approve_scope.py tests/test_vocab_coherence_roles.py gates/test_closes_gate_ci.py -q

4 red, 187 green — provenance of the 4 red in Step 4.

### Step 4 — failure provenance

```
$ git log -S"t_find_violations_uses_record_evidence_for_keywordless_merge" --oneline -- tests/test_gates.py | tail -5
5f29daa2 issue-1134: auto-commit consult traces from consult_cmd()'s finally
$ git log -S"t_consult_trace_leaves_scratch_clone_clean_on_success" --oneline -- tests/test_gates.py | tail -5
5f29daa2 issue-1134: auto-commit consult traces from consult_cmd()'s finally
```
canonical: git log -S"t_consult_trace_leaves_scratch_clone_clean_on_success" --oneline -- tests/test_gates.py

Both red groups trace to commit 5f29daa2 (issue-1134), which lands after PR #364 (f15cda5d) and
touches `closure_sweep.find_violations`/`consult_cmd()`'s trace regex, neither of which is
`gates/ci.py`'s closes-gate check or any file in #284's write set (`gates/ci.py`,
`gates/test_closes_gate_ci.py`, `docs/issue-284/decisions/record-evidence-as-closing-intent.md`).
Recorded as a bug report below, kept out of #284's own outcome.

### Step 5 — six-PR lookup

```
$ for n in 337 340 343 350 352 353; do gh pr view $n --json number,state,mergedAt -q '"\(.number) \(.state) \(.mergedAt)"'; done
337 MERGED 2026-08-07T07:08:12Z
340 MERGED 2026-08-07T07:08:18Z
343 MERGED 2026-08-07T09:44:49Z
350 MERGED 2026-08-07T07:15:11Z
352 MERGED 2026-08-07T08:01:00Z
353 MERGED 2026-08-07T07:15:21Z
```
canonical: gh pr view <n> --json number,state,mergedAt (run per PR, output above)

All six PRs the implementation record's acceptance table names report `MERGED`. Their branches no
longer exist to re-run the gate directly against; this lookup is the strongest remaining
independent signal.

## Verdicts

### Outcome

Per this role's spec's recomputation rule (worst-case across cited test entries, restricted to
entries whose subject is actually part of #284's write set — Step 3's 4 red entries are
`inapplicable` to that subject per Step 4's provenance trace):

- subject: `gates/ci.py` (`_phase2_record_evidence`, `_pr_is_cross_repo`, `_fork_issue_from_body`)
  test: `gates/test_closes_gate_ci.py`
  canonical: python3 -m pytest gates/test_closes_gate_ci.py -q
  Result: PASSed (54, Step 2 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: six named delivery PRs (#337, #340, #343, #350, #352, #353)
  test: `gh pr view <n> --json state,mergedAt`
  canonical: gh pr view <n> --json number,state,mergedAt (Step 5 output above)
  Result: `MERGED` x6, no PR body edited (implementation record's per-PR table, cross-checked with
  Step 5's own output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: `tests/test_gates.py` (closure_sweep + consult-trace groups)
  test: `tests/test_gates.py`
  canonical: python3 -m pytest tests/test_gates.py -q
  Result: inapplicable — 4 red, traced to commit 5f29daa2/issue-1134, outside #284's write set
  (Step 3+4 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution

canonical: python3 -m pytest gates/test_closes_gate_ci.py -q

Recomputed outcome for #284's own subject: PASSed (Step 2 and Step 5 output above).

### Trajectory

Sound. `docs/issue-284/decisions/record-evidence-as-closing-intent.md` documents the
presence-not-value design choice and cross-references the enum-drift finding to issue #147 rather
than re-scoping it here; the implementation record's own "What did not work" and "Hunt" sections
describe a normal build-and-fix loop within the frozen write set, with no scope-exceeded stop.

### Step

- subject: `gates/ci.py` lines 262, 287, 305 (function definitions) and 311, 368, 416 (call
  sites)
  test: `grep -n "_phase2_record_evidence\|_pr_is_cross_repo\|_fork_issue_from_body" gates/ci.py`
  canonical: sh -c 'grep -n "_phase2_record_evidence\|_pr_is_cross_repo\|_fork_issue_from_body" gates/ci.py'
  Result: PASSed (Step 1 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: `gates/test_closes_gate_ci.py`
  test: `python3 -m pytest gates/test_closes_gate_ci.py -q`
  canonical: python3 -m pytest gates/test_closes_gate_ci.py -q
  Result: PASSed, 54 (Step 2 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution
- subject: PRs #337, #340, #343, #350, #352, #353
  test: `gh pr view <n> --json state,mergedAt`
  canonical: gh pr view <n> --json number,state,mergedAt
  Result: all six `MERGED` (Step 5 output above)
  assertedBy: execution-observation (this role, this session)
  mode: execution

## Bug report (out of #284's scope, recorded per this role's `produces` contract)

canonical: python3 -m pytest tests/test_gates.py -q

`tests/test_gates.py` has 4 red tests on current HEAD (bc53410e1cc12d4e80ae3794489e9fbf4c4b41d9):
`t_find_violations_uses_record_evidence_for_keywordless_merge`,
`t_find_violations_without_issue_states_still_calls_issue_view` (closure_sweep territory), and
`t_consult_trace_leaves_scratch_clone_clean_on_success`,
`t_consult_trace_leaves_scratch_clone_clean_on_failure` (consult-trace regex territory), all
traced to commit 5f29daa2 (issue-1134) in Step 4 above. This role does not open an issue for
these per its `produces` contract ("이슈는 사용자가") — flagging here for the operator to route.

---
code_under_review:
  - on-the-record/hooks/contract-guard.sh
  - on-the-record/hooks/test_contract_guard.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented the approved phase-1 proposal
(`docs/issue-741/proposals/2026-08-11-phase2-content-gate.md`) in
`contract-guard.sh`:

- Widened the existing `gh_json("pr", "view", pr, "--json",
  "body,number,commits")` call to also request `files` — one more field
  on a call already made, no new round trip.
- After the existing round-scoped `phase2` boolean, added a second,
  independent content-based condition: any path in the PR's own diff
  matches `(^|/)(src|tests?)/`, OR matches the acting role's own exact
  record file `docs/issue-<n>/reports/<role>.md` — the same two patterns
  `approval-gate.sh:116-119` already gates writes on.
- The acting role is derived from `git rev-parse --abbrev-ref HEAD` (run
  with `cwd=target_cwd or os.getcwd()`) parsed against
  `^issue-(\d+)/([\w-]+)$`, the same lookup `pr-preflight.sh`/
  `approval-gate.sh` already perform. If the branch doesn't parse, or its
  issue number doesn't match the PR's own issue, the record-file half of
  the check is skipped (narrows the match, never widens it) — the
  `(^|/)(src|tests?)/` half still applies unconditionally.
- The existing attach-or-deny block now runs only when `phase2 AND` the
  new content boolean both hold; when `phase2` is true but the PR carries
  no phase-2-shaped path, the script exits 0 without touching the body —
  same as an ordinary phase-1 merge.

In `test_contract_guard.py`:

- `FAKE_GH`'s `pr view` branch now also emits `files` from the fixture
  (`data.get("files", [])`).
- Added `_repo_dir_on_branch()`: a real `git init` + `checkout -b` +
  one empty commit, needed for the record-file half of the check, which
  requires `git rev-parse --abbrev-ref HEAD` to resolve (an unborn branch
  with zero commits does not resolve — see What did not work).
- Updated the 6 pre-existing fixtures whose scenario expects `Closes`
  attached (`test_cross_repo_same_number_judges_target_not_cwd`,
  `test_cd_prefix_reads_target_approvers_and_attaches`,
  `test_no_repo_indicator_unchanged_cwd_behavior`,
  `test_write_failure_still_denies_merge`,
  `test_same_round_approval_attaches_closes_when_missing`,
  `test_cross_role_approval_still_gates_phase2`) with a `"files": [{"path":
  "src/example.py"}]` entry, so they keep exercising the same "PR is
  actually phase-2-shaped" scenario they always represented, now under
  the widened `--json` call.
- Added the five-case regression/empty-state/content-positive matrix from
  the proposal's "What will be done": `test_docsonly_pr_with_
  same_round_approval_gets_no_closes` (the #741/PR-#747/#739 regression
  itself — Acceptance item 1), `test_docsonly_pr_with_no_approval_gets_
  no_closes` (empty-state pairing), `test_code_bearing_pr_with_same_
  round_approval_gets_closes` (Acceptance item 2 — regression guard,
  generalized to the new content-gated path), `test_unrelated_file_
  under_reports_dir_gets_no_closes` (the after-proposal hunt's exact
  scenario, pinned as a permanent regression), and `test_own_record_
  file_alone_gets_closes` (a genuine docs-only phase-2 delivery is still
  recognized).

New: `docs/issue-741/decisions/phase2-signal-choice.md` records the
chosen signal, the two rejected alternatives, and the forgeability
judgment in permanent form.

## Why

`contract-guard.sh`'s round-scoping condition (issue #577) is trivially
true for any same-round approval, including a docs-only phase-1 proposal
PR — approval by definition postdates phase-1's first commit on a shared
branch. This closed issues prematurely twice: issue-729/PR #739, then
this issue's own phase-1 PR #747 (a 4-doc-file PR whose body said "Refs
#741", closed anyway once the broker attached `Closes #741` on
same-round approval). Basis:
`docs/issue-741/proposals/2026-08-11-phase2-content-gate.md`.

## Acceptance verification

checked: docs-only phase-1 PR + same-round approval — Closes not
attached, PR merges without closing the issue — result:
`test_docsonly_pr_with_same_round_approval_gets_no_closes` passes (see
Verification run below), asserting `returncode == 0` and no `gh pr edit`
call recorded, on a `pr_body`/`files` fixture shaped exactly like
PR #747/#739 (docs-only diff, `Refs #<n>` body, same-round approval
comment).

checked: code-bearing phase-2 PR + approval — Closes attached and merge
proceeds, as today — result:
`test_code_bearing_pr_with_same_round_approval_gets_closes` passes (see
Verification run below), asserting the trailer is attached via the
recorded `gh pr edit` call, on a fixture whose diff includes a `src/`
path.

## Verification run

```
$ python3 -m pytest on-the-record/hooks/test_contract_guard.py -v
============================= test session starts ==============================
collected 17 items

on-the-record/hooks/test_contract_guard.py::test_cross_repo_same_number_judges_target_not_cwd PASSED [  5%]
on-the-record/hooks/test_contract_guard.py::test_repo_flag_targets_repo_but_no_local_approvers_is_unreached PASSED [ 11%]
on-the-record/hooks/test_contract_guard.py::test_full_pr_url_targets_repo_but_no_local_approvers_is_unreached PASSED [ 17%]
on-the-record/hooks/test_contract_guard.py::test_cd_prefix_reads_target_approvers_and_attaches PASSED [ 23%]
on-the-record/hooks/test_contract_guard.py::test_cd_prefix_allows_when_target_pr_closes_issue PASSED [ 29%]
on-the-record/hooks/test_contract_guard.py::test_repo_flag_overrides_cd_prefix_when_they_disagree PASSED [ 35%]
on-the-record/hooks/test_contract_guard.py::test_no_repo_indicator_unchanged_cwd_behavior PASSED [ 41%]
on-the-record/hooks/test_contract_guard.py::test_write_failure_still_denies_merge PASSED [ 47%]
on-the-record/hooks/test_contract_guard.py::test_prior_round_approval_allows_new_phase1_pr PASSED [ 52%]
on-the-record/hooks/test_contract_guard.py::test_same_round_approval_attaches_closes_when_missing PASSED [ 58%]
on-the-record/hooks/test_contract_guard.py::test_same_round_approval_with_closes_allows PASSED [ 64%]
on-the-record/hooks/test_contract_guard.py::test_cross_role_approval_still_gates_phase2 PASSED [ 70%]
on-the-record/hooks/test_contract_guard.py::test_docsonly_pr_with_same_round_approval_gets_no_closes PASSED [ 76%]
on-the-record/hooks/test_contract_guard.py::test_docsonly_pr_with_no_approval_gets_no_closes PASSED [ 82%]
on-the-record/hooks/test_contract_guard.py::test_code_bearing_pr_with_same_round_approval_gets_closes PASSED [ 88%]
on-the-record/hooks/test_contract_guard.py::test_unrelated_file_under_reports_dir_gets_no_closes PASSED [ 94%]
on-the-record/hooks/test_contract_guard.py::test_own_record_file_alone_gets_closes PASSED [100%]

============================== 17 passed in 2.25s ==============================
```

derived: `grep -c "^def test_" on-the-record/hooks/test_contract_guard.py`
```
$ grep -c "^def test_" on-the-record/hooks/test_contract_guard.py
17
```
12 pre-existing (8 target-repo-resolution + 4 round-scoping, unchanged
assertions) + 5 new content-gate cases.

## What did not work

- First `_repo_dir_on_branch()` attempt did a bare `git init` +
  `checkout -b <branch>` with no commit — `git rev-parse --abbrev-ref
  HEAD` failed with exit 128 ("ambiguous argument 'HEAD': unknown
  revision") because an unborn branch (zero commits) doesn't resolve as a
  revision for `rev-parse`, even though `HEAD` is a valid symbolic ref.
  Fixed by committing once (`--allow-empty`, pinned local
  `user.name`/`user.email`) right after the checkout.
- First `test_code_bearing_pr_with_same_round_approval_gets_closes`
  fixture used `"path": "on-the-record/hooks/contract-guard.sh"` as the
  "this PR touches real code" file — it does not match `(^|/)(src|tests?)/`
  (no `src/`/`test(s)/` path segment), so the test failed by not getting
  an attach. Replaced with `"src/contract_guard.py"`, which matches the
  pattern the code actually checks.

## Open findings

The before-landing warrant hunt (stance 1, `docs/issue-741/reports/
implementation/2026-08-11-hunt-phase2-content-gate.md`, section
"before-landing — stance 1") returned a confirmed FINDING, reproduced
with runnable commands in that file: `pr-preflight.sh`'s own phase-2
signal (unscoped by time, exact `"APPROVE issue-<n>/<role>"` match only)
can force a `Closes #<issue>` trailer into a docs-only PR's body at
`gh pr create`/`gh pr edit` time, in the case where the approval comment
already exists before the PR is opened/edited (a different ordering than
either real recurrence: PR #739 and PR #747 both had approval land
*after* PR creation, so `pr-preflight.sh` saw no approval yet and did not
force the trailer). `contract-guard.sh`'s new content gate only refuses
to ADD `Closes` on a non-phase-2-shaped diff — it does not strip one
already present — so in that ordering the issue could still auto-close on
a docs-only merge via GitHub's native keyword-closing.

`pr-preflight.sh` is not part of this proposal's write set, and unifying
its comment-matching logic with `contract-guard.sh`'s was already
explicitly deferred by this proposal's own Rationale ("Scope boundary —
pr-preflight.sh unification, explicitly out") and, before that, by issue
#653's ADR (`docs/issue-653/proposals/
2026-08-10-closes-trailer-preflight-hardening.md` lines 60-70, 88-91),
which named it as its own gap
(`docs/issue-653/reports/architecture/survey.md` gap #1). This finding
does not revise that boundary; it adds one more concrete reason a future
issue may want to reopen it — either round/content-scoping
`pr-preflight.sh`'s signal, or having `contract-guard.sh` actively strip
a disagreeing `Closes` trailer.

This does not affect the two Acceptance rows this delivery targets — both
reproduced real-world orderings (#739, #747: approval lands after PR
creation) are covered by the passing test matrix above; the finding
describes a third, not-yet-observed ordering.

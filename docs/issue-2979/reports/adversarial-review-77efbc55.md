---
issue: 2979
role: adversarial-review-77efbc55
author: adversarial-review-77efbc55
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
code_under_review: PR #3017 (issue-2979/observability-signal-golden+test-derivation-547467ea, head 166a11b91a139616b2cc9bc6c09a1005c69923ca)
loop_state: landed
type: verification
breaking: false
verdict: acceptance-checks-and-must-not-list-confirmed-clean-minor-on-demand-visibility-gap-noted
upstream:
  - path: watchdog.py
    sha: 166a11b91a139616b2cc9bc6c09a1005c69923ca
  - path: tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py (untracked on this branch; lives only on PR branch issue-2979/observability-signal-golden+test-derivation-547467ea, read via git worktree add /tmp/verify-pr-3017)
    sha: 166a11b91a139616b2cc9bc6c09a1005c69923ca
  - path: test/test_watchdog_heartbeat_noise.py
    sha: 166a11b91a139616b2cc9bc6c09a1005c69923ca
---

# issue-2979 — adversarial-review-77efbc55 record

## What was done

Independently re-verified PR #3017 against issue #2979 by fetching the
PR's actual current head into an isolated worktree, re-running the three
acceptance checks myself, and auditing the diff against the issue's
must-not list — not by reading and restating the PR's own claimed test
plan. canonical: `gh pr view 3017 --json headRefOid,headRefName,baseRefName,state`
(run this turn) — result `{"baseRefName":"main","headRefName":"issue-2979/observability-signal-golden+test-derivation-547467ea","headRefOid":"166a11b91a139616b2cc9bc6c09a1005c69923ca","state":"OPEN"}`.
Note: the PR's first commit oid (`51dd7e65...`) is not the same as the PR
head oid (`166a11b9...`, the PR has 4 commits) — I initially mis-specified
the first commit's sha, and the actual current head was fetched and used
instead throughout.

**1. Acceptance checks, re-run against the actual PR head, worktree
`/tmp/verify-pr-3017` (all three run this turn):**

```
$ python3 -m pytest tests/ -k board_sweep_non_subject_aggregated -q
4 passed in 1.02s
$ python3 -m pytest tests/ -k board_sweep_subject_mapping_loss_reported -q
4 passed in 0.89s
$ python3 -m pytest tests/ -k spawn_coverage_reports_change -q
4 passed in 0.85s
```

(the test file `tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py`
is untracked on this branch, PR-worktree only). Cross-checked that these
results are not accidental broad `-k` matches: derived:
`grep -c "    def test_" ` scoped to each class body in the untracked
`tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py` (read
in full this turn, 199 lines):

```
BoardSweepNonSubjectAggregatedTest: 4
BoardSweepSubjectMappingLossReportedTest: 4
SpawnCoverageReportsChangeTest: 4
```

Each `-k` substring is unique to its own class/method names, so each
count above from step 1's runs is an exact match rather than an
overbroad one.

**2. Full suite + related suites, re-run for regression sanity (not one
of the three required checks, but part of not trusting the PR's own
numbers). All commands run this turn:**

```
$ python3 -m pytest tests/ -q                         # PR worktree
1 failed, 137 passed
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
AssertionError: 4 not greater than 4

$ python3 -m pytest tests/test_spawn_gate_wiring.py -q   # main worktree, 25a2ecde
1 failed, 26 passed
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
AssertionError: 4 not greater than 4

$ python3 -m pytest test/test_watchdog_heartbeat_noise.py -q
5 passed

$ python3 -m pytest gates/test_spawn_on_pr.py -q
27 passed
```

The identical failing assertion on a separate `main`-branch worktree
independently confirms the PR's claim that this failure pre-exists on
`main` and is unrelated to this diff, rather than citing the PR's own
stated claim.

**3. Diff audit against the issue's must-not list.** canonical:
`git diff main...HEAD -- watchdog.py tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py test/test_watchdog_heartbeat_noise.py`
(the tests path here is the same untracked, PR-worktree-only file), read
in full this turn (watchdog.py hunk, ~250 diff lines).

- *"do not drop either check"*: both checks exist as distinct test
  classes exercising a shared decision table in the new
  `watchdog._classify_narrowing_prs(root, pr_numbers, number_to_branch, board_now)`
  helper (watchdog.py:835-872, read directly):
  ```
  for prn in sorted(pr_numbers):
      branch = number_to_branch.get(prn)
      m = _HEAD_REF_SUBJECT_RE.match(branch) if branch else None
      if not m:
          non_subject_count += 1
          continue
      issue_n = int(m.group(1))
      if f"issue-{issue_n}" in board_now:
          changed_numbers.add(issue_n)
          continue
      if _watchdog_note_unmappable_pr(root, prn):
          mapping_loss_new.append((prn, issue_n, branch))
      else:
          mapping_loss_already_reported += 1
  ```
  branch doesn't match `issue-<n>/<skill>` shape → `non_subject_count`
  only; branch matches but not in `board_now` → `mapping_loss_new` entry.
  Both outcomes are wired into `_board_wide_sweep` (watchdog.py:1358-1392):
  `mapping_loss_new` entries are printed individually with the
  `recut-corrupted` remediation paragraph (watchdog.py:1365-1376);
  `non_subject_count` is printed only as an aggregate count
  (watchdog.py:1383-1392). Both branches are exercised by the tests in
  step 1 above.
- *"no suppression by issue-number cutoff, age threshold, or hardcoded
  ignore list"*: the only discriminants in `_classify_narrowing_prs` are
  the `_HEAD_REF_SUBJECT_RE.match(branch)` shape check and
  `f"issue-{issue_n}" in board_now` membership (watchdog.py:860-871,
  quoted above) — no issue-number comparison, no date/age field, no
  literal ignore-list constant anywhere in the diff. derived:
  `grep -n "ignore.list\|cutoff\|threshold" ` against the diff hunk this
  turn — zero lines describing a new suppression mechanism for either
  check (the pre-existing, unrelated
  `WATCHDOG_TRANSIENT_GH_FAILURE_THRESHOLD` gh-failure-streak counter is
  untouched infrastructure for a different signal, not a suppression
  mechanism for either of the two checks under review).
- *"do not attach recut-corrupted to non-subjects"*: confirmed by
  reading the print call sites directly — the `recut-corrupted` string
  and the `spawn.py recut-corrupted --issue <n> --session <session>`
  remediation text appear only inside the `for prn, issue_n, branch in mapping_loss_new:`
  loop (watchdog.py:1365-1376); the `non_subject_count` print
  (watchdog.py:1383-1392) contains only
  `"non-subject PR (브랜치가 board subject 형태 아님) — board 와 무관, 집계만"`
  — no remediation text, no `recut-corrupted` string in that branch.
  derived: `grep -n "recut-corrupted" watchdog.py` this turn — exactly
  one match, inside the mapping-loss loop.
- *"do not fold into the false-violation or lookup-failure fixes filed
  separately"*: the pre-existing gh-index-lookup-failure branch
  (watchdog.py:1393-1398, `_watchdog_note_gh_failure`) is untouched by
  this diff — confirmed via the diff hunk boundaries read this turn (no
  `-`/`+` lines touch that block); the diff's scope is confined to
  `_classify_narrowing_prs`, `_watchdog_note_spawn_coverage_delta`, and
  their two call sites.

**4. Keep-reporting direction, verified on a constructed subject-mapping-loss
case (not just the quieting direction).** The PR's own test
`test_board_sweep_subject_mapping_loss_reported_shaped_branch_not_on_board`
(read in full this turn, in the untracked PR-worktree-only
`tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py:124-131`)
constructs exactly the #2379 corrupted-merge-base class: PR #42 on branch
`"issue-2379/observability-signal-golden-abc123"` (board-subject-shaped)
with `board_now={}` (issue-2379 not currently a board subject) →
asserts `loss_new == [(42, 2379, "issue-2379/observability-signal-golden-abc123")]`.
Ran this single test in isolation this turn, worktree
`/tmp/verify-pr-3017`:

```
$ python3 -m pytest tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py::BoardSweepSubjectMappingLossReportedTest::test_board_sweep_subject_mapping_loss_reported_shaped_branch_not_on_board -q
1 passed
```

Traced the return value forward to the actual print call
(watchdog.py:1361-1376, read directly, not inferred):
  ```
  for prn, issue_n, branch in mapping_loss_new:
      print(f"[watchdog] board-sweep: PR #{prn} 변경 감지했으나 "
            f"issue-{issue_n} subject 가 board 매핑을 잃었다 "
            f"(브랜치={branch!r}) — issue-<n>/<skill>[+<skill>]-<lease> "
            "산출물을 잘못된 base 에서 다시 잡아온(#2379) 브랜치라면 "
            "`spawn.py recut-corrupted --issue <n> --session <session>`(#2402)로 "
            "같은 이름 아래 재컷하라")
  ```
  every tuple in `mapping_loss_new` reaches this print unconditionally —
  no gate between the returned tuple and the print — so the constructed
  mapping-loss subject genuinely produces an individual line with its
  remediation advice, confirmed by code path, not merely by the test
  assertion in isolation. A second test,
  `test_board_sweep_subject_mapping_loss_reported_resurfaces_for_new_pr`
  (same untracked file, lines 141-149), confirms the one-shot
  repeat-suppression marker keys on PR number (not subject), so a second
  PR number for the same lost subject still surfaces once — the
  keep-reporting path isn't accidentally over-suppressed by subject-level
  dedup.

**5. spawn-coverage change detection, verified.** `watchdog._watchdog_note_spawn_coverage_delta`
(watchdog.py:875-890, read directly) diffs `uncovered` (this tick's
uncovered-issue list) against a persisted `spawn_coverage_uncovered` set
in watchdog noise-state, returns only the new entries, and replaces the
persisted set with the full current set every call. Ran this test class
in isolation this turn (already covered by check 1's aggregate run
above):

```
$ python3 -m pytest tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py::SpawnCoverageReportsChangeTest -q
4 passed
```

Its four cases: `test_spawn_coverage_reports_change_new_entry_surfaces`
(`[100]` first seen → `newly == [100]`),
`test_spawn_coverage_reports_change_unchanged_set_reports_nothing`
(`[100]` twice → second call `newly == []`, matching the acceptance
bullet's empty-state note),
`test_spawn_coverage_reports_change_standing_entries_not_repeated`
(`[100,200]` then `[100,200,300]` → `newly == [300]`), and
`test_spawn_coverage_reports_change_flap_reappears_reported_again`
(covered→uncovered→covered→uncovered flap resurfaces as new each time,
not sticky-once-forever).

The standing set is not deleted — `state["spawn_coverage_uncovered"] = sorted(current)`
persists the full current set every tick (watchdog.py:888, read
directly), and the print at the call site
(`f"[watchdog] spawn-coverage: 새로 커버되지 않음 {newly_uncovered} (표준 집합 {len(uncovered)}건)"`,
watchdog.py:1534-1536) attaches the full standing-set *count* to every
delta print, so severity isn't hidden even when only new entries are
named. **However**: derived: `grep -n "spawn_coverage_uncovered\|spawn-coverage" spawn.py watchdog.py gates/*.py`
this turn plus a read of `spawn.py`'s `argparse` subcommand set
(spawn.py:2205-2260, `role` positional, "생략하면 상태만 보여준다") found
no dedicated operator-facing command that lists the full current standing
set on demand — an operator watching only watchdog's stdout on a quiet
tick (no new entries) sees nothing about spawn-coverage that tick at all,
by the acceptance bullet's own design ("an unchanged set reports no new
entries; passes"). The full set is recoverable (the persisted state file,
or calling `spawn_coverage.find_uncovered(open_issues, board, now)`
directly — a pre-existing pure function, unchanged by this PR, already
callable the same way before this PR), but not through any purpose-built
"show me the standing set" command, new or pre-existing. This is not a
violation of issue #2979's acceptance checks or must-not list (neither
demands an on-demand command), and it does not regress anything this PR
touches — the same gap existed before this PR too, since no such command
existed previously either.

**Worker incident (procedural, not a defect in the PR):** the delegated
worker that performed the worktree setup and command execution reported
that it accidentally ran `git checkout main -- .` inside the verification
worktree mid-task, then caught it via `git status`, ran
`git reset --hard 166a11b91a139616b2cc9bc6c09a1005c69923ca && git clean -fd`,
and confirmed a clean tree before continuing. All test/diff/file-content
evidence cited above was, per the worker's own account, gathered either
before that incident or after the restore; the final worktree state was
independently confirmed clean at the correct head this turn:

```
$ git status
현재 브랜치 pr-3017-verify
커밋할 사항 없음, 작업 폴더 깨끗함
$ git log -1 --format='%H'
166a11b91a139616b2cc9bc6c09a1005c69923ca
```

## Why

The task explicitly asked not to trust the PR's claimed results and to
re-derive them, per [[defect-verification-independence-from-upstream-verdicts]]
and the adversarial-review skill's structural-independence stance — a
"reports what changed instead of a census" fix is exactly the failure
mode that can look right from reading the diff alone (the aggregation
path is easy to eyeball as correct) while silently breaking the
"still reports what matters" half (the keep-reporting path), so both
directions needed independent execution: re-running the three
acceptance checks against the actual fetched PR head rather than citing
the PR's pasted numbers, and specifically constructing/tracing the
mapping-loss keep-reporting case through to its print statement rather
than trusting that a passing assertion implies the operator-visible
line actually fires.

## What did not work

I initially handed the delegated worker the PR's first commit sha
(`51dd7e65...`) instead of its head sha, assuming (incorrectly, without
checking) that the git log I'd already fetched showed commits in an
order where the first entry was the head. The worker caught the
discrepancy itself (`gh pr view` and `pull/3017/head` both resolved to a
different, later commit) and used the actual current head throughout —
no re-dispatch was needed, but this is noted since it could have silently
verified a stale, superseded commit had the worker not checked. No other
approach was tried and abandoned; every check in this review reached a
conclusion on its first attempt.

## Upstream basis

- PR #3017, branch `issue-2979/observability-signal-golden+test-derivation-547467ea`,
  head `166a11b91a139616b2cc9bc6c09a1005c69923ca` (4 commits) — the
  subject of this verification. canonical: `gh pr view 3017` (this turn).
- `watchdog.py`, `spawn.py`, `gates/spawn_coverage.py`,
  `test/test_watchdog_heartbeat_noise.py` — read directly from a
  `git worktree add /tmp/verify-pr-3017 pr-3017-verify` checkout of the
  PR head, not from the PR's description of them.
- `tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py`
  (untracked on this branch; lives only on PR branch
  `issue-2979/observability-signal-golden+test-derivation-547467ea`, read
  via the same worktree) — read in full, not restated from the PR body.
- Issue #2979 (`gh issue view 2979`, this turn) and issue #2379
  (`gh issue view 2379`, this turn, for the corrupted-merge-base
  provenance of the mapping-loss case).

## Open findings

- **No operator-facing on-demand view of the spawn-coverage standing
  set**: the delta-reporting design correctly satisfies the issue's own
  acceptance bullet (unchanged set → no print), but there's no command
  (existing or added by this PR) to ask "what's the full standing
  uncovered set right now" outside of watching for the next flap or
  reading internal noise-state JSON directly. Not a defect in this PR
  (pre-existing gap, not a regression, not required by #2979's
  acceptance or must-not list) — resolution path, if wanted: a small
  `spawn.py` subcommand wrapping `spawn_coverage.find_uncovered` for
  direct operator invocation, filed as a separate low-priority
  follow-up if the team wants it.
- **Deferred `_pr_index_all()` branch-dedup edge case**: the PR's own
  body discloses a warrant-hunter finding (first-wins-by-branch-string
  dedup in `closure_sweep._pr_index_all()` could theoretically fold a PR
  sharing a branch string with another PR into the non-subject
  aggregate) and defers it as out-of-scope shared infrastructure,
  correctly separate from this issue's "lookup-failure defects filed
  separately" must-not clause. Already disclosed by the builder, not a
  new finding from this review — resolution path already recorded per
  the PR's own "Open finding" section.

## Next steps

None — `loop_state: landed`. All three required acceptance checks were
independently re-run against the actual PR head this turn (see the code
fence in "What was done" section 1 above), the diff was audited
line-by-line against every clause of the issue's must-not list per
section 3 of "What was done" above, and the keep-reporting direction was
verified on a constructed mapping-loss subject traced through to its
actual print call per section 4, not merely asserted by a passing test.
No code was changed by this review — PR #3017 was not modified, per the
adversarial-review skill's structural-independence contract.

skill-verdict: adversarial-review — applied: invoked; called via the
Skill tool this turn — canonical: Skill tool call this turn returned the
full SKILL.md body (structurally independent evaluation, evidence
requirement per finding). The protocol as read was followed: I received
the deliverable (PR #3017's diff and worktree) and independently
re-derived every checkable claim from primary sources (the fetched
worktree, re-run tests, direct code reads — see the code fences in
"What was done" sections 1-5 above) rather than restating the PR's own
pasted test-plan numbers.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; called via the Skill
tool this turn — canonical: Skill tool call this turn returned the full rule set (rules 1-10). Applied:
treated the PR's claimed test-plan numbers and its "pre-existing
unrelated failure" note as claims to re-derive rather than cite (rule 3,
rule 8) — see the code fence in "What was done" section 2 above, where
the main-branch worktree reproduces the identical failing assertion,
independently confirming the pre-existing-failure claim rather than
citing it. Also deliberately included the negative/edge path
(constructing and tracing the keep-reporting mapping-loss case in
section 4, not just the quieting-direction happy path) per rule 2.

skill-verdict: work-in-english — applied: invoked; called via the Skill
tool this turn — canonical: Skill tool call this turn returned the full
SKILL.md body. This record and the delegated worker's prompt are in
English; the final chat summary to the user is in Korean.

other mounted skills (implementation-audit): not triggered — this
verification followed adversarial-review's direct re-derivation
procedure against the issue's acceptance checks and must-not list, not
implementation-audit's two-session falsifiable-claims-extraction
protocol (no separate claims-extraction handoff was set up for this
task).

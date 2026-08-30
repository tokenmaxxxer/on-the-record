---
issue: 2894
role: adversarial-review-3fb40e3e
author: adversarial-review-3fb40e3e
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: done
upstream:
  - path: roster.py
    sha: 6bf67b9836df94fb85a9452abca53e5da28d3b1d
  - path: spawn.py
    sha: 6bf67b9836df94fb85a9452abca53e5da28d3b1d
  - path: watchdog.py
    sha: 6bf67b9836df94fb85a9452abca53e5da28d3b1d
  - path: gates/gh_rest.py
    sha: 6bf67b9836df94fb85a9452abca53e5da28d3b1d
---

# issue-2894 — adversarial-review-3fb40e3e record

## What was done

Independent adversarial verification of PR #2896 (commit
`6bf67b9836df94fb85a9452abca53e5da28d3b1d`, branch
`issue-2894/silent-failure-audit-0c41a52b`, OPEN/unmerged at review
time), which adds `spawn._attempt_issue_closed()` as a third fallback in
the spawn-attempt halt resolve pipeline. Nothing below was copied from
PR #2896's own body/commit message/record — every claim was re-read from
the diff and re-run live against a worktree of the PR's head commit
(`git worktree add /tmp/pr2896-wt <pr-head>`, since removed) and against
this branch (`origin/main` tip) for comparison.

derived: `gh pr diff 2896` (read this session) — root-cause chain,
re-derived directly from source, not from the PR's own description:

```
spawn.py:1236-1245  _HALT_CLASS_PATTERNS (5 regexes: requirement-tag,
                     acceptance-format, enospc, workspace-origin-mismatch,
                     cwd-invalid)
spawn.py:1247-1256  _classify_halt_reason() falls through to "unknown"
                     when no pattern matches -- the issue's own
                     "skill X not found" examples match none of the five
spawn.py:1369       return False  # unknown class  <- last line of
                     _halt_condition_cleared(): class-recheck structurally
                     can never clear an "unknown" halt
spawn.py:1427-1457  _attempt_superseded(): loops attempts.items() for a
                     LATER attempt on the same (issue, skill-family) with
                     a "session-log" outcome -- can only return True if
                     such a later attempt was ever recorded; a closed
                     issue never gets a future spawn attempt appended, so
                     this loop finds nothing, now or ever
roster.py:669-686   three sequential "if not cleared and ..." checks:
                     class-recheck (669), supersession (671), then the
                     new _attempt_issue_closed(a) (679-685) -- the only
                     change to this function's control flow
```

derived: `gh issue view 614 --json state -q .state` / `gh issue view
488 --json state -q .state` / `gh issue view 489 --json state -q
.state` / `gh issue view 645 --json state -q .state` — the exact
command `_attempt_issue_closed()` runs, against the exact four issue
numbers issue #2894 names — result:

```
614 -> MERGED
488 -> CLOSED
489 -> MERGED
645 -> CLOSED
```

derived: `gh api repos/tokenmaxxxer/on-the-record/issues/614 --jq
'{pull_request,state}'` (and the same for 488/489/645) — result:

```
614: {"pull_request":true,"state":"closed"}   <- a merged PR, not an Issue
488: {"pull_request":false,"state":"closed"}
489: {"pull_request":true,"state":"closed"}   <- a merged PR, not an Issue
645: {"pull_request":false,"state":"closed"}
```

`_attempt_issue_closed()`'s check is `r.stdout.strip().upper() ==
"CLOSED"` (exact match) — the `MERGED` answer fails that comparison. To
confirm this actually changes sweep output rather than being a
theoretical mismatch, a scratch `spawn-attempts.jsonl` was built (four
halts shaped like the issue's own four example lines, `cwd` set to a
real git repo with
`origin=https://github.com/tokenmaxxxer/on-the-record.git` so `gh`
could resolve repo context) and run through `roster.spawn_attempt_sweep()`
from the PR worktree with the real, unmocked `gh` binary. derived:
`python3 -c "..."` harness invoking `roster.spawn_attempt_sweep()`
directly, run this session — result:

```
BEFORE (fallback patched to always return False, i.e. pre-fix shape):
  emitted live-halt lines: 4  (614, 488, 489, 645)

AFTER (fallback active, real gh, real issue numbers, next tick):
  issue-488: halt RESOLVED (resolution=issue-closed)
  issue-645: halt RESOLVED (resolution=issue-closed)
  issue-489: spawn halted pre-workspace ... (STILL REPLAYING)
  issue-614: spawn halted pre-workspace ... (STILL REPLAYING)
  emitted live-halt lines: 2

Following tick: same 2 lines (489, 614) replay again, unchanged.
```

Before/after halt-line count pair for the four halts issue #2894 names:
**4 -> 2**, not 4 -> 0. Two of the four (614, 489) do not resolve
against the real repo state, because `gh issue view` answers `MERGED`
for a number that now belongs to a merged PR, and the exact-match
`== "CLOSED"` rejects that answer.

derived: `python3 -c "..."` harness, continued, same session — signal-
loss check and new-failure-still-reports check:

```
attempt_id format (from this repo's own fixtures, e.g.
test/test_spawn_attempt_staleness.py): "<issue>:<skill>-<hex>:1:1" --
one ledger entry per spawn attempt, keyed by attempt_id. Resolving one
attempt_id's halt cannot affect any other attempt_id's entry.

New halt appended: issue=2894 (a real, currently OPEN issue), skill
"brandnew-eeeeeeee", reason "skill brandnew not found" (an unknown-class
shape distinct from all four issue-2894 examples).
roster.spawn_attempt_sweep() output:
  [spawn-attempt] issue-2894/brandnew-eeeeeeee: spawn halted
  pre-workspace ...: skill brandnew not found
  emitted live-halt lines: 1
```

The new failure reports normally, on an independent `attempt_id`,
unaffected by the four already-processed entries above — the signal a
future recurrence would carry is never attached to the OLD attempt_id
being resolved; it is carried by the new attempt's own new ledger
entry, which `_attempt_issue_closed()` never touches.

derived: `python3 -c "..."` harness calling `spawn._attempt_issue_closed()`
directly with constructed attempt dicts, from the PR worktree, this
session — result:

```
missing issue ({"cwd": "/tmp"})                          -> False
missing cwd ({"issue": 1})                                -> False
gone workspace ({"issue": 1, "cwd": "/does/not/exist..."}) -> False
gh non-zero exit (mock returncode=1)                       -> False
gh exception (mock side_effect=OSError)                     -> False
  (plus one stderr diagnostic line naming the exception type)
```

All five ambiguous-case paths return the conservative "still live"
`False`; none silently resolves.

canonical: `spawn.py`, body of `_attempt_issue_closed()` (read this
session, PR worktree) — the `subprocess.run(["gh", "issue", "view",
...])` call inside it carries no `timeout=` keyword argument anywhere
in the function. derived: `grep -n "subprocess.run\|timeout"
gates/gh_rest.py gates/acceptance_gate.py` (run this session, PR
worktree) — zero `timeout=` hits in either file, confirming the two
sibling gh-calling class-recheck paths (`requirement_linkage.check()`,
`acceptance_gate.check()`) are equally untimed — this PR extends an
existing codebase-wide gap rather than introducing a new pattern, but it
does add one more untimed network call to the heartbeat's hot path.

canonical: `gates/gh_rest.py:2-12` (read this session) — this helper
exists specifically because `gh issue view`/`gh pr view` consume a
GraphQL quota (5000/hour) shared across all issue/PR GraphQL calls, and
routes reads through `gh api` REST instead (separate quota pool). The
two sibling class-recheck paths already go through this helper;
`_attempt_issue_closed()` calls `gh issue view --json state` directly
instead, reintroducing the GraphQL call this helper was built to avoid,
on a call site proportional to the count of still-open halts per tick.

canonical: `spawn.py:1756-1759` (read this session, PR worktree) —
`_prune_spawn_attempts()`'s `elif outcome.get("outcome") == "halted":`
branch applies `SPAWN_ATTEMPTS_RETENTION_SEC` (7 days,
`spawn.py:1551`) to halted outcomes the same way the `session-log`
branch is treated — retention already covers halts, ruling out that
candidate cause.

canonical: `watchdog.py:1590,1597` and `roster.py:734` (read this
session, PR worktree) — `watchdog.py:1590` captures
`spawn_attempt_sweep()`'s own return value (reported-line count) into
`anomaly_count`; the comment at `watchdog.py:1597` refers to
`spawn_attempt_sweep()`'s internal, unconditional call to
`_prune_spawn_attempts(now=now)` at `roster.py:734`, whose return value
(pruned-line count) is discarded — pruning still runs every tick;
only an observability metric is lost. Neither candidate was the root
cause.

derived: `python3 gates/retirement_count.py` — run on the PR worktree
and on this branch (`origin/main` tip), this session — result:

```
PR worktree:   1136 matched lines
this branch:   1136 matched lines
diff of the two full outputs (line-number-stripped): empty
```

derived: `python3 -m pytest . -q` — run on the PR worktree and on this
branch, this session — result:

```
PR worktree:   17 failed, 659 passed, 3 xfailed
this branch:   17 failed, 651 passed, 3 xfailed
diff of sorted FAILED-line sets: empty (identical 17 names both sides)
passed-count delta: +8, exactly the new AttemptIssueClosedTest (6) +
  SpawnAttemptSweepIssueClosedTest (2) tests added by this PR
```

The 17 pre-existing failing test names (both branches, unaffected by
this PR — none touch `spawn.py`'s halt-resolve path, `roster.py`, or
`watchdog.py`'s sweep call sites) are listed verbatim in "Open findings"
item 5 below.

derived: `python3 -c "..."` timing harness, PR worktree, this session —
a single `unknown`-class halt (a shape that called `gh` zero times
pre-fix, since neither class-recheck nor supersession touches `gh` for
`unknown`), fallback disabled vs enabled, same ledger, same process —
result:

```
tick with fallback disabled (0 gh calls):  0.0003s
tick with fallback enabled (1 gh call):    0.4229s
```

The entire added cost is one `gh issue view` network round trip
(~0.42s), scaling with the count of concurrently unresolved halts in
the classes that previously never called `gh` (`unknown`, `enospc`,
`cwd-invalid`, `workspace-origin-mismatch`), until each resolves or ages
out of the 7-day retention window.

## Why

canonical: this session's own live `gh` calls and harness runs quoted
under "What was done" — the reason to re-run everything live rather
than reading PR #2896's own record is that its test harness and demo
both mock `gh` to return a clean `"CLOSED"`/`"OPEN"` answer, which
cannot expose the shape `gh issue view` actually returns for a number
that now belongs to a merged pull request rather than a closed issue.
That gap is only visible by invoking the real binary against the real
numbers the issue names, and it changes the outcome of the central
acceptance criterion (the four-halt before/after count), not just a
peripheral detail — which is why the check was worth re-running live
here instead of accepting the control-flow derivation (already
independently confirmed by source-reading) as sufficient on its own.

## What did not work

An initial before/after harness run used a scratch git repo with no
`origin` remote configured — `gh issue view` failed to resolve repo
context for all four entries (non-zero exit, conservative `False` from
every branch), producing a misleading "nothing resolves either way"
result that looked like a code defect but was a harness setup gap.
Fixed by running `git remote add origin
https://github.com/tokenmaxxxer/on-the-record.git` in the scratch repo
before re-running; the corrected run is what "What was done" reports.

## Upstream basis

- PR #2896, commit `6bf67b9836df94fb85a9452abca53e5da28d3b1d`
  (`roster.py` +7, `spawn.py` +53, `test/test_spawn_attempt_staleness.py`
  +127) — `gh pr view 2896`, `gh pr diff 2896`, read this session.
- `roster.py:613-734` (`spawn_attempt_sweep`, resolve loop and wiring).
- `spawn.py:1236-1369` (`_HALT_CLASS_PATTERNS`, `_classify_halt_reason`,
  `_halt_condition_cleared`), `spawn.py:1427-1457`
  (`_attempt_superseded`), `spawn.py:1460-1503` (new
  `_attempt_issue_closed`), `spawn.py:1551`
  (`SPAWN_ATTEMPTS_RETENTION_SEC`), `spawn.py:1652-1770`
  (`_prune_spawn_attempts`).
- `watchdog.py:1580-1599` (sweep call site).
- `gates/gh_rest.py:1-50`, `gates/acceptance_gate.py:207` (REST-vs-GraphQL
  convention).
- 6bf67b9836df94fb85a9452abca53e5da28d3b1d:spawn.py:1460 (new function,
  commit-pinned).
- PR #2896's own record, branch `issue-2894/silent-failure-audit-0c41a52b`
  (untracked/not present on this branch since PR #2896 is unmerged —
  read via `git show <pr-head-sha>:docs/issue-2894/reports/silent-failure-audit-0c41a52b.md`
  this session for orientation, not trusted as fact).
- Live `gh` calls against the real repo (commands quoted in "What was
  done" above).

## Open findings

1. Acceptance criterion 2 only half-satisfied against the real repo
   state. `_attempt_issue_closed()`'s exact match against `"CLOSED"`
   does not match `gh issue view`'s `MERGED` answer for a GitHub number
   that now belongs to a merged PR. derived: the before/after harness
   quoted above under "What was done" — before/after count is 4 -> 2,
   not 4 -> 0; issue-614 and issue-489 (two of the four halts issue
   #2894 names by number) keep replaying against the current, real
   state of this repo. Resolution path: needs a follow-up code change —
   accept `MERGED` too, or branch to `gh pr view` when the target is a
   PR rather than an Issue.
2. Missing `gh` subprocess timeout on the new call. Confirmed present
   as a gap, and confirmed (via the `gh_rest.py`/`acceptance_gate.py`
   grep above) to match a pre-existing, codebase-wide untimed pattern
   rather than a new one this PR introduces — extends the gap rather
   than creating it. Resolution path: add `timeout=` to this call and
   its untimed siblings in a follow-up, not blocking.
3. GraphQL quota reintroduction. The new function bypasses
   `gates/gh_rest.py`'s REST convention (built at issue #1569
   specifically to avoid `gh issue view`/`gh pr view`'s shared GraphQL
   quota) that its two sibling class-recheck paths already use.
   Resolution path: route through `gh_rest.py` in a follow-up; not
   exercised at scale in this session, so severity is structural
   (convention drift) rather than measured impact.
4. Signal-loss question — resolved, no code change needed. Confirmed by
   reading the `attempt_id` keying and the resolve loop, and
   live-demonstrated in "What was done": resolving one closed-issue
   halt cannot suppress detection of a future recurrence on a different
   issue, since each spawn attempt is its own independently-keyed
   ledger entry.
5. Test regression: none found. derived: `python3 -m pytest . -q`
   (quoted above) — identical 17-name failing set on the PR worktree
   and this branch:

   ```
   harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
   test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
   test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
   test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
   test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
   test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
   test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
   test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
   test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
   test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
   test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
   test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
   test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
   tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
   ```

6. Overhead: real, not provably unbounded at this session's scale.
   derived: the timing harness quoted above under "What was done" —
   ~0.42s added per still-unresolved, previously-gh-free-class halt per
   watchdog tick, scaling with the concurrently-unresolved population.

## Next steps

canonical: finding 1 above, grounded in the before/after harness quoted
under "What was done" (before/after count 4 -> 2 against the real repo
state) — this record's own status is terminal (see frontmatter
`loop_state`); no further action is expected from this record itself.
Finding 1 (the `MERGED`-vs-`CLOSED` gap, reproduced live against the
real four target halts) needs a follow-up code change in a new PR
against `spawn.py`'s `_attempt_issue_closed()`; making that change is
out of scope here, since this review is verification-only.

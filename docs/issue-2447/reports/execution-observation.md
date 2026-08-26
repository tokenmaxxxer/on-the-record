---
issue: 2447
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2447/reports/implementation.md
    sha: 46ee6b819adc76d975da31752c0dba5805b6da9f
  - path: lifecycle.py
    sha: 46ee6b819adc76d975da31752c0dba5805b6da9f
  - path: spawn.py
    sha: 46ee6b819adc76d975da31752c0dba5805b6da9f
subject: PR #2478 (issue-2447/implementation, head 46ee6b819adc76d975da31752c0dba5805b6da9f, base main)
test: issue #2447 Acceptance section — 5 check bullets
result: passed
assertedBy: execution-observation, independently re-run and independently re-fixtured this turn
---

# issue-2447 — execution-observation record

Path convention: every file cited below lives on `issue-2447/implementation`
at sha `46ee6b81` (checked out into an isolated worktree, `git worktree add
/tmp/otr-2447-eo 46ee6b81`, removed after use), not on this record's own
branch (`issue-2447/execution-observation`, based on `origin/main` — this
branch carries no code changes, only this record). A second worktree at
unmodified `origin/main` (`28c776d9`, also removed after use) was used only
for the pre-existing-failure cross-check quoted under "What was done"
below. Scratch verification scripts under `/tmp/otr-2447-eo-verify/` were
authored fresh this turn, distinct from the PR's own fixtures, and removed
after use.

## What was done

Independently re-derived all five `check` bullets of issue #2447's
Acceptance section against PR #2478, rather than citing the implementation
record's own claims.

**Existing targeted suite, re-run this turn, in the `46ee6b81` worktree:**

acceptance: `python3 -m pytest gates/test_clean_reconcile_safety.py tests/test_auto_sweep_nonblocking.py -q` — result:
```
17 passed, 1 xfailed in 1.26s
```
Matches the record's own claimed 17 passed, 1 xfailed.

**Code-path confirmation, read directly (not test-mediated).**

canonical: `46ee6b81:lifecycle.py:1014-1023`
```
candidates = []  # (mtime, size, path)
if wb.is_dir():
    for w in sorted(wb.glob("*")):
        if not (w / ".git").is_dir():
            continue
        reason, _detail = _sp._workspace_clean_state(w, live)
        if reason is not None:
            continue
        ...
        candidates.append([mtime, None, w])
```
Confirms the merge-trigger loop (below) only ever sees workspaces
`_workspace_clean_state()` already classified `reason is None` (safe,
non-live, non-dirty) — the same #1124 safety gate `roster_clean()` shares —
before the new trigger is even consulted.

canonical: `46ee6b81:lifecycle.py:1044-1049`
```
after_merge = []
for entry in candidates:
    removable, detail = _sp._workspace_merge_trigger_status(entry[2])
    if removable:
        _reap(entry, "merge", detail)
    else:
        after_merge.append(entry)
```
Confirms the three triggers run in the order the record claims (merge →
age → size) and that a workspace the merge-trigger declines to remove
(`removable=False`, any reason) falls straight through to the pre-existing
age/size logic on `after_merge`, unmodified.

canonical: `46ee6b81:lifecycle.py:971-985` (`_workspace_merge_trigger_status`,
paraphrased): resolves the branch via `git rev-parse --abbrev-ref HEAD`; if
no branch, returns `(False, "no-branch")`; if `_sp._pr_list_call_ok()`
(the underlying `gh pr list` call itself) returns `False`, returns
`(False, "pr-check-failed")` *without* calling `_merged_pr_for_branch()`;
otherwise returns `(True, "PR #N merged")` only if
`_merged_pr_for_branch()` finds a `MERGED`-state PR, else
`(False, "not-merged")`. Every non-`True` path is a no-op, never a delete —
matches the "ambiguity always degrades to not-yet, never to a delete"
claim.

**Independent scratch fixtures (own workspace names/ages/mock shapes,
distinct from the PR's own — issue numbers 500-505, a ~14-minute-old
workspace for the fast-removal case, 40-day-old fixtures for the
survives-regardless-of-age cases), via a scratch script
(`/tmp/otr-2447-eo-verify/verify_merge_trigger.py`, removed after use),
mocking `spawn._pr_list_call_ok`/`spawn._merged_pr_for_branch` (the same
seam the pre-existing suite and the implementation record both use in
place of live `gh` calls):**

acceptance: `python3 /tmp/otr-2447-eo-verify/verify_merge_trigger.py` — result:
```
[auto-sweep] 지움 (merge-triggered): on-the-record-issue-500-implementation (PR #9001 merged)
[auto-sweep] 지움 1 (merge 1, age 0, size 0)
[auto-sweep] 지움 (age-triggered): on-the-record-issue-503-implementation
[auto-sweep] 지움 1 (merge 0, age 1, size 0)
{
  "bullet1_merged_ended_removed_fast": {
    "before_exists": true, "after_exists": false,
    "sweep_result": {"removed": 1, "failed": 0}
  },
  "bullet2a_live_session_merged_pr_survives": {
    "exists": true, "sweep_result": {"removed": 0, "failed": 0}
  },
  "bullet2b_ended_unmerged_pr_survives_even_old": {
    "exists": true, "sweep_result": {"removed": 0, "failed": 0}
  },
  "bullet3_gh_api_failure_degrades_age_size_unaffected": {
    "exists": false, "sweep_result": {"removed": 1, "failed": 0}
  },
  "bullet4_log_distinguishes_trigger": {
    "sweep_result": {"removed": 2, "failed": 0},
    "has_merge_triggered_line": true,
    "has_age_triggered_line": true,
    "has_per_trigger_summary": true,
    "log": "[auto-sweep] 지움 (merge-triggered): on-the-record-issue-504-implementation (PR #9004 merged)\n[auto-sweep] 지움 (age-triggered): on-the-record-issue-505-implementation\n[auto-sweep] 지움 2 (merge 1, age 1, size 0)\n"
  }
}
```
Bullet 1 (removed well inside 14d/5GiB bounds — this fixture used a
~14-minute-old workspace, far tighter than the record's own 1-hour
example): confirmed. Bullet 2 (live session survives regardless of PR
state; ended-but-unmerged survives even at 40 days old with age-bound
effectively disabled): both sub-cases confirmed, `removed: 0` in both.
Bullet 3 (`_pr_list_call_ok` mocked `False`, `_merged_pr_for_branch`
mocked to raise `AssertionError` if called at all — it wasn't; the
30-day-old workspace still got removed via the *age* bound): confirmed,
`AssertionError` never fired. Bullet 4 (log tagging): both
`merge-triggered` and `age-triggered` lines present, plus the per-trigger
summary line — confirmed.

**Independent size-bound-path-under-gh-failure check (bullet 4's fourth
sub-case, re-derived with a distinct fixture — own byte sizes and issue
numbers, 600-602 — via a second scratch script,
`/tmp/otr-2447-eo-verify/verify_size_path_gh_failure.py`, removed after
use), to confirm the size path is independently unaffected too, not just
the age path:**

acceptance: `python3 /tmp/otr-2447-eo-verify/verify_size_path_gh_failure.py` — result:
```
[auto-sweep] 지움 (size-triggered): on-the-record-issue-600-implementation
[auto-sweep] 지움 1 (merge 0, age 0, size 1)
{
  "sweep_result": {"removed": 1, "failed": 0},
  "w1_oldest_exists": false, "w2_exists": true, "w3_exists": true
}
```
With `_pr_list_call_ok` mocked `False` (forced API failure) and a
size-bound tight enough to reap only the oldest of three pushed
workspaces, the size path fires exactly as it would without the merge
trigger present — confirms the "existing age/size prune still runs
unaffected" claim covers *both* fallback paths, not just age.

**Independent live-backlog read-only scan (bullet 5), re-run this turn
against whatever `$MUSTER_WORKSPACE_ROOT` looks like right now (a shared,
concurrently-changing backlog — not trusting the implementation record's
own snapshot numbers), via a third scratch script
(`/tmp/otr-2447-eo-verify/scan_real_backlog.py`, removed after use), using
only the read-only classification helpers
(`spawn._workspace_clean_state()`, `spawn._workspace_merge_trigger_status()`)
— no `_delete_workspace()` call against real data:**

acceptance: `python3 /tmp/otr-2447-eo-verify/scan_real_backlog.py` — result:
```
scanned 41 workspaces in 29.34s (read-only, no deletions performed)
  merge-removable now: 0
  kept (live or dirty): 40
  safe but not-yet-merged: 1
```
Backlog size differs from the implementation record's own scan (41 vs. 31
workspaces — expected, since this backlog is shared with other
concurrently running sessions and changes between scans) but the shape
matches: zero naturally-occurring "session-ended, PR-reached-MERGED" cases
at either scan time, and the classification logic completes cheaply
(29s for 41 workspaces this turn, most of that in per-candidate `gh`
calls for the one safe-but-unmerged workspace and the `git fetch`
refresh path for ahead-marked clean worktrees — 1.72s in the record's own
scan when it found the same shape but fewer ahead-marked candidates)
without mutating shared state. This independently confirms the
implementation record's disclosed deviation (see "Upstream basis" below)
was reasonable: no naturally-occurring merged+ended workspace was
available in the real backlog at either scan time to demonstrate against
non-destructively, so the synthetic fixtures above are what carry bullet
5's actual before/after evidence — before: bounded only by the 14-day age
check or an unrelated size-pressure event; after: bounded by the next
sweep pass, shown completing in ~1-2s worth of classification work per
dozens of workspaces (canonical fences above), not up to 14 days.

**Full regression sweep — no other prune path shifted:**

acceptance: `python3 -m pytest $(grep -rl "import spawn\|import lifecycle\|import board" tests/ gates/) -q` (52 files — a broader, independently-assembled set than the record's own claimed 46) — result:
```
FAILED tests/test_checkpoint_mode.py::CheckpointDirectiveAssembly::test_flag_appends_checkpoint_block
1 failed, 670 passed, 9 xfailed, 1 xpassed in 114.10s (0:01:54)
```
Same single failure the record discloses.

canonical: `python3 -m pytest tests/test_checkpoint_mode.py::CheckpointDirectiveAssembly::test_flag_appends_checkpoint_block -q` re-run this turn in a second worktree checked out at unmodified `origin/main` (`28c776d9`, zero code changes present) — result:
```
FAILED tests/test_checkpoint_mode.py::CheckpointDirectiveAssembly::test_flag_appends_checkpoint_block
1 failed in 1.27s
```
Fails identically with zero code changes present — independently confirms
this failure predates and is unrelated to this PR's diff, matching the
record's own disclosure ("reproduces identically on a `git stash`").

**Diff-scope confirmation:**

acceptance: `git diff origin/main...HEAD --stat` (from the `46ee6b81` worktree) — result:
```
docs/issue-2447/reports/implementation.md          | 276 +++++++++++++++++++++
.../20260826T004658993396-d29943cde3af7f7c.md      |   1 +
lifecycle.py                                       |  72 +++++-
spawn.py                                           |   1 +
4 files changed, 339 insertions(+), 11 deletions(-)
```
Matches the PR's own reported 339 additions/11 deletions, no unrelated
changes.

## Why

derived: the targeted pytest run, the four independent scratch-fixture
scripts (merge-trigger fixtures, size-path-under-failure fixture,
real-backlog scan), the broader 52-file regression run, the
pre-existing-failure cross-check on unmodified `origin/main`, and the
direct reads of `lifecycle.py`'s candidate-gating and trigger-ordering
code, all quoted in full under "What was done" above — every claim in
this section draws only on those already-cited transcripts and file:line
reads.

Re-derived each Acceptance bullet independently rather than trusting the
implementation record's own transcripts: authored fresh fixtures with
different issue numbers, ages, and mock shapes than the record's own (its
bullet 1 used a 1-hour-old workspace; this turn's used ~14 minutes — both
demonstrate "well inside 14d/5GiB" but from different starting points,
reducing the chance a coincidental fixture choice on either side masked a
boundary bug).

Added one check the record's own bullet-4 fixtures didn't isolate on
their own: re-ran the size-bound-under-gh-failure case with its own
distinct byte sizes/issue numbers, to confirm independently that *both*
fallback paths (age and size), not just the one the record's bullet 3
happened to exercise, are unaffected by a merge-status API failure — the
Acceptance text says "the existing age/size prune still runs unaffected"
(both), and the record's bullet 3 only fixtures the age half directly (its
bullet 4's fourth sub-case does cover size, but under a different
scenario — this turn's fixture isolates size-under-failure specifically as
its own independent check).

Read the actual candidate-gating and trigger-ordering code directly
(`lifecycle.py:1014-1023`, `lifecycle.py:1044-1049`, quoted above under
"What was done") rather than trusting only the record's own prose summary,
to confirm structurally that the merge-trigger sits *after* the existing
`_workspace_clean_state()` safety gate and *before* (not replacing) the
age/size loop — this is what makes the "additive, never widens what's
considered safe" claim actually hold, not just asserted.

Cross-checked the one disclosed pre-existing test failure
(`test_flag_appends_checkpoint_block`) against unmodified `origin/main` in
a second worktree, rather than accepting the record's "reproduces
identically on a `git stash`" claim at face value — confirmed above under
"What was done" that it fails identically with zero code changes present.

## Upstream basis

- `46ee6b81:docs/issue-2447/reports/implementation.md` — the delivered
  work's own account; re-derived rather than cited, per this role's
  independent-execution mandate.
- `46ee6b81:lifecycle.py`, `46ee6b81:spawn.py` — the actual code changes,
  read and imported directly this turn via the `/tmp/otr-2447-eo`
  worktree.
- `46ee6b81:docs/issue-2447/reports/implementation/deviation-log/20260826T004658993396-d29943cde3af7f7c.md`
  — the implementation record's own disclosed substitution of a read-only
  backlog scan for a live destructive demonstration against bullet 5
  (shared backlog, other concurrently running sessions' state);
  independently re-run and independently assessed as reasonable above
  under "What was done" (the live-backlog-scan paragraph), rather than
  accepted on the record's word alone.
- issue #2447's live body (`gh issue view 2447`, fetched this turn) — the
  real Acceptance text (five `check` bullets, each with its own `must
  not` clause) this record checks the delivery against.
- this branch's own unmodified `lifecycle.py`/`spawn.py`/test suite
  (`origin/main`, no diff on this branch) — implicit "before" state for
  the diff-scope confirmation and the pre-existing-failure cross-check
  above.

## Open findings

derived: direct reads of `_pr_list_call_ok()`/`_merged_pr_for_branch()`
in `lifecycle.py`/`board.py`, and a grep across every `gh` subprocess call
site in `lifecycle.py`/`board.py`/`spawn.py` (10 call sites: `board.py:129,498,513,526,545`,
`lifecycle.py:157,218,244,257,297`), this turn.

Two residual gaps, both non-blocking against this issue's own Acceptance
criteria:

1. `_pr_list_call_ok()`/`_merged_pr_for_branch()` call `subprocess.run(["gh", ...])`
   with no timeout and no exception handling around the call itself
   failing to spawn (e.g. `gh` not on `PATH`, or hanging indefinitely on a
   network stall). An uncaught `OSError`/`FileNotFoundError` or an
   unbounded hang there would propagate out of
   `_workspace_merge_trigger_status()` and interrupt the *entire*
   `auto_sweep()` call for that sweep pass — not just no-op for the one
   workspace being checked — which is narrower than "degrades to a no-op
   for that workspace" might suggest on first read of the Acceptance
   text. However: this is a pre-existing convention across every `gh`
   subprocess call in this codebase (all 10 sites checked, quoted above,
   carry no timeout and no try/except around spawn failure), not a new
   gap this PR introduces; the scenario the Acceptance bullet's own tests
   actually exercise — `gh` executing and returning a nonzero exit or
   malformed JSON — is exactly what `_pr_list_call_ok()`'s
   `returncode == 0` check degrades correctly (confirmed above under
   bullet 3). Not one of this issue's named Acceptance checks — no
   resolution path opened here; noted for whoever next hardens the
   `gh`-call surface generally, per this repo's own precedent
   (#2278/#2313/#2233/#2463, also cited in the #2379 execution-observation
   record) of fixing one observed failure mode at a time rather than
   speculative hardening.
2. `_workspace_merge_trigger_status()` issues two separate `gh pr list`
   round-trips per safe candidate per sweep (`_pr_list_call_ok()` then, if
   that succeeds, `_merged_pr_for_branch()` — each running its own
   `gh pr list --head branch --state all --json number,state`), doubling
   gh-call latency/rate-limit pressure versus a single combined call that
   reused one response. Not a correctness gap — both calls return
   consistent data, confirmed by the fixtures above — and the
   implementation record's own "Why" section explicitly chose this to
   keep the API-failure and not-yet-merged cases distinguishable by
   reusing existing named helpers as-is, a reasonable reuse-over-new-code
   tradeoff given the issue's own `design-research-skip: mechanical`
   framing. Noted as a minor efficiency observation only.

## What did not work

None — every independently-authored fixture and cross-check behaved as
its own hypothesis predicted on the first run this turn; no wording or
fixture-shape correction was needed.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the five independently-executed Acceptance items
above — result:
```
check  "merged+ended workspace removed well inside 14d/5GiB bounds, before/after": ~14-minute-old synthetic fixture removed immediately via merge-trigger (this turn, quoted above under "What was done"); code-path read confirms the merge check runs before age/size and is not gated by either bound
check  "unmerged/in-progress workspace never removed by new trigger regardless of age": both sub-cases (live session + PR merged; ended session + PR unmerged) survived a 40-day-old, age-bound-disabled fixture (this turn, quoted above)
check  "gh API failure degrades new trigger to no-op; existing age/size prune unaffected": age path confirmed via 30-day-old fixture with _merged_pr_for_branch mocked to raise if called (never called, still age-removed, this turn, quoted above); size path independently re-confirmed via its own distinct fixture (this turn, quoted above) — both fallback paths shown unaffected, not just one
check  "prune log output distinguishes merge/age/size trigger": merge-triggered and age-triggered lines plus per-trigger summary line all present in this turn's own fixture output (quoted above); size-triggered line present in the size-path fixture (quoted above)
check  "live demonstration against real backlog, measured numbers": read-only scan re-run this turn against the live, changing backlog (41 workspaces scanned in 29.34s, 0 merge-removable at scan time, matching the record's own disclosed shape); independently assessed the record's destructive-action-avoidance deviation as reasonable (see Upstream basis); synthetic fixtures above carry the actual before/after measurement — before: bounded by the 14-day age check or an unrelated size event; after: bounded by the next sweep pass (sub-30-second classification cost for dozens of workspaces, this turn's own measurement)
regression: 670 passed, 9 xfailed, 1 xpassed, 1 pre-existing-and-independently-confirmed-unrelated failure across a 52-file, independently-assembled set (broader than the record's own 46) — matches the record's disclosed shape
```

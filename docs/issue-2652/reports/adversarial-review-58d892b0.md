---
issue: 2652
role: adversarial-review-58d892b0
author: adversarial-review-58d892b0
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2768, the subject's own deliverable for issue-2652
loop_state: terminal
upstream:
  - path: gates/spawn_on_pr.py
    sha: e71e8d2599efc3254194b8dced1ff61f67103ee3
  - path: docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md
    sha: e71e8d2599efc3254194b8dced1ff61f67103ee3  # untracked in this worktree (main); present only on PR #2768's branch
---

# issue-2652 — adversarial-review-58d892b0 record

## What was done

canonical: `gh pr view 2768 --json state,baseRefName,headRefName,mergeable,isDraft`
— result: `state: OPEN`, `baseRefName: main`, `headRefOid:
e71e8d2599efc3254194b8dced1ff61f67103ee3`.

Independent adversarial review of PR #2768 (`gates/spawn_on_pr.py::missing_verification()`
reorders the pr_index-membership check and the is-open check so is-open runs
first, suppressing the "branch not found" line for closed subjects). A prior
adversarial-review+architecture-coupling-classification record and a prior
independent-verification record (PR #2772) already reviewed this PR. Per
this task's instruction this review does not restate their checks — it
builds an independent fixture from scratch and specifically probes the case
neither prior record's text mentions: what the reordered code does when the
issue-state lookup itself is degraded.

```
$ git merge-base --is-ancestor 6d6727b946348a55146f695e08a02775f8c88271 HEAD; echo "exit=$?"
exit=1
```
derived: the command above, this session — this review branch (based on
`main`) does not contain PR #2768's fix commit, so its own
`gates/spawn_on_pr.py` is usable directly as the "before" (pre-fix) tree.

### Setup: two real checkouts, not one file diffed in the head

```
$ git fetch origin pull/2768/head:pr2768-review
$ git worktree add /tmp/pr2768_wt pr2768-review
```
derived: the two commands above, this session — gave a real pre-fix tree
(this review branch) and a real post-fix tree (`/tmp/pr2768_wt`) to run the
same fixture script against.

### The reorder itself, confirmed by line position, not by reading the diff

```
$ grep -n "if not _issue_is_open\|branch = subject_deliverable_branch" gates/spawn_on_pr.py
403:        branch = subject_deliverable_branch(subject, pr_index)
419:        if not _issue_is_open(issue, issue_states):
677:        branch = subject_deliverable_branch(subject, pr_index)
820:        branch = subject_deliverable_branch(subject, pr_index)

$ cd /tmp/pr2768_wt && grep -n "if not _issue_is_open\|branch = subject_deliverable_branch" gates/spawn_on_pr.py
409:        if not _issue_is_open(issue, issue_states):
416:        branch = subject_deliverable_branch(subject, pr_index)
687:        branch = subject_deliverable_branch(subject, pr_index)
830:        branch = subject_deliverable_branch(subject, pr_index)
```
derived: both `grep -n` commands above, run live this session. Pre-fix,
inside `missing_verification()`'s loop, `branch = subject_deliverable_branch(...)`
(line 403) precedes `if not _issue_is_open(...)` (line 419). Post-fix, the
order is reversed: `_issue_is_open()` (line 409) now precedes
`subject_deliverable_branch()` (line 416). This is the reorder PR #2768
claims, confirmed by line position rather than by reading the PR's diff
text.

### Fixture, built independently (not the PR's own script)

`/tmp/repro_2652.py`: imports `gates.spawn_on_pr` fresh from a given repo
root, monkeypatches only `spawn.board()` and
`spawn._watchdog_note_unmappable_subject_branch` (forced to always report
"first time seen", so any regression that would print is not hidden by the
one-shot marker), and calls `missing_verification()` directly with
constructed `board` / `issue_states` / `pr_index` values, capturing stdout.
Six cases, run against both trees:

- A: empty board
- B: one OPEN issue, branch never in `pr_index` at all
- C: one CLOSED issue whose branch **is** mapped in `pr_index` (closed after
  its branch was already known — the "closed after mapping" case named in
  this task)
- D: `issue_states=None` (the shape `missing_verification()` itself
  constructs when `closure_sweep.issue_state_index_all()` returns
  `ok=False`), one subject with a genuinely missing branch
- E: `issue_states=None`, one subject whose branch **is** mapped to a real
  open PR
- F: mixed board, 30 closed subjects + 1 open/unmappable + 1 open/mapped
  (same shape as the PR's own repro, built independently to cross-check the
  headline 31→1 number)

derived: `python3 /tmp/repro_2652.py <root>`, run twice (pre-fix root, then
`/tmp/pr2768_wt`), this session. Full stdout transcript:

```
=== A: empty board ===                              (identical both trees)
spawn-candidates: {}  stdout: (empty)

=== B: open issue, no branch in pr_index at all ===  (identical both trees)
spawn-candidates: {}
stdout: [spawn-on-pr] issue-40001: deliverable 브랜치를 pr_index 에서 찾지 못했다 — 이번 틱은 건너뜀 (deficit=2)

=== C: closed issue, branch present+mapped in pr_index ===  (identical both trees)
spawn-candidates: {}  stdout: (empty)

=== D: degraded issue_states=None, subject's branch genuinely missing ===
  PRE-FIX  stdout: [spawn-on-pr] issue-40003: deliverable 브랜치를 pr_index 에서 찾지 못했다 — 이번 틱은 건너뜀 (deficit=2)
  POST-FIX stdout: (empty)                          <-- DIVERGES

=== E: degraded issue_states=None, subject's branch IS mapped/open ===  (identical both trees)
spawn-candidates: {}  stdout: (empty)

=== F: mixed board (30 closed + 2 open) ===
  PRE-FIX:  spawn-candidates: {'issue-50200': 2}, 31 branch-missing lines (issue-50000..50029, issue-50100)
  POST-FIX: spawn-candidates: {'issue-50200': 2}, 1 branch-missing line (issue-50100 only)
```

Case F re-derives the PR's headline claim independently: 31→1, the same
subject set survives (`issue-50100`, the one genuinely-open+unmappable
subject), the same spawn-candidate dict (`issue-50200`) on both sides.
Cases A-C and E show no divergence — confirmed unaffected by the reorder.
**Case D diverges.**

### Following up on D: the "already reported" / summary-count path also goes silent

```
$ sed -n '441,444p' gates/spawn_on_pr.py   # /tmp/pr2768_wt, identical on pre-fix tree
    if unmappable_branch_already_reported:
        print(f"[spawn-on-pr] {unmappable_branch_already_reported}건 이전에 보고된 "
              "매핑-불가 subject — 계속 무시 (반복 안 찍음)")
    return out
```
derived: the `sed` command above, this session — a second reporting path
that collapses subjects already reported missing on a prior tick into a
single count line instead of repeating the per-subject line.

```
$ python3 /tmp/repro_2652_degraded_summary.py <pre-fix-root>
out: {}
stdout: '[spawn-on-pr] 5건 이전에 보고된 매핑-불가 subject — 계속 무시 (반복 안 찍음)\n'

$ python3 /tmp/repro_2652_degraded_summary.py /tmp/pr2768_wt
out: {}
stdout: ''
```
derived: both commands above, run live this session, with
`_watchdog_note_unmappable_subject_branch` forced to `False` (already-seen)
for 5 subjects under `issue_states=None`. Not just the individual line —
the aggregate fallback line goes silent too, because post-fix the loop body
never reaches the branch-check block at all when `issue_states` is `None`;
`unmappable_branch_already_reported` stays `0`.

### Why this happens

```
$ sed -n '251,259p' gates/spawn_on_pr.py
def _issue_is_open(issue: int, issue_states: dict[int, str] | None) -> bool:
    """`issue_states`(이슈 #-> state 사전) 에서 `issue` 가 OPEN 인지
    판정한다. 사전이 없거나(gh 실패/truncated) `issue` 가 사전에 없으면
    (조회 불가) 안전한 쪽으로 fail-closed — OPEN 이 아니라고 본다: 상태를
    모르는 subject 를 자동 스폰하지 않는 편이 이 게이트가 고치려는
    사고(board-wide 재귀 스폰)를 반복하지 않는다."""
    if issue_states is None:
        return False
    return issue_states.get(issue) == "OPEN"
```
derived: the `sed` command above, this session (unchanged by this PR — same
text on both trees). `_issue_is_open()` fail-closes on unknown state by
design: `if issue_states is None: return False`. That design choice
predates this PR and is sound for the *spawning* decision (an automation
that cannot confirm an issue is open should not auto-spawn against it).

The defect is not in `_issue_is_open()` itself — it is in where this PR now
calls it relative to the branch check, per the line-position `grep -n`
evidence in "The reorder itself" above (pre-fix: branch check at line 403,
is-open check at line 419; post-fix: is-open check at line 409, branch
check at line 416). Before the reorder, a subject with `branch is None` hit
`continue` unconditionally before the loop ever reached `_issue_is_open()`
in that iteration — the branch-missing print/one-shot-marker fired
regardless of whether `issue_states` was populated, empty, or `None`
(demonstrated directly by Case D's pre-fix output above: it prints even
though `issue_states=None`). After the reorder, `_issue_is_open()` runs
first, so on a tick where the bulk `gh` issue-state lookup fails:

```
$ sed -n '374,380p' gates/spawn_on_pr.py
    out: dict[str, int] = {}
    if issue_states is None:
        issue_states, ok = closure_sweep.issue_state_index_all(root)
        if not ok:
            issue_states = None
    if pr_index is None:
        pr_index, _ = closure_sweep._pr_index_all(root)
```
derived: the `sed` command above, this session — `issue_states` is set to
`None` when the bulk `gh` lookup itself fails (`ok=False`). On such a tick,
every subject — open or closed — now fails `_issue_is_open()` and is
skipped before the branch check runs, and the branch-missing line (both
forms) never fires for anyone. This is exactly what Case D and the
summary-line follow-up above demonstrate.

This is a real, not hypothetical, trigger condition — this codebase already
has dedicated machinery elsewhere for exactly this class of event:

```
$ sed -n '1135,1140p' watchdog.py
        if skips:
            count += 1
            # 이슈 #2196: 단발 gh blip 은 조용히 넘어간다 — 연속 N틱
            # 실패면 그때부터 경고한다.
            if _sp._watchdog_note_gh_failure(root, "closure-sweep", True):
                print(f"[watchdog] closure-sweep: 확인 불가 (gh 실패) {len(skips)}건")

$ grep -n '"spawn-on-pr" in this_tick' watchdog.py
1095:    if "spawn-on-pr" in this_tick:
```
derived: both commands above, this session. The `closure-sweep` branch of
the same tick driver warns after a consecutive run of `gh` failures. The
`spawn-on-pr` branch (starting at line 1095, read directly this session)
has no equivalent — it does not thread `issue_states_ok` into
`spawn_missing_for_pr`/`missing_verification()` at all, and, as shown
above, `missing_verification()` itself has no fallback print on `ok=False`
either. So: pre-fix, a degraded lookup tick was noisy but not blind.
Post-fix, a degraded lookup tick for spawn-on-pr is indistinguishable from
a perfectly healthy, quiet tick with nothing to report.

Note the scope of this finding precisely: it does not touch
`missing_verification()`'s spawn-eligibility output (`out`, the dict that
drives spawning) — Case E above shows that path was already silently
excluded pre-fix too (`out: {}` on both trees), since `_issue_is_open()`'s
fail-closed design already guarded the *spawn* decision before this PR
touched anything. The divergence is confined to the diagnostic print —
exactly the signal this issue is about.

### dry_run byte-identical claim, re-derived independently

Built a second, independent fixture (`/tmp/repro_2652_dryrun.py`) with a
different subject numbering than either the PR's own repro or my `Case F`
above, calling `spawn_missing_for_pr(..., dry_run=True)` directly (not just
`missing_verification()`), with `state_paths.STATE_ROOT` monkeypatched to a
throwaway tmp dir so this run cannot touch the real orchestrator's park
state:

```
$ python3 /tmp/repro_2652_dryrun.py <pre-fix-root>
pairs: [('issue-60200', 'independent-verification-1'), ('issue-60200', 'independent-verification-2')]

$ python3 /tmp/repro_2652_dryrun.py /tmp/pr2768_wt
pairs: [('issue-60200', 'independent-verification-1'), ('issue-60200', 'independent-verification-2')]
```
derived: both commands above, this session. Byte-identical, confirmed
independently of the PR's own dry_run number.

### Disjoint-state claim, re-derived by reading the file

```
$ grep -n "issue_states\[\|pr_index\[\|issue_states\.pop\|pr_index\.pop\|issue_states\.update\|pr_index\.update" gates/spawn_on_pr.py
(no output, /tmp/pr2768_wt)
```
derived: the grep above, this session — no mutation of either dict anywhere
in the file; every use is a `.get()` read. Confirms the PR's "neither sets
state the other reads" claim by direct inspection.

### Four standing invariants, re-run live

- **No return of the retired role axis**: `git show
  6d6727b946348a55146f695e08a02775f8c88271 -- gates/spawn_on_pr.py` (read
  directly, this session) touches only the two-check reorder inside
  `missing_verification()`'s loop body — no `role`/`kind` name list, no
  closed-set enumeration in the diff.
- **No new bug — failing-test set vs `main`, as sets of names, not counts**:
  ```
  $ python3 -m pytest -q                          → 16 failed, 550 passed, 3 xfailed   (this review branch = main)
  $ cd /tmp/pr2768_wt && python3 -m pytest -q     → 16 failed, 553 passed, 3 xfailed   (post-fix: +3 new passing tests)
  $ diff <(sort main_failed.txt) <(sort pr_failed.txt) && echo "IDENTICAL SETS"
  IDENTICAL SETS
  ```
  derived: both `pytest -q` runs and the `diff`, this session. Same 16
  failing test **names** both sides (pre-existing `gh`/network-boundary
  failures unrelated to this change); the 3-test delta is entirely the new
  passing regression tests, not new failures.
- **No overhead increase**: the disjoint-state grep above confirms
  `_issue_is_open()` only reads the already-fetched `issue_states` dict —
  the reorder swaps two existing dict-lookup/int-parse checks with no new
  `gh` call, no new bulk index, no new I/O. No timing probe run (nothing in
  this diff is I/O-bound), confirmed by direct code reading rather than by
  trusting the PR's own commit-message assertion.
- **Monitor and watch machinery must not go quieter**: this is where the
  finding above lands. For the issue's own three named acceptance criteria
  (closed→silent, open+missing→still printed, spawn set unchanged), the fix
  is correct and independently confirmed (Cases A, B, C, F above). But
  under a degraded `gh` issue-state lookup (Case D above) — a real,
  already-documented-elsewhere failure mode in this same codebase
  (`watchdog.py:1135-1140` quoted above) — the reorder makes
  `missing_verification()`'s diagnostic output for every subject in that
  tick (open or closed) go from "noisy but present" to "silent," including
  the aggregate fallback line. The monitor did go quieter, in exactly the
  one condition this drive singles out as the question that matters.

## Why

```
$ grep -n "issue_states" gates/test_spawn_on_pr.py | grep -c "OPEN\|CLOSED"
3
$ grep -n "issue_states=None" gates/test_spawn_on_pr.py
(no output)
```
derived: both commands above, run against this review branch's working
tree (the same `gates/test_spawn_on_pr.py` content exists on the PR branch
— PR #2768's diff only appends new tests at the end of the file, per the
earlier `git diff main -- gates/test_spawn_on_pr.py` read in this session,
all three of which pass explicit `issue_states={...: "OPEN"}` /
`{...: "CLOSED"}` dicts; none pass `issue_states=None`).

The task asked specifically to look where the two prior reviews of this PR
did not, and named the degraded-lookup case as the one that matters most.
The grep above confirms the PR's own regression tests never exercise
`issue_states=None`. Building a fixture that explicitly drives that value
through the real `missing_verification()` entrypoint, on both the pre-fix
and post-fix trees, was the direct way to answer the question rather than
reason about it from the diff alone.

## Upstream basis

- `gates/spawn_on_pr.py` @ `e71e8d2599efc3254194b8dced1ff61f67103ee3` (PR
  #2768 head, fetched via `git fetch origin pull/2768/head:pr2768-review`
  and checked out in a worktree at `/tmp/pr2768_wt`) — the code under
  review.
- `docs/issue-2652/reports/adversarial-review+architecture-coupling-classification-3b733611.md`
  (untracked in this worktree/main; present only on PR #2768's branch,
  read via the `/tmp/pr2768_wt` worktree) @
  `e71e8d2599efc3254194b8dced1ff61f67103ee3` — the subject's own
  deliverable record for issue-2652, which this record independently
  verifies (`verifies_subject: true`).
- Comparison point: this review branch's own `gates/spawn_on_pr.py`
  (pre-fix, tracks `main` — confirmed via the `git merge-base
  --is-ancestor` command in "What was done" above), used as the "before"
  tree for every paired run.

## Open findings

1. **Degraded issue-state lookup silences `missing_verification()`'s
   diagnostic output entirely, for all subjects, including open ones.**
   derived: Case D transcript and the summary-line follow-up transcript in
   "What was done" above (both run live this session, reproduced on both
   the pre-fix and post-fix trees). Root cause, per the line-position
   `grep -n` evidence in "The reorder itself" above: post-fix,
   `_issue_is_open()` (line 409, fail-closed on `issue_states is None` —
   see the `sed` quote in "Why this happens" above) now runs before the
   branch check (line 416), so a `gh`-lookup failure now produces zero
   output from spawn-on-pr where the pre-fix code produced (noisy,
   unlabeled, but present) branch-missing lines. This does not violate the
   issue's three stated acceptance criteria (all three hold, per Cases
   A/B/C/F above) and does not change any spawn-eligibility decision (Case
   E above: already silent pre-fix too) — it is a new, reproducible
   regression in the diagnostic/monitor-visibility surface specifically,
   which the task's own framing marks as the central standing invariant
   for this PR.
   **Resolution path:** not attempted in this review (out of scope for a
   review-only record) — a plausible fix is either (a) keep printing the
   branch-missing line when `issue_states is None` (treat "state unknown"
   as "no information to suppress on," the pre-fix behavior for exactly
   this case), or (b) add an explicit one-shot warning line for
   `issue_states is None` mirroring watchdog.py's `closure-sweep`-branch
   pattern (`watchdog.py:1135-1140`, quoted above), so a degraded tick is
   visibly degraded rather than indistinguishable from a healthy quiet
   one. Flagging for the PR author/reviewers to decide before merge, given
   the task's explicit framing of this exact question as load-bearing.

## Next steps

None — `loop_state: terminal`.

acceptance: `python3 /tmp/repro_2652.py <pre-fix-root>` and `python3
/tmp/repro_2652.py /tmp/pr2768_wt` — result:
```
Case F, PRE-FIX:  spawn-candidates: {'issue-50200': 2}, 31 branch-missing lines
Case F, POST-FIX: spawn-candidates: {'issue-50200': 2}, 1 branch-missing line (issue-50100 only)
Case B (open subject, genuinely missing branch): identical branch-missing line on both trees
```
This reproduces the issue's three named acceptance criteria independently
— closed subjects print nothing post-fix, the genuinely-missing-branch
open subject still prints, and the spawn-candidate set is unchanged (also
confirmed byte-identical via `spawn_missing_for_pr(dry_run=True)`,
transcript in the "dry_run byte-identical claim" subsection above).

The one open finding above is a real, demonstrated regression in the
monitor's diagnostic output under a degraded-lookup condition that neither
prior review of this PR touched (per the "## Why" grep above) — reported
here for the PR author/reviewers to weigh before merge, not resolved in
this record.

## What did not work

None.

skill-verdict: adversarial-review — applied: invoked; loaded via Skill tool
this session, then followed its "structurally independent evaluator"
protocol by building an independent fixture from scratch (not reusing the
PR's own repro script or either prior review's evidence) and specifically
targeting the untested degraded-lookup condition the task named as central.
skill-verdict: work-in-english — applied: invoked; this record and all
harness scripts are written in English per the skill's policy for a
Korean-speaking session; the final summary to the user will be in Korean.

---
issue: 2447
role: conformance-review
author: conformance-review
loop_state: complete
upstream:
  - path: 46ee6b819adc76d975da31752c0dba5805b6da9f:docs/issue-2447/reports/implementation.md
    sha: 46ee6b819adc76d975da31752c0dba5805b6da9f
subject: PR #2478 (issue-2447/implementation)
test: gates/test_clean_reconcile_safety.py, tests/test_auto_sweep_nonblocking.py
result: passed
assertedBy: conformance-review (independent re-run, this session)
---

# issue-2447 — conformance-review record

## What was done

Builder-blind conformance review of PR #2478 (`issue-2447/implementation`,
head `46ee6b819adc76d975da31752c0dba5805b6da9f`, hereafter `46ee6b81`)
against issue #2447's own Acceptance section, never against the PR's own
account of itself.

derived: `git worktree add /tmp/pr2478-review pr-2478-review` (fetched
from `refs/pull/2478/head`) — result:
```
HEAD의 현재 위치는 46ee6b81입니다 issue-2447: append deviation-log entry for the read-only backlog-scan substitution
```

The issue's 5 Acceptance lines split into 6 checkable requirements per
conformance-review-requirement-extraction rule 1 (bullet 3 bundles "the
new trigger degrades to a no-op" and "the existing age/size prune still
runs unaffected" — two distinct obligations, one about the new code, one
about the old code's isolation from the new code's failure):

- REQ-1 (functional): a workspace whose session ended and whose PR
  reached `MERGED` is removed on the next sweep pass, well inside the
  14-day/5GiB bounds.
- REQ-2 (scope-boundary): an unmerged, still-open, or still-live
  workspace is never removed by the new trigger regardless of age (folds
  in bullet 1's own "must not" clause, which restates this same
  condition — conformance-review-requirement-extraction rule 3).
- REQ-3a (error-handling): a GitHub API (`gh`) failure degrades the new
  trigger to a no-op for that workspace.
- REQ-3b (error-handling): that same API failure does not block or break
  the pre-existing age/size prune — it still fires on schedule.
- REQ-4 (functional/logging): prune log output distinguishes which
  trigger removed a given workspace (merge/age/size), per-line and in
  the sweep summary.
- REQ-5 (demonstration): a live measurement against the real current
  `$MUSTER_WORKSPACE_ROOT` backlog of how long a merged workspace's
  inodes stay occupied before vs after this fix, with actual numbers.

### REQ-1 — Present

verification method: Demonstration (qualitative functional claim — must
exercise the actual `auto_sweep()` flow with representative stimuli, per
conformance-review-verification-method-selection rule 3; no persistent
test exists for this path, per this role protocol's "do not author
persistent test files by default").

- requirement: "a workspace whose session has ended and whose PR is
  confirmed merged gets removed by the next sweep pass, well inside the
  14-day/5GiB bounds"
- spec_ref: issue #2447 Acceptance, bullet 1 (main clause)
- canonical: `46ee6b81:lifecycle.py:958-983` (`_workspace_merge_trigger_status`, read directly in `/tmp/pr2478-review`, this session)
```
def _workspace_merge_trigger_status(w: Path) -> tuple[bool, str]:
    branch = subprocess.run(
        ["git", "-C", str(w), "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True).stdout.strip()
    if not branch:
        return (False, "no-branch")
    if not _sp._pr_list_call_ok(w, branch):
        return (False, "pr-check-failed")
    merged_pr = _sp._merged_pr_for_branch(w, branch)
    if merged_pr is None:
        return (False, "not-merged")
    return (True, f"PR #{merged_pr} merged")
```
- canonical: `46ee6b81:lifecycle.py:1044-1050` (the merge-trigger pass runs
  first, before the age-bound loop, read directly in `/tmp/pr2478-review`)
```
    after_merge = []
    for entry in candidates:
        removable, detail = _sp._workspace_merge_trigger_status(entry[2])
        if removable:
            _reap(entry, "merge", detail)
        else:
            after_merge.append(entry)
```
- acceptance: independently written fixture, not copied from the PR body
  (isolated `tempfile.TemporaryDirectory`, a real git repo with a real
  `origin` remote so `_workspace_clean_state`'s ahead-check passes,
  1-hour-old mtime, `max_age_days=14`, `max_bytes=5GiB`,
  `spawn._pr_list_call_ok`/`spawn._merged_pr_for_branch` mocked to report
  a merged PR) — result:
```
[auto-sweep] 지움 (merge-triggered): on-the-record-issue-100-impl (PR #4242 merged)
[auto-sweep] 지움 1 (merge 1, age 0, size 0)
before True after False result {'removed': 1, 'failed': 0}
```
- rationale: the workspace is removed in a single `auto_sweep()` call at
  1 hour of age against a 14-day/5GiB bound — nowhere near either bound —
  confirming the merge-trigger fires ahead of, and independent of, the
  age/size checks, matching the requirement's "well inside the bounds."

### REQ-2 — Present

verification method: Demonstration (two independent isolated fixtures:
still-live session, and ended-but-unmerged session, both aged past the
disabled age bound to isolate the new trigger).

- requirement: "an unmerged or in-progress workspace is never removed by
  the new trigger regardless of its age" (+ bullet 1's duplicate "must
  not remove a workspace whose session is still active, or whose PR is
  open/unmerged, even if old")
- spec_ref: issue #2447 Acceptance, bullet 2 (and bullet 1's "must not")
- canonical: `46ee6b81:lifecycle.py:1016-1023` (candidates are only ever
  built from workspaces `_workspace_clean_state()` already judged
  non-live/non-dirty — a live session is excluded before the merge
  trigger is ever consulted, read directly in `/tmp/pr2478-review`)
```
        for w in sorted(wb.glob("*")):
            if not (w / ".git").is_dir():
                continue
            reason, _detail = _sp._workspace_clean_state(w, live)
            if reason is not None:
                continue
```
- acceptance: two independently written, isolated fixtures (each its own
  `tempfile.TemporaryDirectory`, 40 days old, `max_age_days=9999` to rule
  out the age bound explaining a removal) — results:
```
=== live session, PR mocked as MERGED ===
still exists (want True): True {'removed': 0, 'failed': 0}

=== ended session, PR mocked as open/no-PR (None) ===
still exists (want True): True {'removed': 0, 'failed': 0}
```
- rationale: a still-live session is untouched regardless of its PR
  state (the `_workspace_clean_state()` "live" reason wins before the
  merge-trigger function is even called — canonical above), and an
  ended session whose PR has not reached `MERGED` is left alone by the
  new trigger even at 40 days old with the age bound disabled — matches
  the requirement's "never removed... regardless of age."

### REQ-3a — Present

verification method: Demonstration (forced `gh` failure via mock,
assertion-raising mock on the downstream call to prove it is never
reached).

- requirement: "if the GitHub API merge-status check fails/errors, the
  new trigger degrades to a no-op for that workspace"
- spec_ref: issue #2447 Acceptance, bullet 3 (first clause)
- canonical: `46ee6b81:lifecycle.py:963-965` (same
  `_workspace_merge_trigger_status` body quoted under REQ-1 — the
  `pr-check-failed` short-circuit)
```
    if not _sp._pr_list_call_ok(w, branch):
        return (False, "pr-check-failed")
```
- acceptance: independently written fixture — `_pr_list_call_ok` mocked
  to return `False` (forced API failure); `_merged_pr_for_branch` mocked
  to `raise AssertionError` if called at all — result: no
  `AssertionError` raised, workspace removed via age bound instead (see
  REQ-3b), confirming the merge-trigger never reached the second `gh`
  call once the first one failed.
- rationale: the short-circuit at `pr-check-failed` returns `(False,
  ...)` before `_merged_pr_for_branch` is called — independently
  confirmed by an assertion-raising mock on that second call that never
  fired — so the new trigger degrades to "not yet" (a no-op for this
  workspace) rather than raising or misclassifying the failure as
  "not merged."

### REQ-3b — Present

verification method: Demonstration (same fixture as REQ-3a; age-bound
still fires despite the forced API failure).

- requirement: "the existing age/size prune still runs unaffected"
- spec_ref: issue #2447 Acceptance, bullet 3 (second clause)
- canonical: `46ee6b81:lifecycle.py:1052-1057` (the age-bound loop runs
  over `after_merge` — the same candidate list regardless of how the
  merge-trigger resolved each entry — unconditionally, read directly in
  `/tmp/pr2478-review`)
```
    remaining = []
    for entry in after_merge:
        if now - entry[0] > max_age_sec:
            _reap(entry, "age")
        else:
            remaining.append(entry)
```
- acceptance: independently written fixture (30-day-old workspace,
  `max_age_days=14`, `gh` forced to fail via the same mocks as REQ-3a) —
  result:
```
[auto-sweep] 지움 (age-triggered): on-the-record-issue-103-impl
[auto-sweep] 지움 1 (merge 0, age 1, size 0)
age-triggered removal despite API failure (want gone): False {'removed': 1, 'failed': 0}
```
- rationale: the workspace is removed and tagged `age-triggered` despite
  the forced `gh` failure — the age-bound path has no dependency on the
  merge-trigger's outcome, matching "must not let a merge-status API
  failure block or break the existing age/size prune path."

### REQ-4 — Present

verification method: Demonstration (log lines observed directly from
`stderr` during the REQ-1/REQ-3b fixture runs, plus a third isolated run
to exercise the size-triggered label).

- requirement: "prune log output distinguishes which trigger removed a
  given workspace (merge-triggered vs age-bound vs size-bound)"
- spec_ref: issue #2447 Acceptance, bullet 4
- canonical: `46ee6b81:lifecycle.py:1058-1070` (per-workspace tag +
  per-trigger summary breakdown, read directly in `/tmp/pr2478-review`)
```
    if max_bytes > 0 and remaining:
        for entry in remaining:
            entry[1] = _sp._dir_size_bytes(entry[2])
        remaining.sort(key=lambda e: e[0])
        total = sum(e[1] for e in remaining)
        i = 0
        while total > max_bytes and i < len(remaining):
            entry = remaining[i]
            total -= entry[1]
            _reap(entry, "size")
            i += 1

    if removed or failed:
        print(f"[auto-sweep] 지움 {removed} "
              f"(merge {by_trigger['merge']}, age {by_trigger['age']}, "
              f"size {by_trigger['size']})"
              + (f", 실패 {failed}" if failed else ""), file=sys.stderr)
```
- acceptance: independently written fixture (fresh workspace, `gh`
  forced to fail so it can't be merge-removed, `max_bytes=1` to force
  the size bound) — result:
```
[auto-sweep] 지움 (size-triggered): on-the-record-issue-1-impl
[auto-sweep] 지움 1 (merge 0, age 0, size 1)
size-triggered removal: False {'removed': 1, 'failed': 0}
```
  — combined with REQ-1's `(merge-triggered)`/`(merge 1, age 0, size 0)`
  and REQ-3b's `(age-triggered)`/`(merge 0, age 1, size 0)` output above,
  all three per-workspace tags and the summary's three-way breakdown are
  independently observed, not copied from the PR body.
- rationale: each of the three trigger types produces a distinctly
  labeled per-workspace line and a matching non-zero slot in the summary
  breakdown — satisfies "distinguishes which trigger."

### REQ-5 — Surface

verification method: Demonstration (independently re-ran the same
read-only classification scan against the real, live
`$MUSTER_WORKSPACE_ROOT` backlog).

- requirement: "live demonstration against the real current backlog —
  measure how long a merged workspace's inodes stay occupied before vs
  after this fix... report actual measured numbers"
- spec_ref: issue #2447 Acceptance, bullet 5
- canonical: `46ee6b81:docs/issue-2447/reports/implementation/deviation-log/20260826T004658993396-d29943cde3af7f7c.md`
  (exists only at `46ee6b81`/PR #2478's own branch, not on this review's
  branch, same as the implementation record it sits beside — read via
  `git show 46ee6b81:<path>` in this session)
```
2026-08-26T09:50:00Z | filed | issue-2447 | implementation | Acceptance
bullet 5 asked for a live demonstration (with measured numbers) against
the real $MUSTER_WORKSPACE_ROOT backlog; substituted a read-only
classification scan (_workspace_clean_state()/
_workspace_merge_trigger_status(), no _delete_workspace() call) instead
of actually invoking the delete path there, since that backlog is shared
with other concurrently running sessions and a real deletion would be a
destructive, hard-to-reverse action against their state...
```
- acceptance: independently re-run this session (own script, `spawn`
  module imported from `/tmp/pr2478-review`, scanning the real
  `$MUSTER_WORKSPACE_ROOT`, calling only `_workspace_clean_state()`/
  `_workspace_merge_trigger_status()` — no `_delete_workspace()` call) —
  result:
```
kept(live/dirty)=36 merge_removable=0 safe_not_merged=1
```
  (PR's own scan, run ~1 minute earlier in a different session, reported
  `kept=30 merge_removable=0 safe_not_merged=1` out of 31 workspaces;
  this review's independent re-run against the same, still-live,
  still-growing backlog found 36 kept out of 37 — consistent drift from
  new sessions spawned in between, same shape: zero merge-removable
  candidates, one safe-but-unmerged.)
- rationale: assigned Surface, not Present, per
  conformance-review-verdict-assignment rule 1 — the classification
  mechanism genuinely runs correctly and cheaply against the real
  backlog (independently reproduced above), but the specific literal ask
  — an actual measured before/after pair for one real merged workspace's
  inode-occupancy duration — could not be produced because no
  naturally-occurring "session-ended, PR-reached-MERGED" workspace
  existed in the real backlog at either scan (0 merge-removable, both
  independently observed above). What the implementation record reports
  as "before"/"after" numbers (14-day policy bound vs. sub-2-second scan
  latency) are policy-derived and scan-runtime figures, not an actual
  observed single-case latency measurement — a reasonable, transparently
  logged substitution (the canonical deviation-log entry above; also
  consistent with bullet 3's own "must not: delete a workspace tied to a
  PR that is not actually merged" and ordinary care around a shared,
  live backlog), but it does not fully satisfy the bullet's literal
  provenance (`executed-live`, "report actual measured numbers" for a
  real case) as written.

## Why

Sampling: full enumeration used, not a derived sample —
conformance-review-sampling-derivation is not applicable here (5
acceptance lines / 6 extracted requirements, one PR, two production
files changed, no test file changed, no cross-product large enough to
need stratification). conformance-review-severity-classification is
also not applicable — this review's scope was not extended into
risk-weighting a finding, only ordinary fidelity-checking.

acceptance: (from `/tmp/pr2478-review`) `python3 -m pytest
gates/test_clean_reconcile_safety.py tests/test_auto_sweep_nonblocking.py -q`
— result:
```
17 passed, 1 xfailed in 1.31s
```
(matches PR #2478's own claimed count exactly — independently re-run in
a fresh worktree this session, not copied from the PR body.) The PR's
own broader 46-file/508-passed regression sweep was not independently
re-run in full in this session (turn-budget/no scope change to those
files); the targeted suite above plus this review's own from-scratch
fixtures (REQ-1 through REQ-4) are the re-derived evidence this record
relies on, not the PR's pasted counts.

Every Present/Surface verdict above was independently re-derived this
session (fresh worktree at PR head `46ee6b81`, own fixtures constructed
from scratch with a real git remote so `_workspace_clean_state()`'s
ahead-check behaves like a real workspace, own pytest invocation quoted
above, own direct reads of `lifecycle.py`/`spawn.py`) — none copied from
the PR body or `46ee6b81:docs/issue-2447/reports/implementation.md`'s
pasted output, per this role's builder-blind mandate.

Methodology note for the next reviewer (own fixture-construction issue,
not a PR #2478 defect): a first attempt at the REQ-1 fixture used a
synthetic repo with no `origin` remote and got `removed: 0` instead of
the expected removal —

derived: `git -C <synthetic-repo> log --branches --not --remotes --oneline`
(run against that first, remote-less fixture, this session) — result:
```
a1b2c3d (HEAD -> issue-1/impl) init
```
one line printed for the sole commit — `_workspace_clean_state()`
(`46ee6b81:lifecycle.py:610-613`, unmodified by this PR) therefore
classified it `dirty` (non-empty `ahead`) before the merge-trigger was
ever reached, which is why the fixture had to be rebuilt with a real
bare-repo `origin` and a pushed upstream branch to exercise the
merge-trigger at all — an artifact of the fixture, not of the code under
review.

## Upstream basis

`46ee6b81:docs/issue-2447/reports/implementation.md` (PR #2478 head,
`46ee6b819adc76d975da31752c0dba5805b6da9f` — not landed on `main`/this
branch, hence the commit-pinned citations throughout rather than a bare
repo-relative path) is the implementation this record reviews.

## Open findings

1. **REQ-5 (live backlog demonstration) is Surface, not Present** — the
   real backlog happens to hold no naturally-occurring merged+ended
   workspace at scan time (independently confirmed under REQ-5 above: 0
   merge-removable in both the PR's own scan and this review's re-run),
   so the bullet's literal "report actual measured numbers" from one
   real case could not be produced; the implementation record's
   before/after figures are policy-derived/scan-runtime proxies instead.
   Resolution path: no action needed from this PR — the next real
   occurrence of a session-ended, PR-merged workspace in the shared
   backlog would let a future sweep pass's own log line
   (`46ee6b81:lifecycle.py:1060-1062`, `merge-triggered` tag, cited under
   REQ-4 above) serve as the actual real-case measurement bullet 5 asks
   for; non-blocking, since the mechanism itself is demonstrated correct
   via REQ-1's synthetic fixture and this review's own read-only re-run
   of the real-backlog classification.
2. **Two `gh pr list` calls per merge-trigger check, not one** (minor,
   non-blocking, not tied to any acceptance bullet) —
   `_workspace_merge_trigger_status()` (cited in full under REQ-1 above,
   `46ee6b81:lifecycle.py:958-968`) calls `_pr_list_call_ok()` and then,
   if that succeeds, `_merged_pr_for_branch()` — both run the same
   underlying `gh pr list --head <branch> --state all --json
   number,state` call independently rather than sharing one result. Not
   a correctness defect (no acceptance bullet requires a single API
   call), and the same two-helper combination pre-exists unmodified in
   `_post_session_end_comment()` (`46ee6b81:lifecycle.py:289-292`).

## Next steps

None — terminal (`loop_state: complete`). If a real merged+ended
workspace is observed in the shared backlog by a future session, its
`merge-triggered` sweep log line (per REQ-4's canonical citation above,
`46ee6b81:lifecycle.py:1058-1070`) would upgrade REQ-5 to Present with an
actual real-case number; no code change is being requested by this
review itself.

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue's 5 acceptance lines into 6 one-obligation items (REQ-3a/REQ-3b split from bullet 3's bundled "degrades to no-op...and the existing prune still runs unaffected"; bullet 1's duplicate "must not" folded into REQ-2 per rule 3), dimension-tagged each.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; Demonstration for every requirement (all six concern actual runtime behavior of `auto_sweep()`/`_workspace_merge_trigger_status()`, none a bare structural/static property), reusing no pre-existing test since none of the PR's four synthetic-fixture claims correspond to a persisted test file (matches this role protocol's "do not author persistent test files by default").
skill-verdict: conformance-review-verdict-assignment — applied: invoked; REQ-5 assigned Surface (not Present) per rule 1 — the mechanism is real and independently demonstrated, but does not fire on the literal real-case condition the bullet names (no naturally-occurring candidate existed at scan time); every other requirement assigned Present with its own independently-derived evidence, never carried forward from the PR's own account.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every canonical citation pins file:line-range plus the commit sha actually read (`46ee6b81`, this review's own worktree, not the PR body); REQ-3a and REQ-3b cite the same fixture run once each for their own distinct clause rather than duplicating the full transcript.
skill-verdict: conformance-review-finding-record — applied: invoked; every requirement block carries requirement/spec_ref/verdict/evidence(canonical+acceptance)/rationale; Open findings section names each finding's resolution path and blocking status.
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 6 extracted requirements was feasible (one PR, two production files changed, no test file changed), no stratified sample was needed.
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was ordinary fidelity-checking, never extended into risk-weighting a recorded finding.
skill-verdict: adversarial-review — not-applicable: this session is already the structurally independent evaluator this protocol calls for (separate builder-blind conformance-review session against a separately-authored PR, no shared context with the implementation session), not a case requiring the cross-family protocol to be separately invoked.

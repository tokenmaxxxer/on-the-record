---
issue: 2978
role: adversarial-review-29f20beb
author: adversarial-review-29f20beb
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #3012, the deliverable for issue #2978
loop_state: landed
upstream:
  - path: gates/spawn_on_pr.py, gates/closure_sweep.py, test/test_watchdog_heartbeat_noise.py
    sha: 34b954737fa232add2f36a83502f86ae4b35791d
  - path: 34b954737fa232add2f36a83502f86ae4b35791d:tests/test_watchdog_normal_state_not_violation_2978.py
    sha: 34b954737fa232add2f36a83502f86ae4b35791d
  - path: 34b954737fa232add2f36a83502f86ae4b35791d:docs/issue-2978/reports/observability-signal-golden+test-derivation-5c7f5864.md
    sha: 34b954737fa232add2f36a83502f86ae4b35791d
---

# issue-2978 — adversarial-review-29f20beb record

## What was done

Independent verification of PR #3012 (`issue-2978/observability-signal-golden+test-derivation-5c7f5864`,
head `34b954737fa232add2f36a83502f86ae4b35791d`) against issue #2978.
canonical: `gh pr view 3012` output — state OPEN, headRefOid
`34b954737fa232add2f36a83502f86ae4b35791d`. Fetched the PR's head into
an isolated worktree (`git fetch origin pull/3012/head:pr-3012-verify
&& git worktree add /tmp/verify-pr-3012 pr-3012-verify`) and re-ran
everything myself rather than trusting the PR's claimed results.

Acceptance requirement met — checked: `python3 -m pytest tests/ -k spawn_on_pr_no_pr_yet -q` — result:
```
1 passed in 0.96s
```
Acceptance requirement met — checked: `python3 -m pytest tests/ -k spawn_on_pr_genuinely_missing_branch -q` — result:
```
1 passed in 0.89s
```
Acceptance requirement met — checked: `python3 -m pytest tests/ -k closure_sweep_record_after_merge -q` — result:
```
1 passed in 0.88s
```
Acceptance requirement met — checked: `python3 -m pytest tests/ -k closure_sweep_genuine_violation -q` — result:
```
1 passed in 0.89s
```
acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py gates/test_spawn_on_pr.py -q` — result:
```
33 passed in 1.27s
```

**Diff audit.** canonical: `git diff main...HEAD --stat` in the
worktree —
```
 ...ility-signal-golden+test-derivation-5c7f5864.md | 201 +++++++++++++++++++++
 .../20260901T052720565274-f30022c57b072825.md      |  24 +++
 gates/closure_sweep.py                             |  39 ++++
 gates/spawn_on_pr.py                               |  16 ++
 test/test_watchdog_heartbeat_noise.py              |  20 +-
 ...est_watchdog_normal_state_not_violation_2978.py | 167 +++++++++++++++++
 6 files changed, 464 insertions(+), 3 deletions(-)
```
No scope-filter or lookup-failure files touched — the must-not against
folding into those separately-filed fixes holds.

Fix 1 (`gates/spawn_on_pr.py::missing_verification()`) — canonical: `git diff main...HEAD -- gates/spawn_on_pr.py`:
```
         branch = subject_deliverable_branch(subject, pr_index)
         if branch is None:
+            # issue #2978: `_slug` (from `subject_deliverable_record()`
+            # above) is `None` when this subject's OWN deliverable record
+            # has never landed to main ...
+            if _slug is None:
+                continue
```
`_slug` is `subject_deliverable_record(subject_board)`'s first element,
already computed earlier in the loop (line 428) for
`subject_author`/`verification_deficit` — canonical:
`sed -n '428p' gates/spawn_on_pr.py` in the worktree →
`        _slug, subject_fm = subject_deliverable_record(subject_board)`.
Re-reads an existing structural fact (does this subject's own
non-verifying record already exist in `board()`, i.e. has its
deliverable already landed to main) rather than adding an age/window/
issue-number check.

Fix 2 (`gates/closure_sweep.py::find_violations()`) — canonical: `git diff main...HEAD -- gates/closure_sweep.py`:
```
+def _pr_is_record_only(root: Path, pr: int) -> bool:
+    ...
+    paths = check_runner.pr_diff_paths(root, pr)
+    return not check_runner.touches_implementation_paths(paths)
...
+            if kind and _pr_is_record_only(root, pr):
+                kind = None
             if kind:
                 violations.append(...)
```
`_pr_is_record_only()` is called only after `classify()` already named a
violation candidate (`if kind and ...`), the same lazy placement
discipline as the pre-existing `ci._phase2_record_evidence()` call a few
lines above — a healthy tick costs no extra `gh` call.

`check_runner.pr_diff_paths()`/`touches_implementation_paths()` are
issue #2974's own functions, not reinvented here. derived: `git log
--oneline --all | grep 2974` in the worktree →
`7961f712 issue-2974: check-runner record-only distinction, batch-merge
scoping, R-ID canon growth (#2994)`, which predates this PR's head
`34b954737fa232add2f36a83502f86ae4b35791d`. canonical: `sed -n
'451,476p' gates/check_runner.py` in the worktree confirms
`touches_implementation_paths(None)` returns `True` (fail-closed on an
unreadable diff — matches the function's own docstring), read directly
rather than trusted from the PR's description of it.

**Genuine-violation direction verified on real, live data (not just the
PR's mocked fixtures).** Wrote independent scripts run against the
worktree's real, unmocked `check_runner.pr_diff_paths()` (live `gh`
calls) and the repo's real `spawn.board()`:
- closure-sweep, false-positive direction, real data — canonical: `gh
  issue view 2827 --json state` → `{"state":"OPEN"}`; canonical: `gh pr
  diff 2851 --name-only` →
  `docs/issue-2827/reports/diagnose-first-6c16a19d.md` and one nested
  path under it, docs-only. Fed real issue #2827 (OPEN) + real PR #2851
  (`"Closes #2827"` body, `MERGED`) into the worktree's
  `closure_sweep.find_violations()` with `check_runner.pr_diff_paths`
  UNMOCKED (real `gh pr diff 2851` call) — derived: python script output
  → `record-only (real PR #2851) violations: []`. This reproduces the
  issue's own cited example (`issue #2827 / PR #2851:
  merged-delivery-issue-open`) with live data and confirms it no longer
  fires.
- closure-sweep, genuine-violation direction, real data — canonical: `gh
  pr diff 2994 --name-only` → includes `gates/check_runner.py`,
  `gates/merge_gate.py`, etc., confirming `touches_implementation_paths`
  → `True` on live data. Fed real PR #2994 (real, unmocked diff) plus a
  constructed still-open issue (88888, no record PR pending) into
  `find_violations()` — derived: python script output →
  `genuine violation (real PR #2994) violations: [{'issue': 88888, 'pr':
  2994, 'skill': 'implementation', 'kind': 'merged-delivery-issue-open'}]`.
  Still reported, using a real diff, not a mock.
- spawn-on-pr, both directions, real board — derived:
  `spawn_on_pr.spawn.board(root)` run against the live repo (script
  output) → `total subjects on real board: 700`, `subjects with NO
  landed deliverable record: 147`, `subjects WITH a landed deliverable
  record: 553`. Running the real `missing_verification()` end-to-end
  against this live board (derived: script output) printed exactly one
  "찾지 못했다" line, for `issue-2865` — none of the 147 no-deliverable-
  yet subjects printed anything. canonical:
  `subject_deliverable_record()` on `issue-2865`'s real board entry
  resolves to `('conformance-review-requirement-extraction-496d0e6b',
  {...})` (script output), i.e. its deliverable HAS landed, and `gh pr
  list --search "issue-2865 in:head" --state all` confirms a real merged
  deliverable PR #2868 — so the fix correctly did NOT suppress this
  subject. (The reason issue-2865's branch is unmappable —
  `subject_deliverable_branch()`'s own ambiguity rule matching 2
  non-verification-slot branches — is a pre-existing, separately
  one-shot-marked condition unrelated to this PR's fix; what matters
  here is that the new `_slug is None` gate correctly did NOT suppress a
  subject whose deliverable has genuinely landed.)

**Structural-not-time-based check.** canonical: full `git diff
main...HEAD -- gates/spawn_on_pr.py gates/closure_sweep.py` (quoted
above) — neither fix references an issue number, a date, or a duration;
both branch purely on already-computed board/diff facts (`_slug is
None`, `touches_implementation_paths()`).

**Regression check.** derived: `python3 -m pytest gates/ tests/ test/ -q
-k "not slow"` in the worktree → `16 failed, 716 passed, 3 xfailed`.
Re-ran the identical 16 failing test IDs against `main` in the same
worktree (`git checkout main`) — derived: same pytest invocation on
`main` → identical `16 failed`, identical test names (spawn
skill-selection, hooks wiring, convention equivalence — none touch
`spawn_on_pr.py` or `closure_sweep.py`), confirming these are
pre-existing and unrelated to this PR's diff.

## Why

Verification independence (per this task and the
`defect-verification-independence-from-upstream-verdicts` skill's
concern): I did not take the PR description's test-plan checkmarks or
the linked implementation record's citations at face value. Every
acceptance check above was re-run from a freshly fetched worktree (see
`canonical:`/`derived:`/`acceptance:` tags in `## What was done`), the
diff was read directly rather than summarized from the PR body, and —
since the task specifically asked for the genuine-violation direction to
be checked on real data, not only the PR's own mocked unit tests — I
constructed independent scripts against this repo's live `gh` state
(real issues/PRs #2827, #2851, #2865, #2868, #2994) rather than reusing
the PR's fixtures, as shown in the real-data results above.

## Upstream basis

- PR #3012 (`issue-2978/observability-signal-golden+test-derivation-5c7f5864`,
  head `34b954737fa232add2f36a83502f86ae4b35791d`) — the deliverable
  verified.
- `34b954737fa232add2f36a83502f86ae4b35791d:docs/issue-2978/reports/observability-signal-golden+test-derivation-5c7f5864.md`
  — the builder's own record, read for its claims but not trusted
  without independent re-derivation (see `## Why`).
- Issue #2978 (verbatim acceptance + must-not clause, `gh issue view
  2978`) — the standard verified against.
- Issue #2974, commit `7961f712` — origin of the reused
  `touches_implementation_paths()`/`pr_diff_paths()` signal. derived:
  `git log --oneline --all | grep 2974` in the worktree →
  `7961f712 issue-2974: check-runner record-only distinction,
  batch-merge scoping, R-ID canon growth (#2994)`, predating this PR's
  head `34b954737fa232add2f36a83502f86ae4b35791d`.

## Open findings

None. acceptance: `python3 -m pytest tests/ -k "spawn_on_pr_no_pr_yet or
spawn_on_pr_genuinely_missing_branch or closure_sweep_record_after_merge
or closure_sweep_genuine_violation" -q` — result:
```
4 passed in 0.94s
```
No defect surfaced across the diff audit, the live regression run, or
the independent real-data reconstruction of both the false-positive and
genuine-violation directions for both checks (see `## What was done`).

## Next steps

None — loop_state: landed.

skill-verdict: adversarial-review — applied: invoked; ran this entire
verification in that posture (independent worktree, live `gh`
re-derivation, no reliance on the builder's stated test-plan results).
skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; treated the PR's own "Present"/passing test-plan
claims as unverified until re-derived from a freshly fetched worktree
and live `gh` data, per this skill's concern.
other mounted skills: not triggered (test-depth-audit,
growth-analytics-experiment-trust,
negotiation-interests-vs-positions-framing, implementation-audit — none
match a verification-of-a-PR task; the adversarial-review skill above is
the applicable one).

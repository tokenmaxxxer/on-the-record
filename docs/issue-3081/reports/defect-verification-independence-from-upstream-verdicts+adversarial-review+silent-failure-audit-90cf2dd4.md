---
issue: 3081
role: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-90cf2dd4
author: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-90cf2dd4
skills: defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification (pass 1) of PR #3084's own deliverable against issue #3081
code_under_review: 4fefe107db388bb2eb8b6439a0274549a8b84f59
type: defect-verification-record
breaking: false
verdict: Criterion 1 (repo-scoped heartbeat) Present. Criterion 2 (mechanism
  named) Present. Must-not #1 (don't suppress drift line) satisfied. Must-not
  #2 (check spawn-on-pr's waiting-for-human) Absent -- reproduced directly.
  Test suite unchanged (5 pre-existing failures both branches, +7 new
  passing tests on the PR branch).
loop_state: landed
upstream:
  - path: PR #3084 (github.com/tokenmaxxxer/on-the-record/pull/3084), head
      commit 4fefe107 -- not merged to main, fetched read-only this session
      as local ref pr-3084-review
    sha: 4fefe107db388bb2eb8b6439a0274549a8b84f59
---

# issue-3081 — defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-90cf2dd4 record

## What was done

Independent, builder-blind verification of PR #3084 against issue #3081's
two acceptance criteria and two must-not clauses, per defect-
verification-independence-from-upstream-verdicts: every claim below is
re-derived by running code directly against `pr-3084-review` (PR #3084's
fetched branch, head `4fefe107`), not cited from PR #3084's own record or
test file on trust. Own scratch probes used: `/tmp/probe_independent.py`,
`/tmp/probe_retention.py`, `/tmp/probe_park.py` (not committed, written
independently of the PR's own `tests/test_requirement_drift_repo_scope.py`).

canonical: `gh issue view 3081` — result: state OPEN, 7 comments.
canonical: `gh pr view 3084` — result: state OPEN, base main, +747/-17.
derived: `git fetch origin pull/3084/head:pr-3084-review && git diff main
pr-3084-review --stat` — result:
```
watchdog.py                                        |  88 +++++--
spawn.py                                           |   1 +
gates/probe_drift_repo_leak.py                     | 170 ++++++++++++++
tests/test_requirement_drift_repo_scope.py         | 249 ++++++++++++++++++++
docs/specs/enforcement-boundary.md                 |   1 +
 7 files changed, 747 insertions(+), 17 deletions(-)
```

### Criterion 1 — "a heartbeat tagged with a repo reports only that repo's issues and PRs"

The issue's literal check
(`python3 watchdog.py --once --repo /home/jwjung/study-companion ...`) is
vacuous on this codebase.
derived: `python3 watchdog.py --once --repo /home/jwjung/study-companion`
on both `main` (573e738) and `pr-3084-review` (4fefe107) — result: exit 0,
no output on either. `watchdog.py` has no `__main__` block and no
`argparse` (`grep -n "argparse\|__main__" watchdog.py` — 0 matches for
either), so this check passes trivially regardless of the fix and cannot
grade this criterion. Grading below is behavioral instead, via direct
calls to `watchdog.requirement_drift`.

derived (`/tmp/probe_independent.py`): seeded two simulated repos
(`acct/on-the-record`, `acct/study-companion`, via monkeypatched
`spawn._repo_slug`), ran `requirement_drift` in delta mode for each with
distinct PR numbers (3048 for repo A, 9999 for repo B), then re-swept both
a second time with unrelated numbers (4242 for A, 5150 for B) to force the
delta-mode reuse pass to read cached entries back. Result on
`pr-3084-review`:
```
repo A output contains 9999 (repo B leak): False
repo B output contains 3048 (repo A leak): False
repo A output mentions its own 3048: True
repo B output mentions its own 9999: True
outputs identical: False
```
derived: same probe script, unmodified, re-run against `main` (573e738) —
result:
```
repo A output contains 9999 (repo B leak): True
repo B output contains 3048 (repo A leak): True
```
This is the sensitivity check: the probe flags the leak on `main` and
clears it on `pr-3084-review` with no change to the probe itself, so the
`False`/`False` result above is not a probe that never could have failed.
Repo A's own #3048 and #4242, and repo B's own #9999 and #5150, all
printed in both branches' own-repo checks — the fix is not achieving the
`False`/`False` leak result by suppressing genuine own-repo output.

derived (`/tmp/probe_retention.py`): seeded repo A with a genuine cached
entry for #100 and repo B with one for #200, then forced a lookup failure
(`_fetch_issue_or_pr_via_cache` mocked to return `None`) for repo A on (a)
its own #100 and (b) foreign #200. Result on `pr-3084-review`:
```
own transient failure retained (cache-retained line present): True
foreign entry NOT retained as own (cache-retained line absent for 200): True
foreign entry instead reported unknown: True
```
Read `watchdog.py:1188-1191` (the `cached_failed`/`uncached_failed` split):
```
            cached_failed = [n for n in failed_numbers
                              if _sp._drift_cache_key(repo_slug, n) in cache]
            uncached_failed = [n for n in failed_numbers
                                if _sp._drift_cache_key(repo_slug, n) not in cache]
```
this keys the lookup on `repo_slug`, so a foreign entry (stored under the
other repo's composite key) structurally cannot satisfy this repo's
membership test — the two failure causes are distinguishable by
construction, not by a bolted-on flag.

Verdict: **Present**.

### Criterion 2 — "the leak's mechanism is named"

acceptance: `bash -c "grep -rn 'cross-repo|foreign repo'
docs/issue-3081/reports/[a-z]*.md"` — result:
```
docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f.md:143:cross-repo-mismatch case would classify as Handled (an explicit, distinct
```
exit 0, literal check passes.

canonical: builder's record
(`docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+
test-derivation+defect-verification-independence-from-upstream-verdicts-
ba2a806f.md`, lines 40-58, "Why" section) names the mechanism as: cache
entries carried no repo-of-origin field, so (a) the reuse pass read back
every repo's entries indiscriminately (report-time leak) and (b) a failed
lookup for a foreign entry was indistinguishable from a transient failure
and retained (retention leak) — read as sound: it identifies "state
carries no repo dimension" rather than the issue's other two candidates
(sweep misresolution or print-time-only tagging), and the composite-key
fix mechanically matches that diagnosis. The record also cites `grep -n
"state_paths.orchestrator_state_path" watchdog.py` (2 matches) to confirm
the cache stayed orchestrator-scoped rather than narrowed to `root`, per
the issue's own must-not and issue #2240.

Verdict: **Present**.

### Must-not #1 — "do not fix this by suppressing the requirement-drift line"

derived: same run as criterion 1's `/tmp/probe_independent.py` above —
repo A's own drift entries (3048, then 4242) print unsuppressed on both
sweeps; repo B's own entries (9999, then 5150) likewise. Frequency and
content of each repo's own signal is unchanged by the fix.

Verdict: **satisfied**.

### Must-not #2 — "check whether spawn-on-pr's waiting-for-human list leaks the same way"

derived: `git diff main pr-3084-review --stat -- gates/spawn_on_pr.py` —
result: empty (no output) — the PR makes zero changes to that file.

derived (`/tmp/probe_park.py`), run against `pr-3084-review`:
```python
state = spawn_on_pr.load_park_state(root_a)
state["issue-3059/independent-verification"] = {"parked": True, "blocked": True}
spawn_on_pr._save_park_state(root_a, state)
report_b = spawn_on_pr.parked_report(root_b)
```
result:
```
repo B's parked_report(): ['issue-3059/independent-verification']
VERDICT: repo A's parked subject leaks into repo B's report: True
park state path identical for both roots: True
```
Read `gates/spawn_on_pr.py:675-680`:
```
def _park_state_path(root: Path) -> Path:
    """issue #2240: orchestrator cross-tick memory, not target-repo state —
    anchored via state_paths, never `root`. `root` is accepted for
    call-site symmetry with the rest of this module's `root`-scoped
    helpers; it is not used here."""
    return state_paths.orchestrator_state_path(PARK_STATE_FILENAME)
```
and `gates/spawn_on_pr.py:766-773` (`parked_report`):
```
def parked_report(root: Path) -> list[str]:
    """현재 park 상태에서 `blocked=True` 인 subject 목록을 돌려준다 —
    watchdog 출력이 park 된 항목을 waiting-for-human 으로 계속 보여주는
    데 쓴다(요구 3, watch-coverage 불가침). issue #2628: park state 가
    subject 단위로 바뀌면서 `(subject, role)` 쌍 대신 subject 하나만
    돌려준다."""
    return sorted(subject for subject, entry in load_park_state(root).items()
                  if entry.get("parked"))
```
`root` is accepted but unused past path resolution in both functions; no
park entry carries a repo field. This is the same orchestrator-scoped-
sharing pattern as the (correctly unchanged) requirement-drift cache, but
without the repo dimension PR #3084 added there.

derived: `grep -n -i "spawn-on-pr\|waiting-for-human\|parked\|park_state"
docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+
test-derivation+defect-verification-independence-from-upstream-verdicts-
ba2a806f.md` — result: no matches — the builder's own record does not
mention `spawn_on_pr.py`, park state, or waiting-for-human anywhere, and
carries no deviation note explaining a deliberate scope narrowing.

Verdict: **Absent**. The must-not clause required checking this path
before treating the fix as complete; the check does not appear to have
been performed, and the leak it would have found reproduces unchanged on
`pr-3084-review`.

### Test suite

derived: `python3 -m pytest tests/ -q` on `pr-3084-review` (4fefe107) —
result: `5 failed, 189 passed`. Same command on `main` (573e738) —
result: `5 failed, 182 passed`. Failing test names identical on both
branches (`tests/test_respawn_deliverable_gate.py` ×4 plus
`tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::
test_pre_existing_post_tool_use_commands_are_all_still_present`) — same
pre-existing failures issue #3083 tracks, unaffected by this PR either
direction.
derived: `grep -c '^    def test_' tests/test_requirement_drift_repo_scope.py`
— result: `7`, matching the +7 passing delta exactly.
derived: `python3 gates/probe_drift_repo_leak.py` — result: `ok`, exit 0.

## Why

defect-verification-independence-from-upstream-verdicts rule 1/rule 3:
every number above came from directly calling `watchdog.requirement_drift`
and `spawn_on_pr.parked_report` with freshly seeded state, not from citing
PR #3084's own test assertions. Rule 2 (deliberate negative case): the
retention-distinction probe and the own-genuine-entries check both exist
specifically because a leak-suppression fix that filters everything to
empty would pass a naive "no leak" check while failing the actual
requirement. Rule 9 (a clean self-report does not lower the attempt
count) is why must-not #2 got the same independent-reproduction depth as
criterion 1 rather than being taken on the PR description's word.
canonical: builder's record, "## Open findings" section — result:
`None.` (the single word, the whole section) — this verification's own
"Open findings" section below lists one, obtained independently rather
than by deferring to that line.

adversarial-review: this session is the structurally independent
evaluator relative to PR #3084's builder session (separate session, no
shared context). Every result above was produced before reading the
builder's own record; the record was read afterward only to cross-check
claims against independently-obtained results, not to derive results from
it.

silent-failure-audit: applied H/S/U classification to the delta-mode
failure-retention branch in `watchdog.py`.
derived: read `watchdog.py:1196-1203` —
```
            for n in cached_failed:
                observed_at = cache.get(_sp._drift_cache_key(repo_slug, n), {}).get(
                    "cached_at", "unknown")
                print(f"[watchdog] requirement-drift-cache-retained: 조회 실패 {n} — "
                      f"이전 캐시 판정 유지 (관측: {observed_at})")
            if uncached_failed:
                print(f"[watchdog] requirement-drift-unknown: 조회 실패 {uncached_failed} — "
                      "이전 판정 없음, unknown")
```
`cached_failed`/`uncached_failed` classifies as Handled (H): each case
prints an explicit, distinct line rather than falling through silently.
`spawn_on_pr.py`'s park-state read path has no failure branch for "this
parked subject belongs to a different repo" at all — not caught-and-
absorbed so much as never checked, a missing-guard defect shape rather
than a stubbed catch, detailed in must-not #2 above rather than force-fit
into H/S/U.

## Upstream basis

PR #3084 (`github.com/tokenmaxxxer/on-the-record/pull/3084`, head
`4fefe107`, not merged), diffed against `main`/merge-base `573e7382`.
canonical: `gh issue view 3081` for the issue text and its acceptance
criteria/must-not clauses, and the operator's mid-thread correction (per
the builder's own record, its 4th comment) that the orchestrator cache
must stay shared, not narrowed to `root`.

## Open findings

1. **Must-not #2 unmet: `gates/spawn_on_pr.py`'s waiting-for-human list
   still leaks cross-repo**, reproduced directly above
   (`/tmp/probe_park.py`). Resolution path: apply the same
   `repo:subject`-composite-key pattern PR #3084 used for
   `_drift_cache_key` to `PARK_STATE_FILENAME`'s entries
   (`load_park_state`/`_save_park_state`/`parked_report` in
   `gates/spawn_on_pr.py:675-773`) in a follow-up change, or amend PR
   #3084 before merge. Issue #3081 should not be treated as fully closed
   by PR #3084 alone on the strength of this finding.
2. The issue's own literal acceptance check for criterion 1 is vacuous
   against this codebase (`watchdog.py` has no CLI entry point) —
   pre-existing, not introduced by PR #3084.
   derived: see "Criterion 1" above — same command run on both branches,
   exit 0 with no output either time, independent of the fix. Noting it
   here so a later re-grading round does not run the literal check
   without this context.

## Next steps

Recommendation, per defect-verification-independence-from-upstream-
verdicts rule 4 (quoted above in "Why", against relying on a single clean
attempt): have a second, independently-run reviewer session re-check PR
#3084 against the same criteria. Finding 1 above (`/tmp/probe_park.py`)
is available as a ready-made failing-case specification for a follow-up
builder session, if one is scoped.

## What did not work

None — every probe run in this session produced a clear result on the
first attempt; no deviations from the assigned verification task occurred.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; re-derived both acceptance criteria and both must-not clauses from direct code execution rather than citing PR #3084's own record or test file, and specifically re-tested must-not #2 instead of accepting the PR's "Open findings: None" claim
skill-verdict: adversarial-review — applied: invoked; acted as the structurally independent evaluator for PR #3084's builder session, deriving results before reading the builder's own record
skill-verdict: silent-failure-audit — applied: invoked; classified the delta-mode failure-retention branch in watchdog.py as Handled via the trace above, and identified spawn_on_pr.py's cross-repo gap as a missing-guard defect distinct from the H/S/U taxonomy

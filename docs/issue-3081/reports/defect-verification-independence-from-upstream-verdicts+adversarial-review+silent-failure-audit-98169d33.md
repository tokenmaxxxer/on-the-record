---
issue: 3081
role: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-98169d33
author: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-98169d33
skills: defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3084's own deliverable against issue #3081
code_under_review: 4fefe107db388bb2eb8b6439a0274549a8b84f59
type: defect-verification-record
breaking: false
verdict: Mixed. requirement_drift attribution/retention fix is Present and
  mutation-tested real (not cosmetic). Acceptance check 1 as literally
  written in the issue is Unverifiable (no CLI surface exists to run it).
  Acceptance check 2 (mechanism named) is Present. Must-not 1 (cache stays
  orchestrator-scoped) is Present. Must-not 2 (foreign-repo lookup failure
  not silently retained) is Present, mutation-tested. The issue's own
  second must-not clause -- checking whether spawn-on-pr's waiting-for-
  human list leaks the same way -- is Absent: gates/spawn_on_pr.py is
  untouched by this PR and this session reproduced the identical leak
  live on the PR branch. Full suite unchanged in shape: same 5 pre-
  existing failure names on both the PR branch and main, 7 net-new passes
  on the PR branch, 0 regressions.
loop_state: landed
upstream:
  - path: PR #3084 (github.com/tokenmaxxxer/on-the-record/pull/3084), head
      commit 4fefe107 -- not merged to main, untracked in this repo's own
      checkout; fetched read-only this session as local ref pr-3084-review
      and checked out into a disposable worktree, since removed
    sha: 4fefe107db388bb2eb8b6439a0274549a8b84f59
  - path: main (baseline for the full-suite comparison)
    sha: 573e7382282be24439c223c1603be648dd0e158f
---

# issue-3081 — defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-98169d33 record

## What was done

Independent, builder-blind verification of PR #3084 against issue #3081.
canonical: `gh issue view 3081 --repo tokenmaxxxer/on-the-record --comments`
— all 7 comments read, including the operator's 4th-comment correction
(shared orchestrator cache is not the defect, do not re-anchor to `root`)
and the 5th comment establishing the leak is bidirectional.
canonical: `gh pr view 3084 --repo tokenmaxxxer/on-the-record` — state OPEN,
+747/-17, "Fixes #3081".

Fetched PR #3084 read-only (`git fetch origin pull/3084/head:pr-3084-review`)
and worked from two disposable git worktrees, `/tmp/pr3084-check` on the PR
head (`4fefe107`) and `/tmp/main-check` on `main` (`573e7382`, the PR's own
stated parent). Both worktrees were removed (`git worktree remove --force`)
before this record was written; every path from PR #3084's own diff cited
below is untracked (untracked) in this session's own checkout and existed
only inside the now-removed `/tmp/pr3084-check` worktree. No merge, no
edit to PR #3084's branch.

### 1. Diff shape

canonical: `git diff main...pr-3084-review -- watchdog.py spawn.py gates/ tests/`
(full diff read in this session; excerpt of the load-side change):

```diff
-    return data if isinstance(data, dict) else {}
+    data = data if isinstance(data, dict) else {}
+    return {k: v for k, v in data.items() if isinstance(v, dict) and "repo" in v}
```

and the delta-mode reuse pass:

```diff
-        for key, val in cache.items():
-            try:
-                key_num = int(key)
-            except ValueError:
+        for val in cache.values():
+            if val.get("repo") != repo_slug:
                 continue
-            if key_num in fetched_numbers:
+            key_num = val.get("number")
+            if key_num is None or key_num in fetched_numbers:
                 continue
```

`_requirement_drift_cache_path` itself is unchanged.
derived: `grep -n "_requirement_drift_cache_path" watchdog.py` (run inside
`/tmp/pr3084-check`) — result: one definition (line 701, still calling
`state_paths.orchestrator_state_path`), one call site (line 1066) — no
`root`-anchored path introduced. Confirms must-not 1 (cache stays
orchestrator-scoped) holds.

### 2. Re-ran the PR's own artifacts myself, from the PR branch

Both `gates/probe_drift_repo_leak.py` (untracked) and `tests/test_requirement_drift_repo_scope.py` (untracked) below are PR #3084 branch only, run from `/tmp/pr3084-check`.

derived: `python3 gates/probe_drift_repo_leak.py` (untracked) — inside
`/tmp/pr3084-check`, commit `4fefe107` — result:

```
ok
```
exit 0.

derived: same probe, `gates/probe_drift_repo_leak.py` (untracked), against
pre-fix code — `git checkout 573e7382 -- watchdog.py spawn.py && python3 gates/probe_drift_repo_leak.py` (untracked) — inside `/tmp/pr3084-check` — result:

```
FAIL: repo B's number 77 appeared in repo A's sweep output -- a cache entry leaked across repos without attribution (issue #3081).
```
exit 1. File restored with `git checkout HEAD -- watchdog.py spawn.py`
afterward. Confirms the probe discriminates pre-fix from post-fix on this
exact repo checkout, independently of the PR's own claim of this.

derived: `python3 -m pytest tests/test_requirement_drift_repo_scope.py -v`
(untracked) — inside `/tmp/pr3084-check` — result:

```
tests/test_requirement_drift_repo_scope.py::TestFullModeMerges::test_full_mode_merges_other_repos_entries PASSED
tests/test_requirement_drift_repo_scope.py::TestDeltaReusePassFiltersByRepo::test_delta_reuse_pass_excludes_other_repo PASSED
tests/test_requirement_drift_repo_scope.py::TestDeltaReusePassFiltersByRepo::test_delta_reuse_pass_leak_is_not_one_directional PASSED
tests/test_requirement_drift_repo_scope.py::TestDeltaReusePassFiltersByRepo::test_delta_reuse_pass_includes_own_repo PASSED
tests/test_requirement_drift_repo_scope.py::TestRetentionRepoScoped::test_retention_when_repo_matches PASSED
tests/test_requirement_drift_repo_scope.py::TestRetentionRepoScoped::test_no_retention_when_entry_is_another_repos PASSED
tests/test_requirement_drift_repo_scope.py::TestLegacyCacheEntries::test_legacy_entry_without_repo_key_not_retained PASSED
7 passed in 0.92s
```

### 3. Mutation-tested the two claims load-bearing for "not merely cosmetic"

Both mutations below were applied to and reverted from `watchdog.py`
(untracked mutation, restored after) inside `/tmp/pr3084-check`, checked
with `gates/probe_drift_repo_leak.py` (untracked).

**Report-time filter.** Patched the delta-mode reuse loop to drop the
`if val.get("repo") != repo_slug: continue` guard, restoring the old
read-everything-back shape.
derived: `python3 gates/probe_drift_repo_leak.py` (untracked) against that
mutation — result:

```
FAIL: repo B's number 77 appeared in repo A's sweep output -- a cache entry leaked across repos without attribution (issue #3081).
```
exit 1. File restored, re-ran clean, exit 0 (`ok`, same output as step 2).
Confirms the probe would catch a "filters at print, doesn't actually gate
the reuse pass" regression.

**Retention distinguishing logic.** Patched `cached_failed`/`uncached_failed`
to check "does *any* repo's cache entry have this number" instead of "does
*this repo's* composite key exist" (simulating the pre-fix, repo-blind
retention check).
derived: `python3 -m pytest tests/test_requirement_drift_repo_scope.py -k "no_retention_when_entry_is_another_repos or retention_when_repo_matches"` (untracked) against that mutation — result:

```
FAILED tests/test_requirement_drift_repo_scope.py::TestRetentionRepoScoped::test_no_retention_when_entry_is_another_repos
AssertionError: a lookup failure for a number that only exists in another repo's cache must not be reported as retained: '[watchdog] requirement-drift-cache-retained: 조회 실패 3048 — 이전 캐시 판정 유지 (관측: unknown)\n'
1 failed, 1 passed in 1.17s
```
File restored, re-ran the same `-k` filter clean — result:
```
2 passed in 0.90s
```
Confirms `test_no_retention_when_entry_is_another_repos` has real
discriminating power, and that the fix structurally distinguishes "lookup
failed, entry is this repo's" (retain — `test_retention_when_repo_matches`,
behavior unchanged from pre-fix) from "lookup failed, entry belongs to
another repo" (evict / report as unknown —
`test_no_retention_when_entry_is_another_repos`) — the two cases this
session's assignment specifically asked to check are distinguishable.

### 4. Second must-not: spawn-on-pr's waiting-for-human list

derived: `git diff main...pr-3084-review --stat -- gates/spawn_on_pr.py` —
result: empty output. `gates/spawn_on_pr.py` (tracked on main, same content
on the PR branch, unchanged by the PR) is untouched by this PR.

canonical: `gates/spawn_on_pr.py`, read inside `/tmp/pr3084-check`,
identical content to `main` —

```python
def _park_state_path(root: Path) -> Path:
    """issue #2240: orchestrator cross-tick memory, not target-repo state --
    anchored via state_paths, never `root`. ..."""
    return state_paths.orchestrator_state_path(PARK_STATE_FILENAME)
```
one shared file, no repo dimension in `load_park_state`/`_save_park_state`/
`parked_report` anywhere in this function cluster.

Reproduced the leak live, on the PR branch, with a short script run from
`/tmp/pr3084-check` (STATE_ROOT patched to a temp dir via
`mock.patch.object(state_paths, "STATE_ROOT", ...)`):

```python
state = spawn_on_pr.load_park_state(root_a)
state["issue-3059"] = {"parked": True, "blocked": True}
spawn_on_pr._save_park_state(root_a, state)
parked_b = spawn_on_pr.parked_report(root_b)   # sweeping a DIFFERENT repo
```
derived: ran the script above — result:
```
parked_report(root_b) sees: ['issue-3059']
LEAK CONFIRMED
```
The exact defect shape from the issue's original report
(`spawn-on-pr: waiting-for-human 1건: ['issue-3059']`, `issue-3059` being
an on-the-record issue leaking onto study-companion's board) is still live
on PR #3084's branch, unchanged from `main`.

PR #3084's own record does not mention spawn-on-pr at all.
derived: `git show pr-3084-review:docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f.md | grep -in "spawn-on-pr\|waiting-for-human\|park"`
(that record path is untracked here) — result: no match (empty output).
This was not investigated by that session, not investigated-and-found-clean.

### 5. Issue's own literal acceptance check 1

derived: `grep -n "__main__" watchdog.py` (inside `/tmp/pr3084-check`) —
result: no match — no script entrypoint exists.
derived: `python3 watchdog.py --once --repo /home/jwjung/study-companion`
(inside `/tmp/pr3084-check`) — result: no output, exit 0.
derived: `bash -c "python3 watchdog.py --once --repo /home/jwjung/study-companion 2>&1 | grep -c 'issue-30\|30[0-9][0-9]' | grep -qx 0"`
(the issue's exact check, inside `/tmp/pr3084-check`) — result: exit 0
(passes), because `grep -c` on empty stdin prints `0` and `grep -qx 0`
then matches that trivially. `requirement_drift()` is never invoked by
this command. Re-ran the identical command against `main` at `573e7382`
(before any fix existed) — same result, exit 0, for the same reason: no
CLI surface existed on `main` either, so this check cannot distinguish
pre-fix from post-fix and is Unverifiable as literally written, not
Present or Absent.

### 6. Full suite, both branches, from scratch

derived: `python3 -m pytest tests/ -q` inside `/tmp/pr3084-check` (PR
branch, commit `4fefe107`) — result:

```
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_when_gate_finds_none
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_never_silent_even_without_pr_number
5 failed, 189 passed, 2 warnings in 10.46s
```

derived: `python3 -m pytest tests/ -q` inside `/tmp/main-check` (`main`,
commit `573e7382`) — result:

```
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_never_silent_even_without_pr_number
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_still_respawns_genuine_crash
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_proceeds_without_deliverable_when_gate_finds_none
FAILED tests/test_respawn_deliverable_gate.py::AutoRespawnConsultsDeliverableGateTest::test_respawn_skip_is_reported_names_the_pr_in_stderr_and_ledger
5 failed, 182 passed, 2 warnings in 7.08s
```

Same 5 failure names both sides, 189-182=7 net-new passes on the PR branch
— matches the new test file's own test count, `tests/test_requirement_drift_repo_scope.py` (untracked).
derived: `grep -c "^    def test_" tests/test_requirement_drift_repo_scope.py`
(inside `/tmp/pr3084-check`) — result: `7`. Zero new failures, zero fixed
pre-existing failures. Not attributing the 5 failures to this PR: same
names/count on both branches, and the PR's diff (step 1) touches neither
`test_respawn_deliverable_gate.py`'s subject (`spawn_respawn.py`/
deliverable-gate logic) nor `hooks.json`.

This session's own measured baseline (182 passed on `main`) differs from
the "5 failed / 105 passed" figure given in the spawning prompt. Re-derived
directly against current `main` rather than assuming the prompt's figure;
105 does not match anything measured in this session.

## Why

Every check above was re-run from a fresh worktree on the PR's actual head
commit rather than cited from the PR's own description, per the
defect-verification-independence-from-upstream-verdicts skill. Two things
got extra weight specifically: mutation testing the report-time filter and
the retention logic (step 3), because a rerun-only verification (just
execute the same probe/tests the PR wrote alongside its own fix) cannot
distinguish "the filter is real" from "the filter looks real and happens
to pass the one probe written to test it" — this task's own assignment
named that exact risk ("check specifically that the fix is not merely
cosmetic filtering at print"). And a from-scratch reproduction of the
spawn-on-pr leak (step 4) rather than a grep for its name in the diff,
because an empty diff on `gates/spawn_on_pr.py` is consistent with either
"already fine, nothing to fix" or "not checked at all" — the issue text
says both signals leaked in the same tick on the same board, so silence
needed a live check, not an inference from absence.

## Upstream basis

See frontmatter `upstream:`. Also: issue #3081 and its 7 comments
(`gh issue view 3081 --repo tokenmaxxxer/on-the-record --comments`,
cited in "What was done" above), and PR #3084's own record — the path
is untracked here, `docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f.md` (untracked), read via `git show pr-3084-review:<that path>`. Checked
against independent re-derivation, not cited on trust:
derived: `git show pr-3084-review:docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f.md | grep -in "spawn-on-pr\|waiting-for-human\|park"`
— result: no match, confirming the absence noted in step 4 above.

## Open findings

**Absent — issue's second must-not not covered.** PR #3084 fixes
`requirement_drift`'s cache attribution and retention but does not touch
`gates/spawn_on_pr.py` (tracked on main; exists on both `main` and PR
#3084's branch, unchanged by the PR — see step 4 above). The issue's
acceptance section says explicitly: "Do not scope the fix to
`requirement-drift` alone without checking whether `spawn-on-pr`'s
`waiting-for-human` list leaks the same way; both were observed doing it
in the same tick." This session reproduced that exact leak live on PR
#3084's own branch —
canonical: step 4 above, this session's own script run — `parked_report(root_b)`
returned `['issue-3059']` after only `root_a`'s park state was written.
Resolution path: a follow-up applying the same `repo:number`-style keying
used in `watchdog._drift_cache_key` to `gates/spawn_on_pr.py`'s park-state
entries (`load_park_state`/`_save_park_state`/`parked_report`) is needed
before issue #3081's acceptance can be called fully met.

**Unverifiable — issue's own acceptance check 1 does not exercise the
fix.** See step 5 above. Not a defect in PR #3084 itself (no `--once`/
`--repo` CLI existed on `main` before it either) — a defect in the issue's
own acceptance check, worth flagging back on the issue.

## Next steps

canonical: this session's own transcript above (steps 1-6 under "What was
done") — the basis for closing this record at `loop_state: landed`.

None from this session beyond the two Open findings above — this is a
terminal verification record. Whether to reopen scope on PR #3084 or file
a follow-up for the spawn-on-pr gap is an operator/board decision, not
something this defect-verification session resolves itself, per the
defect-verification-independence-from-upstream-verdicts skill (report the
verdict; don't quietly fix the upstream deliverable from inside a
verification pass).

## What did not work

Nothing to report — the mutation tests, the pre-fix reproduction, and the
spawn-on-pr reproduction all worked as designed on the first attempt.

## Rationale for deviations

No deviations from the assignment. Grading against the assignment's own
four items:

- Acceptance 1 (heartbeat reports only its own repo's issues/PRs):
  Present for `requirement_drift` (step 3, mutation-tested); Absent for
  `spawn-on-pr`'s `waiting-for-human` (step 4, untouched, leak reproduced
  live); the issue's own literal check for this criterion is Unverifiable
  (step 5, no CLI surface). Net: partial — not fully met while
  `spawn-on-pr` still leaks.
- Acceptance 2 (mechanism named): Present.
  derived: `grep -rn 'cross-repo\|foreign repo' docs/issue-3081/reports/[a-z]*.md`
  (inside `/tmp/pr3084-check`; the matched record path is untracked here)
  — result:
  `...ba2a806f.md:143:cross-repo-mismatch case would classify as Handled` —
  match found, exit 0.
- Must-not 1 (cache stays orchestrator-scoped): Present (step 1, diff +
  grep).
- Must-not 2 (foreign-repo lookup failure not silently retained,
  distinguishable from same-repo transient failure): Present (step 3,
  mutation-tested).

canonical: this session's own transcript — the Skill tool was called for
all three skills below only after PR #3093 was already opened (flagged by
the Stop hook's skill-verdict-guard); see the deviation log entry under
`deviation-log/` for the correction. The verification work itself (steps
1-6 above) already matched each skill's actual procedure once read.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked, after landing; every claim re-derived from a fresh
worktree on the PR's actual head commit rather than cited from PR #3084's
own record, including re-running the pre-fix reproduction myself and
mutation-testing both fixes rather than accepting "the probe passes" at
face value.
skill-verdict: adversarial-review — applied: invoked, after landing;
treated PR #3084's record and test-plan checklist as an artifact to
check, not a source of truth — the "5 pre-existing failures unrelated to
this change" and "no CLI surface" claims were independently re-derived
(full suite on both branches, `grep -n "__main__"`), and the spawn-on-pr
silence in the PR's own record was treated as a gap to investigate rather
than evidence of nothing to find.
skill-verdict: silent-failure-audit — applied: invoked, after landing;
checked the retention branch's two failure paths (same-repo lookup
failure vs. cross-repo lookup failure) are both classified as Handled
with a distinct printed line (`requirement-drift-cache-retained:` vs.
`requirement-drift-unknown:`), not one falling silently to a no-op —
verified by mutation (step 3) that the distinction is structurally real.

other mounted skills: not triggered — `work-in-english` (this record and
PR #3093 were already written in English, nothing needed translating) and
`implementation-audit` (this task used the dedicated
`defect-verification-independence-from-upstream-verdicts` skill instead
of the two-session implementation-audit protocol) were mounted but not
invoked via the Skill tool.

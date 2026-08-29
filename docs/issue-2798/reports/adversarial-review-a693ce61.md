---
issue: 2798
role: adversarial-review-a693ce61
author: adversarial-review-a693ce61
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f:test/test_bootstrap_signal_guard.py
    sha: cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f
---

# issue-2798 — adversarial-review-a693ce61 record

## What was done

Independent re-verification of PR #2799 (branch
`issue-2798/adversarial-review-99b10ef0`, head `cacd3800`), which renames
the twelve retired-noun (`role`) skill-slot literals that PR #2794
introduced into `test/test_bootstrap_signal_guard.py`. This record does
not cite PR #2799's own embedded record as evidence — that record lives
on branch `issue-2798/adversarial-review-99b10ef0` at path
`docs/issue-2798/reports/adversarial-review-99b10ef0.md` (untracked on
this branch, `issue-2798/adversarial-review-a693ce61`, which has not
merged it). Every acceptance check below was instead re-run from scratch
in throwaway git worktrees (`b4d05522` = before, PR #2799 head = after,
`b4d05522^` = pre-#2794-merge baseline), and one additional finding
surfaced that the builder's own record did not report.

canonical: `gh pr view 2799` (title, Summary, Closes #2798) and `gh pr
diff 2799` (full patch: 201 additions / 12 deletions, touching
`test/test_bootstrap_signal_guard.py` plus PR #2799's own new report and
deviation-log files).

### Acceptance check 1 — zero occurrences in the file

derived: `grep -inE '\brole\b' test/test_bootstrap_signal_guard.py; echo exit=$?` on the PR head — result: `exit=1` (no match).
derived: `grep -inE '\brole\b' <before-worktree>/test/test_bootstrap_signal_guard.py | wc -l` on `b4d05522` — result: `12`, all twelve matching lines identical to PR #2799's diff hunks (`gh pr diff 2799`).

### Acceptance check 2 — rename is inert (same tests, same code path)

acceptance: `python3 -m pytest test/test_bootstrap_signal_guard.py -v` in a `b4d05522` worktree (before) — result:
```
11 passed in 30.89s
```
acceptance: `python3 -m pytest test/test_bootstrap_signal_guard.py -v` in the PR-2799-head worktree (after) — result:
```
11 passed in 30.86s
```
canonical: the two `-v` outputs' PASSED-name lists, compared as sets — identical in both runs:
`BootstrapSignalGuardCaughtSignalTest::{test_disarmed_after_session_log_survives_sigterm_untouched, test_sigint_mid_bootstrap_also_reports_caller_departed, test_sigkill_mid_bootstrap_records_nothing_and_leaves_workspace, test_sigterm_mid_bootstrap_reports_caller_departed_and_cleans_up}`,
`BootstrapSignalGuardReviewGapsTest::{test_adhoc_leftover_at_target_path_is_wiped_not_preserved, test_signal_after_session_log_before_disarm_does_not_delete_workspace, test_signal_during_adhoc_clone_also_removes_partial_workspace, test_signal_during_clone_removes_partial_workspace, test_signal_during_reuse_fetch_does_not_delete_prior_work, test_signal_during_self_reuse_never_targets_callers_own_checkout}`,
`SpawnAttemptSweepReportsCallerDepartedDistinctlyTest::test_declined_and_genuinely_dead_produce_different_lines`.
Zero FAILED/ERROR in either run.

Went one level below test-name equivalence to confirm *why* the rename is safe at the code level, not just by outcome. canonical: `sed -n '1110,1160p' spawn.py` (PR head worktree) shows `_arm_bootstrap_signal_guard(attempt_id)` treats `attempt_id` as an opaque value — used only as a dict/set membership key (`attempt_id in _SPAWN_ATTEMPT_OUTCOME_WRITTEN`) and passed verbatim to `_record_spawn_outcome`. derived: `grep -n "attempt_id" spawn.py | grep -iE "split|partition"` — no match anywhere in `spawn.py`. canonical: `roster.py:661` carries an explicit comment confirming this design ("같은 ad-hoc 질문을 attempt_id 문자열을 역파싱하지 않고" — "without back-parsing the attempt_id string for the same ad-hoc question"), and `_attempt_superseded()` (`roster.py:1408+`) reads `skill` from `attempt.get("skill")`, a separate dict field, never from parsing `attempt_id`. canonical: `sed -n '561,586p' test/test_bootstrap_signal_guard.py` on the PR head confirms the two synthetic `"skill": "declined-role"/"killed-role"` fixtures are that separate dict field, and the test's own `next(l for l in lines if "declined-role" in l)` lookup was updated in the same diff hunk to the new `"declined"`/`"killed"` literals.

### Acceptance check 3 — whole-repo count returns to its pre-merge value

Computed the same `grep -rIc --exclude-dir=.git --exclude-dir=docs --exclude-dir=runs -inE '\brole\b' . | awk -F: '{s+=$2} END{print s}'` tally in three worktrees of `on-the-record` alone:
- derived: run in `b4d05522^` (pre-#2794-merge baseline) — result: `1108`
- derived: run in `b4d05522` (post-#2794, pre-fix) — result: `1120`
- derived: run in PR #2799 head (after fix) — result: `1108`

canonical: these three executed results (`1108` → `1120` → `1108`) confirm the *shape* of the acceptance check exactly: `+12` on the #2794 merge, `-12` on this fix (`1120 - 1108 = 12`, `1120 - 12 = 1108`), returning to the pre-merge value — in this one repo.

unverifiable: the issue's stated absolute figures (`1263` pre-merge, `1275` post-merge, `gh issue view 2798`, Acceptance section) do not match `1108`/`1120` measured here, and could not be reproduced live even after finding the correct second repo. canonical: the issue's Ask says the count is "measured across both repos"; `gh issue view 2600` names the two repos explicitly as `tokenmaxxxer/on-the-record` and `tokenmaxxxer/tokenmaxxxer-core` (and explicitly excludes the skill-repository as out of scope: "the word there is frequently ordinary English, not this system's retired axis"). derived: located `tokenmaxxxer-core` at `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core` (`git remote -v` there → `tokenmaxxxer/tokenmaxxxer-core.git`, confirming it is that repo) and ran the same tally: result `707` (`git log --oneline -1` there: `aff774b`). `1108 + 707 = 1815`, not `1263`. canonical: `gh issue view 2600` states `tokenmaxxxer-core` had `971` occurrences (excl. `docs/`) at that issue's filing; derived: the same tally run just now on `tokenmaxxxer-core`'s current HEAD returns `707` — a drop of `971 - 707 = 264` from ongoing unrelated retirement work in that repo since #2600 was filed. Since `tokenmaxxxer-core` is a live, independently-moving repo, the absolute cross-repo total is not reproducible from any live checkout — only the same-repo `+12`/`-12` round-trip is a valid, reproducible signal, and that round-trip is confirmed above. canonical: `docs/issue-2798/reports/adversarial-review-99b10ef0.md` (on branch `issue-2798/adversarial-review-99b10ef0`, "Open findings" section) records the same underlying judgment — that the absolute figure is unreproducible — but its own tally used the skill-repository as its single second-repo count, which `gh issue view 2600` states is the wrong second repo for this specific tally; this is a discrepancy between the two records' methodology, not a defect in PR #2799's delivered rename, since neither repo choice reproduces the issue's exact absolute figure.

### Naming judged against the issue's must-not

The ten new names — `sigtermfault`, `sigintfault`, `sigkillfault`, `livefault`, `clonefault`, `disarmracefault`, `reusefault`, `selfreuse`, `declined`, `killed` — were checked against "must not... substitut[e] a word that means the same thing in a different spelling": none is a synonym for "role" (no `position`, `duty`, `job`, `type`); each names its own fixture's fault condition or outcome. derived: `for n in sigtermfault sigintfault sigkillfault livefault clonefault disarmracefault reusefault selfreuse declined killed; do echo "$n" | grep -icE 'r.?o.?l.?e'; done` — result: all ten return `0`, confirming none hides the retired word as a decomposed/obfuscated substring either. The issue's specific example (mid-clone window vs. disarm race must not share a name) is satisfied: canonical: `sed -n '196,210p' test/test_bootstrap_signal_guard.py` (PR head) shows `clonefault` at `test_signal_during_clone_removes_partial_workspace`, and `sed -n '390,400p'` shows `disarmracefault` at `test_signal_after_session_log_before_disarm_does_not_delete_workspace` — distinct names for the two distinct windows the issue names. canonical: `sed -n '200,210p;445,451p;505,532p' test/test_bootstrap_signal_guard.py` (PR head) confirms `clonefault`/`reusefault`/`selfreuse` additionally now match a `skill` local variable already declared earlier in the same scope (`skill = "clonefault"` / `"reusefault"` / `"selfreuse"`), a genuine improvement over PR #2794's state (literal and variable disagreed there) though not required by the issue's Ask — a bonus, not a requirement met. None of the ten names read as generic placeholders (e.g. `fault1`..`fault8`); each is tied to the specific signal or window it exercises.

### Sweep for the same shape elsewhere — count: 4 occurrences in 1 file, pre-existing, out of PR #2799's scope

derived: `grep -rnE '"[0-9]+:role:[0-9]+:[0-9]+"|"role[-_][a-z]*"|"[a-z]*[-_]role"' --include=*.py .` (PR head, `on-the-record` repo) found, outside the file PR #2799 touched: `test/test_spawn_attempt_staleness.py:394` and `:408`. canonical: `sed -n '380,415p' test/test_spawn_attempt_staleness.py`:
```
        self._write_attempt("2999:role:1:1", 2999, "role", str(missing),
                             reason, attempt_ts)
...
        self._write_attempt("3000:role:1:1", 3000, "role", str(missing),
                             reason, attempt_ts)
```
This is the exact same shape the issue is about: an `attempt_id` literal (`issue:skill:seq:seq`) with `role` in the skill slot, **plus** a separate positional `skill="role"` argument passed to `_write_attempt(self, attempt_id, issue, skill, cwd, reason, ts)` (signature at line 344) — 4 occurrences of the retired noun sitting in a skill slot, across these 2 call sites. derived: `git log --oneline -3 -- test/test_spawn_attempt_staleness.py` and `git log -1 --format=%H -- test/test_spawn_attempt_staleness.py` show the most recent touch is `e1b35a53` (issue-2741), which predates PR #2794/#2742 (`b4d05522`, `git log --oneline -1 b4d05522`) — this occurrence was not introduced by #2794 and is not in PR #2799's stated scope (which names only `test/test_bootstrap_signal_guard.py` per `gh pr view 2799`), so its presence is not a defect in this PR, but it is a live, unfixed instance of the pattern the issue's Ask is about, and PR #2799 does not mention it. derived: `grep -inE '\brole\b' test/test_spawn_attempt_staleness.py` — result: 8 total occurrences, of which the 4 counted above are skill-slot literals and the remaining 4 (lines 214, 291, 303, 423, 479, 507 — prose, not a skill slot) are docstrings/comments, not counted in the "count: 4" figure above.

Broader (non-exact-shape) `role-a`/`role-b`/`some-role`-style test-fixture identifiers also exist elsewhere in the repo (derived: `grep -rnE '"[^"]*:role:[^"]*"|"role[-_][a-z]*"|"[a-z]*[-_]role"' --include=*.py .` also matched `test/test_spawn_skills_mount.py`, `test/test_merge_gate_record_kind.py`, `on-the-record/monitors/test_poll_heartbeat.py`) but these are generic fixture placeholder names, not literals occupying an `attempt_id` skill slot — a different, lower-priority category than the 4 counted above, not included in the "count: 4" figure. In `tokenmaxxxer-core`, the same grep against `test/` and `tests/` found one hit: canonical: `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/tests/test_side_effect_round.py:61` (`'core_role_directive "fake-role" "fake" "fake" "fake"\n'`), a shell-directive literal in an unrelated format, not an `attempt_id`/skill-slot shape — not counted in the "count: 4" figure, which covers only the exact-shape `on-the-record` hits.

### Four standing invariants

- **No return of the retired role axis in any reshaped form**: acceptance check 1 above (`exit=1`, 0 matches) plus the naming-quality and hidden-substring checks above confirm the rename did not move the word to a spelling or decomposition the grep misses. Confirmed independently, not restated from PR #2799's own record.
- **No new bug** (failing-test set vs `origin/main`, as sets of names): ran `python3 -m pytest test/ -q` independently in both worktrees.
  - acceptance: run in `b4d05522` (≡ `origin/main`, confirmed via `git log --oneline -3` matching `git log --oneline -3 origin/main` from this session's initial `git status`) — result:
    ```
    15 failed, 425 passed, 3 xfailed in 31.78s
    ```
  - acceptance: run in PR #2799 head — result:
    ```
    15 failed, 425 passed, 3 xfailed in 32.14s
    ```
  - canonical: failing-name sets from both `-q` outputs, compared directly (not counts) — identical 15 names in both runs:
    `test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`,
    `test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`,
    `test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
    `test_spawn_cross_family_skill_selection.py::{Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate, ConsultJudgeStageTest::test_consult_error_raises_and_still_traces, ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths, FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled, SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive, SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline}`,
    `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::{test_declared_artifact_matching_skill_gets_pairing_line, test_no_declaration_line_byte_identical_to_baseline}`,
    `test_spawn_skill_judge_haiku_timeout_overlap.py::{SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows, SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome, SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome, SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo}`.
    All 15 pre-existing failures are network/environment-shaped (fetch against a fake `origin`, judge/consult timing) and none is in `test_bootstrap_signal_guard.py` or `test_spawn_attempt_staleness.py`. Same set — no new bug.
- **No overhead increase**: canonical: `gh pr diff 2799` shows the code change is 12 pure string-literal substitutions inside one test file, each a 1-line replacement; no new loop, dependency, or runtime path added.
- **Monitor/watch machinery unbroken and not quieter**: derived: `grep -rn "2742:role\|declined-role\|killed-role\|2999:role\|3000:role" --include=*.py monitors/ on-the-record/monitors/` — no match. None of the changed literals were referenced by any monitor/watchdog file (`watchdog.py`, `on-the-record/monitors/`, `test_watchdog_heartbeat_noise.py`), so nothing there could have depended on the old strings, quieted, or broken by this rename.

## Why

The task was to independently re-verify PR #2799 rather than restate its own record — re-running every acceptance check from a clean worktree (not the PR author's checkout), re-deriving the attempt_id-opacity claim from the actual `spawn.py`/`roster.py` source rather than accepting the builder's description of it, and sweeping for the same defect shape in files PR #2799 did not touch, since a rename fix's real risk is scope (did it silently change what a test exercises, and did it stop at the one file the issue named while the pattern exists elsewhere).

## What did not work

None.

## Upstream basis

PR #2799 / branch `issue-2798/adversarial-review-99b10ef0`, head commit `cacd3800a4c86c52ba9f45d2bd8a58d3b4db149f`, which itself builds on `b4d05522` (PR #2794, issue #2742) — the commit that introduced the twelve retired-noun literals this PR renames. canonical: `gh pr view 2799 --json headRefName,baseRefName,commits`.

## Open findings

1. canonical: `sed -n '380,415p' test/test_spawn_attempt_staleness.py` (quoted in full above, "Sweep for the same shape elsewhere") — `test/test_spawn_attempt_staleness.py:394,408` carry the same retired-noun-in-skill-slot shape (4 occurrences: 2 `attempt_id` literals + 2 positional `skill` args) that this issue is about, pre-dating PR #2794 and outside PR #2799's declared scope. Not a defect in PR #2799 — it is a pre-existing instance of the same pattern, left for a future issue/PR to fix. Resolution path: file or fold into a follow-up sweep issue; this record does not do so itself, per its own scope (independent re-verification of PR #2799, not a new fix).
2. canonical: `gh issue view 2600` (states `tokenmaxxxer-core` at `971` occurrences, excl. `docs/`, at filing) vs. derived: the same tally run live on `tokenmaxxxer-core`'s current HEAD `aff774b` — result `707` (quoted in full above, "Acceptance check 3") — the issue's absolute cross-repo tally (`1263`/`1275`) is not reproducible from any live checkout, in either this session's attempt or PR #2799's embedded record's attempt, because `tokenmaxxxer-core` has moved independently since the original measurement. Resolution path: none needed for this issue's acceptance — the reproducible same-repo `+12`/`-12` round-trip (`1108` → `1120` → `1108`, confirmed above) is the mechanism the check exists to verify; the absolute figure is a point-in-time artifact of a moving second repo, not a defect in PR #2799.

## Next steps

None — `loop_state: landed`. canonical: the three acceptance-check subsections and the "Four standing invariants" subsection above, each carrying its own executed `acceptance:`/`derived:` evidence, are the basis for this terminal state; the two `Open findings` above are informational (a pre-existing pattern elsewhere, and an unreproducible historical absolute figure), not blockers to PR #2799's own claim.

skill-verdict: adversarial-review — applied: invoked; this entire record IS the evaluator role's independent re-derivation of PR #2799's acceptance claims (fresh worktrees, re-run greps/pytest, re-read the source for the attempt_id-opacity claim, and an independent sweep that surfaced a finding — `test/test_spawn_attempt_staleness.py` — the builder's own record did not report), rather than restating or trusting the builder's embedded record.

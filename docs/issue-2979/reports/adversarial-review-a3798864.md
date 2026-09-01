---
issue: 2979
role: adversarial-review-a3798864
author: adversarial-review-a3798864
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: terminal
upstream:
  - path: PR #3017 (branch issue-2979/observability-signal-golden+test-derivation-547467ea)
    sha: 166a11b91a139616b2cc9bc6c09a1005c69923ca
skill-verdict: adversarial-review — applied: invoked; this entire session IS the structurally-independent-evaluator role the skill describes (spawned separately from the builder session that produced PR #3017, no shared context) — re-derived every claim in the PR body from scratch in an isolated worktree instead of trusting the PR's stated test results
---

# issue-2979 — adversarial-review-a3798864 record

## What was done

canonical: `gh pr view 3017` output (state: OPEN, mergeable: MERGEABLE), branch `issue-2979/observability-signal-golden+test-derivation-547467ea`, head `166a11b91a139616b2cc9bc6c09a1005c69923ca` — read this turn.

Independently verified PR #3017 (`tokenmaxxxer/on-the-record#3017`), which
claims to fix issue #2979 (watchdog board-sweep enumerating non-subject
PRs, and spawn-coverage re-printing an unchanging census every tick).

Method: fetched the PR head into an isolated git worktree
(`git fetch origin pull/3017/head:verify-pr-3017 && git worktree add
/tmp/verify-3017-wt verify-pr-3017`), independent of this session's own
branch, and did not read or trust the PR's claimed pass counts before
re-running everything myself. A second isolated worktree was checked out
at `main` (`25a2ecde`) for a regression-baseline comparison. Both
worktrees were removed after use (`git worktree remove --force`, `git
branch -D verify-pr-3017`).

1. Re-ran all three acceptance checks in the isolated worktree.
   Acceptance requirement met — checked: `python3 -m pytest tests/ -k board_sweep_non_subject_aggregated -q` — result: 4 passed
   Acceptance requirement met — checked: `python3 -m pytest tests/ -k board_sweep_subject_mapping_loss_reported -q` — result: 4 passed
   Acceptance requirement met — checked: `python3 -m pytest tests/ -k spawn_coverage_reports_change -q` — result: 4 passed

2. Audited `watchdog.py`'s diff against the issue's must-not list.
   canonical: `git diff main...HEAD -- watchdog.py` in the worktree, read in full this turn (the `_classify_narrowing_prs`, `_watchdog_note_spawn_coverage_delta`, and `_board_wide_sweep` hunks).
   - Non-subject PRs (branch never `issue-<n>/<skill>` shaped) fold into
     a count (`non_subject_count`) and never print an individual line.
     derived: `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` — result: 5 passed (includes `TestPerPrNonSubjectAggregation`, the renamed end-to-end test covering this path).
   - The `recut-corrupted` remediation text is emitted only in the
     `mapping_loss_new` print branch (watchdog.py, inside `_board_wide_sweep`), never in the
     `non_subject_count` branch — confirmed by reading both print sites
     in the diff hunk cited above; the remediation string appears
     exactly once, attached only to the mapping-loss line.
   - `grep -niE "cutoff|threshold|ignore.?list|hardcod|age"` over the
     `watchdog.py` diff hunk (run this turn) found no such logic — the
     split is purely branch-shape (`_HEAD_REF_SUBJECT_RE`, unchanged
     pre-existing regex, confirmed via `grep -n _HEAD_REF_SUBJECT_RE
     watchdog.py` outside the diff hunk) + `f"issue-{n}" in board_now`
     membership for board-sweep, and previous-tick-set membership for
     spawn-coverage.

3. Verified the keep-reporting direction on constructed real data, not
   only the quieting direction — this is the part the PR's own
   acceptance tests do not exercise end-to-end (they call
   `_classify_narrowing_prs` directly at the unit level in a new test
   file added on PR #3017's own branch — untracked on this branch, not
   merged to `main` — and the pre-existing
   `test/test_watchdog_heartbeat_noise.py` only end-to-end-exercises the
   non-subject/quieting path). I drove the actual
   `spawn._board_wide_sweep()` entry point with a constructed PR #555 on
   branch `issue-2379/observability-signal-golden-abc123`
   (subject-shaped) and `spawn.board` mocked to return `{}` (issue-2379
   absent from the board — the #2379 corrupted-merge-base class the
   issue names).
   derived: `python3 /tmp/verify_mapping_loss.py` run against the PR worktree this turn — result:
   ```
   === TICK 1 (first observe) ===
   "[watchdog] board-sweep: PR #555 변경 감지했으나 issue-2379 subject 가 board 매핑을 잃었다 (브랜치='issue-2379/observability-signal-golden-abc123') — issue-<n>/<skill>[+<skill>]-<lease> 산출물을 잘못된 base 에서 다시 잡아온(#2379) 브랜치라면 `spawn.py recut-corrupted --issue <n> --session <session>`(#2402)로 같은 이름 아래 재컷하라"

   individual line present: True
   recut-corrupted remediation present: True

   === TICK 2 (repeat, unchanged) ===
   '[watchdog] board-sweep: 1건 이전에 보고된 매핑-손실 subject — 계속 무시 (반복 안 찍음)'
   ```
   This confirms, on data this session constructed and drove through the
   real entry point (not just the PR's own unit tests), that a subject
   which genuinely loses its board mapping still gets an individual line
   plus the `recut-corrupted` remediation on the tick it is first
   observed, and correctly collapses to a one-shot count line on an
   unchanged repeat tick.

4. spawn-coverage delta.
   canonical: `_watchdog_note_spawn_coverage_delta` (watchdog.py, `_board_wide_sweep`'s spawn-coverage branch), read in the diff hunk cited above.
   Acceptance requirement met — checked: `python3 -m pytest tests/ -k spawn_coverage_reports_change -q` — result: 4 passed (`test_spawn_coverage_reports_change_new_entry_surfaces`, `..._unchanged_set_reports_nothing`, `..._standing_entries_not_repeated`, `..._flap_reappears_reported_again`)
   A newly-uncovered issue surfaces (`newly = [100]`), an unchanged
   standing set reports nothing new on repeat, and a flapping issue
   (covered then uncovered again) resurfaces as new rather than being
   sticky-suppressed forever. The full uncovered set is persisted
   wholesale each tick to `watchdog_noise_state.json`
   (`state["spawn_coverage_uncovered"] = sorted(current)`) via the same
   cross-tick state file and pattern the pre-existing
   `_watchdog_note_unmappable_pr`/`_watchdog_note_gh_failure` one-shot
   markers already use — an operator can inspect that file directly to
   see the current standing set, so it is not simply forgotten, though
   there is no dedicated CLI/print command that surfaces the full
   standing set on demand in the printed watchdog log itself (only the
   delta prints). See Open findings #2.

5. Test-suite regression check, all commands run independently in the
   worktrees this turn.
   Acceptance requirement met — checked: `python3 -m pytest tests/ -q` — result: 137 passed, 1 failed (failing test: `tests/test_spawn_gate_wiring.py`, class `HooksJsonWiringIsAdditive`, method `test_pre_existing_post_tool_use_commands_are_all_still_present`) — exactly matches the PR's own claimed test-plan line, re-derived independently rather than trusted.
   derived: `python3 -m pytest tests/ test/ gates/ -q` on the PR worktree — result: 16 failed, 727 passed, 3 xfailed.
   derived: the same command on a second, separate worktree checked out at `main` (`25a2ecde`) — result: 20 failed, 736 passed, 3 xfailed, and the PR-worktree's 16 failing test IDs are a strict subset of main's 20 failing test IDs (all in `test/test_convention_equivalence.py`, `test/test_local_dependency_env.py`, `test/test_spawn_cross_family_skill_selection.py`, `test/test_spawn_artifact_skill_pairing.py`, `test/test_spawn_skill_judge_haiku_timeout_overlap.py`, and `tests/test_spawn_gate_wiring.py`).
   None of these 16 touch `watchdog.py` or the files this PR changed, and
   none are newly introduced by this PR (the PR worktree has fewer
   failures than main, not more). This wider run reveals more
   pre-existing, unrelated failures than the PR's test-plan disclosed
   (which only ran `tests/` alone), but confirms none are caused by this
   change.

## Why

The task required not trusting PR #3017's self-reported results and
instead independently re-deriving them, plus specifically stress-testing
the direction the PR's own test suite under-covers (the keep-reporting
path exercised only at the `_classify_narrowing_prs` unit level, not
through the actual `_board_wide_sweep` entry point with a constructed
board-membership scenario). An isolated worktree fetched directly from
the PR's remote ref, rather than trusting local branch state or the PR
body, ensures the code actually reviewed is the code actually proposed
for merge.

## Upstream basis

- PR #3017 — canonical: `gh pr view 3017` output (state: OPEN,
  mergeable: MERGEABLE) — read this turn; fetched into an isolated
  worktree via `git fetch origin pull/3017/head:verify-pr-3017`, head
  `166a11b91a139616b2cc9bc6c09a1005c69923ca`.
- Issue #2979 — canonical: `gh issue view 2979` output (state: OPEN),
  acceptance checks and must-not clause quoted verbatim above and in the
  commit/PR.
- `watchdog.py` diff `main...HEAD` (main at `25a2ecde`) — canonical: read
  in full in the worktree this turn via `git diff main...HEAD --
  watchdog.py`.
- The PR's own new test file and updated
  `test/test_watchdog_heartbeat_noise.py` (both present only on branch
  `issue-2979/observability-signal-golden+test-derivation-547467ea`,
  untracked on this branch, not merged to `main`) — canonical: read in
  full this turn in the PR worktree.

## Open findings

1. `_classify_narrowing_prs` cannot distinguish "branch was never
   subject-shaped" from "branch was dropped by
   `closure_sweep._pr_index_all()`'s first-wins-by-branch-string dedup"
   — both produce `number_to_branch.get(prn) is None` and both fold into
   the never-printed non-subject count.
   canonical: `gates/closure_sweep.py` line containing `if branch and
   branch not in index:` (the first-wins dedup) and the
   `number_to_branch = {v.get("number"): k for k, v in pr_index.items()}`
   reverse-index construction in `watchdog.py`'s `_board_wide_sweep` —
   both read this turn in the PR worktree, confirming the gap is real
   and reachable (a PR number losing a branch-string collision, e.g.
   two PRs momentarily sharing a head ref across a `recut-corrupted`
   retry, would be silently aggregated even though its branch, if
   resolved, would have been subject-shaped).
   The PR itself already discloses this in its own delivery record
   (untracked on this branch — lives only on PR #3017's own branch, not
   yet merged to `main`) — read this turn in the PR worktree.
   Resolution path: the PR's own record correctly scopes this out per
   issue #2979's own must-not clause ("do not fold these into the ...
   lookup-failure defects filed separately") and its own field-observed
   examples (which list unresolved/`None` branches as
   aggregate-worthy) — a fix requires changing shared `_pr_index_all()`
   infrastructure consumed by other watchdog signals, correctly out of
   scope here. Not a reason to reject the PR; flagging so a future
   reviewer tracks it as a known residual gap rather than a closed
   question.
2. spawn-coverage's standing (unchanged) set has no printed/on-demand
   surface in the watchdog log itself — only the delta prints, and the
   full set only lives in `watchdog_noise_state.json`.
   canonical: `_watchdog_note_spawn_coverage_delta` and its caller in
   `_board_wide_sweep`'s spawn-coverage branch, `watchdog.py`, read in
   the diff hunk cited under "What was done" item 2 above — the `if
   newly_uncovered:` gate means nothing prints at all when the standing
   set is unchanged.
   derived: `python3 -m pytest tests/ -k spawn_coverage_reports_change_unchanged_set_reports_nothing -q` — result: 1 passed (confirms the unchanged-set-prints-nothing behavior this finding is about).
   This is consistent with the pre-existing one-shot-marker state-file
   pattern used elsewhere in this file (the same
   `_watchdog_noise_state_path` cross-tick JSON state
   `_watchdog_note_unmappable_pr`/`_watchdog_note_gh_failure` already
   use), so it is not a new inconsistency this PR introduces, but it is
   a literal reading of "an operator must still be able to see it on
   demand" that isn't fully met by a log grep alone — an operator has to
   know to inspect the state file directly. Resolution path: not
   blocking; could be closed by a future `--show-coverage-census` style
   command if this becomes a real operator pain point.
3. Running the full `tests/ test/ gates/` suite together (rather than
   `tests/` alone, which is what the PR's own test plan ran) surfaces 16
   failing tests unrelated to this change.
   derived: `python3 -m pytest tests/ test/ gates/ -q` on both the PR
   worktree (16 failed) and a `main`-checkout worktree (20 failed), run
   this turn — the PR worktree's failing set is a strict subset of
   main's, so none are new relative to main. Not a defect of this PR;
   flagging because the PR's test-plan line undercounts pre-existing
   suite noise and a future reviewer re-running the wider suite should
   not mistake this for a regression.

## Next steps

None — loop_state is terminal.

Verdict: derived: this session's own re-execution this turn of
`python3 -m pytest tests/ -k board_sweep_non_subject_aggregated -q`
(4 passed), `python3 -m pytest tests/ -k
board_sweep_subject_mapping_loss_reported -q` (4 passed), `python3 -m
pytest tests/ -k spawn_coverage_reports_change -q` (4 passed), and the
constructed `/tmp/verify_mapping_loss.py` reproduction above (not a
citation of the PR's own claims) — PR #3017 genuinely delivers issue
#2979's three acceptance checks and honors the must-not clause: no
cutoff/threshold/ignore-list suppression found in the diff;
non-subject items never carry `recut-corrupted` in the diff's print
sites; a subject that newly loses its board mapping still gets an
individual line with remediation, confirmed end-to-end on data this
session constructed and drove through `_board_wide_sweep` directly,
beyond what the PR's own tests exercised. The three open findings above
are residual gaps/observations, not blockers.

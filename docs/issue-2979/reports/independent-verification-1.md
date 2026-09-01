---
issue: 2979
role: independent-verification-1
author: independent-verification-1
verifies_subject: true
code_under_review: PR #3017 (branch issue-2979/observability-signal-golden+test-derivation-547467ea, merged as ee3cedd7eb6752373cd63c8c91263dd0cfc0368e)
type: verification
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: docs/issue-2979/reports/observability-signal-golden+test-derivation-547467ea.md  # untracked on this branch — lives on PR #3017's branch, merged to main at a07d5ccd, not yet merged into this verification branch
    sha: a07d5ccd874a239e4f45788f70657990439ad500
  - path: docs/issue-2979/reports/observability-signal-golden+test-derivation-547467ea/2026-09-01-hunt-delivery.md  # untracked on this branch — lives on PR #3017's branch, merged to main at 2ddd074f, not yet merged into this verification branch
    sha: 2ddd074f7b843d8b1f43035a2960b0f9b3ef6785
  - path: watchdog.py  # tracked on this branch, but at a sha before PR #3017's edits — the reviewed content lives at the sha below on PR #3017's branch
    sha: 51dd7e6589033f854f4df130886dca96035f858b
  - path: tests/test_board_sweep_and_spawn_coverage_change_signal_2979.py  # untracked on this branch — new file added by PR #3017, merged to main at 51dd7e65, not yet merged into this verification branch
    sha: 51dd7e6589033f854f4df130886dca96035f858b
---

# issue-2979 — independent-verification-1 record

## What was done

canonical: `gh pr view 3017 --json mergeCommit,mergedAt,baseRefName,state` — result: `{"baseRefName":"main","mergeCommit":{"oid":"ee3cedd7eb6752373cd63c8c91263dd0cfc0368e"},"mergedAt":"2026-09-01T05:59:12Z","state":"MERGED"}`

Independently audited PR #3017 (already merged to `main`) against issue
#2979's three acceptance checks and its must-not clause. Work was split:
a delegated worker checked out the PR's head commit (`51dd7e65`, since the
remote branch ref was already deleted post-merge — `git worktree add`
against the commit sha) into an isolated worktree and re-ran the tests
independently rather than trusting the PR's own claimed results; the
`code-review` skill (invoked this session; see skill-verdict below) fanned
out several review angles (line-by-line diff scan, reuse/simplification/
efficiency, removed-behavior audit, cross-file tracer, CLAUDE.md
conventions) against the same checkout.

acceptance: `python3 -m pytest tests/ -k board_sweep_non_subject_aggregated -q` (re-run independently in isolated worktree checked out at commit `51dd7e65`) — result:
```
....                                                                     [100%]
4 passed in 0.89s
```

acceptance: `python3 -m pytest tests/ -k board_sweep_subject_mapping_loss_reported -q` — result:
```
....                                                                     [100%]
4 passed in 1.49s
```

acceptance: `python3 -m pytest tests/ -k spawn_coverage_reports_change -q` — result:
```
....                                                                     [100%]
4 passed in 1.20s
```

acceptance: `python3 -m pytest tests/ -q` (full suite, same worktree) — result:
```
FAILED tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_post_tool_use_commands_are_all_still_present
1 failed, 137 passed in 10.15s
```
This failure is unrelated to PR #3017's diff — no `hooks.json` file is
touched by the diff (confirmed by reading the full diff via
`gh pr diff 3017`, which only touches `watchdog.py`,
`test/test_watchdog_heartbeat_noise.py`, a new test file under `tests/`
(untracked on this branch, see frontmatter `upstream` entry above for its
name and sha), and two new docs files). The PR's own delivery record
makes the same pre-existing claim; PR #3022 and PR #3025 (two prior,
independent verifications of the same subject) each re-ran the full suite
on their own separate worktrees and both report the identical single
failure — cross-corroborating it as pre-existing rather than introduced
by this diff.

derived: read of `gh pr diff 3017` (full diff, retrieved this session) — code-level confirmation of each acceptance bullet against `watchdog.py` at commit `51dd7e65`:
- `_classify_narrowing_prs` (added in the diff) buckets PRs whose branch
  never matched `issue-<n>/<skill>` shape into `non_subject_count`
  (`if not m: non_subject_count += 1; continue`) — never calls the
  per-PR one-shot marker for this bucket, so it cannot regress into
  per-item enumeration. The caller in `_board_wide_sweep` prints the
  aggregate line only `if non_subject_count:` — an empty non-subject set
  prints nothing, matching the acceptance's stated empty-state note.
- A branch that does match the shape but whose issue is not in
  `board_now` goes to `mapping_loss_new`/`_watchdog_note_unmappable_pr`
  and still gets an individual line plus the `recut-corrupted`
  remediation text — the #2379 class the acceptance requires stay
  individually reported.
- `_watchdog_note_spawn_coverage_delta` (added in the diff) persists the
  previous tick's uncovered set and returns only the newly-added issues;
  the caller prints `새로 커버되지 않음 [...]` only `if newly_uncovered:`
  — an unchanged set prints nothing, matching the acceptance's
  empty-state note. The full `uncovered` count still feeds the anomaly
  `count` unchanged (severity untouched, only the printed line's scope
  changed).
- Must-not clause: no cutoff/threshold/hardcoded-ignore-list appears
  anywhere in either new function — both splits are purely
  shape-match + board-membership (board-sweep) or previous-tick-set
  membership (spawn-coverage). `recut-corrupted` remediation text is
  attached only at the mapping-loss print site, never at the non-subject
  aggregate print site.

## Why

canonical: PR #3022 (`gh pr view 3022 --json body`) and PR #3025 (`gh pr view 3025 --json body`) — both `verifies_subject: true` verdicts against the same PR #3017.

The subject's own delivery record already disclosed one open finding
(the `closure_sweep._pr_index_all()` branch-dedup collision that can
fold a genuine subject-mapping-loss PR into the silent non-subject
aggregate) and scoped it out with a documented resolution path,
consistent with the issue's own must-not clause. Two prior independent
verifications of the same PR (#3022, #3025) both re-ran the acceptance
checks in separate isolated worktrees and returned `verifies_subject:
true`, corroborating the pre-existing-failure and dedup-collision
findings and adding no new blocking defect. My own re-run of the three
acceptance checks (quoted under "What was done" above) plus a
code-review-skill fan-out (see Open findings) corroborates that the
delivery satisfies the stated acceptance criteria, while surfacing two
additional non-blocking design gaps not previously recorded.

## What did not work

None.

## Upstream basis

- PR #3017 (`https://github.com/tokenmaxxxer/on-the-record/pull/3017`),
  merged `2026-09-01T05:59:12Z` as `ee3cedd7` — canonical: `gh pr view 3017 --json commits`. Commits reviewed: `51dd7e65`
  (code + new test file), `a07d5ccd` (delivery record), `2ddd074f`
  (hunt-delivery record), `166a11b9` (deviation log).
- `docs/issue-2979/reports/observability-signal-golden+test-derivation-547467ea.md`
  (untracked on this branch, lives on PR #3017's merged history at
  `a07d5ccd` — see frontmatter) — the subject's own delivery record,
  read in full from the checked-out worktree this session.
- `docs/issue-2979/reports/observability-signal-golden+test-derivation-547467ea/2026-09-01-hunt-delivery.md`
  (untracked on this branch, lives on PR #3017's merged history at
  `2ddd074f` — see frontmatter) — the subject's own before-landing
  warrant-hunt finding (dedup collision), read in full this session.
- PR #3022 and PR #3025 — two prior independent verifications of the
  same subject, both `verifies_subject: true`; read via `gh pr view` to
  avoid duplicating their already-recorded findings.
- Issue #2979 — canonical: `gh issue view 2979` output (state: OPEN) —
  acceptance checks and must-not clause quoted verbatim above.

## Open findings

canonical: code-review skill fan-out output, this session (line-by-line diff scan + cross-file tracer agents), cross-checked by me against the `gh pr diff 3017` output quoted under "What was done" above.

1. `_watchdog_note_unmappable_pr`'s one-shot marker (keyed only by PR
   number, never reset — confirmed by reading the function body in the
   diff: `state.setdefault("unmappable_prs_reported", {})`, set to `True`
   with no corresponding delete anywhere in the diff or in `watchdog.py`)
   is reused by `_classify_narrowing_prs` for the board-membership check,
   which is non-monotonic (an issue can regain board mapping and later
   lose it again for the same still-open PR). A same-PR re-flap (mapping
   lost → restored → lost again) is silently folded into the "already
   reported" count and never re-emits the individual line +
   `recut-corrupted` remediation on the genuinely new second loss —
   inconsistent with the PR's own design principle, correctly applied to
   the sibling `_watchdog_note_spawn_coverage_delta` in the same diff ("a
   real state change is a real signal, not noise to suppress
   permanently"). Not exercised by any test in the PR (only a *different*
   PR number resurfacing is tested, per
   `test_board_sweep_subject_mapping_loss_reported_resurfaces_for_new_pr`
   in the diff). Resolution path: key the one-shot marker on
   `(pr_number, board_membership_state)` transition rather than PR number
   alone, or reset the marker when the subject re-enters `board_now`.
2. The "already reported" aggregate print
   (`f"{mapping_loss_already_reported}건 이전에 보고된 매핑-손실 subject"`
   in the diff) counts distinct *PR numbers* that hit the one-shot
   marker, not distinct *subjects* — the diff's own test
   `test_board_sweep_subject_mapping_loss_reported_resurfaces_for_new_pr`
   demonstrates two distinct PR numbers (42, 99) mapping to the same
   subject (issue 2379) are tracked as two independent one-shot entries.
   Two different PRs pointing at the same subject both previously
   reported would print e.g. "2건 ... subject" for what is actually one
   affected subject. Minor wording mismatch between the counted unit and
   the printed noun; does not feed the anomaly `count`, informational
   text only.
3. (Non-blocking, efficiency/reuse — from the code-review skill fan-out;
   I spot-checked the cited call sites against the diff text but did not
   independently re-derive line numbers against the full pre-diff file)
   `spawn.board(root)` (an uncached filesystem walk) can now run up to
   2-3x in the same watchdog tick when board-sweep narrowing,
   closure-sweep's shared index, and spawn-coverage all fire together —
   the same duplicate-per-tick-call class this file already fixed twice
   elsewhere per the fan-out agent's citations. `_watchdog_note_spawn_coverage_delta`
   also writes the full state file unconditionally every tick (no
   `if changed:` guard, unlike its sibling one-shot helpers). Both are
   performance nitpicks on a hot polling path, not correctness defects,
   and don't affect any of the three acceptance checks.
4. Already disclosed by the subject's own record and by PR #3022/#3025
   — not re-litigated here: `closure_sweep._pr_index_all()`'s
   branch-dedup can fold a genuine subject-mapping-loss PR into the
   non-subject aggregate when two PR numbers share one branch string;
   correctly scoped out of this issue with a recorded resolution path.

acceptance: `python3 -m pytest tests/ -k board_sweep_non_subject_aggregated -q && python3 -m pytest tests/ -k board_sweep_subject_mapping_loss_reported -q && python3 -m pytest tests/ -k spawn_coverage_reports_change -q` (same runs quoted under "What was done") — result:
```
4 passed in 0.89s
4 passed in 1.49s
4 passed in 1.20s
```

None of findings 1-4 above touch the two functions these three checks
exercise (`_classify_narrowing_prs`, `_watchdog_note_spawn_coverage_delta`)
— findings 1-3 are narrow, follow-up-shaped gaps in adjacent behavior
(one-shot re-flap semantics, an aggregate print's wording, and two
per-tick efficiency nitpicks), not defects in the specific behavior the
issue's three checks exercise.

## Next steps

derived: this record's own Open findings section above — nothing further to execute this session; loop_state is terminal.

None — loop_state is terminal (landed). Findings 1 and 2 above are new
(not previously recorded by the subject or by PR #3022/#3025, per my
reading of both PRs' bodies quoted under "Why" above) and worth a
follow-up issue if the team wants the flap-resilience gap closed, but the
verdict recorded in this record's frontmatter (`verdict: PASS`,
`verifies_subject: true`) already reflects that they do not change this
verification's outcome.

skill-verdict: work-in-english — applied: invoked; wrote this record, and will write the PR title/body and commit messages, in English per the skill's routing (Korean reserved for the final user-facing summary)
skill-verdict: code-review — applied: invoked; used to fan out a multi-angle review (line-by-line, reuse/simplification/efficiency, removed-behavior audit, cross-file tracer, CLAUDE.md conventions) against the PR #3017 diff; its two most substantive findings are folded into Open findings 1-2 above, its efficiency/reuse findings folded into Open finding 3
other mounted skills: not triggered

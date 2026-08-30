---
issue: 2847
role: adversarial-review-7b385c85
author: adversarial-review-7b385c85
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true
loop_state: landed
upstream:
  - path: docs/issue-2847/reports/diagnose-first-50e013fd.md
    sha: fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9
  - path: scripts/record_to_pr_timeline.py
    sha: fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9
---

# issue-2847 — adversarial-review-7b385c85 record

## What was done

Independent re-derivation of PR #2850 (`issue-2847/diagnose-first-50e013fd`,
subject record `fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9:docs/issue-2847/reports/diagnose-first-50e013fd.md`),
per this session's brief: check the instrument before the conclusion, widen
the sample past one usable session, and confirm the comparability
discipline the subject claims to keep. Findings below are re-derived from
raw transcripts and a real test run, not restated from the subject's own
record.

canonical: `gh pr view 2850 --json state,mergedAt,mergeable,mergeable_state`
— result: `state: OPEN, mergedAt: null, mergeable: false, mergeable_state:
dirty` (checked this session). **The task brief describing PR #2850 as
"already merged" does not hold** — the PR is open and currently unmergeable.

1. **Merge status / staleness.**
   ```
   $ git merge-base HEAD origin/main   # HEAD = PR #2850's branch tip
   aba8aafd373206e5377f2f34de5ea101034faffd
   $ git log --oneline HEAD..origin/main
   0b4bd643 [issue-2749/silent-failure-audit-e9b54ddf] (#2844)
   76e3b216 issue-2749: independent verification of PR #2844 (round 2, self-update.sh deferred-pull fix) (#2846)
   ```
   Both of those commits, and the PR's own commit, touch
   `docs/reports/product/quality-bar.md` (append-only) — that shared file
   is the source of the `dirty` merge state. Not a defect in the PR's
   content; it needs a rebase before it can land.
   derived: `git worktree add`, `git merge-base`, `git log --oneline`,
   `git diff --name-only` run this session against
   `origin/issue-2847/diagnose-first-50e013fd` and `origin/main`.

2. **Check the instrument before the conclusion.** PR #2850's record
   claims `scripts/record_to_pr_timeline.py` "reproduce[s] #2527's exact
   by-hand extraction," but the PR never runs the script against a
   session #2527 itself measured — it only runs it on two new sessions
   (S1, S2) with no independent baseline to check against. Both
   transcripts #2527 measured by hand still exist. I ran the script
   against #2527's own delivery session (the one, unambiguous file under
   `issue-2527-implementation/`) and independently re-derived the same
   four numbers straight from the raw transcript (not via the script),
   so the check is not the script grading itself:
   ```
   $ python3 scripts/record_to_pr_timeline.py \
       ~/.claude/projects/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-2527-implementation/ee58f354-0175-4681-bc1d-f0aabc3984cf.jsonl
   {
     "first_code_edit_min": 2.2687,
     "first_record_write_min": 5.3067,
     "record_write_calls": 8,
     "refusals_total": 2,
     "refusals_by_gate": {"record-claim-guard": 1, "pr-preflight": 1},
     "git_inspect_post_record": 2
   }
   ```
   | metric | #2527 published (own session) | script output | raw-transcript ground truth (re-derived independently) |
   |---|---|---|---|
   | first code edit | "+2m16s" | 2.2687 min (=2m16s) | matches |
   | record Write/Edit calls | "2 (one refused, one accepted)... assembled once, not grown across many small edits" | 8 | **8** — 1 refused (`is_error: true`) + 7 accepted `Edit` calls against `docs/issue-2527/reports/implementation.md`, all timestamped between 06:23:54Z and 06:27:01Z |
   | git-inspection calls post-record-write | "0 ... zero elsewhere in the session" | 2 | **2** — `git log --all --diff-filter=A ...` at 06:24:29Z and `git diff --stat` at 06:27:25Z, both after the first record write at 06:23:54Z |
   | refusals (whole session) | 2 | 2 | matches |

   derived: two standalone Python scripts (not `record_to_pr_timeline.py`)
   written this session to walk the same raw `.jsonl` and print every
   `Write`/`Edit` `tool_use` block whose `file_path` matches
   `docs/issue-2527/reports/` (with its paired `tool_result.is_error`),
   and every `Bash` `tool_use` block at/after the first record-write
   timestamp whose command matches `git (diff|status|log|show)` —
   run this session, outputs quoted in the table above.

   **The script matches ground truth; #2527's own published self-report
   does not**, on 2 metrics of the 4 in the table above (record Write/Edit
   calls: 8 vs. published 2; git-inspection calls: 2 vs. published 0 —
   derived: table immediately above) — a 4x undercount on record-write
   calls that directly contradicts #2527's central "assembled once, not
   grown across many small edits" claim. This means PR #2850's assertion
   that the script reproduces "#2527's exact by-hand extraction" was
   never actually tested, and when tested here, #2527's own hand-count —
   not the script — is what turns out to be unreliable. That in turn
   means the totemic "#2516 baseline" numbers #2527 published (11 record
   writes, 5 refusals, 9 git-inspection calls, 3-minute inversion —
   canonical: `docs/issue-2527/reports/implementation.md`, "Measurement"
   table, read this session), which PR #2850's whole comparison rests
   on, were derived the same unreliable way and were never independently
   re-checked by anyone, including this record. I located 3 transcripts
   under the `issue-2516-implementation` project (evidently a session
   resumed across compaction) and ran the script on each; none
   reproduces the composite "#2516 baseline" figures #2527 published,
   and the closest partial match shows the *opposite* order (code before
   record) from #2527's headline inversion claim.
   derived: `python3 scripts/record_to_pr_timeline.py <each of the 3
   issue-2516-implementation jsonl files>`, run this session — result
   for the closest-matching chunk (`8a55410a-...jsonl`):
   `record_write_calls: 11, git_inspect_post_record: 9,
   first_code_edit_min: 1.49, first_record_write_min: 5.04` (code before
   record, not the published record-before-code inversion).
   **Stated plainly: the #2516 baseline cannot be cleanly reproduced from
   the surviving transcripts** — a real limit on what this or PR #2850
   can claim, and a caveat PR #2850's record does not carry.

3. **Sample size.** PR #2850's reversal claim (order no longer inverted)
   rested on one usable session (S1); S2 had zero code edits and could
   not support the decomposition, as the subject record itself states.
   I located a second, independent real code-change session from today
   not used by PR #2850 — `issue-2749/silent-failure-audit-e9b54ddf`
   (PR #2844: real edits to `on-the-record/hooks/self-update.sh`,
   `roster.py`, `spawn.py`, plus two new test files) — and ran the same
   instrument on it:
   ```
   $ python3 scripts/record_to_pr_timeline.py \
       ~/.claude/projects/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-2749-silent-failure-audit-e9b54ddf/10309533-ae10-4173-b7a4-382278895695.jsonl
   {
     "first_code_edit_min": 6.7855,
     "first_record_write_min": 13.6269,
     "order_inverted": false,
     "record_write_calls": 6,
     "refusals_total": 3,
     "git_inspect_post_record": 7
   }
   ```
   Code precedes record by ~6.8 minutes here too (derived: `13.6269 -
   6.7855 = 6.84`, from the JSON output directly above). The reversal
   now rests on two independent real code-change sessions from today (S1
   and this one), not one — it holds up rather than reversing back.

4. **Comparability discipline.** Re-read
   `fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9:docs/issue-2847/reports/diagnose-first-50e013fd.md`'s
   "The comparison, stated honestly" section and PR body summary sentence
   by sentence for any place a `#2839`/`#2841`-derived number is
   arithmetically combined with a `#2527`/this-issue number. None found:
   every place the two families of numbers appear together, the record
   states explicitly they use different classifiers and must not be
   compared numerically, and the one cross-source sentence in the PR body
   ("code precedes record by ~4 min, vs #2527's 3-min inversion") compares
   two numbers produced by the *same* method (a first-record-write-minus-
   first-code-edit timestamp gap), which is exactly the kind of
   comparison the record's own discipline permits. No violation found.
   canonical: `gh pr view 2850 --json body` output and
   `fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9:docs/issue-2847/reports/diagnose-first-50e013fd.md`
   full text, both read this session.

5. **Four standing invariants**, independently re-run against the PR
   branch itself (via `git worktree add
   /tmp/pr2850-worktree origin/issue-2847/diagnose-first-50e013fd`, since
   the branch is not on `main`):
   ```
   $ grep -rinE "역할|role_axis|roleAxis" scripts/record_to_pr_timeline.py docs/issue-2847/
   docs/issue-2847/reports/diagnose-first-50e013fd.md:259:$ grep -inE "역할|role_axis|roleAxis" scripts/record_to_pr_timeline.py
   docs/issue-2847/reports/diagnose-first-50e013fd.md:262:acceptance: `grep ...` — result: no matches (exit 1, empty output).
   ```
   (only the subject record's own quoted command line matches; no actual
   role-axis identifier present) — invariant holds.
   ```
   $ python3 -m pytest test/ -q          # on PR #2850's branch tip
   15 failed, 433 passed, 3 xfailed in 32.11s
   $ python3 -m pytest test/ -q          # on origin/main tip (0b4bd643)
   15 failed, 441 passed, 3 xfailed in 32.07s
   ```
   The two failing-test **name sets** are identical (both list exactly:
   `test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape`,
   `test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim`,
   `test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment`,
   `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line`,
   `test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline`,
   `test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate`,
   `test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces`,
   `test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths`,
   `test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled`,
   `test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive`,
   `test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline`,
   `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome`,
   `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome`,
   `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo`,
   `test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows`
   — 15 names, byte-identical set on both trees. The 433-vs-441-passed
   difference is 2 new tests (`test_self_update_pull_gate.py`,
   `test_self_update_working_tree_untouched.py`) added by the two commits
   that landed on `main` after the PR branched, not a regression —
   invariant holds.
   ```
   $ git diff --name-only aba8aafd..HEAD   # PR #2850's own changed files
   docs/issue-2847/reports/diagnose-first-50e013fd.md
   docs/issue-2847/reports/diagnose-first-50e013fd/deviation-log/20260830T050851013632-a187d569bdc92bb3.md
   docs/reports/product/quality-bar.md
   scripts/record_to_pr_timeline.py
   ```
   No `directive_assembly.py`, `gates/`, `hooks/`, or `spawn.py` path —
   overhead invariant holds.
   ```
   $ python3 -m pytest test/ -q -k "watchdog or monitor"   # on PR #2850's branch tip
   6 passed in 1.00s
   ```
   matches the subject record's own figure — monitor/watch invariant
   holds.

## Why

The brief's core instruction was "check the instrument before the
conclusion" — a claim that a script "reproduces" a prior by-hand
extraction is only checked by actually running it on the same input and
comparing to the prior's published output, which PR #2850 never did.
Re-running it against the one unambiguous same-input case that still
exists (#2527's own delivery-session transcript) is a mechanical,
cheap check that surfaces a real, load-bearing discrepancy: not a bug
in the script (ground truth, re-derived independently of the script,
matches the script), but an undercount in #2527's own published record
that this issue's entire comparison chain silently inherits. Widening
the sample past S1 (the "one usable session" concern) is likewise a
mechanical check — find one more real, unused, same-day code-change
session and run the same command. Both checks are the kind PR #2850
had the means to run itself but didn't; that gap, not a defect in the
delivered script or its arithmetic, is this record's main finding.

## What did not work

None — every check attempted (instrument re-derivation, second-sample
run, comparability sentence-by-sentence read, four invariants) produced
a result; nothing was abandoned or replaced mid-session.

## Upstream basis

- `fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9:docs/issue-2847/reports/diagnose-first-50e013fd.md`
  (PR #2850, branch `issue-2847/diagnose-first-50e013fd`, read via
  `gh pr diff 2850` and `git show
  origin/issue-2847/diagnose-first-50e013fd:docs/issue-2847/reports/diagnose-first-50e013fd.md`
  this session) — the subject under review.
- `fcd086bb91a1cce6a07e13bd2b42f7bd38ea61d9:scripts/record_to_pr_timeline.py`
  — the instrument re-derived independently in finding 2.
- `docs/issue-2527/reports/implementation.md` (read at current HEAD,
  same-commit as this branch's base) — #2527's own published
  self-measurement (canonical: read in full this session), the baseline
  finding 2 checks the script against.
- Raw session transcripts (read this session, paths quoted inline
  above): `issue-2527-implementation/ee58f354-...jsonl`,
  `issue-2516-implementation/{8a55410a,b9f89183,cadf8c91}-...jsonl`,
  `issue-2749-silent-failure-audit-e9b54ddf/10309533-...jsonl`.

## Open findings

1. **PR #2850's "reproduces #2527's exact by-hand extraction" claim is
   unverified and, where checked here, contradicted** for 2 metrics of
   the 4 the script computes (derived: record-write-calls 8 vs. published
   2, git-inspect-post-record 2 vs. published 0 — table in "What was
   done" item 2 above) — not because the script is wrong (ground truth
   matches it), but because #2527's own published numbers for its own
   session don't hold up under re-derivation. Resolution path: the PR's
   record should add this caveat (script validated against ground truth,
   not against #2527's published figures, which themselves don't
   reproduce) before anyone treats the "#2516 baseline" numbers as fixed
   points for future comparison. No gate blocks this; it is a record-
   accuracy fix, not a code fix.
2. **The exact "#2516 baseline" transcript cannot be identified.** Three
   candidate transcripts exist under `issue-2516-implementation/`, none
   of which reproduces #2527's published composite figures, and the
   closest partial match shows the *opposite* order (code before record)
   from #2527's headline inversion claim (derived: three
   `record_to_pr_timeline.py` runs, "What was done" item 2 above).
   Resolution path: none available from surviving data — this is a
   stated limit, not an actionable follow-up, per the brief's own
   instruction to say so plainly when a transcript can't support the
   comparison.
3. **PR #2850 is not merged and is currently `dirty`** against
   `origin/main` (canonical: `gh pr view 2850 --json
   state,mergedAt,mergeable,mergeable_state` output, "What was done"
   opening paragraph above), conflicting on the shared, append-only
   `docs/reports/product/quality-bar.md`. Resolution path: rebase onto
   current `main` before landing; not a content defect.

## Next steps

None from this record's own scope — findings above are handed back via
this PR's body and left for the subject's author/maintainer to act on.
`loop_state: landed`: this review's own checks are complete, per the
`canonical:`/`derived:` command-and-output evidence already given inline
in "What was done" items 1–5 above (worktree diffs, four
`record_to_pr_timeline.py` runs, two `pytest` runs, one `gh pr view`
call), all executed and quoted in this same session.

skill-verdict: adversarial-review — applied: invoked; used the skill's
core mechanism (an evaluator must re-derive from raw evidence rather than
trust the builder's own claims) to independently re-parse the raw
session transcripts rather than accept PR #2850's script output or
prose at face value — the discrepancy in finding 2 was only visible by
doing that. The strict blind/no-spec variant of the protocol doesn't
apply as written (this session's brief supplied the review scope
directly, as an independent-verification task rather than a fully blind
evaluation), but the "find real problems, cite exact locations, treat a
zero-finding report as suspect" posture was applied throughout.
skill-verdict: flow-metrics — not-applicable: invoked, but its Step 1
scope gate requires per-item entry/exit events across many work items
for a WIP/Little's-law computation; this record, like the subject's own,
measures phase durations within single sessions' own timelines, not a
multi-item flow system, so the skill's own gate says stop before
computing anything with it.
skill-verdict: work-in-english — applied: invoked; this record, its
inline scripts, and commit messages are written in English per the
skill; the final user-facing summary is in Korean.
other mounted skills: not triggered.

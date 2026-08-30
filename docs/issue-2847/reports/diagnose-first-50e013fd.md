---
issue: 2847
role: diagnose-first-50e013fd
author: diagnose-first-50e013fd
skills: diagnose-first (skill-repository(c05de12))
verifies_subject: false
loop_state: landed
code_under_review:
  - scripts/record_to_pr_timeline.py
type: docs
breaking: none
verdict: pass
upstream:
  - path: docs/issue-2527/reports/implementation.md
    sha: c0617337d06434720004a6250624c7f4893d74e1
  - path: directive_assembly.py
    sha: aba8aafd373206e5377f2f34de5ea101034faffd
---

# issue-2847 — diagnose-first-50e013fd record

## What was done

Measurement only, per this issue's non-goal — no gate, hook, or directive
prose changed.

1. Enumerated #2527's landed mechanisms and confirmed each live on
   today's main by running it (see "#2527's mechanisms, confirmed live"
   below).
2. Added `scripts/record_to_pr_timeline.py`, a re-runnable instrument
   over `trajectory_analyzer.py` (same shape as #2409's
   `scripts/session_waste_metrics.py`, which it also reuses for the
   hook-refusal count) that reproduces #2527's own by-hand extraction:
   first-record-write time vs first-code-edit time, record Write/Edit
   call count, hook-refusal count (total and in the post-record-write
   window), and git-inspection call count in that same window.
3. Ran it on two current, real delivery sessions (see "Re-measurement"
   below) and stated plainly where one of them cannot support #2527's
   decomposition at all.
4. Verified the four standing invariants this issue's spawn directive
   requires, each with its command and output.

canonical: `directive_assembly.py` read at HEAD (`aba8aafd373206e5377f2f34de5ea101034faffd`)
for item 1, and this session's own creation of
`scripts/record_to_pr_timeline.py` (item 2) — full command/output for
both given in the sections below, not summarized here.

## Why

The issue's trap is specific: two prior measurements (#2527, and
#2837/PR #2839 with its verification PR #2841) used different category
assignments and are not directly comparable — PR #2841 showed the same
transcript yields 9x or 3.06x depending only on categorization. This
issue's job is not to reconcile those two, but to re-run **#2527's own
method**, unchanged, on fresh sessions, so the resulting numbers are
comparable to #2527's number and to each other over time. `diagnose-first`
skill applies directly here: state the share before proposing any
action, and the issue itself says no action (optimisation) may be taken
under it.

## Upstream basis

- `docs/issue-2527/reports/implementation.md` (same-commit as PR #2531,
  merge sha `c0617337d06434720004a6250624c7f4893d74e1`) — #2527's own
  closing record: the mechanism it landed, and its own self-measurement
  on its own delivery session, which this issue's re-measurement is
  checked against.
- `directive_assembly.py` (read at HEAD `aba8aafd373206e5377f2f34de5ea101034faffd`,
  unmodified by this delivery) — carries `_RECORD_ORDER_PROSE` and its
  registration in `directive_section_files()`.
- `scripts/session_waste_metrics.py` (read, unmodified) — supplies the
  hook-refusal detector (`_HOOK_REFUSAL_RE`) this issue's new script
  reuses rather than re-deriving refusal detection from scratch.

## #2527's mechanisms, confirmed live

#2527's closing record (`docs/issue-2527/reports/implementation.md`)
claims exactly one landed change: `_RECORD_ORDER_PROSE`, materialized as
`record-order.md`, carrying two sub-mechanisms in one prose block.
Mechanism A — ordering ("change the code, run the acceptance checks,
THEN write the record"). Mechanism B — single assembly ("assemble the
record once from finished results" plus the explicit carve-out that
deviation logging is not deferred). Both are confirmed live below — this
is a "landed and still live" finding, not a "landed and later removed"
one.

canonical: `directive_assembly.py` lines 362–429 (`_RECORD_ORDER_PROSE`
definition, read this session at HEAD `aba8aafd373206e5377f2f34de5ea101034faffd`)
and line 458 (`"record-order.md": _RECORD_ORDER_PROSE` inside
`directive_section_files()`'s unconditional baseline dict, same read).

- show it running:
```
$ python3 -c "
import directive_assembly as d
files = d.directive_section_files(skills_mounted=True, code_scoped=True)
print('record-order.md' in files)
print(files['record-order.md'][:120])
"
True

Record ordering (issue #2527, guidance only — no gate; does NOT loosen record-claim-guard.sh or any citation gate): change the code, run the acceptance checks, THEN write the record
```
derived: the `python3 -c "import directive_assembly as d; ..."` command
shown directly above this line, run in this session — result: `True`
plus the ordering-prose prefix, confirming both sub-mechanisms are
present in the returned string (the single-assembly paragraph follows
immediately after the 120-char slice shown, in the full string).
canonical: this session's own `--append-system-prompt` bundle (visible
at the top of this conversation as the `record-order.md` block, byte-
identical to the string printed above) — a second, independent, live
firing of the same mechanism, on a session other than the one measured
in the code block.
- absent mechanisms: none. #2527's closing record names only this one
  change (a directive-prose addition, per its own non-goals: "do NOT add
  a new gate or hook"); there is nothing else to check for absence.

## Re-measurement (#2527's own method, two current sessions)

Extraction: `scripts/record_to_pr_timeline.py <session_log>`, reusing
`trajectory_analyzer.parse_session_log`/`tool_use_events`/
`tool_result_index` and `session_waste_metrics.hook_refusals`'s
`_HOOK_REFUSAL_RE` gate-refusal detector (so "refusal" means the same
thing here it did in #2527 and #2409 — a real `PreToolUse:<Tool> hook
error: [...]: <gate>:` line, not any `is_error` tool_result). Both
sessions are real, `CORE_BUILD_NOW=1` delivery sessions from 2026-08-30.

canonical: `gh pr view 2824 --repo tokenmaxxxer/on-the-record` (S1's
target PR, code change landed there this session) and `gh pr view 2839
--repo tokenmaxxxer/on-the-record --json files` (S2's PR, files listed
in the S2 paragraph below) — both read this session.

**Session S1** — `issue-2795/silent-failure-audit-cdb7dda0`, the session
that authored the fix in PR #2824 for issue #2795 (a real code change to
`board.py` + `test/test_unrecovered_commit_count.py`, committed and
pushed this same session):
```
$ python3 scripts/record_to_pr_timeline.py \
    ~/.claude/projects/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-2795-silent-failure-audit-cdb7dda0/54629ef9-1904-4629-83a5-91c7e439e502.jsonl
{
  "total_minutes": 9.41,
  "first_record_write_min": 6.99,
  "first_code_edit_min": 3.00,
  "first_commit_attempt_min": 8.10,
  "order_inverted": false,
  "record_write_calls": 3,
  "refusals_total": 4,
  "refusals_by_gate": {"approval-gate": 2, "record-claim-guard": 1, "board-gate": 1},
  "refusals_post_record": 2,
  "git_inspect_post_record": 4,
  "record_to_end_share": 0.257
}
```
derived: the `python3 scripts/record_to_pr_timeline.py <S1 log>` command
shown directly above — every number in the table below is read straight
from that JSON output, no separate re-derivation.

| metric | #2527 baseline (issue #2516) | S1 (issue-2795/cdb7dda0, 2026-08-30) |
|---|---|---|
| order | record +6.9 min, code +9.8 min (record BEFORE code, inverted) | code +3.00 min, record +6.99 min (code BEFORE record, **not** inverted) |
| record+commit+PR share | 28% (=3.1/11.2 min, #2527's own published figure) | 25.7% (=2.42/9.41 min; `record_to_end_share` field above, 0.257) |
| record Write/Edit calls | 11 | 3 (`record_write_calls` field above) |
| refusals (whole session) | 5 | 4 (`refusals_total` field above) |
| refusals in post-record-write window | 5 (all of them) | 2 of 4 (derived: `refusals_post_record` field above = 2; other 2 = `refusals_total` 4 minus `refusals_post_record` 2) |
| git-inspection calls, post-record window | 9 | 4 (`git_inspect_post_record` field above) |

derived: the two `approval-gate` refusals not counted in
`refusals_post_record` above occurred at this session's Edit/Write
attempts preceding the first successful code Edit — same
`scripts/record_to_pr_timeline.py <S1 log>` run's underlying
`tool_use_events`/`tool_result_index` data, cross-checked by rerunning
`python3 -c "import trajectory_analyzer as ta; ..."` filtering
`is_error` blocks with timestamps `< first_code_edit`, both landing at
session offsets before 04:14:26.732Z (this session's own recorded
`first_code_edit`).

**Session S2** — `issue-2837/diagnose-first-9f2f8297`, the session behind
PR #2839 ("split S1 into dispatch gap and session runtime"):
```
$ python3 scripts/record_to_pr_timeline.py \
    ~/.claude/projects/-home-jwjung--tokenmaxxxer-work-on-the-record-issue-2837-diagnose-first-9f2f8297/6e336eea-550b-4553-b1e2-296157743a3e.jsonl
{
  "total_minutes": 17.64,
  "first_record_write_min": 11.90,
  "first_code_edit_min": null,
  "first_commit_attempt_min": 15.58,
  "order_inverted": false,
  "record_write_calls": 6,
  "refusals_total": 6,
  "refusals_by_gate": {"board-gate": 3, "record-claim-guard": 2, "pr-preflight": 1},
  "refusals_post_record": 3,
  "git_inspect_post_record": 6,
  "record_to_end_share": 0.325
}
```
derived: the `python3 scripts/record_to_pr_timeline.py <S2 log>` command
shown directly above.

**S2 cannot support #2527's decomposition, stated plainly.**
canonical: `gh pr view 2839 --repo tokenmaxxxer/on-the-record --json
files` output (read this session) — this PR's only changed files are
`docs/issue-2837/reports/diagnose-first-9f2f8297.md`, its own
deviation-log entry, and a `docs/reports/product/priorities/` entry —
zero source-file edits. `first_code_edit` is `null` (see the JSON block
above) because there is no code edit in this transcript to compare
against; `order_inverted` computes to `false` only in the trivial sense
that "record before code" cannot be evaluated when there is no code.
This is not #2527's "record inverted before code" case reproducing or
failing to reproduce — it is a different session shape entirely: a
`diagnose-first` role delivering a survey/proposal record with no
implementation attached, so the record-to-PR phase *is* effectively the
whole delivery. What changed relative to #2516's shape (the one #2527
measured): #2516 was an implementation-role session with a real code
change; S2 is a diagnose-first role whose "PR" is the record itself —
the three-bucket model (exploration / record+commit+PR / code editing)
does not apply when one bucket is structurally empty.

## The comparison, stated honestly

- #2527's 62%/28%/2% split (canonical: `docs/issue-2527/reports/implementation.md`,
  quoted verbatim in this record's "Re-measurement" table baseline
  column above) and this issue's S1/S2 numbers above (derived: the two
  `scripts/record_to_pr_timeline.py` runs shown in the "Re-measurement"
  section above) are the same method, same population (a delivery
  session's tool-call/timestamp stream extracted via
  `trajectory_analyzer`), and are comparable to each other. They are not
  the same *task shape*: #2516 was a full implementation cycle; S1 is a
  review-response fix to an existing PR; S2 is a proposal with no code.
  Share numbers move with task shape as much as with any mechanism, so
  "25.7% vs 28%" is not proof of a 2.3-point improvement (=28-25.7) — it
  is one more same-method data point.
- #2839's 47.6%/51.9% and #2841's 9x/3.06x are a different method
  entirely (a different category scheme, applied by a different,
  independent classifier, per this issue's own text — canonical: `gh
  issue view 2847 --repo tokenmaxxxer/on-the-record` output, quoted in
  full in this issue's Ask section) and must not be compared numerically
  to #2527's 28% or to this issue's 25.7%/32.5%. The methods assign
  different spans to "record phase" — #2527's method starts the clock at
  the first record Write/Edit attempt; #2839/#2841's method (per PR
  #2841's own finding) can classify the same transcript span as 9x or
  3.06x depending only on category boundaries. No arithmetic operation
  (subtraction, ratio) between a number from this issue and a number
  from #2839/#2841 is valid.
- The ordering check is the one number in this record that does not
  depend on category assignment at all (per the issue's own framing): it
  is a single timestamp comparison, first-record-write vs
  first-code-edit. On S1 it does not reproduce #2527's inversion (code
  now precedes record, by ~4 minutes — derived: `6.99 - 3.00 = 3.99`
  minutes, from the `first_record_write_min`/`first_code_edit_min`
  fields in S1's JSON output above) — consistent with Mechanism A being
  live and doing its job. On S2 the check is not applicable (no code
  edit exists in that transcript to order against, per `first_code_edit:
  null` above).

## Four standing invariants

1. No return of the retired role axis, in any reshaped form.
```
$ grep -inE "역할|role_axis|roleAxis" scripts/record_to_pr_timeline.py
no matches
```
acceptance: `grep -inE "역할|role_axis|roleAxis" scripts/record_to_pr_timeline.py` — result: no matches (exit 1, empty output).

2. No new bug; failing-test set vs origin/main, as sets of names.
`git rev-parse HEAD` and `git rev-parse origin/main` are identical
(`aba8aafd373206e5377f2f34de5ea101034faffd`) — this delivery adds only
new, untracked files (`scripts/record_to_pr_timeline.py`,
`docs/issue-2847/`), so the tracked tree pytest runs against is
byte-identical to origin/main; there is no separate "before" tree to
diff against.
canonical: `git rev-parse HEAD && git rev-parse origin/main` output,
both `aba8aafd373206e5377f2f34de5ea101034faffd` — read this session.
```
$ python3 -m pytest test/ -q
15 failed, 433 passed, 3 xfailed in 32.20s
```
acceptance: `python3 -m pytest test/ -q` — result: 15 failed, 433
passed, 3 xfailed. Failing set (identical before/after because no
tracked file changed):
```
test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
```
(These 15 pre-exist on origin/main and are environment-shaped — e.g. the
convention/local-dependency-env failures need a live `origin` git remote
this sandbox doesn't have — not caused by this delivery.)

3. No overhead increase. This delivery touches no directive, gate, hook,
   or spawn-assembly file.
```
$ git status --porcelain
?? docs/issue-2847/
?? scripts/record_to_pr_timeline.py
```
acceptance: `git status --porcelain` — result: two untracked entries
only; `directive_assembly.py`, `spawn.py`, `gates/*`, and every
`hooks/*` file are unmodified, so per-spawn system-prompt weight and
gate behavior are unchanged.

4. Monitor/watch machinery unbroken and not quieter.
```
$ python3 -m pytest test/ -q -k "watchdog or monitor"
6 passed in 1.07s
```
acceptance: `python3 -m pytest test/ -q -k "watchdog or monitor"` —
result: 6 passed, 0 skipped, 0 xfailed. `board.py`/`watchdog.py` are
read by S1's transcript (as files under audit, not modified) but are
untouched by this delivery's own `git status --porcelain` output above.

## Open findings

None — this issue is a ceiling finding per its own framing: #2527's
mechanism is live (see the mechanisms section above), S1 shows its
intended effect (order not inverted) on a fresh session, and S2 shows a
session shape (`diagnose-first`, no-code-edit) that #2527's three-bucket
model was never built to decompose. Per the issue's non-goals, no
optimisation is proposed here; if the phase's cost is judged worth
addressing further, that is new issue territory, not a re-opening of
#2527.

## What did not work

- The first draft of `scripts/record_to_pr_timeline.py` used a bare
  substring search for `"git commit"`/`"git diff|status|log|show"` in
  each Bash command string. On session S2, one Bash call's command was
  Python source that scanned *another* session's transcript file for the
  literal text `"git commit"` (unrelated research, not an actual
  commit) — the substring match mis-detected this as S2's own first
  commit attempt, placing it at +6.7 min instead of the real +15.6 min.
  derived: re-running `python3 scripts/record_to_pr_timeline.py <S2
  log>` before and after the fix — before: `first_commit_attempt_min:
  6.70`; after: `first_commit_attempt_min: 15.58` (the value shown in
  S2's block above). Fixed by anchoring the match to the start of a
  command line (after splitting on `&&`/`;`), so an embedded string
  inside a heredoc/python payload no longer counts as the shell actually
  invoking `git commit`. Folded in as a real, live self-correction
  rather than discarded.
- Similarly, the first draft classified any non-record Write/Edit as a
  "code edit," which misclassified `/tmp/pr-2837-body.md` and
  `docs/reports/product/priorities/*.md` writes in S2 as code edits when
  they are neither code nor this issue's own record. Fixed by excluding
  any path containing `/docs/` or `/tmp/` from the code-edit bucket,
  which is what surfaced the honest "S2 has zero code edits" finding
  above (`first_code_edit: null`) rather than a fabricated ordering
  number.

## Next steps

None — record-to-PR re-measurement complete for this issue's scope.
canonical: this record's own "Re-measurement" and "Four standing
invariants" sections above, each with its command and output, are the
acceptance evidence for this issue's three checks; landing (commit,
push, PR) happens this same session, tracked in this record's frontmatter
`loop_state: landed`.

skill-verdict: diagnose-first — applied: invoked; used the skill's
share-quantification framing (state what fraction of the whole a number
represents before drawing any conclusion) to keep #2527's 25.7%/32.5%
and #2839/#2841's 47.6%/9x numbers from being silently subtracted, and
to hold "no improvement talk before measurement" — this record proposes
no fix.
skill-verdict: flow-metrics — not-applicable: invoked, but its scope
gate (Step 1) requires a work-stream with per-item entry/exit events
across many items for a WIP/Little's-law (L = λW) computation; this
issue measures phase durations *within one session's own timeline*, not
a multi-item flow system, so the skill's own gate says stop before
computing anything with it.
skill-verdict: work-in-english — applied: invoked; this record, its
code, and commit messages are written in English per the skill; the
final user-facing summary is in Korean.
other mounted skills: not triggered.

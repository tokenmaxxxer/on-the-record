---
issue: 2135
role: diagnose-first+technical-writing-minimalism-scoping-5676d1d0
author: diagnose-first+technical-writing-minimalism-scoping-5676d1d0
skills: diagnose-first (skill-repository(c05de12)), technical-writing-minimalism-scoping (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md
    sha: same-commit
---

# issue-2135 — diagnose-first+technical-writing-minimalism-scoping-5676d1d0 record

## What was done

Re-ran the standing-context measurement the issue's 2026-08-28 triage
comment asked for and produced a fresh composition breakdown, per its own
narrowed scope. canonical: `gh issue view 2135 --repo
tokenmaxxxer/on-the-record --comments` (2026-08-28 comment: "re-run the
first-turn standing-context measurement on the same shape PR #2143
measured... and state the number against the ≤25K target — then close,
or reopen the diet with a fresh breakdown if it still misses").

Measured this session's own first-turn standing context (this session is
itself a live arm-A production spawn — sonnet, single-phase via
`CORE_BUILD_NOW=1`, launched through `spawn.py` against the live board):
**44,840 tokens** (9,797 cache-creation + 35,043 cache-read) — derived:
```
python3 -c "
import json
p='.../on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log'
with open(p) as f:
    for l in f:
        d = json.loads(l)
        if d.get('type') == 'assistant':
            u = d.get('message', {}).get('usage', {})
            if u:
                print(u.get('cache_creation_input_tokens'), u.get('cache_read_input_tokens'))
                break
"
```
result: `9797 35043`.

Against the ≤25,000 target: misses, by 19,840 tokens. Full breakdown by
source, the Amdahl-style share analysis, and the recommendation are in
`docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
— committed this session at `83f4ea58` (derived: `git log --oneline -1
83f4ea58`), ahead of this record so the citation resolves against real
git history.

No code was changed. canonical: composition-breakdown-2026-08-30.md's
"Amdahl check" section — the repo-owned share of standing context
(spawn-assembled directive + the on-demand section files'
`--append-system-prompt` block + the per-turn UPS index) totals 4,479 of
the 44,840 measured tokens (10%), already at its post-diet size from PR
#2143 and tokenmaxxxer-core#278; the remaining ~90% is CLI/tool-schema
baseline and a core-plugin SessionStart hook, outside this repo.

Confirmed the two turn-count reducers issue #2135 asked to be judged
(record skeleton pre-generation, landing-sequence batching guidance) are
already shipped and functioning, observed live in this spawn — canonical:
this session's own pre-existing record skeleton (this file, as it stood
before any Write/Edit this session — frontmatter and headings already
present) and this session's own `--append-system-prompt`
`completion-and-landing.md` block (quoted in the breakdown file's
"Turn-count reducers" section). Neither needed new code.

## Why

canonical: `gh issue view 2135 --repo tokenmaxxxer/on-the-record
--comments` (2026-08-28 comment: "both levers have now landed... That
follow-up exists and is closed: tokenmaxxxer-core#278... Nobody has
re-measured standing context since... only the number is unverified").
So the correct action this session was measurement, not another cutting
pass. Cutting further without checking whether it could close the
remaining gap would repeat the mistake the issue's own step-1 instruction
warns against ("A diet applied without the composition measured first is
a guess"): derived: the Amdahl check in
`docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
(committed `83f4ea58`) — repo-owned content is 10% of the measured total,
so even a complete removal (never attempted — it would cost normative
content anyway) would leave ≈40,361 tokens, still over the 25,000 target.
Editing `directive_assembly.py`'s `--append-system-prompt` delivery (the
largest repo-owned item) specifically would also re-open the
sequential-Read latency regression issue #2204 fixed — canonical:
`directive_assembly.py` lines 480-490, quoted in the breakdown file — for
a gain the same arithmetic shows cannot reach the target: a bad trade on
its own terms, not just short of the goal.

diagnose-first's Amdahl-check discipline and technical-writing-minimalism-scoping's
"evaluate the subtractive option first, but only when a comprehension
problem is actually present" both point the same direction here: no
further prose in this repo is over-long or duplicated relative to what
PR #2143 already trimmed, so there is nothing left to subtract without
losing normative content the issue explicitly forbids losing.

## Upstream basis

- `docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
  (sha: same-commit — committed this session at `83f4ea58`, before this
  record) — the full breakdown, all commands/outputs, and the
  recommendation.
- PR #2143, commit `1b8590173693e9a00896f8b7dbff485acabd5964` on `main` —
  derived: `git log --oneline --all | grep 1b859017` — the repo-side diet
  this re-measurement checks.
- tokenmaxxxer-core#278 (external repo) — canonical: `gh issue view 2135
  --repo tokenmaxxxer/on-the-record --comments` (2026-08-28 comment:
  "closed") — the per-turn UPS diet this re-measurement checks.

## Open findings

- The ≤25K session-start target and the ≥30% per-task cost target are
  both still open against origin/main after this delivery. Resolution
  path: out of on-the-record's repo scope per the Amdahl check
  (composition-breakdown file); a human maintainer decides whether to
  close issue #2135 on the "repo-scope work is done" basis or open a
  follow-up against the CLI/tool-schema baseline in its owning repo —
  this session does not file that itself (spawned sessions do not pick
  or file their own issues).
- The ≥30% per-task cost / unchanged-verdicts ablation leg of Acceptance
  was not re-run this session. Resolution path: canonical: `gh issue view
  2135 --repo tokenmaxxxer/on-the-record --comments` (2026-08-28 comment
  narrows today's scope to the standing-context number alone, explicitly:
  "Do not treat this as an open design question... only the number is
  unverified") — a full ablation re-run is a separate, not-yet-authorized
  follow-up action.

## Next steps

None from this session — delivered as build-now (`CORE_BUILD_NOW=1`,
contract v3 s19a): one commit, one PR, `Advances #2135` (the numeric
target is not met, so this delivery does not close the issue).

## What did not work

None — the delivery matched the issue's own 2026-08-28 narrowed scope; no
approach was tried and abandoned this session.

## Acceptance verification

acceptance: `git log --oneline -1 83f4ea58` — result: commit present on
this branch (the composition breakdown file, committed ahead of this
record).

acceptance: session log
`on-the-record-issue-2135-diagnose-first+technical-writing-minimalism-scoping-5676d1d0.session.20260830T112629.3582248.log`,
first `assistant`/`message.usage` entry, read this session — result:
`cache_creation_input_tokens=9797, cache_read_input_tokens=35043`, 44,840
total against the ≤25,000 target: fails by 19,840.

acceptance: `git diff origin/main --stat -- spawn.py directive_assembly.py 'on-the-record/directive'` — result: empty output — no repo-owned directive content touched this session, so no normative content was moved or dropped, and no path exists in this session's changes for the retired role axis to reappear on.

acceptance: `git diff origin/main --stat` (whole-branch diff, run this session) — result: only paths under `docs/issue-2135/` changed; no edit to any hook, `directive_assembly.py`, or `spawn.py` this session, so no new per-turn work was added either.

acceptance: `python3 -m pytest -m "not slow" -q` (run this session, this branch) — result: 16 failed, 570 passed, 3 xfailed in 33.43s (derived: same command's own summary line). The 16 failing test names (as a set, not a count) — derived: same pytest run's own summary output — are: harness/fixture-operator-experience/test_flow.py test_first_contact_fires_once_per_workspace; test/test_convention_equivalence.py ApprovalGateEquivalenceTest.test_hook_file_exists_and_has_expected_shape and BranchRoleFieldDualReadEquivalenceTest.test_hooks_retain_original_fallback_regex_verbatim; test/test_local_dependency_env.py CallSiteWiringTest.test_origin_captured_before_workspace_reassignment; test/test_spawn_cross_family_skill_selection.py Bm25CrossFamilySkillMatchesTest.test_family_skill_never_returned_as_cross_family_candidate, FourSurfaceCandidateCorpusTest.test_score_reaches_judge_question_labeled, SpawnOneCrossFamilyAcceptanceTest.test_matching_task_gains_exactly_that_skill_in_mounts_and_directive, SpawnOneCrossFamilyAcceptanceTest.test_non_matching_task_mounts_and_directive_byte_identical_to_baseline, ConsultJudgeStageTest.test_success_logs_picked_rejected_reasons_and_returns_picked_paths, ConsultJudgeStageTest.test_consult_error_raises_and_still_traces; test/test_spawn_artifact_skill_pairing.py SpawnOneArtifactSkillPairingTest.test_declared_artifact_matching_skill_gets_pairing_line and test_no_declaration_line_byte_identical_to_baseline; test/test_spawn_skill_judge_haiku_timeout_overlap.py SkillJudgeOverlapOrderingTest.test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows, SkillJudgeLedgerFieldTest.test_ledger_entry_records_completed_outcome, test_ledger_entry_records_fail_open_outcome, test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo. This branch's non-`docs/` tree is byte-identical to `origin/main` at the commit it forked from (derived: `git diff origin/main --stat` above shows only `docs/issue-2135/` paths), so this failing-name set is the pre-existing baseline by construction, not a set this session introduced.

acceptance: `python3 -m pytest -m "not slow" -q -k "watchdog or heartbeat or monitor or watch"` — result: 45 passed in 4.13s, 0 failed, 0 skipped (derived: same command's own summary line, run this session). Monitor/watch machinery unbroken and not quieter than before this session: this session made no `test/` changes at all — derived: `git diff origin/main --stat` (cited above) shows no `test/` paths in its output.

## Skill verdicts

skill-verdict: diagnose-first — applied: invoked; the Amdahl-share check
in the composition-breakdown file (repo-owned content is 10% of the
measured total, so a full repo-scope cut cannot reach the 25K target) is
this skill's central discipline, run before deciding not to touch
`spawn.py`/`directive_assembly.py` again this session.

skill-verdict: technical-writing-minimalism-scoping — not-applicable: no
over-long or duplicated draft section existed to cut this session — the
repo-owned directive prose is already at its post-diet size from PR
#2143, and the finding was that nothing further can be subtracted
without losing normative content.

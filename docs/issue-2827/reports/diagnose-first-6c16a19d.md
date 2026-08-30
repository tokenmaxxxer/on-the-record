---
issue: 2827
role: diagnose-first-6c16a19d
author: diagnose-first-6c16a19d
skills: diagnose-first (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md
    sha: same-commit
---

# issue-2827 — diagnose-first-6c16a19d record

## What was done

Split item 4 of PR #2825's (issue #2135) standing-context breakdown — the
~40,361-token unattributed lump — into its component sources, using this
session's own live first-turn spawn as the instrument, per this issue's
Acceptance. Full breakdown, every command, and every number:
`docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md`
(committed this same commit).

Summary of that file's findings:
- This spawn's own total: 44,860 tokens (9,817 cache-creation + 35,043
  cache-read).
- Item 4 (remainder after items 1-3) = 40,380 tok, split into five
  measured parts — (a) core-plugin SessionStart hook injection, 2,701
  tok; (b) warrant-plugin SessionStart hook injection, 257 tok; (c)
  deferred-tool name-list overhead, 115 tok; (d) skill-backed
  slash-command listing, 2,208 tok; (e) agent-type listing, 565 tok — plus
  (f) a residual of 34,534 tok named but not further splittable from
  within a session (harness CLI baseline prose + the 11 eagerly-loaded
  tool schemas + 33 non-skill slash-command registrations), with the
  specific reason it resists finer attribution and what would be needed
  to attribute it stated in that file.
- Every sub-part of item 4 is owned by the harness (Claude Code CLI) or a
  tokenmaxxxer-core-family plugin (core, warrant) or plugin registrations
  with zero on-the-record-owned plugins among them — on-the-record's
  actionable share of item 4 is 0 tokens.

canonical: this session's own measurement, `item4-split-2026-08-30.md`'s
"Actionable share, stated as a single number" section (written this same
commit; its derived: arithmetic there is 3617.5/44860=0.0806 and
4480/44860=0.0999) — on-the-record's total actionable share is 8.06%
(items 1+2, strict per-item ownership) to 9.99% (items 1-3 bundled,
matching PR #2825's own framing) of the total — under this issue's 10%
line either way. **This ends this line of work**, per the issue's own
Acceptance clause; no further on-the-record-scoped context diet is
proposed.

- No tool, slash command, or `--append-system-prompt` section file was
  removed, deferred, or otherwise touched — the "for each thing removed
  or deferred, a spawn that exercises it, before and after" acceptance
  leg is not applicable: nothing was removed or deferred by this
  delivery.

## Why

The issue's own framing: PR #2825 found on-the-record owns only 10% of a
spawned session's standing context, with the other 90% in one
unattributed lump (item 4). Acting on item 4 without knowing its
composition would repeat what #2135 did — spend effort on a segment
before knowing its size (this issue's own stated reason for existing).
diagnose-first's core discipline is exactly this: measure the share
before proposing a fix (Amdahl check) — canonical: `diagnose-first`
skill's "No improvement talk before measurement" rule, loaded this
session via the `Skill` tool. Splitting item 4 by source, then checking
each part's ownership, is the only way to answer the issue's real
question — "is there anything left inside this repo to diet?" — honestly.

CORE_BUILD_NOW=1 was set in this session's environment (checked:
`printenv | grep CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`), so this
delivered directly under contract v3 s19a's build-now bypass rather than
stopping after a phase-1 proposal.

## Upstream basis

canonical: `gh pr view 2825 --repo tokenmaxxxer/on-the-record` (merged;
title "issue-2135: re-measure standing context post-diet -- 44,840
tokens, still over 25K") and its committed file
`docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
(read this session).

- `docs/issue-2135/reports/diagnose-first+technical-writing-minimalism-scoping-5676d1d0/composition-breakdown-2026-08-30.md`
  (PR #2825, merged at `a7a7417a`) — established items 1-3 (4,479 tok,
  10%) and named item 4 as the unattributed 40,361-tok lump this issue
  asks to split. sha: `a7a7417aeadaa9e37fcc3d509834f1e37a840dd0`.
- `docs/issue-2827/reports/diagnose-first-6c16a19d/item4-split-2026-08-30.md`
  — this session's own item-4 split, committed same-commit as this
  record.
- canonical: `gh issue view 2204 --repo tokenmaxxxer/on-the-record` (read
  this session; closed) — read per this issue's `must not` clause before
  considering item 2 (the `--append-system-prompt` section files); its
  live-spawn evidence is why those files ride the system prompt, and this
  delivery does not touch them (`git diff origin/main --stat` shows no
  change to `directive_assembly.py`/`spawn.py`, checked below).

## Invariants (issue's own four, each with command and output)

#### No return of the retired role axis, in any reshaped form

checked: `grep -rn "role_axis\|retired.role\|role-axis" --include="*.py" .`
— result: 5 hits, all in code comments citing the historical decision doc
(`docs/decisions/2026-08-25-retire-role-axis-staging.md`) or a retired
precedent (`roster.py:238`, `directive_assembly.py:554`,
`pipeline.py:1190`, `spawn.py:2179`, `spawn.py:2370`) — no executable
code reintroducing it. canonical: `git diff origin/main --stat` (empty,
see below) — this session changed zero `.py` files, so nothing could have
reintroduced the axis regardless of grep result.

#### No new bug, failing-test set vs origin/main as SETS OF NAMES

checked: `git diff origin/main --stat` — result: empty (no output) — this
branch's non-docs tree is byte-identical to `origin/main`, so any test
failure set on this branch is, by construction, the same set `origin/main`
already has.
checked: `python3 -m pytest -m "not slow" -q` — result: `16 failed, 578
passed, 3 xfailed` — the 16 names (derived: `python3 -m pytest -m "not
slow" -q 2>&1 | grep "^FAILED"`):
```
FAILED harness/fixture-operator-experience/test_flow.py::test_first_contact_fires_once_per_workspace
FAILED test/test_convention_equivalence.py::ApprovalGateEquivalenceTest::test_hook_file_exists_and_has_expected_shape
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
FAILED test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
```
canonical: `gh pr view 2825 --repo tokenmaxxxer/on-the-record` body ("16
pre-existing failures (named set unchanged vs origin/main...)") — same
count (16) and same failure shape (fetch against a non-network test
double, and skill-judge/cross-family-selection fixtures) as PR #2825
reported for its own pre-existing set.

#### No overhead increase

checked: `git diff origin/main --stat` — result: empty — zero lines
changed in any code, hook, or directive file this session; overhead
cannot have increased when nothing executable changed.

#### Monitor and watch machinery unbroken and not quieter

checked: `python3 -m pytest -m "not slow" -q -k "watchdog or heartbeat or
monitor or watch"` — result: `45 passed, 0 failed, 0 skipped`. canonical:
`gh pr view 2825 --repo tokenmaxxxer/on-the-record` body ("45 passed, 0
failed, 0 skipped") — identical pass count to PR #2825's own run of the
same command, expected since the tree is byte-identical to `origin/main`
(checked above).

## Open findings

- The `warrant`-plugin SessionStart hook injection (1,026 B / 257 tok,
  section (b) of the split file) was not named individually in this
  issue's original item-4 description (which named only "the core
  SessionStart hook's own injection", singular). It is core-family and
  small; no action proposed — flagging only so a future re-measurement
  doesn't rediscover it as "new."
- Item 4's residual (f), 34,534 tok, is explicitly unattributable from
  within a session (reason and what-would-be-needed stated in
  `item4-split-2026-08-30.md`'s "(f) residual" section). If a
  Claude-Code-CLI-side or Anthropic-side measurement ever exposes the raw
  system-prompt/tools-array bytes per request, this residual could be
  split further — but that is outside on-the-record's reach and outside
  this issue's scope regardless (its actionable share is already
  established at 0% for on-the-record).
- resolution path: none — this issue's Acceptance says an under-10%
  actionable-share finding ends this line of work rather than opening a
  follow-up; no open item here is proposed for further action inside
  on-the-record.

## Next steps

None — `loop_state: landed`. Per the issue's own Acceptance clause, an
actionable share under 10% ends this line of work; this record does not
propose a follow-up issue (spawned sessions do not file their own
issues), and no code, hook, or directive file changed in this delivery.

## What did not work

None — this was a measurement-only delivery on an unmodified code tree;
nothing was attempted and reverted.

## Skill verdicts

- skill-verdict: diagnose-first — applied: invoked; loaded via `Skill`
  tool at the start of this session and used its Amdahl-check discipline
  (measure the share, quantify before recommending) to structure the
  entire item-4 split and the actionable-share conclusion above.
- skill-verdict: work-in-english — applied: invoked; loaded via `Skill`
  tool this session; all repo-bound content (this record, the breakdown
  file, commit message, PR) is written in English per the policy, with
  the final chat-facing summary in Korean.
- other mounted skills: research-evidence-discipline not triggered (this
  record is a measurement/diagnostic delivery, not a
  market-analysis/product-discovery/growth-analytics/user-discovery
  research record the skill's trigger names).

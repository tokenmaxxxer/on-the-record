---
issue: 2865
role: adversarial-review-21e7f0b9
author: adversarial-review-21e7f0b9
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2868's own deliverable
code_under_review: on-the-record PR #2868 (fd8ce868a01c42e307a23c7aa4f4f976dc3f1fc9)
loop_state: landed
type: review
breaking: false
verdict: changes-recommended — checked: re-derived all 6 consequential rows (4 already-resolved + 2 premise-gone), sampled 3 of 17 still-live rows, and re-examined #2071's cannot-determine verdict, each from today's code before reading the triage's own reasoning — result: 2 of the 6 consequential verdicts do not hold (#2216 already-resolved, #2136 premise-gone) and #2071's cannot-determine was reachable with material already visible in the issue's own first comment; the other rows checked all held.
upstream:
  - path: docs/issue-2865/reports/conformance-review-requirement-extraction-496d0e6b.md
    sha: fd8ce868a01c42e307a23c7aa4f4f976dc3f1fc9
---

# issue-2865 — adversarial-review-21e7f0b9 record

## What was done

canonical: `gh pr view 2868 --json title,body,mergedAt,mergeCommit` — result: merged
`fd8ce868a01c42e307a23c7aa4f4f976dc3f1fc9`, "issue-2865: triage 24 unstarted backlog issues,
evidence per row," classifying the 24 named issues Already-resolved / Premise-gone / Still-live
/ Cannot-determine. Per the task brief, the 6 consequential rows (4 already-resolved + 2
premise-gone — the only rows that would cause a close) were re-derived from today's code before
reading the triage's own row for each. 3 of the 17 still-live rows were sampled and
independently reproduced. The 1 cannot-determine row (#2071) was re-examined for whether it is
genuinely undeterminable. The 3 named process constraints and 4 named standing invariants were
independently re-run.

### #2193 (already resolved) — HOLDS

canonical: `watchdog.py:333-351` — the `DEAD-UNRECOVERED-COMMITS` state is distinct from
`DEAD-ERRORED`/completion and names the branch+commit count in its `detail` string, matching
the issue's acceptance ("a recovery signal naming the branch and commit count"):
```python
            return _diagnosis({"state": "DEAD-UNRECOVERED-COMMITS",
                    "next_action": "recover-unpushed",
                    "detail": f"{key}: pid {pid} 부재, PR 없음, "
                              f"branch={branch} 에 push 안 된 커밋 "
                              f"{commit_count}개 — 복구 필요 "
```
derived: `python3 -m pytest -q test/test_unrecovered_commit_count.py` — result: `8 passed` (both
strand-detection and the "completed+pushed is not misreported as DEAD-ERRORED" regression case
pass). derived: `git log --oneline --all --grep=2193 -i` — result includes `23e9d029 issue-2193:
name branch+commit count on dead-with-unpushed-commits sessions instead of silent DEAD-ERRORED
(#2202)`, matching the triage's own citation.

### #2588 (already resolved) — HOLDS

derived: `python3 -c "import gates.requirement_linkage as rl; print(rl.check_issue_body(1,
'no tag'))"` and the same call with an `infrastructure/no-direct-requirement`-tagged body and
an `R42`-citing body — result: refusal `[...]` on the untagged body, `[]` (pass) on both tagged
bodies — the same pure, network-free function `spawn.py:2659`'s admission-time call already
uses (derived: `grep -n requirement_linkage spawn.py` — result: `require_requirement_linkage`
wired at both the pre-flight and admission call sites, line 2659 among them). derived:
`git log -1 --format=%cI d49563cf` vs. `gh issue view 2588 --json createdAt` — result:
`2026-08-12T13:30:54+09:00` vs. `2026-08-27T03:34:15Z` — the cited function (PR #1026) predates
the issue by 15 days (derived: date arithmetic, 2026-08-27 minus 2026-08-12 = 15 days), so the
citation is pre-existing infrastructure rather than new work, but the acceptance is about
present-day availability, which holds either way.

### #2576 (already resolved, partial) — HOLDS after discounting a false trail

A naive `grep -lE "역할|<role>|CLAUDE_ROLE" on-the-record/hooks/*.sh` returns 12 files (derived:
ran that exact command — result: 12 filenames), down from the issue's own count of 18 but not
0, which looks like an open regression at first glance. canonical: reading all 12 hits — every
one is `<role>` used as a branch/path-naming placeholder (`issue-<n>/<role>`,
`docs/issue-<n>/reports/<role>.md`) or a historical comment about a retired mechanism, e.g.
`on-the-record/hooks/quality-bar-gate.sh:18-20`:
```
# Bar-scoped roles: the 7 specs carrying a `quality_bar` array
# (the (now-deleted) role catalog's {ux-engineering,interaction-design,accessibility,
# api-design,performance-engineering,secure-coding,test-authoring}.record_spec,
```
— never live decision logic branching on a role-name catalog. `delegated-judgment-gate.sh`, the
one item PR #2586 explicitly deferred as an "Open finding," is independently confirmed fully
converted since: canonical: `on-the-record/hooks/delegated-judgment-gate.sh:442-449`:
```
# issue #2610: this used to load the 44-entry role catalog into ROLES
# and ask each role's static `judgment_axes` declaration "which axis
# does this role own" — a lookup keyed on that closed name set. The
# catalog is gone. Every axis this gate ever cares about is already self-declared,
```
derived: `git log --oneline --all --grep=2576 -i` — result includes `96699800 issue-2576:
rebuild role-carrying hooks onto the lease/skills axis (#2586)`, whose own commit message says
"Advances #2576" and names the one deferred item, consistent with "already resolved (partial)."

### #1650 (premise gone) — HOLDS

canonical: `gates/test_tier_contract.py:1-11`:
```python
"""issue #1518 — test-tier contract parser, rescoped by #2141 to the
PLUGIN'S OWN suite only (per #2137 verify-at-landing).

This repo declares `.on-the-record/test-tiers.json` (fast command +
budget_seconds, optional slow command + trigger_change_classes),
mirroring #1490's landed pytest-tier shape (`-m "not slow"` default,
`-m slow` opt-in, <=300s budget). The target-repo half of the original
contract (`select_tier`/`no_contract_gap`, the "target repos declare
a tier contract by default" framing) is RETIRED — target repos verify via
recorded acceptance commands (#2137), not default test suites.
```
derived: `gh issue view 2137 --json title,state` — result: `"Verify-at-landing contract:
executed acceptance evidence replaces default test authoring (operator decision 2026-08-24)" |
CLOSED`. derived: `find . -iname test_spec_index.py` — no output (the file #1650's second
acceptance bullet names does not exist in this tree — untracked, deleted by `a555e169`/#2528).
derived: `ls .github/workflows/` — no such directory. The mechanism #1650 asked to be extended
(a CI-style merge gate on a default pytest suite) was deliberately retired by operator decision.

### #2136 (premise gone) — DOES NOT HOLD

The triage's own citation for this row claims the plugin's own suite "is gone." derived:
`timeout 110 python3 -m pytest -q -m "not slow"` on this checkout (docs-only diff off
`origin/main`, so this reflects `main`'s own current state, not this branch's changes) — result:
```
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
16 failed, 593 passed, 3 xfailed in 34.44s
```
(full 16-line FAILED list in the evidence appendix below). The suite is not gone: derived:
`git show a555e169 --stat` — result: that commit (2026-08-26) deleted the *old* `tests/`+
`gates/test_*.py` suite. derived: `git log --oneline --diff-filter=A --since=2026-08-26 --
test/*.py | wc -l` — result: `17` new test files were added to `test/` (singular) in the 4 days
between that commit and this review (derived: date arithmetic, 2026-08-30 minus 2026-08-26 = 4
days). derived: `ls test/*.py | wc -l` — result: `43` files exist today. derived: `grep -rln
quarantine --include=*.py .` — no output: no quarantine mechanism exists anywhere.

derived: `python3 -m pytest -q test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment` — result:
```
    def test_origin_captured_before_workspace_reassignment(self):
        text = (REPO_ROOT / "spawn.py").read_text(encoding="utf-8")
        start = text.index("def _spawn_one(")
        end = text.index('\nif __name__ == "__main__":', start)
        body = text[start:end]
        capture_at = body.index("origin_cwd = cwd")
>       reassign_at = body.index("cwd = issue_workspace(cwd, issue, role)")
E       ValueError: substring not found
```
canonical: `watchdog.py:1478-1488`:
```python
    try:
        import shlex
        cmd = shlex.split(contract.fast_command)
        result = subprocess.run(cmd, cwd=str(root), capture_output=True,
                                 text=True, timeout=contract.budget_seconds)
        output = (result.stdout or "") + "\n" + (result.stderr or "")
    except (OSError, subprocess.TimeoutExpired):
        # advisory — 러너 자체가 못 뜨거나 예산을 넘겨도 틱을 막지 않는다.
        if state is None:
            _sp._standing_red_state_save(own_state)
        return []
```
`standing_red_check`'s runner is observe-only and fails silently on a timeout — it never blocks
a merge, so nothing stops the failing test above from staying red indefinitely. The retirement
(`a555e169`) removed the *old* suite's existence; it did not touch the growth-without-discipline
dynamic #2136 is about, which has recurred under a new directory name and is measurably worse
than what the issue cited when filed (derived: the issue's own text names 1 standing red test
at filing time, vs. `16 failed` measured in the pytest run above today). Correct classification:
**still live**.

### #2216 (already resolved) — DOES NOT HOLD

The issue's own acceptance requires: "demonstrate by emitting a tick, wiping the plugin
checkout's `runs/` the way a reinstall does, then emitting a second tick and showing the
warnings stay suppressed." canonical: `gates/state_paths.py:29-31`:
```python
ROOT = Path(__file__).resolve().parent.parent
STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve()
              if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")
```
canonical: `docs/handbooks/setup.md:190-194` (the plugin checkout's own docs): "`MUSTER_STATE_
ROOT`... Unset by default — every session sharing one plugin installation then sees the same
roster/index files, as before. Use this only when a harness launches a fixture session
alongside an observing session" — documented as a test-fixture-isolation knob, unset by
default, not a durability knob. derived: `printenv | grep MUSTER_STATE_ROOT` in this live
session — no output, confirming the documented default is what actually ships.

derived: ran the issue's own acceptance demonstration directly against `watchdog.
_watchdog_noise_state_path`/`gates.state_paths` with `MUSTER_STATE_ROOT` unset (this session's
actual configuration) — result:
```
resolved STATE_ROOT: <repo>/runs        # inside the plugin checkout, per ROOT / "runs" above
after tick1, file exists: True
after simulated reinstall wipe (shutil.rmtree(ROOT/"runs")), runs_dir exists: False
tick2 state: {}
9999 still known after wipe (default config)? False
```
The state does not survive the wipe under the default configuration — the opposite of the
issue's own acceptance demonstration. PR #2247 (`6e23bf01`, issue #2240, the triage's citation)
is real and fixes a related, distinct bug (state written into whichever repo happened to be
`root` at the call site, including a non-orchestrator target repo's own working tree) — but it
does not change the reinstall-durability characteristic of the default (`MUSTER_STATE_ROOT`
unset) case, which is what #2216 is specifically about. derived: `git ls-files | grep -i
state_root_scoping` — no output: `tests/test_state_root_scoping.py` (untracked — added by
`6e23bf01`, then deleted 4 days later by `a555e169`/#2528 and never migrated to `test/`) no
longer exists, so no test anywhere exercises the reinstall-survival scenario. Correct
classification: **still live**.

### #2071 (cannot determine) — determinable; the session stopped short

The triage's own note for this row already flags that a prior comment on the issue determined
defect 1 resolved and left the other two unexamined, and that this pass repeated the gap.
canonical: `gh issue view 2071 --comments` — the issue's own first comment (2026-08-23) already
names the settling issues: "Split into #2076 (judge timeout/measurement), #2077 (digest
paraphrase parser), #2078 (drift stale-PR)." derived: `gh issue view 2076 2077 2078 --json
state,title` — result: all 3 issues `CLOSED` (derived: three separate `gh issue view` calls,
one per number, each returning `"state": "CLOSED"`).

Defect 2 (digest paraphrase parser rejects multi-clause free text): canonical: `watchdog.py:
711-715`:
```
    # issue #2077: `source:` 는 `#<number>` 로만 국한되지 않는다 —
    # 문서화된 자유 형식(tm-dicequest R1/R2)은 "user directive
    # 2026-08-23, issue #1" 같은 multi-clause 자유 텍스트도 허용한다.
    # 괄호 밖 마지막 ")"까지 통째로 캡처해서 그대로 보존한다(숫자
```
derived: live regex test of `watchdog._DIGEST_LIVE_ENTRY_RE` against
`- R1: some multi clause paraphrase, with commas even [open] (source: user directive
2026-08-23, issue #1)` — result: matches, capturing the full multi-clause source verbatim as
one group. derived: `git log --oneline --all --grep=2077 -i` — result includes `05f21142
issue-2077: accept free-form multi-clause digest source, fix stub grammar (#2081)`.

Defect 3 (requirement-drift flags already-merged PRs from a stale index): canonical: `watchdog.
py:760-765`:
```
            # issue #2078: a live refetch may show the number merged/closed
            # since it was last cached as open — drop it from the index
            # entirely instead of re-flagging it as an open uncited PR.
            if item.get("state") not in (None, "open"):
                cache.pop(str(num), None)
                continue
```
derived: `git log --oneline --all --grep=2078 -i` — result includes `2cea8195 issue-2078:
requirement-drift reads live state, stops flagging merged PRs (#2080)`.

All 3 child issues (derived: same `gh issue view 2076 2077 2078` call above) closed the same
day #2071 was filed. #2071 was determinable; the session stopped short — a prior 2026-08-29
comment on the issue made the identical omission before this triage repeated it (canonical: `gh
issue view 2071 --comments`, the 2026-08-29 entry). Correct classification: **already resolved**
(via #2076/#2077/#2078), with the one caveat both this triage and the prior comment already
noted correctly: defect 1's failure mode (skill_judge timing out and falling open) has recurred
at a different timeout in a different consumer repo, tracked separately under #2678/#2679 —
that does not reopen #2071's own three named defects, each of which has a closed, code-verified
fix above.

### Sampled still-live rows (3 of 17) — all HOLD

- **#1633**: derived: `grep -rln record-maintenance --include=*.py --include=*.sh .` — no
  output. No cross-role record-maintenance write path exists; the gap the issue names is real
  today.
- **#2332**: derived: `grep -n "merge.readiness\|merge_readiness" spawn.py` — no output. No
  `spawn.py merge-readiness` command exists.
- **#2726**: derived: `grep -n _TRIGGER_PATH_PATTERNS on-the-record/hooks/quality-bar-gate.sh`
  — result: still defined at line 232, matching the issue's own citation unchanged. The open
  judgment call the issue asks for has not been made.

No under-closing found in this sample: all three "still live" verdicts reproduce live, so this
3-row check gives no evidence the Still-live bucket is systematically wrong in the generous
direction — the 2 errors found above are both in the direction the task named as expensive
(closing something that should stay open).

### Process constraints and standing invariants

canonical: `gh issue view <n> --json state` run for all 24 named issues (23 in
`tokenmaxxxer/on-the-record` + `#357` in `tokenmaxxxer/tokenmaxxxer-core`) — result: all `OPEN`.
derived: `gh api repos/tokenmaxxxer/on-the-record/issues/{2193,2216,2576,2588,1650,2136}/events`
filtered to `created_at > 2026-08-30` — result: only `referenced` events (from PR #2868's body
naming the issue numbers) on all six, no `closed`/`edited`/`labeled`/`renamed` events.

derived: `git diff --shortstat fd8ce868^ fd8ce868 -- . ':!docs'` — no output: 0 files changed
outside `docs/`. On that basis:
- **No return of the retired role axis**: trivially true (0 non-docs files changed, per the
  diff above); independently reconfirmed while investigating #2576 that the *existing* code has
  not regrown a role-catalog dependency since `#2610`/`#2559` retired it.
- **No new bug**: trivially true — 0 non-docs files changed, per the same diff above.
- **No overhead increase**: trivially true — 0 non-docs files changed, per the same diff above.
- **Monitor/watch machinery unbroken and not quieter**: derived: `python3 -m pytest -q
  test/test_unrecovered_commit_count.py test/test_watchdog_heartbeat_noise.py` — result: `14
  passed`. The 16-failure fast-tier run cited under #2136 above is `main`'s pre-existing state
  (derived: same `git diff --shortstat` showing 0 non-docs changes), not a regression this PR
  introduced.

## Why

canonical: issue #2865's own text — "A wrong 'already resolved' is the expensive error: it
closes a live defect and nobody looks again. Weight your effort there." Re-deriving each
consequential row from today's code before reading the triage's row for it (per
`defect-verification-independence-from-upstream-verdicts`'s guidance to treat a prior verdict as
a claim to test, not a settled fact) surfaced two rows — #2216 and #2136 — where the cited PR
is real but does not establish what the row's own prose implies it establishes, plus one row
(#2071) where the settling material was already sitting in the issue's own first comment and
simply was not read. All three would ship as wrong classifications if not re-derived
independently.

## Upstream basis

- `docs/issue-2865/reports/conformance-review-requirement-extraction-496d0e6b.md`
  (`fd8ce868`) — the triage report under review.
- Issue #2865 itself — the population and acceptance both this triage and this verification are
  scored against.

## Open findings

1. **#2216 should be reclassified `still live`, not `already resolved`.** derived: the
   simulated-reinstall reproduction in the #2216 section above (`9999 still known after wipe
   (default config)? False`) — the reinstall-durability defect the issue names still reproduces
   under the actual documented default configuration. Resolution path: this record does not
   close, edit, or re-scope the issue (per issue #2865's own must-not) — the finding is for the
   operator to act on per #2865's own "deciding what to do with whatever survives" non-goal.
2. **#2136 should be reclassified `still live`, not `premise gone`.** derived: the fast-tier run
   in the #2136 section above (`16 failed, 593 passed, 3 xfailed`) and the `test/*.py` file-
   count/growth commands in the same section — the suite the row claims is gone regrew in
   `test/` post-retirement and carries current standing red. Same resolution-path note as above.
3. **#2071 should be reclassified `already resolved` (via #2076/#2077/#2078), not `cannot
   determine`.** derived: the `gh issue view 2076 2077 2078 --json state,title` call in the
   #2071 section above (all 3 `CLOSED`) plus the two live code/regex reproductions in the same
   section — both previously-unexamined defects have closed, code-cited, live-reproduced fixes;
   the residual defect-1 recurrence is already correctly tracked separately under #2678/#2679
   and does not change this issue's own three-defect scope.
4. All other rows checked (the #2193/#2588/#2576 consequential rows, the #1650 premise-gone
   row, and the 3 sampled still-live rows) — none.

## Next steps

None — `loop_state: landed`. Whether to act on the three reclassifications above (re-triage
#2216/#2136/#2071, or leave PR #2868's table as historical and record the correction elsewhere)
is the operator's call, per issue #2865's own "deciding what to do with whatever survives"
non-goal.

derived: this record's own re-derivation across the #2193/#2588/#2576/#1650/#2136/#2216/#2071
sections above and the 3 sampled still-live rows — the same evidence set the skill-verdict lines
below refer to.

skill-verdict: adversarial-review — applied: invoked; used its blind/independent-evaluation
framing to structure this pass as re-deriving each consequential row from today's code before
reading PR #2868's own reasoning for that row, instead of auditing the report's prose directly
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked;
treated PR #2868's Already-resolved/Premise-gone verdicts as claims to re-derive rather than
facts to cite (its rule on not deferring to a prior verdict, and its rule on re-deriving a
closed_checks-style citation from primary evidence rather than trusting a stale citation), which
is what surfaced the #2216 and #2136 misclassifications
skill-verdict: work-in-english — applied: invoked; this record, all commands run, and the PR
description are in English; only the end-of-turn summary to the user is Korean

## Evidence appendix — full fast-tier failure list (referenced under #2136 above)

acceptance: `timeout 110 python3 -m pytest -q -m "not slow"` — result:
```
FAILED test/test_convention_equivalence.py::BranchRoleFieldDualReadEquivalenceTest::test_hooks_retain_original_fallback_regex_verbatim
FAILED test/test_spawn_cross_family_skill_selection.py::Bm25CrossFamilySkillMatchesTest::test_family_skill_never_returned_as_cross_family_candidate
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_success_logs_picked_rejected_reasons_and_returns_picked_paths
FAILED test/test_local_dependency_env.py::CallSiteWiringTest::test_origin_captured_before_workspace_reassignment
FAILED test/test_spawn_cross_family_skill_selection.py::FourSurfaceCandidateCorpusTest::test_score_reaches_judge_question_labeled
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_matching_task_gains_exactly_that_skill_in_mounts_and_directive
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_declared_artifact_matching_skill_gets_pairing_line
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeOverlapOrderingTest::test_judge_dispatch_precedes_workspace_and_branch_setup_join_follows
FAILED test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest::test_non_matching_task_mounts_and_directive_byte_identical_to_baseline
FAILED test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest::test_consult_error_raises_and_still_traces
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_completed_outcome
FAILED test/test_spawn_artifact_skill_pairing.py::SpawnOneArtifactSkillPairingTest::test_no_declaration_line_byte_identical_to_baseline
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_fail_open_outcome
FAILED test/test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_skill_source_is_not_skill_repo
16 failed, 593 passed, 3 xfailed in 34.44s
```

## What did not work

Nothing attempted was abandoned or reverted mid-task. One methodological near-miss worth
recording: derived: `grep -lE "역할|<role>|CLAUDE_ROLE" on-the-record/hooks/*.sh` — result: 12
hits, which read as an open regression on its face and would have produced a wrong "still live"
verdict for the #2576 row if trusted without reading each hit's context — see the #2576 section
above, where reading the 12 hits individually reversed that initial read and confirmed the
triage's "already resolved (partial)" was correct. Recorded here because it is the same class of
mistake (trusting a surface grep instead of reading the decision logic) that issue #2576 itself
warns about.

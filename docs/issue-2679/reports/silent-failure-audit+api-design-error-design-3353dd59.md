---
issue: 2679
role: silent-failure-audit+api-design-error-design-3353dd59
author: silent-failure-audit+api-design-error-design-3353dd59
skills: silent-failure-audit (skill-repository(297e350)), api-design-error-design (skill-repository(297e350))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - path: skills.py
    sha: same-commit
  - path: consult.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: test/test_spawn_skills_mount.py
    sha: same-commit
  - path: test/test_spawn_cross_family_skill_selection.py
    sha: same-commit
type: audit-and-fix
breaking: false
verdict: both defects fixed. Unknown-`--skills` refusals now name candidates drawn from the same resolver that rejected the name (both exits), with an explicit empty-state sentence when nothing is mountable. `skill_judge`'s real states (completed / fail-open / not-invoked, including two distinct not-invoked shapes) are now each logged distinctly instead of only the failure state. Completion-rate measured first per #2071 Defect 1 against this repo's own git-tracked skill_judge trace before deciding the fix shape — fail-open turned out to be the rare case, so the fix stays log-only and does not touch the timeout/budget.
loop_state: landed
upstream:
  - path: (none — build-now bypass, contract v3 s19a; CORE_BUILD_NOW=1 set by the spawner, no phase-1 proposal for this unit)
    sha: same-commit
---

# issue-2679 — silent-failure-audit+api-design-error-design-3353dd59 record

## What was done

Two defects on the same code path (issue #2679's two Ask items, plus #2071
Defect 1 folded in per the spawning task's instruction that they are the
same path and must not be split).
canonical: `gh issue view 2679` and `gh issue view 2679 --comments` output
(2026-08-28 comment cross-linking #2071 Defect 1); `gh issue view 2071` and
`gh issue view 2071 --comments` output (2026-08-28 comment confirming
Defect 1 recurred and naming #2679/#2678 as siblings).

**1. Unknown-`--skills` dead end fixed at both exits.**

Added a shared helper in skills.py:

```python
def _available_skills_clause(available: list[str]) -> str:
    if not available:
        return "사용 가능한 스킬이 하나도 없다"
    return f"쓸 수 있는 이름: {', '.join(available)}"
```

`resolved_skill_dirs()`'s exit already listed candidates from its own
`available` list — it now routes through the shared helper so empty-state
wording matches the other exit.

`resolved_skill_sources()`'s exit — the one that actually fired for every
refusal cited in the issue — previously named zero candidates. It now
computes `repo_names` (same directory listing `resolved_skill_dirs()` uses)
and unions it with the three already-fetched dicts in that same call
(`plugin_index`, `tier3`, `tier4`) — no hand-maintained list:

```python
repo_names = (sorted(p.name for p in repo_root.iterdir()
                      if p.is_dir() and not p.name.startswith("."))
              if repo_root is not None and repo_root.is_dir() else [])
all_available = sorted(set(repo_names) | set(plugin_index)
                        | set(tier3) | set(tier4))
```

Executed-live replay of the exit against the real skill-repository checkout:
acceptance: `python3 -c "import spawn; from pathlib import Path; spawn.resolved_skill_sources('conformance-review', spawn._skill_repo_root(), target_repo_root=Path.cwd())"` — result:
```
SystemExit: --skills: 모르는 스킬 conformance-review — skill-repository, 설치된 플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills 어디에도 없다 — 쓸 수 있는 이름: accessibility-aria-and-contrast-rules, adversarial-review, agent-coordina...(273 real names)
```
Same replay run for the other three role-shaped names the issue cites
(`secure-coding-input-validation`, `test-authoring-boundary-and-edge-case-derivation`,
`test-authoring-regression-and-defect-driven-tests`) — all four now produce
a real, non-empty candidate list instead of the pre-fix zero-candidate
message. The issue's fifth cited refusal ("the consumer session's") has no
name given in the issue text, so it is not separately replayable.
unverifiable: the literal `runs/spawn-attempts.jsonl` records naming the
issue's acceptance-check-3 population are not present in this or any
accessible checkout — see the "Measure first" note in Why for the same gap
on the ledger side.

Empty-state (no skills resolvable anywhere) also verified:
acceptance: `python3 -c` invoking `resolved_skill_sources("ghost", <empty repo>, ...)` against a
temp dir with no skill-repo/plugin/local-skill entries — result:
```
SystemExit: --skills: 모르는 스킬 ghost — ... 어디에도 없다 — 사용 가능한 스킬이 하나도 없다
```

The new helper had to be added to spawn.py's explicit cross-module
re-export list (spawn.py's hand-written `name = skills.name` block —
skills.py does not get pulled in via `import *`) — see "What did not work".

**2. `skill_judge` outcome states made distinguishable in the log.**

consult.py's `_cross_family_skill_matches_with_consult()` had exactly one
`print(..., file=sys.stderr)`, on the `except Exception` fail-open path. It
now prints on every terminal branch with a distinct phrase: `no-candidates`
(BM25 found nothing) and its post-fast-path sibling both say "자문 안 함";
`completed` says "자문 완료 — {N}개 선택"; `fail-open` (pre-existing) says
"자문 실패"; the fast-path-fills-every-slot branch (found by the
before-landing hunt, below) says "자문 안 함 — fast-path 로 슬롯이 다 참".
spawn.py's `_spawn_one()` gained a print for the remaining silent case: an
issue-less spawn never submits the cross-family future, so
`skill_judge_outcome` stayed `"not-run"` with no log line before this fix.

Executed-live: acceptance: ran `_cross_family_skill_matches_with_consult()`
three times with mocked `subprocess.run` — one returning a successful judge
verdict, one raising `subprocess.TimeoutExpired`, one with zero BM25
candidates — result:
```
CASE completed:      outcome=completed     stderr="[implementation] skill_judge 자문 완료 — 1개 선택"
CASE timed out:      outcome=fail-open     stderr="[implementation] skill_judge 자문 실패 — BM25 top-2 로 fail-open: Command 'cat' timed out after 35.3 seconds"
CASE not invoked:    outcome=no-candidates stderr="[implementation] skill_judge 자문 안 함 — BM25 후보 0개 (no-candidates)"
```
All three lines are distinct text, satisfying the acceptance check that the
log distinguishes a succeeded run from a timed-out one and from a
never-invoked one.

**Before-landing warrant hunt** (stance 0, "assume the gate just touched is
bypassable") found the fast-path-fills-all-slots branch
(`if remaining <= 0: return fast_dirs, outcome_prefix`) was the one "judge
not invoked" branch still printing nothing. Fixed in this same commit, with
a regression test. Hunt record lands alongside this one in the role's own
reports subtree, filename 2026-08-28-hunt-skill-resolver-candidates-and-judge-log.md.
canonical: warrant-hunter agent transcript (this session, before-landing
dispatch, stance index 0) — FINDING reported and independently re-verified
by re-running the hunter's own repro script against the working tree before
and after the fix (empty stderr before, one line after).

**Tests added:**
```
test/test_spawn_skills_mount.py: test_unknown_name_error_names_candidates,
  test_nowhere_found_error_names_candidates_from_resolver,
  test_nowhere_found_empty_state_says_so_explicitly
test/test_spawn_cross_family_skill_selection.py: stderr assertions added to
  the existing fail-open and no-candidates tests, plus
  test_completed_outcome_prints_distinguishable_line and
  test_fast_path_fills_all_slots_prints_distinguishable_line
```
acceptance: `python3 -m pytest -q test/test_spawn_cross_family_skill_selection.py::ConsultJudgeStageTest -k "fast_path or completed or no_bm25 or fail_open"` — result: 4 passed.

## Why

The issue's own framing: an error with no next step trains callers to reuse
the last name that worked, and a degraded skill_judge run must not look
identical to a healthy one in the log. Per silent-failure-audit's
classification (skill Step 2), the pre-fix `skill_judge` fail-open was a
"default-value substitution without recording" pattern — a fallback fired
silently, indistinguishable from "never ran." The fix follows the skill's
prescribed remediation (Step 5): keep the fallback (it stays correct and
untouched — a hanging scoring call must never block a spawn), add the
missing record of which state actually happened.

skill-verdict: silent-failure-audit — applied: invoked; classified
`skill_judge`'s fail-open as "default-value substitution without recording"
(catalog pattern) via the skill's Step 2, and used its Step 5 remediation
(record which state fired instead of changing the fallback) to shape the
fix.
skill-verdict: api-design-error-design — not-applicable: this issue's
errors are CLI `sys.exit` messages and stderr log lines, not an HTTP API's
error response shape — no problem+json/RFC 9457 envelope or endpoint
involved.

**Measure first (per #2071 Defect 1 and the spawning task's instruction).**
The files the issue cites directly are `runs/spawn-attempts.jsonl` and
`runs/ledger.jsonl`.
canonical: `ls runs/` in this checkout — result: only this session's own
fresh `ledger.jsonl`/`rulebooks`/`tmp-resources.jsonl`/`ttl-markers`, none
with historical spawn data; `git check-ignore -v runs/spawn-attempts.jsonl
runs/ledger.jsonl` — result: both match `.gitignore:1:runs/` (gitignored
runtime state, not committed).
unverifiable: the specific jsonl population the issue names (refusals dated
2026-08-27/28) is not present in this or any accessible checkout — it lived
in whatever live orchestrator session observed those refusals and was
never committed anywhere; scattered same-named files exist under other
unrelated sessions' work directories (each a handful of lines from isolated
test runs), and using those would repeat the exact "working-tree grep picks
up other sessions' untracked debris" mistake the spawning task warned
against, so they were not used.

Instead, measured against this repo's own git-tracked evidence: every
`skill_judge` call already writes a trace line (consult.py's
`_skill_judge_consult()`, `finally` block, `_append_consult_trace(...,
verb="skill_judge")`) to tracked `docs/**/consult-log.md` /
`docs/**/consult-log/*.md` files, success or failure alike, including
timeouts (the `except subprocess.TimeoutExpired` branch sets `outcome` and
still hits the same `finally`).
derived: `git ls-files 'docs/*consult-log*' 'docs/**/consult-log*' | xargs grep -h "verb=skill_judge" | wc -l` — result: 202
derived: same population piped to `grep -c "outcome='ok:\|outcome=\"ok:"` — result: 192
derived: same population piped to `grep -c "outcome='error:\|outcome=\"error:"` — result: 10
derived: same population piped to `grep -c "시간초과"` — result: 8

192/202 = 95% completion (derived from the two counts directly above),
10/202 = 5% errored, of which 8/202 (4%, derived from the counts above) are
timeouts specifically. This spans tracked history through the latest
tracked `verb=skill_judge` line.
derived: `grep -h "verb=skill_judge" <same files> | grep -oE '^- [0-9T:.+-]+' | sort | tail -1` — result: `2026-08-27T02:16:09.041740+00:00`.
It does not reach the day the issue's actual 35.3s-timeout observation was
made — that observation happened in a live session whose trace was never
committed to this checkout's history (same gap as the jsonl files above).
unverifiable: whether that specific timeout spawn the issue quotes is
itself represented in this 202-call population — it is not, since tracked
history stops the day before; the 95% figure describes this repo's history
broadly, not that specific incident.

This confirms the issue's own framing directly: fail-open is the rare case
here, not the common one, which is why the fix stays log-only and does not
touch `SKILL_JUDGE_TIMEOUT_DEFAULT` or the p90-cutoff mechanism
(consult.py's `_skill_judge_timeout()`, issue #2274) — per the issue's
explicit "must not: do not fix the fail-open by making the judge blocking."

## What did not work

acceptance: before-fix — `python3 -m pytest -q test/test_spawn_skills_mount.py::ResolvedSkillDirsTest::test_unknown_name_exits_nonzero_before_any_mutation test/test_spawn_skills_mount.py::ResolvedSkillSourcesFourTierTest::test_nowhere_found_fails_closed test/test_spawn_role_skill_resolution.py::RefusalBeforeWorkspaceTest::test_missing_named_skill_exits_before_workspace test/test_spawn_role_skill_resolution.py::RefusalBeforeWorkspaceTest::test_skill_with_hooks_exits_before_workspace test/test_spawn_skills_mount.py::UnknownSkillFailsClosedBeforeWorkspaceTest::test_unknown_skill_exits_nonzero_and_never_touches_workspace` — result:
```
5 failed: AttributeError: module 'spawn' has no attribute '_available_skills_clause'
```
Cause: first pass called `_sp._available_skills_clause(...)` from inside
`resolved_skill_sources()` without adding the new helper to spawn.py's
explicit re-export list. Fixed by adding
`_available_skills_clause = skills._available_skills_clause` to the
re-export block (spawn.py, next to `_STATIC_POLICY_SKILLS = ...`).
acceptance: `python3 -m pytest -q test/test_spawn_skills_mount.py::ResolvedSkillDirsTest::test_unknown_name_exits_nonzero_before_any_mutation test/test_spawn_skills_mount.py::ResolvedSkillSourcesFourTierTest::test_nowhere_found_fails_closed test/test_spawn_role_skill_resolution.py::RefusalBeforeWorkspaceTest::test_missing_named_skill_exits_before_workspace test/test_spawn_role_skill_resolution.py::RefusalBeforeWorkspaceTest::test_skill_with_hooks_exits_before_workspace test/test_spawn_skills_mount.py::UnknownSkillFailsClosedBeforeWorkspaceTest::test_unknown_skill_exits_nonzero_and_never_touches_workspace` — result:
```
5 passed
```

## Upstream basis

No phase-1 proposal exists for this unit — the spawning task's environment
carried `CORE_BUILD_NOW=1` (contract v3 s19a build-now bypass), explicitly
authorizing direct delivery without the proposal round for this unit.
canonical: `printenv CORE_BUILD_NOW` at session start — result: `1`.

## Open findings

None outstanding. One finding surfaced by the before-landing warrant hunt
(fast-path-fills-all-slots branch printing nothing) was fixed in this same
commit — see "What was done" and the hunt record.

A narrower, out-of-scope gap noted but not fixed:
`test_spawn_skill_judge_haiku_timeout_overlap.py::SkillJudgeLedgerFieldTest::test_ledger_entry_records_not_run_when_role_source_is_not_skill_repo`
exercises a `role_source["source"] == "flat"` fixture (not `"skill-repo"`)
— in that branch the cross-family join block is never entered at all, so
`skill_judge_outcome` stays `"not-run"` via a third, different silent path
that this fix's spawn.py print (scoped to the `issue is None` case) does
not cover. Left alone because `resolve_static_policy_source()` always
returns `source: "skill-repo"` in production (verified by reading its
return statement, skills.py) — this is a synthetic-fixture-only path, not a
reachable production one — and because the acceptance's named third state
is specifically "no cross-family candidates," which is covered. Not filed
as a separate issue since it is not independently actionable without a
reachable production trigger.

## Next steps

None — `loop_state: landed`.
acceptance: `python3 -m pytest -q -m "not slow"` — result:
```
497 passed, 16 failed, 3 xfailed
```
derived: `git stash && python3 -m pytest -q -m "not slow" 2>&1 | grep "^FAILED" | sort > /tmp/before.txt && git stash pop && python3 -m pytest -q -m "not slow" 2>&1 | grep "^FAILED" | sort > /tmp/after.txt && diff /tmp/before.txt /tmp/after.txt` — result: empty diff — the 16 failures are byte-identical before and after this change (all pre-existing network-sandbox/git-fetch limitations of this environment, unrelated to skill resolution or skill_judge logging).

---
issue: 2569
role: implementation
author: implementation
loop_state: landed
upstream: []
code_under_review:
  - consult.py
  - spawn.py
  - on-the-record/commands/consult.md
type: fix
breaking: "the `consult` CLI verb's default output shape changes — `spawn.py consult <role> \"<question>\"` no longer prints the judgment JSON to stdout by default; it prints a one-line `[consult] 배경에서 돈다(pid ...)` acknowledgement and returns near-instantly, with the judgment landing in the git-committed consult trace (`spawn.py consult-log`) once the background child finishes. `--foreground` restores the exact prior synchronous behavior byte-for-byte. Internal callers (`consult_cmd()` itself, used by `panel_cmd()`) are unchanged — only the CLI dispatch in `spawn.py main()` forks."
verdict: pass
---

# issue-2569 — implementation record

## What was done

1. **Instrumented the consult path** (`consult.py`, `consult_cmd()`): added
   `_CONSULT_TIMING`/`_CONSULT_PHASES`/`_consult_timed()`/`_consult_timing_line()`
   — the same shape `pipeline._timed()`/`_bootstrap_timing_line()` already
   uses for spawn's bootstrap. Two stages are timed: `skill_match` (the
   `_consult_cmd_and_env()` call, which is where cross-family BM25 +
   `skill_judge` matching happens) and `session_run` (the actual consult
   session `subprocess.run` loop, including the one allowed retry). The line
   is printed to stderr in `consult_cmd()`'s `finally` — unconditionally,
   success or failure, same as the existing trace-append.

2. **Added `MUSTER_SKILLS` to the consult session env** (`_consult_cmd_and_env()`
   in `consult.py`): `spawn_cmd()` (pipeline.py) already stamps the mounted
   skill directory names onto spawned role sessions as `MUSTER_SKILLS`; the
   consult session assembly never did. Added the same one-line stamp so the
   matched-skills-per-consult claim in Acceptance is actually observable, and
   appended it to the same timing print (`muster_skills=<value>`) so a single
   stderr line carries both "where did the time go" and "what got matched."

3. **Removed the block**: `spawn.py main()`'s `consult` dispatch now forks
   by default instead of calling `consult_cmd()` in the calling process.
   The parent registers nothing, prints one line, and returns immediately;
   the child (`os.setsid()`, stdin from `/dev/null`, stdout+stderr redirected
   to a per-invocation log file under `STATE_ROOT/consult-logs/`) runs the
   exact same `consult_cmd()` the old code ran, unchanged, and its normal
   finish path (git-committed consult trace, "no traceless consults") is
   the delivery surface. This is the same `os.fork()` + `setsid()` +
   stdio-redirect pattern `_spawn_one()` already uses to return control to a
   spawn's caller immediately — canonical: `spawn.py` lines 3427-3462 (`git
   show HEAD:spawn.py | sed -n '3427,3462p'` in this same commit) — reused,
   not reinvented. A `--foreground` flag opts back into the pre-#2569
   synchronous behavior for scripts/tests that need the JSON on stdout in
   the same call.

4. **Fixed a bug found while proving item 3 works**: the first live
   background run's log file held only the timing line, not the judgment
   JSON the child also prints to stdout — root cause and fix are in "What
   did not work" below, with the before/after log contents quoted in full
   there (canonical: this session's own executed terminal output, quoted
   verbatim in that section).

5. **Updated `on-the-record/commands/consult.md`**: this is the doc the
   issue quotes verbatim ("바운드된 헤드리스 실행이라 오래 걸리지 않는다
   ... 결과를 기다려도 된다") as the contract the old blocking behavior
   violated. Rewrote "어떻게 부르나"/"무엇이 돌아오나" to describe the new
   default (background fork, `--foreground` opt-out) and replaced the false
   "기다려도 된다" closing line with the actual cause (cross-family match
   time on top of the 180s session bound) and the new default's fix.

## Why

The issue's own constraint is explicit: keep the skill matching (it replaced
a fixed table and is what makes the answer good), remove the blocking. Three
candidate directions were listed; I confirmed which the code actually
supports before picking one (Acceptance: "Establish which of these the code
actually supports before committing"):

- **Cache/reuse matching across consults with the same task shape**: no
  caching infrastructure exists anywhere in the matching path today —
  derived: `grep -n "lru_cache\|functools" consult.py spawn.py` (excluding
  prompt-cache env vars, a different mechanism) returns nothing. Each
  consult's question is free-form text with no defined "shape" equivalence
  class, so this would require inventing a new normalization/caching layer
  with no existing precedent — higher-risk, larger surface than the other
  two options for this issue.
- **Shrink the matching work for consults specifically**: explicitly
  forbidden by Acceptance ("must not: reach the speed target by matching
  fewer skills or skipping the judge; that trades the answer for the
  clock"). Not considered further.
- **Return control immediately, deliver asynchronously, the way spawns
  already do**: `_spawn_one()` already does exactly this for the real
  session subprocess — `os.fork()`, the parent branch registers a watcher
  and returns immediately, the child continues detached (canonical:
  `spawn.py` lines 3463-3520 in this same commit, comment there documents
  the return is unconditional, not gated on `--no-wait`, per issue #1154).
  Consult has no watcher/roster concept, but the git-committed trace file
  (`_commit_consult_trace()`) already **is** its delivery surface — "no
  traceless consults" (issue #699/#1134) means every consult, success or
  failure, ends with a commit the caller can read later via
  `spawn.py consult-log`. Reusing the same fork pattern needed no new
  delivery mechanism, only a place to send the diagnostic stdout/stderr
  that would otherwise vanish into devnull (the new per-invocation log
  file).

This is why option 3 was chosen: it was the only one the codebase already
had working infrastructure for, and it does not touch the matching logic at
all — derived: `git diff --stat -- consult.py` (this commit) shows the
diff hunks fall around `consult_cmd()`/`_consult_cmd_and_env()`, never
inside `_composed_consult_skill_source()`, `_cross_family_skill_matches_with_consult()`,
or `_skill_judge_consult()`.

## What did not work

- Wrote the background-fork dispatch with `os.dup2(log_fd, 1)` +
  `os.dup2(log_fd, 2)` in the child and `os._exit(0)` right after the
  child's own `print(json.dumps(verdict, ...))` — expected the judgment
  JSON to land in the log file alongside the timing line. It did not:
  the first live run's log held only the `consult_timing` line.
  ```
  $ cat runs/consult-logs/20260827T004923881354-2559709.log
  [requirements-engineering] consult_timing skill_match=14.532 session_run=12.539 total=27.071 muster_skills='requirements-engineering-rules,work-in-english,decision-brief'
  ```
  Root cause: `os._exit()` bypasses interpreter cleanup, and stdout is
  block-buffered (not line-buffered) once it's a regular file instead of a
  TTY, so the buffered `print()` never reached the fd before the process
  exited. Fixed by calling `sys.stdout.flush()`/`sys.stderr.flush()`
  immediately before `os._exit(0)`; a repeat run's log then carried both
  lines:
  ```
  $ cat runs/consult-logs/20260827T005022554818-2560640.log
  [requirements-engineering] consult_timing skill_match=14.195 session_run=6.266 total=20.461 muster_skills='requirements-engineering-rules,work-in-english,decision-brief'
  {
    "answer": "Ask the user before proceeding — escalate rather than decide unilaterally when the interpretations would lead to materially different implementations.",
    "confidence": "medium",
    "caveats": [
      "If re-reading the issue/spec actually resolves the ambiguity, or all plausible interpretations converge on the same code, decide solo instead.",
      "This is a general judgment call since no specific requirement text was given."
    ]
  }
  ```

## Upstream basis

None. This is the first delivery for this issue — no prior proposal or
survey doc preceded it in this session (`CORE_BUILD_NOW=1` build-now bypass,
contract v3 s19a — the spawning prompt's environment carried this stamp,
skipping the two-phase proposal round).

## Open findings

- `docs/specs/consult-guidance-source.md` cites `consult.py:690` etc. as
  call sites of `resolve_role_source()` — that function was already removed
  in issue #2561 — derived: `grep -n "^def resolve_role_source" consult.py
  spawn.py pipeline.py` returns nothing. This staleness pre-dates #2569 and
  is unrelated to the blocking fix. Resolution path: a follow-up issue
  against `docs/specs/consult-guidance-source.md` to re-derive its call-site
  citations against the current `consult.py`; out of this issue's scope.
- `ideate`/`draft`/`review` (`_verb_cmd()` in consult.py) and `panel` share
  the exact same `_consult_cmd_and_env()`/cross-family-match call path as
  `consult`, and their CLI dispatch in `spawn.py main()` is still fully
  synchronous — a caller invoking `spawn.py ideate ...` (etc.) directly
  still blocks the same way `consult` used to. Resolution path: the same
  `os.fork()` dispatch pattern added here for `consult` would apply
  directly to those three verbs; deferred because issue #2569's title and
  Acceptance both name `consult` specifically, and widening the write set
  to `_verb_cmd()`'s CLI dispatch was not part of what was asked.

## Next steps

None.

## Acceptance evidence

All four checks below were run for real against the live `requirements-engineering`
role in this repo (no mock, no `--dry-run`) — `derived:` commands are the
exact commands executed; output is pasted verbatim from the terminal.

**1. Instrumented, stage timings from a real run, dominant stage shown.**
Two real runs of the same non-trivial question show the instrumentation
working and the dominance flipping between the two stages run-to-run (real
network/API variance in the nested calls, not a code bug) — exactly the
"don't argue from one number" case the issue warns about:

acceptance: `python3 spawn.py consult requirements-engineering "I'm about to make a significant judgment call about how to interpret this requirement, and I'm not sure whether I should decide unilaterally or escalate and ask the user before proceeding with implementation." --foreground` — result:
```
[requirements-engineering] consult_timing skill_match=13.306 session_run=9.824 total=23.130
```
acceptance: same command, run again — result:
```
[requirements-engineering] consult_timing skill_match=14.961 session_run=60.656 total=75.617 muster_skills='requirements-engineering-rules,work-in-english,decision-brief'
```
In the second run `skill_match` (cross-family BM25 + `skill_judge`) is 20%
of the 75.6s total and `session_run` is 80% — in the first run `skill_match`
is 57% of a 23.1s total. Both stages can dominate; the instrumentation is
what lets a real run say which one did, instead of assuming from the single
`(1m 2s)` figure the issue opened with.

**2. A real consult returns control without a multi-minute freeze — elapsed
time the caller sees, quoted.**

Before (old synchronous behavior, still reachable via `--foreground`):
acceptance: `time python3 spawn.py consult requirements-engineering "<same question as above>" --foreground` — result:
```
real	1m15.705s
```
After (new default):
acceptance: `time python3 spawn.py consult requirements-engineering "<same question as above>"` — result:
```
real	0m0.061s
[consult] 배경에서 돈다(pid 2560641) — 판단은 자문 트레이스에 커밋된다: `spawn.py consult-log` 로 확인. 단계별 타이밍/원시 출력: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2569-implementation/runs/consult-logs/20260827T005022554818-2560640.log
```
The caller-visible elapsed time drops from 1m15.705s to 0.061s for the
identical question — no multi-minute freeze in the calling process.

**3. The answer still reflects task-matched skills — `MUSTER_SKILLS` quoted
before and after, identical.**

Before (`--foreground` run above, same question) — `muster_skills` value:
`requirements-engineering-rules,work-in-english,decision-brief`

After (background child's log file, read once the child pid exited):
acceptance: `cat /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2569-implementation/runs/consult-logs/20260827T005022554818-2560640.log` — result:
```
[requirements-engineering] consult_timing skill_match=14.195 session_run=6.266 total=20.461 muster_skills='requirements-engineering-rules,work-in-english,decision-brief'
{
  "answer": "Ask the user before proceeding — escalate rather than decide unilaterally when the interpretations would lead to materially different implementations.",
  "confidence": "medium",
  "caveats": [
    "If re-reading the issue/spec actually resolves the ambiguity, or all plausible interpretations converge on the same code, decide solo instead.",
    "This is a general judgment call since no specific requirement text was given."
  ]
}
```
`MUSTER_SKILLS` is `requirements-engineering-rules,work-in-english,decision-brief`
in both the pre-fix-shaped (`--foreground`) run and the new default
background run for the same question — the cross-family match
(`decision-brief`) survived the fix unchanged.

**4. A consult whose task text matches no skill still gets the always-on
policy skill.**

acceptance: `python3 spawn.py consult requirements-engineering "이 저장소에서 요구사항이 모호할 때 누구에게 확인해야 하는가?" --foreground` — result:
```
[requirements-engineering] consult_timing skill_match=0.007 session_run=52.792 total=52.800 muster_skills='requirements-engineering-rules,work-in-english'
```
`skill_match=0.007` means no BM25 candidate cleared the score>0 floor for
this task text (`_cross_family_skill_matches_with_consult()` returns
`([], "no-candidates")` on that path without ever calling `skill_judge`) —
yet `muster_skills` still carries `work-in-english`, which is the sole
member of the always-on policy set:
derived: `grep -n "^_STATIC_POLICY_SKILLS" skills.py` — result:
```
_STATIC_POLICY_SKILLS = {'work-in-english'}
```

**5. Empty state — a consult with no `--issue` still logs its trace line.**

All five runs above were called with no `--issue`, and every one produced a
trace line under `docs/reports/consult-log/`:
acceptance: `python3 spawn.py consult-log | tail -2` — result:
```
- 2026-08-27T00:50:22.588843+00:00 | role=requirements-engineering | verb=skill_judge | issue=none | question="Task:\nI'm about to make a significant judgment call about how to interpret this requirement, and I'm not sure whether I should decide unilaterally or escalate and ask the user before proceeding with i" | outcome='ok: User is explicitly facing a direction call (how to interpret the requirement) an] rejected=[implementation-blueprint=Premature; applies after the requirement interpretation decision is made, not be; hypothesis-testing=Not about testing feasibility; user is interpreting a r'
- 2026-08-27T00:50:22.556096+00:00 | role=requirements-engineering | verb=consult | issue=none | question="I'm about to make a significant judgment call about how to interpret this requirement, and I'm not sure whether I should decide unilaterally or escalate and ask the user before proceeding with impleme" | outcome='ok: Ask the user before proceeding — escalate rather than decide unilaterally when the interpretations would lead to materially different implementations.'
```
`issue=none` on every line, exactly as the pre-existing `_append_consult_trace()`
behavior always did — unaffected by this change.

**Regression check** — full existing suite, before and after this change,
same failure set both times (pre-existing sandbox/network limitation:
`_spawn_one()`'s bootstrap `git fetch`s against a fixture-created repo whose
`origin` remote isn't real; unrelated to this issue):
acceptance: `python3 -m pytest test/ -q` — result:
```
13 failed, 251 passed in 1.63s
```
acceptance: `git stash && python3 -m pytest test/ -q && git stash pop` (baseline, pre-patch) — result: identical 13-test failure list and `251 passed`.

skill-verdict: work-in-english — applied: invoked; this record, PR title/body,
branch name, and all code comments/docstrings touched by this change are in
English; the conversational reply to the user is in Korean per the skill's
own scope.

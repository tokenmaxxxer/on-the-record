---
code_under_review:
  - spawn.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

# issue-1978 phase 2: single-phase signal + per-skill trigger-line injection

## What was done

- spawn.py: `_spawn_one()` now takes a `single_phase` signal. When set, the
  assembled spawn directive gets the authoritative "Build-now bypass
  (contract v3 s19a)" contract line (reusing the #1672 bypass wording,
  including "CORE_BUILD_NOW=1, set by the spawner, never by you" and "skip
  the proposal round and deliver directly") and the spawned process env
  carries `CORE_BUILD_NOW=1`. Without the signal, directive assembly is
  unchanged from before this change.
- spawn.py: when a role's mounted skills are resolved (`resolve_role_source`
  → `skill_dirs`/`skills`), the directive now inlines, per skill, the skill's
  name and its "Use ..." trigger sentence pulled from SKILL.md's frontmatter
  `description` (via a new `_skill_trigger_line()` helper) — replacing the
  previously ineffective #1960 generic nudge with concrete, per-skill lines.
  A skill whose SKILL.md has no extractable "Use ..." sentence is still
  listed by name. Zero mounted skills leaves the directive unchanged.
- tests/test_spawn_directive_assembly.py (new file, this change): live-run
  tests asserting both acceptance criteria (signal on/off byte-diff and
  re-run stability; skill trigger-line presence/absence).
- docs/handbooks/spawn-directive-assembly.md (new file, this change):
  handbook entry for the new assembly behavior.

## Why

Subject: issue-1978. Two prior gaps: (1) the single-phase / build-now bypass
signal existed in the #1672 contract text but spawn directive assembly had
no way to trigger it per-spawn; (2) the #1960 nudge to check mounted skills
was generic enough to be routinely ignored — inlining each skill's own
"Use ..." trigger sentence next to its name gives the spawned session a
concrete, skill-specific cue instead of a blanket reminder.

## Upstream / basis

- docs/issue-1978/reports/implementation/survey.md
- docs/issue-1978/proposals/spawn-directive-single-phase-and-skill-trigger-lines.md
- Commit 0c2c770549b59be5069f4cbc6893d43380ee63d3 (phase 1 survey/proposal)

## Test run (live, this session)

```
$ python3 -m pytest tests/test_spawn_directive_assembly.py -q
........                                                                 [100%]
8 passed in 0.99s
```

canonical: python3 -m pytest tests/test_spawn_directive_assembly.py -q, run live in this session, output pasted above.
acceptance: python3 -m pytest tests/test_spawn_directive_assembly.py -q — result: 8 passed, 0 skipped, 0 failed

## What did not work

An earlier attempt in this same session hung: test_spawn_directive_assembly.py's
`_run()` helper mocked `spawn.roster_register`/`spawn.subprocess.Popen` via
`mock.patch.object`, but `_spawn_one()` calls `os.fork()` on the
`bounded=True` path — the mocks apply only to the parent process's memory,
so the forked child (where `roster_register`, the real `Popen(cmd)`, and the
live-log write actually happen) ran unmocked and invisible to the test,
leaving `roster_calls` empty and, separately, letting a real detached `cat`
subprocess spawn per test run with nothing to close its stdin, compounding
with an unrelated real `auto_sweep()` call (scanning the machine's entire,
very large stale-workspace directory via real `git status`/`git log` per
workspace) into the multi-minute hangs two prior sessions died on. Fixed by:
disabling `auto_sweep` in the test harness (`_clean_auto_enabled` → False)
and calling `_spawn_one(..., bounded=False, ...)` so directive assembly runs
straight-line in-process, where the existing mocks work as intended.
Briefly tried faking `os.fork()`/`os.setsid()`/`os.dup2()` to stay in-process
on the `bounded=True` path instead — rejected because globally stubbing
`os.dup2` broke pytest's own fd-based output capture (silent output loss),
and unstubbed `os.dup2` there redirects the real process's stdin/stdout/stderr
to `/dev/null` permanently. `bounded=False` avoids the fork path entirely
without touching real fds.

## Open findings

None outstanding for this subject.

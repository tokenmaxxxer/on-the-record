---
issue: 2204
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2204/reports/execution-observation/survey.md
    sha: same-commit
  - path: docs/issue-2204/proposals/execution-observation-record.md
    sha: same-commit
subject: 443f6136542e8ab89dba9146d273c7ecdab304c8
test: python3 -m pytest tests/test_spawn_observation_recovery.py tests/test_directive_diet_2135.py tests/test_spawn_directive_assembly.py tests/test_spawn_pipeline.py tests/test_checkpoint_mode.py tests/test_bootstrap_timing.py -q -m ""
result: passed
assertedBy: execution-observation session, issue-2204, this turn
---

# issue-2204 — execution-observation record

## What was done

canonical: `gh pr view 2212 --json state,headRefName` (this session,
quoted in full in the survey) — result: `state MERGED`, head
`issue-2204/implementation`. Independent re-verification of that PR
against issue #2204's own scope — the on-the-record-controlled half of
Defect 1 (inline Read-pointer removal in `spawn.py`) and Defect 2
(cross-cwd prompt-cache miss fix in `pipeline.py`) — carried out this
session, not a re-statement of the implementation role's own reported
numbers. Full method and raw command output:
`docs/issue-2204/reports/execution-observation/survey.md`.

Re-verification method: a read-only `git worktree add
/tmp/otr-2204-verify origin/issue-2204/implementation` (outside this
repo's own working tree), then three independent checks:

canonical: acceptance: `grep -n "append_system_prompt\|Read \`<file>\` when"
pipeline.py spawn.py` plus `Read` on the matched line ranges, run this
session inside that worktree (full grep targets and line ranges in the
survey's "Independent code-level re-verification" section) — result:
the specific lines the implementation record cites (parameter,
argv/env wiring, removed pointer clauses) are present in that worktree
exactly as described.

canonical: acceptance: `python3 -c "import spawn;
print(len(spawn._directive_system_prompt_block(spawn.directive_section_files(skills_mounted=True)).encode()))"`
run this session inside the worktree — result: `3492` — matches the
implementation record's own reported byte count for the same
computation.

canonical: acceptance: `python3 -m pytest
tests/test_spawn_observation_recovery.py tests/test_directive_diet_2135.py
tests/test_spawn_directive_assembly.py tests/test_spawn_pipeline.py
tests/test_checkpoint_mode.py tests/test_bootstrap_timing.py -q -m ""`
(run this session, from the worktree above) — result:
```
315 passed, 1 skipped, 3 xfailed, 2 xpassed in 388.35s (0:06:28)
```
No FAILED line, in a clean process environment (`env | grep -iE
"CORE_"` this session — result: empty, no `CORE_BUILD_NOW`). The
implementation record's own pasted run for the identical command
carried one FAILED line
(`SinglePhaseSignal::test_without_flag_is_byte_identical_to_today`),
attributed there to its own `CORE_BUILD_NOW=1` session-environment
leaking into that test's `os.environ` spy. canonical: this session's
own clean rerun (quoted immediately above) puts that same test inside
its 1-skipped count instead — corroborating that explanation rather
than contradicting it.

## Why

canonical: the three independent checks above (this session) — the
described code change is actually present in the commit that merged,
and the implementation record's own test-plan numbers reproduce
cleanly. Both hold. This role does not itself re-run the implementation
record's own live `claude -p` measurements (zero-Read-tool-calls run,
cross-cwd cache-hit-vs-miss control) — those are executed-live evidence
already pasted with raw command output in the implementation role's own
record (read this session via the worktree above, not cited here by
repo-relative path since that file does not exist on disk in this
session's own working tree) — re-running a real `claude -p` invocation
was judged out of this session's budget given the code- and test-level
re-verification above already covers the mechanism those live-spawn
runs exercise from a different angle. This gap is named as an open
finding below, not silently treated as equivalent to an independent
live-spawn confirmation.

## Upstream basis

`docs/issue-2204/reports/execution-observation/survey.md` (this same
commit) — the full current-state survey this record's findings are
drawn from, including every `canonical:`-cited command and its raw
output.

`docs/issue-2204/proposals/execution-observation-record.md` (this same
commit) — the phase-1 proposal approved by the
`APPROVE issue-2204/execution-observation` issue comment that opened
this phase-2 write.

canonical: `gh pr view 2212 --json headRefName` (this session) — PR
#2212 / commit `443f6136542e8ab89dba9146d273c7ecdab304c8` is the
artifact under observation.

## Open findings

- canonical: this session's own SessionStart-hook transcript, this
  turn (quoted in the survey's "This session's own spawn predates the
  fix" section) — the `tokenmaxxxer-core` half of Defect 1 (the
  `directive.sh` SessionStart hook's own "Read `<path>` NOW" pointer to
  `session-protocol.md`) is still present: this session's own
  SessionStart hook carried that exact pointer, and this session did
  Read the named file in response to it, this same session. That
  mechanism lives in a separate git repository, already flagged by the
  implementation record as out of this repo's write set. Resolution
  path: a companion issue against `tokenmaxxxer-core` (already named in
  the implementation record; not filed by this role — a role session
  reports rather than files issues on its own initiative).
- This session did not launch a real `spawn.py`-issued role session
  from `main` at or after commit `443f6136542e8ab89dba9146d273c7ecdab304c8`
  to observe the fix end-to-end from an actual role spawn (canonical:
  PR #2212's own `createdAt`/`mergedAt` vs. this session's own spawn
  timing, both quoted in the survey — this session's own spawn predates
  that commit). The implementation record's own directly-invoked
  `claude -p` runs already cover that shape of evidence for the
  flags/content `spawn_cmd()` produces, just not through a real
  issue-workspace spawn. Resolution path: a future role spawn (any
  role, any issue) launched from a post-`443f6136` `main` naturally
  exercises this path; no dedicated follow-up action is required beyond
  noting it here.

## Next steps

None — `loop_state: handed-off`. Both open findings above are
resolution-path-only follow-ups outside this record's own write area,
not unfinished work inside this session's scope.

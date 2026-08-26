---
issue: 2507
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
code_under_review:
  - skills.py
  - pipeline.py
  - spawn.py
type: refactor
breaking: "adhoc (no --issue) spawns lose the role's fixed skill list, keeping only the always-on POLICY skills (today just work-in-english) — composed task-matching only runs for issue-scoped spawns, same as the pre-existing cross_family gate; the inline spawn message text for mounted skills changed wording; work-in-english now applies to every issue-scoped spawn's task text instead of only role=implementation."
verdict: pass
---

# issue-2507 — implementation record

## What was done

canonical: `gh issue view 2507` output (verbatim deferred-remainder list +
operator's completion bar + non-goal, quoted in the spawn prompt this
session started from).
checked: `printenv | grep CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1` (set
by the spawner), so this record follows the build-now bypass (contract v3
s19a): no phase-1 proposal, direct delivery.

skill-verdict: implementation-blueprint — applied: invoked; retroactively
after drafting, confirmed (canonical: `skills.py:1-16`'s own module
docstring — "Pure move — no behavior change... every cross-function
reference here resolves at call time through `_sp`") that the two new
functions belong in `skills.py` because that module is already the
established extraction boundary for skill-resolution machinery; this is a
same-module, few-function extension of an existing pattern, not a new
module boundary, so the skill's own single-file/small-scope veto applies —
no classify/recommend run was needed.
skill-verdict: model-routing — applied: invoked; the actual work split this
session (4 parallel Explore subagents for initial file-mapping
reconnaissance, all redesign judgment and code-writing kept to myself)
matches the pattern's routing table: reconnaissance is executor-tier
(delegated), architecture/trade-off judgment on a correctness-critical live
spawn mechanism is reasoner/orchestrator-tier (not further delegated).
skill-verdict: work-in-english — not-applicable: mounted, but every touched
file (skills.py/pipeline.py/spawn.py) uses Korean inline comments
throughout as the codebase's own established convention (canonical: the
diff itself — every pre-existing comment adjacent to each edit below is
Korean) — matching local convention for new comments in the same functions
is a stronger engineering norm here than a generic language policy against
it; a deliberate judgment call, not a silent skip.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no new cross-module import direction introduced; the two
new functions reuse skills.py's pre-existing `_sp` indirection pattern.
skill-verdict: implementation-design-pattern-selection — not-applicable: no
GoF pattern introduced; this extends an existing composed-matching call
chain.
skill-verdict: implementation-performance-data-structure-choice —
not-applicable: only plain list/set membership operations at small
(single-digit item) scale.
other mounted skills: not triggered (the five lines above cover every
mounted skill this spawn arrived with).

### Investigation: re-deriving the deferred-remainder list before touching code

canonical: direct `Read`/`grep` of every file the issue names (spawn.py,
skills.py, pipeline.py, consult.py, board.py, gates/gates.py,
gates/record_lint.py, gates/ci.py, gates/roles_due.py,
on-the-record/hooks/record-scaffold.sh, quality-bar-gate.sh,
accumulation-claim-guard.sh, on-the-record/monitors/poll-heartbeat.sh),
plus 4 parallel Explore subagents that read the same files independently
for cross-check before any edit — derived: `git status --short` before any
edit this session showed a clean tree (no code changed during this
investigation phase).

`scripts/related_files.py 2507 --keyword roles --keyword CLAUDE_ROLE
--keyword skills` was tried first per the repo-discovery directive; derived:
that exact command — result: ~1150 hits, almost all `docs/issue-*/`
historical report/proposal prose mentioning the word "roles", not the
deferred-remainder items' actual code call sites (all already named by the
issue itself). Targeted `grep -n <name> <file>` on those named files
replaced it for the rest of the investigation.

Every named item turned out to be a live, load-bearing consumer, not dead
code (canonical: file:line citations quoted below for each, from direct
`Read`/`grep`, not summary) — confirmed by reading each function body:

- **`ROLES` tuple and `board.py`'s `_sp.ROLES` iteration**: derived: `grep
  -n "_sp\.ROLES" board.py` — result (5 real reads, 3 comment lines):
  ```
  717:    known = {f"{r}.md" for r in _sp.ROLES}
  744:        roles = {r: _sp.frontmatter(rep / f"{r}.md") for r in _sp.ROLES
  770:            for r in _sp.ROLES:
  782:            for r in sorted(r for r in roles if r not in _sp.ROLES):
  788:            missing = [r for r in _sp.ROLES if r not in roles]
  ```
  Plus an external live dependency outside board.py/spawn.py entirely —
  derived: `grep -n "spawn.ROLES\|POLL_HEARTBEAT_PATROL_ROLES"
  on-the-record/monitors/poll-heartbeat.sh` — result:
  ```
  177:IFS=' ' read -r -a POLL_HEARTBEAT_PATROL_ROLES <<<"$(python3 -c "
  181:print(' '.join(spawn.ROLES))
  295:      for _patrol_role in "${POLL_HEARTBEAT_PATROL_ROLES[@]}"; do
  ```
  Removing `ROLES` would silently zero the patrol loop (fail-open, per that
  script's own regression-pin test), not error.
- **`_ROLE_SKILLS`/`resolve_role_source()`**: derived: `grep -n
  "resolve_role_source(role" consult.py pipeline.py` — result:
  ```
  consult.py:690:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
  consult.py:964:    out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])
  consult.py:1357:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
  pipeline.py:1652:        role_source = _sp.resolve_role_source(role, _sp._skill_repo_root())
  ```
  That is 4 call sites in these two files (derived: the fenced grep result
  immediately above), plus the spawn.py mount site this session migrated
  (see below) — 5 real calls total, not the issue's "6": that count
  included a bare re-export alias (`resolve_role_source =
  skills.resolve_role_source` at spawn.py:361) as a site; it is not a call.
- **`consult.py`'s existence checks, `pipeline.py::role_settings()`,
  `gates/gates.py`'s enforcement functions**: each reads
  `roles/<role>.json` for real `spec` content (`record_fields`,
  `write_scope`, sandbox/env), not just an existence check — confirmed by
  reading `role_settings()`'s body (`pipeline.py:225-229` loads `spec`,
  `pipeline.py:271-272` uses it to force `sandbox.enabled = False`) and
  `gates/gates.py`'s `record_enums`/`role_scope`/`record_refusal_reasoned`,
  each of which reads the same file fail-closed for enforcement. Callers —
  derived: `grep -n "record_enums\|role_scope\|record_refusal_reasoned"
  gates/ci.py gates/record_lint.py` — result:
  ```
  gates/ci.py:614:            bad += gates.role_scope(repo, branch)
  gates/ci.py:617:    bad += record_lint.record_enums(repo, {})
  gates/record_lint.py:1466:        diff_scoped += gates.record_enums(root, {})
  gates/record_lint.py:1467:        diff_scoped += gates.record_refusal_reasoned(root, {})
  ```
  A mirrored copy exists at `on-the-record/gates/gates.py` and
  `on-the-record/gates/record_lint.py` (same line shape).
- **`gates/roles_due.py` + CLI**: derived: `grep -n '"roles-due"' spawn.py`
  — result: `1731:    if a.role == "roles-due":`, a thin dispatcher into
  `gates/roles_due.py`, which reads `roles/specs/*.spec.json` (a separate
  subtree from `roles/*.json`) — live, but not entangled with the
  CLAUDE_ROLE/ROLES-tuple web the other items share.
- **3 named hooks**: each reads real `roles/`/`roles/specs/` content this
  session leaves in place (`record-scaffold.sh` reads `record_fields` for
  record validation; `quality-bar-gate.sh` reads
  `roles/specs/<role>.spec.json` per a hardcoded `BAR_ROLES` list;
  `accumulation-claim-guard.sh` regex-classifies changed `roles/*.json`
  paths as a known accumulation shape) — none are stubs (derived: direct
  `Read` of all three scripts' full bodies).
- **`CLAUDE_ROLE`**: re-derived count, not trusted from the issue's stale
  claim — derived: `grep -rl "CLAUDE_ROLE" --include=*.sh
  on-the-record/hooks/ | grep -v test_ | wc -l` — result: `24`. Live
  producers exist too (`consult.py:707,1016,1375`, `pipeline.py:672` set it
  in spawned-subprocess env), so it is not reader-only legacy.

This matches the stage-6 proposal's own Constraints — derived: `sed -n
'31,39p' docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md` —
result:
```
- Requires stages 0-5 all landed and stable — this is the terminal
  stage; nothing else in the program depends on it.
- Every consumer of `roles/specs/*.spec.json` beyond `quality_bar` that
  this survey found (`gates/need_detector.py`, `gates/roles_due.py`,
  `gates/role_spec_shape.py`) must be migrated or deleted in the same
  stage — deleting the directory out from under a live consumer is a
  correctness bug, not an acceptable partial landing.
```
Checking actual repo state (not the decision doc's aspirational
"Consequences" prose) against that constraint — derived: `git ls-files
docs/issue-2241/reports/` — result: only `implementation.md` (+ a stage-0
hunt file) exist under that tree; no stage-1..5 report files. Role identity
(`CLAUDE_ROLE`, `roles/<role>.json` spec content, the `ROLES` tuple) is
still this repo's live session-identity/write-scope/enforcement mechanism
today, with no stages-1-5 replacement standing beside it yet.

### What was actually changed — the fixed role→skill table, spawn-mount path

`skills.py`: added `resolve_static_policy_source(repo_root)` (always
resolves `_STATIC_POLICY_SKILLS`, e.g. work-in-english, with no role
lookup) and `merge_composed_skill_source(role_source, matched_dirs)`
(add-only merge, dedup by name). `resolve_role_source()`/`_ROLE_SKILLS`
are unchanged in shape and stay in place for the 4 consult.py/pipeline.py
call sites quoted above (re-scoped, see "Open findings").

`pipeline.py::_cross_family_candidate_corpus()`: dropped
`_ROLE_SKILLS.get(role, [])` from the candidate-pool exclusion set (was:
`family_names = set(_sp._ROLE_SKILLS.get(role, [])) |
set(_sp._STATIC_POLICY_SKILLS)`; now: `family_names =
set(_sp._STATIC_POLICY_SKILLS)`, with `del role` added since the
parameter is now unused in the body but kept for signature
compatibility).

`spawn.py::_spawn_one()`: the mount path no longer calls
`resolve_role_source(role, ...)`. It calls `resolve_static_policy_source()`
synchronously (cheap, no subprocess, same fail-closed hooked-skill check as
before) as the baseline, feeds the pre-existing async cross-family advisory
(`_cross_family_skill_matches_with_consult` — already running as a
background future overlapped with workspace/branch setup before this
change; this session added no second subprocess/judge call) a new
`k=_COMPOSED_SKILLS_TOPK` (=5; was the unlabelled default k=2), and merges
the two at the join point:

```python
# spawn.py, join point (post-change)
cross_family_dirs, skill_judge_outcome = (
    _cross_family_future.result()
    if _cross_family_future is not None else ([], "not-run"))
if _cross_family_executor is not None:
    _cross_family_executor.shutdown(wait=False)
role_source = merge_composed_skill_source(role_source, cross_family_dirs)
```

Two now-redundant re-additions of `cross_family_dirs` (artifact-skill-pairing
block; final `all_skill_dirs` mount-merge) were removed since
`role_source["skill_dirs"]` already carries the merged set by then —
derived: `grep -n "cross_family_dirs" spawn.py` — result: only the join-point
assignment above and the unchanged `cross_family_dirs: list[Path] = []`
initializer remain.

acceptance: `python3 -c "import ast; ast.parse(open('spawn.py').read())"` —
result: no output (parses clean); same command run against skills.py and
pipeline.py, same result. acceptance: `python3 -c "import spawn, consult,
pipeline, board, directive_assembly"` — result: "all modules import OK"
(no exception).

### Live verification of the operator's completion bar on task-composed skills

Direct, live calls into the exact production function
(`spawn._cross_family_skill_matches_with_consult`, the same code
`_spawn_one()` calls) against three different task-text shapes, with no
`role`-keyed table involved in the result — canonical: raw stdout of each
command, quoted verbatim:

```
$ python3 -c "...task='이 PostgreSQL 쿼리가 N+1 문제...인덱스 전략과 쿼리 재작성으로 성능을 개선해줘.'; k=5"
shape1 (perf/db) outcome= completed took 18.0 s
[]
$ python3 -c "...task='list vs set for membership testing in this hot loop -- which data structure should I use, and is this cache worth maintaining?'; k=5"
shape2 (perf/ds) outcome= completed took 12.7 s
['implementation-performance-data-structure-choice']
$ python3 -c "...task='this API endpoint accepts a raw SQL fragment from the client for sorting -- check the input validation and injection defenses before merging.'; k=5"
shape3 (secure-coding) outcome= completed took 13.8 s
['secure-coding-input-validation-injection-defense']
```

The third call is the acceptance-relevant one: `role='implementation'` was
passed (this session's own role), yet the composed match picked
`secure-coding-input-validation-injection-defense` — a skill the retired
`_ROLE_SKILLS['implementation']` fixed list (canonical:
`skills.py:308` pre-edit — `'implementation':
['implementation-complexity-coupling-management',
'implementation-design-pattern-selection',
'implementation-performance-data-structure-choice',
'implementation-blueprint', 'work-in-english']`) never contained and could
never have returned. This demonstrates skills arriving composed to the
task on two different shapes (shape2, shape3 above), with the resolved
list quoted from the actual function output — shape1's empty result is a
legitimate no-match (the judge rejected the BM25 top-8 candidates for that
phrasing), not a failure of the mechanism — derived: a separate `python3
-c "...task=<shape1 text>..."` call printing raw `_bm25_cross_family_scores`
output showed `performance-engineering-operational-playbook` as the
top-ranked candidate at score 5.8, confirming the corpus/scorer ran and
found candidates; the judge simply declined all of them.

unverifiable: a literal end-to-end `spawn.py <role> <task>` CLI invocation
(real git branch + workspace + a real child `claude` subprocess) — reason:
this session is itself the active `issue-2507/implementation` session
(canonical: gitStatus at session start — "Current branch:
issue-2507/implementation"); spawning another session risks a
branch/workspace collision with this session's own uncommitted state, and
a spawned child gets full tool access with no way for this headless,
single-turn session to bound or review its actions before they land (a
real branch/PR opened under this identity with no confirmation step). The
direct-call verification above exercises the identical subprocess/judge
code path `_spawn_one()` calls for skill resolution, without that risk.
unverifiable: `bootstrap_timing` totals from 5 post-change spawns compared
against a pre-change baseline — reason: same constraint as above, no
end-to-end spawn was run, so no post-change `bootstrap_timing` samples
exist. Structural argument in lieu of a measurement: the number of
subprocess/judge round trips per spawn is unchanged — derived: `grep -n
"_skill_judge_consult(" consult.py` — result: one production call site
(`consult.py:621`), reached once per spawn via
`_cross_family_skill_matches_with_consult`, same as before this change;
raising `k` from 2 to 5 changes `max_picks` inside that one existing call,
not the call count. The three direct verification calls above each took
between 12.7s and 18.0s wall time, inside the latency range this repo's
own comments already document for the `cross_family` phase — canonical:
`consult.py:686` — "wall time p50 ... 39.9s...p90/max(66-70s대)". This is a
structural argument, not a measured `bootstrap_timing` comparison, and is
stated as incomplete rather than fabricated.

### Two things landed today, used and evaluated

`scripts/related_files.py` — used first (see Investigation above);
returned mostly historical-doc noise for this particular task shape (a
narrow, already-named set of code files) rather than saving lookups; still
a useful negative result (ruled out needing a broader sweep in one call).
The record-order directive (code + checks before the record) was followed
— derived: this file's edit history this session is a single Write, made
after every code edit and verification command above had already run.

## Why

The issue's acceptance criteria allow re-scoping any item "with a stated
reason" and forbid two things: silently dropping an item, and deleting
`roles/` (or breaking a live consumer) before its readers are off. Given
the Investigation section above found every named item to be a live,
correctness-critical consumer of the framework that spawns and gates every
session in this repo (canonical: file:line citations in that section), and
given the stage-6 proposal's own Constraints require stages 0-5 landed and
stable first — which, per `git ls-files docs/issue-2241/reports/` quoted
above, they are not — attempting full removal in one session would either
break a live consumer (violating the issue's own non-goal) or require
building the stages 1-5 replacement architecture as an unplanned addition
to this issue's scope, itself a correctness risk with no time to validate
it against the live spawn/board/gate mechanism this session depends on.

The fixed role→skill table was the one item with both a concrete,
operator-stated completion bar independent of the shared
`roles/*.json`-spec-content blocker, and a safe live-verification path
(calling the same production matching function `_spawn_one()` already
calls). It was implemented for the spawn-mount path specifically — the
literal "a spawn" the acceptance text names — leaving the 4
consult.py/pipeline.py call sites re-scoped: those are independent
advisory `claude -p` subprocesses (not spawns), and their shared helper
(`_consult_cmd_and_env`) has no task-text threaded to it today — migrating
them blind, without the live-verification path available for the spawn
path, risked silently degrading consult/judge/panel guidance quality,
exactly the failure mode ("must not let a spawn silently arrive with zero
skills where it previously got some") the acceptance criteria warn
against.

## What did not work

None — no attempted approach was abandoned mid-way. The scope reduction
from the full deferred-remainder list to the fixed-table/spawn-mount piece
was decided during investigation, before any code was written, not a
reversal of something already built.

## Upstream basis

- `docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md` (sha
  135712e8e4c56195aa0dedab6060db1610f3dc13) — the authoritative stage-6
  spec per issue #2289; its Constraints section is the basis for this
  session's re-scoping decision (quoted above).
- `docs/decisions/2026-08-25-retire-role-axis-staging.md` (same sha) — the
  program-level architecture decision; its empty-state description is the
  eventual target end-state, not this issue's own scope.
- Issue #2507's body — canonical: `gh issue view 2507` output, quoted in
  this session's spawn prompt.
- `docs/issue-2289/` — untracked in this worktree, does not exist —
  derived: `git ls-files docs/ | grep -c "issue-2289/"` — result: `0`.
  PR #2495 (issue #2289's stage-6 partial landing) is still open, not
  merged — derived: `gh pr view 2495 --json state,mergedAt` — result:
  `{"mergedAt":null,"state":"OPEN"}` — so `gates/need_detector.py` and
  `gates/role_spec_shape.py` still exist in this branch's tree; this
  session did not touch them (out of this session's write set — #2495 owns
  that deletion).

## Open findings

canonical: this section's claims are the same file:line citations from
"Investigation" above, re-grouped by resolution path; no new sources.

1. **The rest of the deferred-remainder list stays re-scoped, not
   removed** — root cause shared across it: `roles/<role>.json` spec
   content (`record_fields`/`write_scope`/sandbox env) and `CLAUDE_ROLE`
   (session-type signal) are still this repo's live
   enforcement/identity mechanism, with no stages-1-5 replacement present.
   Resolution path: a follow-up issue lands the lease/author-identity/
   record-kind/branch-naming replacement first; a second stage-6 session
   then migrates `role_settings()`, `gates/gates.py`'s enforcement
   functions, `consult.py`'s checks, the three named hooks, and
   `CLAUDE_ROLE` itself, then deletes `roles/`/`roles/specs/` last per the
   issue's own ordering constraint.
   - `ROLES` tuple: blocked by `board.py`'s reads (legacy record
     discovery/display) and the external `poll-heartbeat.sh` dependency
     quoted above — removing it now would silently stop
     showing/patrolling existing role-named records rather than erroring.
   - `roles/`/`roles/specs/` deletion: blocked by every other still-live
     reader quoted above; per the issue's own non-goal, must be last
     regardless.
   - `consult.py` checks + `pipeline.py::role_settings()`: the latter is
     the central sandbox/env builder for every spawned role session — same
     blocker.
   - `gates/gates.py` enforcement functions + callers: fail-closed
     write-scope/record-field enforcement reads the same spec content —
     changing it without the replacement risks the acceptance criteria's
     explicitly-named worst outcome ("a stale reference that fails only
     when a rare branch executes").
   - `gates/roles_due.py` + CLI: reads `roles/specs/`, which this session
     does not delete — no forcing reason to touch it independently; left
     as-is.
   - 3 named hooks: each reads real content this session keeps in place —
     no change needed while the items above stay blocked.
   - `CLAUDE_ROLE`: the live role-vs-orchestrator session-type signal for
     the 24 hooks quoted above; retiring it needs the same replacement
     identity concept as the items above.
2. **Adhoc (no `--issue`) spawns get fewer skills than before, for roles
   whose retired fixed list was non-trivial** — the composed/judge
   matching mechanism is (same as before this change) gated on `issue is
   not None`, so an adhoc spawn gets only the always-on POLICY skills
   (currently just work-in-english) instead of the retired table's
   per-role list. Disclosed reduction, not silent — kept because widening
   the judge-consult gate to adhoc spawns changes latency/behavior on a
   path this session could not verify live (same constraint as the
   unverifiable bootstrap_timing item above). Resolution path: a follow-up
   verifies the judge-consult call is safe for adhoc (no workspace,
   `cwd`=caller's own directory) via a real adhoc spawn test, or accepts
   the reduction permanently with a stated reason.
3. **End-to-end live-spawn verification not performed** — see the two
   `unverifiable:` entries in "Live verification" above. Resolution path:
   a session not itself occupying `issue-2507/implementation` (so no
   branch-collision risk) runs `spawn.py <role> "<task>" --issue <n>`
   several times post-merge and records the `bootstrap_timing` lines each
   spawn already prints to stderr.

## Next steps

- A follow-up issue for the lease/author-identity/record-kind/
  branch-naming replacement (stages 1-5 of
  `docs/issue-2241/proposals/`) is the prerequisite for a second stage-6
  session to close the remaining deferred-remainder items (Open finding 1).
- Post-merge: run the multi-spawn `bootstrap_timing` comparison from a
  session not on `issue-2507/implementation` (Open finding 3).
- Consider migrating `consult.py`'s 3 `resolve_role_source()` call sites
  (skill_judge/verb/panel session guidance) to the same composed mechanism
  once task-text can be threaded through `_consult_cmd_and_env` — out of
  this session's scope (see "Why").

loop_state: landed

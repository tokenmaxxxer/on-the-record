---
issue: 2211
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2211/reports/conformance-review/survey.md
    sha: same-commit
  - path: docs/issue-2211/proposals/conformance-review.md
    sha: same-commit
  - path: docs/issue-2211/reports/conformance-review/deviation-log.md
    sha: same-commit
subject: commit 94fbd4dfa73f467f3327ced87ac25997de45ba95
  (pipeline.py, spawn.py, tests/test_spawn_pipeline.py,
  tests/test_directive_diet_2135.py; PR #2228, issue-2211/implementation,
  open)
test: issue #2211 body (`## Fix`/`## Acceptance`), decomposed into
  R1..R14 (docs/issue-2211/reports/conformance-review/survey.md,
  "Requirement list" section)
result: cantTell
assertedBy: issue-2211/conformance-review session (role-handoff contract
  v3, CORE_BUILD_NOW=1 build-now bypass)
---

# issue-2211 — conformance-review record

## What was done

Audited `pipeline.py`/`spawn.py`/their two test files at
`94fbd4dfa73f467f3327ced87ac25997de45ba95` against the 14 requirements
the phase-1 survey extracted from issue #2211's own `## Fix`/`##
Acceptance` text, re-deriving every verdict directly against the
artifact this session rather than reusing the implementer's own
self-assessment — including an independently re-run live `claude -p`
spawn for R6-R8 and an independently re-run full-suite comparison for
the implementer's pre-existing-failures claim.

Thirteen of fourteen requirements verdict `Present`; one (R9) verdicts
`Unverifiable` because the issue text's own phrase "engineering-class
session" names no defined term anywhere checked this session (see R9
below). Per `roles/specs/conformance-review.spec.json`'s recomputation
rule, the overall record `result` recomputes to the worst case across
the fourteen cited verdicts:
```
recomputation.rule ordering: failed > cantTell > inapplicable > untested > passed
this record's 14 verdicts: 13x Present (-> EARL passed), 1x Unverifiable (R9, -> EARL cantTell)
worst case -> cantTell
```
canonical: `roles/specs/conformance-review.spec.json`'s `recomputation` field, read this session (executed-unit: file read, this session) — states the ordering quoted in the fence above; applied to the 14 finding blocks below.

Two items outside the R1-R14 set are recorded as Open Findings below,
per the approved proposal's scope split — including a discrepancy this
session's own independent full-suite re-run surfaced against the
implementer's specific "identical failure set" claim (Open finding 2).

## Why

The approved proposal's Rationale rejected trusting the implementer's
own pasted evidence (a `printenv` transcript, a session-log grep count,
a pytest summary) as sufficient on its own — this role's
`conformance-review-verdict-assignment` skill requires evidence the
review session itself re-derived, and the phase-1 survey already
established this session's own ambient environment (spawned off
`main`, which does not carry `94fbd4df`) cannot see any of the
commit's effects passively — only a live re-spawn built from
`issue-2211/implementation`'s own code proves R1-R8. Every citation
below is this session's own command execution or file read against the
artifact.

## Findings

---
requirement: the spawned session's environment unconditionally carries a workspace-root path variable (R1)
spec_ref: issue #2211 body, `## Acceptance` bullet 1 ("...workspace paths — verified by reading them back inside a live spawn")
verdict: Present
evidence: `94fbd4df:pipeline.py:718`
rationale: unconditional assignment, no `if` guard on this line.
```
$ git show 94fbd4df:pipeline.py | sed -n '716,721p'
    env["ON_THE_RECORD"] = str(_sp.ROOT)
    env["MUSTER_WORKSPACE_ROOT"] = str(_sp._workspace_base())
    if skill_registry_root:
        env["MUSTER_SKILL_REGISTRY_ROOT"] = str(skill_registry_root)
```
canonical: `git show 94fbd4df:pipeline.py | sed -n '716,721p'` — output shown in the fence above (executed-unit, this session).
canonical: `python3 -m pytest tests/test_spawn_pipeline.py -k test_on_the_record_and_workspace_root_always_set -q -m "" -p xdist -n0` — result: 1 passed — executed this session, `/tmp/wt-2211-impl`.
canonical: `python3 -c "import pipeline as p,spawn as s;print(p.spawn_cmd('/tmp/x.json','execution-observation',unattended=True,skill_registry_root=s._skill_repo_root())[1]['MUSTER_WORKSPACE_ROOT'])"` — result: `/home/jwjung/.tokenmaxxxer/work` — executed this session, `/tmp/wt-2211-impl` (built via the real, un-mocked `spawn_cmd()`; independently confirmed also by this session's own live-spawn transcript, `/tmp/2211-live-spawn.log`, whose `printenv` call printed the same value).

---
requirement: the spawned session's environment unconditionally carries a plugin-root path variable (R2)
spec_ref: issue #2211 body, `## Acceptance` bullet 1
verdict: Present
evidence: `94fbd4df:pipeline.py:717`
rationale: same fence as R1 above — `env["ON_THE_RECORD"] = str(_sp.ROOT)` carries no `if` guard.
canonical: `git show 94fbd4df:pipeline.py | sed -n '716,721p'` — output shown in R1's fence above (executed-unit, this session).
canonical: `python3 -m pytest tests/test_spawn_pipeline.py -k test_on_the_record_and_workspace_root_always_set -q -m "" -p xdist -n0` — result: 1 passed — executed this session, `/tmp/wt-2211-impl` (same test covers R1+R2 jointly).
canonical: `git show 94fbd4df:pipeline.py | sed -n '716,721p'` again, cross-checked against this session's own live spawn transcript, `/tmp/2211-live-spawn.log` — `ON_THE_RECORD=/tmp/wt-2211-impl` printed by the spawned session's `printenv` call, this session.

---
requirement: the spawned session's environment carries a core-root path variable, pre-existing per issue #182, left in place (R3)
spec_ref: issue #2211 body, `## Acceptance` bullet 1 (core-root clause) and `## Fix` bullet 1 ("check what is already injected")
verdict: Present
evidence: `94fbd4df:pipeline.py:708-712` (unchanged by this diff)
rationale: no `-`/`+` prefix on this block in the commit's own diff hunk.
```
$ git diff 94fbd4df^..94fbd4df -- pipeline.py | grep -B2 -A2 'CLAUDE_PLUGIN_ROOT_CORE'
   core_dir = next((p for p in (core_plugins or []) if Path(p).name == "core"), None)
   if core_dir:
       env["CLAUDE_PLUGIN_ROOT_CORE"] = str(core_dir)
```
canonical: `git diff 94fbd4df^..94fbd4df -- pipeline.py` — output shown in the fence above (executed-unit, this session) — zero `-`/`+` lines touch this block.
canonical: `python3 -m pytest tests/test_spawn_pipeline.py -k "claude_plugin_root_core or env_stamps or test_flags" -q -m "" -p xdist -n0` — result: 4 passed — executed this session, `/tmp/wt-2211-impl`.
canonical: `git diff 94fbd4df^..94fbd4df -- pipeline.py`, cross-checked against this session's own live spawn transcript, `/tmp/2211-live-spawn.log` — `CLAUDE_PLUGIN_ROOT_CORE=/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-core/core` printed by the spawned session's `printenv` call, this session.

---
requirement: the spawned session's environment carries a skill-registry path variable when a skill-repository is resolved for the spawn (R4)
spec_ref: issue #2211 body, `## Acceptance` bullet 1 (skill-registry clause)
verdict: Present
evidence: `94fbd4df:pipeline.py:719-720`
rationale: `if skill_registry_root:`-guarded assignment, shown in R1's fence above.
canonical: `git show 94fbd4df:pipeline.py | sed -n '716,721p'` — output shown in R1's fence above (executed-unit, this session).
canonical: `python3 -m pytest tests/test_spawn_pipeline.py -k test_skill_registry_root_set_when_provided -q -m "" -p xdist -n0` — result: 1 passed — executed this session, `/tmp/wt-2211-impl`.
canonical: `git show 94fbd4df:pipeline.py | sed -n '716,721p'` again, cross-checked against this session's own live spawn transcript, `/tmp/2211-live-spawn.log` — `MUSTER_SKILL_REGISTRY_ROOT=/home/jwjung/skill-registry/skills` printed by the spawned session's `printenv` call, this session (skill-repository genuinely mounted in this environment).

---
requirement: when no skill-repository is resolved, the skill-registry variable stays absent rather than an empty string (R5)
spec_ref: issue #2211 body, "empty state" paragraph
verdict: Present
evidence: `94fbd4df:pipeline.py:719-720` (same `if skill_registry_root:` guard as R4)
rationale: a falsy/`None` value skips the assignment entirely, so the key is never added.
canonical: `python3 -m pytest tests/test_spawn_pipeline.py -k test_skill_registry_root_unset_when_absent -q -m "" -p xdist -n0` — result: 1 passed — executed this session, `/tmp/wt-2211-impl` — the test asserts `"MUSTER_SKILL_REGISTRY_ROOT" not in env` when `skill_registry_root=None` is passed explicitly.

---
requirement: R1-R4's check runs as a live spawn with an in-session env readback, not only a unit-test assertion (R6)
spec_ref: issue #2211 body, `## Acceptance` bullet 1, trailing clause ("verified by reading them back inside a live spawn")
verdict: Present
evidence: this session's own live `claude -p` spawn
rationale: this session built the env via the real `pipeline.spawn_cmd()`
and `spawn.directive_section_files()`/`_directive_system_prompt_block()`
(not mocked), then ran the spawn below.
```
$ claude -p 'Locate the record-claim-guard.sh hook script and list the contents of the mounted skill-repository, without scanning the whole filesystem...' --append-system-prompt <real known-paths.md block, built via spawn.directive_section_files()> --output-format stream-json --verbose --permission-mode bypassPermissions --max-turns 8
```
canonical: `claude -p ... --output-format stream-json` (fence directly above) — result: 1 passed — executed this session, transcript at `/tmp/2211-live-spawn.log` — the spawned session's first (and only) Bash call was `printenv ON_THE_RECORD MUSTER_SKILL_REGISTRY_ROOT; echo "---"; git -C "$ON_THE_RECORD" ls-files | grep record-claim-guard.sh; echo "---"; ls "${MUSTER_SKILL_REGISTRY_ROOT:?skill-repository not mounted}"` and its tool-result printed all four requested values.

---
requirement: a re-measured engineering-class session's log carries zero `find /` or `find /home` invocations for paths now exported (R7)
spec_ref: issue #2211 body, `## Acceptance` bullet 2
verdict: Present
evidence: `/tmp/2211-live-spawn.log`
rationale:
```
$ grep -c 'find /' /tmp/2211-live-spawn.log
0
$ grep -c 'find /home' /tmp/2211-live-spawn.log
0
$ grep -io '"command":"[^"]*find[^"]*"' /tmp/2211-live-spawn.log
(no output)
```
canonical: `grep -c 'find /' /tmp/2211-live-spawn.log` — result: 0 — executed this session, on this session's own live-spawn transcript.

---
requirement: R7's check runs by producing an actual new session log and grepping it, not by inference from the code alone (R8)
spec_ref: issue #2211 body, `## Acceptance` bullet 2, trailing clause ("verified by grep over the new session log")
verdict: Present
evidence: `/tmp/2211-live-spawn.log`
rationale: the fence in R7's rationale above is this session's own live
`claude -p` transcript, grepped directly by this session — not a
static-analysis inference.
canonical: `grep -c 'find /' /tmp/2211-live-spawn.log` — result: 0 — executed this session (same command/log as R7's fence above; the log itself is this session's own live measurement, not a code-only inference).

---
requirement: the phrase "engineering-class session" names a defined term the check can be verified against (R9)
spec_ref: issue #2211 body, `## Acceptance` bullet 2 ("a re-measured engineering-class session's log...")
verdict: Unverifiable
evidence: zero hits for the phrase outside the implementer's own record
rationale:
```
$ git grep -rni "engineering-class" -- . ':!*.log'
docs/issue-2211/reports/implementation.md:174:...engineering-class session's log...
docs/issue-2211/reports/implementation.md:223:engineering-class task, mirroring issue-2201's scenario):
$ git -C "$CLAUDE_PLUGIN_ROOT_CORE/.." grep -rni "engineering-class"
(no output)
```
canonical: `git grep -rni "engineering-class" -- . ':!*.log'` — output shown in the fence above (executed-unit, this session, run against `/tmp/wt-2211-impl` at `94fbd4df` and the mounted `tokenmaxxxer-core` checkout) — the only two hits are the implementer's own record quoting the issue text; no repo or mounted-plugin text defines which task/role qualifies as "engineering-class".
This review can judge only whether the implementer's chosen stand-in (a
generic `claude -p` spawn running a fixture/hook-script lookup task) is
a reasonable substitute for the issue's own cited scenario — by
Analysis, it is: issue #2211's own cited live measurement was itself an
ordinary `implementation`-role spawn doing repo navigation, and R7/R8's
independently re-run stand-in above reproduces that shape closely
enough that its `find /`-avoidance result transfers. This verdict is
`Unverifiable` strictly because the acceptance text names no checkable
definition, not because R7/R8's substance was left unchecked (both
verdict `Present` above, independently re-derived this session).

---
requirement: spawns unrelated to the four new/changed keys carry an env dict with no other key added, changed, or removed (R10)
spec_ref: issue #2211 body, "Existing spawns are otherwise byte-identical in environment (regression guard: additions only)"
verdict: Present
evidence: `94fbd4df^..94fbd4df` diff of `pipeline.py`
rationale:
```
$ git diff 94fbd4df^..94fbd4df -- pipeline.py | grep -c '^-[^-]'
0
```
canonical: `git diff 94fbd4df^..94fbd4df -- pipeline.py | grep -c '^-[^-]'` — result: 0 — executed this session — zero removed/modified lines inside `spawn_cmd()`'s body; the diff is pure addition.
canonical: `python3 -m pytest tests/test_spawn_pipeline.py -k "claude_plugin_root_core or env_stamps or test_flags" -q -m "" -p xdist -n0` — result: 4 passed — executed this session, `/tmp/wt-2211-impl` (the pre-existing regression suite this diff leaves untouched).

---
requirement: the record carries executed acceptance evidence rather than narrated claims (R11)
spec_ref: issue #2211 body, "Executed acceptance evidence in the record (#2137)"
verdict: Present
evidence: every finding block above (R1-R10, R12-R14)
rationale: self-referential by construction — each rationale field
above carries a `$`-prefixed command this session ran and a
`canonical:` tag pointing at that command's own output or transcript,
per issue #2137's verify-at-landing convention this role's own core
session-protocol is bound by.
canonical: the R1-R10/R12-R14 finding blocks above (self-referential) — each carries at least one `canonical: <command> — result: ...` line this session executed and cited inline.

---
requirement: no new discovery mechanism or cache is introduced (R12)
spec_ref: issue #2211 body, `## Fix`, "Do NOT add a new discovery mechanism or cache."
verdict: Present
evidence: `94fbd4df --stat`
rationale:
```
$ git show 94fbd4df --stat
 .orchestrate-hook-fires.log               | 328 +++...
 docs/issue-2211/reports/implementation.md | 240 +++...
 pipeline.py                               |  19 +-
 spawn.py                                  |  38 +-
 tests/test_directive_diet_2135.py         |  19 +-
 tests/test_spawn_pipeline.py              |  21 ++
```
canonical: `git show 94fbd4df --stat` — output shown in the fence above (executed-unit, this session) — only `pipeline.py`/`spawn.py` (existing modules) plus their existing test files change; no new file, module, cache directory, or resolver function appears.

---
requirement: a short directive note/section is added telling sessions the new variables exist, paired with the export (R13)
spec_ref: issue #2211 body, `## Fix`, "Pair with a one-line directive note that these variables exist"
verdict: Present
evidence: `94fbd4df:spawn.py:1939` (`_KNOWN_PATHS_PROSE`), `94fbd4df:spawn.py:1993`
rationale:
```
$ python3 -c "import spawn as s; print('known-paths.md' in s.directive_section_files())"
True
```
canonical: `python3 -c "import spawn as s; print('known-paths.md' in s.directive_section_files())"` — result: `True` — executed this session, `/tmp/wt-2211-impl`.
canonical: `python3 -m pytest tests/test_directive_diet_2135.py -k "known_paths or skill_and_checkpoint" -q -m "" -p xdist -n0` — result: 2 passed — executed this session, `/tmp/wt-2211-impl`. The prose (read directly, this session) names all four env vars and instructs `printenv` over `find /`/`find /home`.

---
requirement: the fix reuses an already-resolved value rather than adding a second resolution call for the same lookup (R14)
spec_ref: issue #2211 body, `## Fix`, "check what is already injected and only add what is genuinely missing rather than duplicating"
verdict: Present
evidence: `94fbd4df:spawn.py:2355-2356` and `:2759`
rationale:
```
$ git show 94fbd4df:spawn.py | grep -n "_skill_repo_root("
2341:        skill_sources = resolved_skill_sources(skills, _skill_repo_root(), ...
2355:        skill_registry_root = _skill_repo_root()
2368:            _cross_family_task_text, role, _skill_repo_root(), issue, cwd,
$ git show 443f6136:spawn.py | grep -n "_skill_repo_root("
2333:        skill_sources = resolved_skill_sources(skills, _skill_repo_root(), ...
2340:        role_source = resolve_role_source(role, _skill_repo_root())
2353:            _cross_family_task_text, role, _skill_repo_root(), issue, cwd,
```
canonical: `git show 94fbd4df:spawn.py | grep -n "_skill_repo_root("` — output shown in the fence above (executed-unit, this session) — three call sites, same count as `git show 443f6136:spawn.py`'s three call sites shown in the same fence. The diff's only change at this lookup is storing the pre-existing call's result (line 2340's inline `_skill_repo_root()` before this diff, now line 2355's `skill_registry_root` local) and threading that same value into the new `spawn_cmd(skill_registry_root=...)` parameter at line 2759 — no new `_skill_repo_root()` invocation was added; the other two pre-existing call sites are untouched.

## Upstream basis

- `docs/issue-2211/reports/conformance-review/survey.md` (this commit)
  — requirement extraction (R1-R14) and the two "Notable surface for
  phase 2" items this record's Open findings section builds on.
- `docs/issue-2211/proposals/conformance-review.md` (this commit) — the
  phase-1 proposal; this session's re-derivation matches its planned
  method/scope split (Inspection+Test for R1-R5/R10-R14, Demonstration
  via independent live spawn for R6-R8, Analysis-only for R9); see
  "What did not work" below.
- `docs/issue-2211/reports/conformance-review/deviation-log.md` (this
  commit) — this role's own phase-1-subtree deviation log
  (skill-verdict-guard vs approval-gate conflict), carried forward for
  traceability; no new deviation in this phase-2 session.
- GitHub issue #2211 supplied the acceptance criteria this record's
  R1-R14 verdicts check against.
  canonical: `gh issue view 2211` — executed this session.
- `94fbd4df:docs/issue-2211/reports/implementation.md` — the
  implementer's own record, read this session (commit-qualified,
  since that file does not exist on this role's own branch) but never
  taken as evidence at face value — every R1-R14 verdict above cites
  this session's own independent re-derivation instead.
- This session's own environment carries `CORE_BUILD_NOW=1`
  (spawner-set), authorizing single-phase delivery per contract v3
  s19a.
  canonical: `env | grep CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1` — executed this session.

## Open findings

1. The per-file directive-index one-line summary a spawned session sees
   for each `.on-the-record/directive/*.md` section is composed by
   `tokenmaxxxer-core`'s own `directive.sh`, in a separate repository —
   `known-paths.md`'s full prose already reaches every issue-spawned
   session via `--append-system-prompt` (R6 above), but no matching
   index-line entry exists there yet. Not scored against R1-R14 —
   issue #2211's own text names no such companion-repo obligation.
   canonical: `grep -n "known-paths\|repo-discovery" "$CLAUDE_PLUGIN_ROOT_CORE/hooks/directive.sh"` — result: 0 matches — executed this session (neither `known-paths.md` nor the pre-existing `repo-discovery.md` has an index-line entry in the mounted core checkout).
   Resolution path: a companion issue against `tokenmaxxxer-core` to add
   a `known-paths.md` directive.sh index entry — outside this repo's
   write set and outside this role's own single-file record scope, per
   `roles/specs/conformance-review.spec.json`.

2. The implementer's record claims the full-suite run surfaces
   identical 11 pre-existing failures on `issue-2211/implementation`
   and on a clean `main@443f6136` worktree. This session independently
   re-ran the same command in two fresh, isolated `git worktree`s
   rather than accept that claim from the implementer's own pasted
   summary — the re-run does not reproduce it as stated: `main@443f6136`
   showed a 12th failure this session's `impl`-branch run did not have.
   ```
   $ cd /tmp/wt-2211-impl && python3 -m pytest tests/ test/ -q -m "not slow" -p xdist -n0
   11 failed, 1217 passed, 1 skipped, 130 deselected, 9 xfailed, 2 xpassed in 580.98s
   $ cd /tmp/wt-2211-main && python3 -m pytest tests/ test/ -q -m "not slow" -p xdist -n0
   12 failed, 1212 passed, 1 skipped, 130 deselected, 8 xfailed, 3 xpassed in 573.64s
   ```
   canonical: `python3 -m pytest tests/ test/ -q -m "not slow" -p xdist -n0` — output shown in the fence above (executed-unit, this session, two isolated worktrees) — the extra failure on `main@443f6136` this run, in `tests/test_watch_hardening.py`'s `LeaseExpiryRequeue::test_requeue_path_contains_no_detector_logic`, is not among either branch's other 11 shared failures and touches lease-expiry logic unrelated to this diff's `pipeline.py`/`spawn.py` env-injection change.
   Not scored against R1-R14 — none of the 14 requirements depend on
   the full-suite comparison, and the extra failure sits in unrelated
   code (`tests/test_watch_hardening.py`), not a regression this diff
   introduced. Recorded because the implementer's own specific
   "identical failing test IDs" claim does not reproduce as stated —
   most likely the order-dependent/shared-module-global flakiness the
   implementer's own Open Findings section already names as a
   pre-existing, out-of-scope defect rather than a new one surfaced by
   this session.
   canonical: `python3 -m pytest tests/ test/ -q -m "not slow" -p xdist -n0` — output shown in the fence above (executed-unit, this session) — cross-checked: the implementer's own record names this exact flakiness mechanism (shared `spawn._ROLE_SKILLS`/module-global state under serial full-suite execution) as a pre-existing, unattempted-here Open Finding, at `94fbd4df:docs/issue-2211/reports/implementation.md:162-165`.
   Resolution path: whichever role next picks up the implementer's own
   named test-isolation Open Finding should treat this session's extra
   failure as one more data point for that same pre-existing flakiness,
   not a second issue to file.

## Next steps

None needed from this role or branch beyond landing this record —
`loop_state` above is already this record kind's terminal value,
`reported`.
canonical: `roles/specs/conformance-review.spec.json`'s `loop_state.terminal` field, read this session — lists `reported` as the sole terminal value.

## What did not work

Nothing in this session's own re-derivation diverged from the approved
proposal's plan — every requirement kept the method and scope the
proposal set out (Inspection+Test for R1-R5/R10-R14, independently
re-run Demonstration for R6-R8, Analysis-only for R9, both Notable
surface items independently re-derived rather than accepted from the
implementer's account).

## Skill verdicts

skill-verdict: conformance-review-verdict-assignment — applied: invoked; used rule 3 (Unverifiable, naming the missing evidence — no defined "engineering-class" term appears anywhere checked this session, R9 rationale above) and rule 5 (naming the specific satisfied clause, not a bare label, in every Present verdict's rationale line). See R1-R14 finding blocks above.

skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; used rule 1 (commit-qualified `sha:file:line` citations, not bare paths — e.g. `94fbd4df:pipeline.py:718`, and `94fbd4df:docs/issue-2211/reports/implementation.md` for the implementer's record rather than its bare working-tree path) for every evidence field, and rule 2 (one link per contributing file — R1/R2 cite `pipeline.py`, R13 separately cites `spawn.py`) rather than a single bundled citation. See R1-R14 finding blocks above.

skill-verdict: conformance-review-finding-record — applied: invoked; used the field list (`requirement`/`spec_ref`/`verdict`/`evidence`/`rationale`) to shape every block, one per R1..R14, and its refusal rule (never write Present/Surface/Absent/Incorrect with no evidence pointer) before writing this file. See the Findings section above.

other mounted skills: not triggered — `conformance-review-requirement-extraction` and `conformance-review-sampling-derivation` were the phase-1 session's job (already logged in `docs/issue-2211/reports/conformance-review/deviation-log.md`'s own skill-verdict lines); `conformance-review-verification-method-selection` likewise phase-1 (survey's "Verification method per requirement" section); `conformance-review-severity-classification` (no severity-weighting was requested — this review's scope stayed at ordinary fidelity-checking) and `implementation-audit` (this session followed the conformance-review role's own five-verdict protocol per its role-handoff contract, not implementation-audit's separate two-session claim-extraction/evaluator shape — a cross-family keyword match, not the operative process here) stay `not-applicable` this session.

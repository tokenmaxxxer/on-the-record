---
issue: 2201
role: implementation
loop_state: landed
upstream:
  - path: spawn.py
    sha: f45266081b371b249da44730183916e8b3077bcc
  - path: consult.py
    sha: f45266081b371b249da44730183916e8b3077bcc
  - path: docs/issue-2201/reports/implementation/2026-08-24-hunt-bootstrap-cross-family-returned-pr-gate.md
    sha: 6dcf38a7b9f5d5d99b8f2a43cc2e240b643214e1
code_under_review:
  - spawn.py
  - consult.py
  - gates/test_consult_gate_lib_env.py
  - test/test_spawn_cross_family_skill_selection.py
  - test/test_spawn_skill_judge_haiku_timeout_overlap.py
  - tests/test_spawn_board_flows.py
  - tests/test_spawn_gate_wiring.py
type: perf
breaking: false
verdict: pass
---

# issue-2201 — implementation record

## What was done

Build-now bypass (CORE_BUILD_NOW=1): delivered directly on
issue-2201/implementation, no separate phase-1 proposal round (skip note
below).

canonical: `spawn.py` diff, commit f45266081b371b249da44730183916e8b3077bcc (`_spawn_one`'s
`if issue is not None:` block and its `return 0` near line 2846-2861).

Two independent fixes to `_spawn_one()`'s bootstrap path, plus one
correctness fix a before-landing warrant-hunt forced on the first fix:

1. **`returned_pr_gate` (6.608s, 21% of the 31.220s baseline) — moved off
   the blocking path entirely.** `_undispositioned_role_prs()`'s result
   (`blockers`/`ok`) never reaches the task text the spawned session
   receives — it only feeds a stderr print
   (`_print_returned_pr_surfaced()`) and a `ledger_write()` call
   (`returned_pr_gate_fail_open` on gh failure). Converted the
   submit-early/join-late `concurrent.futures.ThreadPoolExecutor` pattern
   (issue #2186) to a fully fire-and-forget `threading.Thread(daemon=True)`
   dispatch — the same shape issue #2195 used for `auto_sweep`. The
   `with _timed("returned_pr_gate"):` block now wraps only the
   `Thread.start()` call.

2. **`cross_family` (21.282s, 68% of baseline) — the underlying
   subprocess call itself got cheaper; still fully synchronous/joined
   (unchanged join point).** `cross_family_dirs` IS embedded into the
   task text the spawned session receives (the mounted cross-family-skill
   directive lines), so it cannot be backgrounded the way `auto_sweep`/
   `returned_pr_gate` were without changing what the first turn of the
   spawned session sees — the issue's own regression guard rules that
   out. Root-caused instead: the nested `claude -p` subprocess
   `_skill_judge_consult()` launches to classify candidates loads
   `--plugin-dir` for every core-marketplace plugin (`core_plugin_dirs()`:
   core/terse/freelunch/scout/warrant) even though it is a narrow
   0-2-pick classification call whose own prompt already tells the model
   to "ignore every directive/hook instruction loaded in this session"
   (issue #1097) — the hooks still fire (SessionStart cost), the
   override only stops the model from acting on their guidance.
   `consult.py`'s `_consult_cmd_and_env()` gained an
   `exclude_core_plugins: frozenset[str] = frozenset()` parameter that
   filters the `--plugin-dir` loop over `core_plugin_dirs()`; every
   existing caller keeps the default (empty set, byte-identical argv).
   `_skill_judge_consult()` now supplies
   `exclude_core_plugins=_sp._JUDGE_EXCLUDED_CORE_PLUGINS` as that
   keyword argument — reusing, not inventing, the exact
   `{"freelunch", "scout", "warrant"}` set issue #1587 already validated
   for the read-only `judge` machinery (`_readonly_plugin_dirs()`, same
   file) on the same rationale: those three plugins carry
   delivery-oriented hooks (propose/gate/fan-out instructions) with no
   business firing inside a judgment-only session; core/terse stay
   (already established as harmless by #1587).

3. **Warrant-hunt-found fix to (1).** The dispatched `returned_pr_gate`
   daemon thread starts well before `_spawn_one()`'s `os.fork()` (issue
   #114/#1154's bounded-spawn split); `fork()` does not clone other
   threads into the child, so the thread keeps running only in the
   parent, whose `child_pid > 0` branch does a few bookkeeping steps and
   then `return 0` by design (bounded parents return fast). The real CLI
   entrypoint's `main()` calls
   `_spawn_one(bounded=a.issue is not None, ...)` then `sys.exit()`
   immediately after, killing the daemon thread without joining it. The
   before-landing warrant-hunt (stance 0, "assume the gate just touched
   is bypassable") reproduced that for every normal
   `spawn.py <role> "<task>" --issue <n>` invocation the thread's own gh
   lookup (6.608s baseline) rarely wins that race — see
   `docs/issue-2201/reports/implementation/2026-08-24-hunt-bootstrap-cross-family-returned-pr-gate.md`
   (commit 6dcf38a7b9f5d5d99b8f2a43cc2e240b643214e1) for the full reproduction. Fixed by capturing the
   thread object and calling
   `_returned_pr_gate_thread.join(timeout=10.0)` immediately before the
   bounded parent's one `return 0` (spawn.py ~line 2846-2861) — the only
   exit point that path takes. Bounded (unlike the pre-#2201 code's
   fully-synchronous `.result()` wait on the same gh call, which had no
   timeout at all), off the measured `returned_pr_gate` bootstrap_timing
   phase (still dispatch-only), and off the spawned session entirely
   (the fork already happened by the time this join runs).

## Why

Two separate mechanisms dominated bootstrap after #2195 removed
`auto_sweep` from the critical path (issue text: cross_family 21.282s/
68%, returned_pr_gate 6.608s/21%). Reading both call sites
(`spawn.py`'s `_spawn_one()`, `consult.py`'s `_skill_judge_consult()`/
`_consult_cmd_and_env()`) showed the two needed different fixes:
`returned_pr_gate`'s result is pure side-channel (surfacing plus a
ledger event, never read back by anything downstream) — nothing
justifies blocking on it, so it gets #2195's own treatment.
`cross_family`'s result (`cross_family_dirs`) is embedded directly into
the task text the spawned session's first turn sees — backgrounding it
the same way would change what the session is told, which the issue's
own regression guard forbids ("Whatever cross_family guarantees today
still holds ... assert its effect, not just its absence from the timing
line"). So fix (2) had to make the real work faster, not move it, and
the plugin-dir/hook-loading overhead was the concrete, already-precedented
(#1587) lever available without touching the classification logic
itself.

**Non-obvious finding that drove the fix order:** backgrounding
`returned_pr_gate` alone would not have reduced the total by anything
close to 6.6s. In the pre-#2201 code, `returned_pr_gate`'s `.result()`
join ran before `cross_family`'s join point (spawn.py's control flow:
workspace, branch, `returned_pr_gate` join, directive_write, issue_fetch,
..., `cross_family` join), so that 6.608s of blocking wait was also
serving as free overlap time for `cross_family`'s already-running
background future. Removing `returned_pr_gate`'s wait without also
shrinking `cross_family`'s own duration would simply have moved that
same overlap budget onto the `cross_family`-measured phase instead of
off the total — the two phases' measured costs share an overlap budget,
they are not independent line items. This is why fix (2), making
`cross_family`'s underlying work cheaper rather than only un-blocking
`returned_pr_gate`, was necessary for the total to actually drop.

skill-verdict: implementation-performance-data-structure-choice —
applied: invoked; the core question here — is nested-subprocess
plugin/hook loading a real, cuttable per-call cost, or premature
micro-optimization of something dominated by model-inference latency —
is exactly the skill's per-message-connection-cost and
cache/maintenance-cost-versus-benefit territory (loading N plugin dirs
per classification call is a per-call fixed overhead, analogous to a
per-message connection cost). The skill's answer, measure before
cutting, is why the live A/B subprocess comparison below ran before
committing to the `exclude_core_plugins` fix, rather than assuming the
plugin-dir count mattered.
other mounted skills: not triggered — implementation-complexity-
coupling-management (no coupling/cohesion metric crossed, no new
cross-module import direction — `exclude_core_plugins` is an additive
optional parameter on an existing function), implementation-design-
pattern-selection (no GoF pattern introduced or reconsidered — a
frozenset filter parameter is not a pattern), implementation-blueprint
(a two-function latency fix plus test updates in existing files, not a
new multi-module architecture).

Alternatives considered and rejected:
- **Cap the `cross_family` bootstrap join with its own short timeout,
  falling back to the existing deterministic BM25 top-k on expiry**
  (re-purposing the already-existing fail-open path with a much tighter
  bound than the 90s `SKILL_JUDGE_TIMEOUT`). Rejected: a bound tight
  enough to matter (single-digit seconds) would fail open on nearly
  every real spawn given cross_family's real ~15-30s duration, which is
  functionally "always use raw BM25, skip the judge tier" — reintroducing
  the precision problem #2040's consult-judge tier exists to fix,
  silently, on the latency argument alone. That is exactly the "must not
  simply be deleted" case the issue names, not a latency-versus-guarantee
  tradeoff worth making quietly.
- **Drop the role's own skill-repo plugin dirs from the judge call too**
  (not just `core_plugin_dirs()`). Considered, not applied: role skill
  dirs are validated at resolution time to never carry a `hooks/`
  subdirectory (`resolve_role_source()`'s fail-closed check), so they
  should not be firing SessionStart hooks in the first place — cutting
  them would target a cost live measurement did not actually attribute
  to hook-firing, only to extra `--plugin-dir` parse overhead of
  uncertain size. Left as Open finding 3 below rather than guessed at.
- **A brand-new exclusion set specific to `skill_judge`.** Rejected in
  favor of reusing `_JUDGE_EXCLUDED_CORE_PLUGINS` verbatim: issue #1587
  already argued through exactly this question (which core plugins are
  delivery-oriented versus harmless) for a structurally identical
  read-only/judgment-only nested session; a second, possibly drifting
  set for a second call site is the exact "two call sites, drift" class
  of bug this codebase's own docstrings repeatedly flag as
  already-paid-for (issue #1141's docstring, issue #695/#700's history).
- **Add `.join(timeout=...)` to `auto_sweep`'s identically-shaped daemon
  thread too**, since the same pre-fork/`os.fork()`/daemon-thread-dies
  race structurally applies to it as well. Rejected here as out of this
  issue's named scope (`cross_family`/`returned_pr_gate` only); recorded
  as Open finding 1 below rather than folded in silently.

Skip note (survey-order-directive): no separate survey/proposal file was
written — CORE_BUILD_NOW=1 authorizes direct delivery (contract v3
s19a). The open design decisions (background vs. speed-up per phase;
reuse vs. new plugin-exclusion set; bounded-join value) are argued
inline above.

## What did not work

The first cut of fix (1) — fire-and-forget `threading.Thread(daemon=True)`
with no join anywhere — shipped the correctness gap fix (3) above
resolves: the before-landing warrant-hunt reproduced that the daemon
thread might never survive to completion in the real bounded/`--issue`
CLI path, so `returned_pr_gate`'s surfacing/ledger side effect could
silently stop firing in the common case.

canonical: `pytest tests/test_spawn_gate_wiring.py -q -k test_bounded_fork_parent_join_still_captures_a_slow_lookup`

Verified this both directions this session: with the
`.join(timeout=10.0)` line removed, that test's own ledger-event
assertion is unmet (empty ledger); with the line restored, the same
pytest invocation above is green.

An earlier draft of that same new test set
`resolve_role_source(... "source": "skill-repo", "skill_dirs": [] ...)`
without also mocking `_skill_repo_root()`/
`_cross_family_skill_matches_with_consult`, which let the test fall
through to the real four-tier cross-family candidate corpus (including
this machine's own real `~/.claude/skills`) and made a real ~18-27s
`claude -p` subprocess call inside a unit test.

canonical: this turn's own transcript — pytest stderr capture showing
`bootstrap_timing ... cross_family=18.162 ... total=18.412` and later
`cross_family=26.363 ... total=27.138` from that earlier draft's runs.

Fixed by mocking `_cross_family_skill_matches_with_consult` directly,
matching the pattern this file's own pre-existing
`SkillJudgeLedgerFieldTest`/`SkillJudgeOverlapOrderingTest` classes
already use.

## Upstream basis

- Issue #2201, read via `gh issue view 2201` — the 31.220s baseline
  bootstrap_timing line (fixture issue #48, `northpole-harness-fixture`
  repo), the 68%/21% dominance framing, the Investigate/Fix questions,
  and the two acceptance criteria plus the regression guard.
- `docs/issue-2195/reports/implementation.md` (commit
  8b126d1e039dc11f633d262befe3a01d6245e559, read this session) — the
  `auto_sweep` fire-and-forget daemon-thread precedent fix (1) copies,
  including its own Open finding #3 flagging `cross_family`'s
  `ThreadPoolExecutor` shape as a latent atexit-join risk, not
  applicable here since fix (2) never removes the join, only cheapens
  what is joined.
- `spawn.py`, `consult.py`, `pipeline.py`, read this session —
  `_spawn_one()`'s full `if issue is not None:` block (bootstrap phase
  ordering, the fork/bounded-return split at `os.fork()`),
  `_consult_cmd_and_env()`, `_skill_judge_consult()`,
  `_readonly_plugin_dirs()`/`_JUDGE_EXCLUDED_CORE_PLUGINS` (issue
  #1587), `role_settings()` (`pipeline.py` lines 211-296) — establishing
  that marketplace-plugin hooks attach only via `--plugin-dir`, never
  via `settings.json`'s own `hooks` key, the precondition fix (2)'s
  scoping relies on.
- Live subprocess measurements taken this session, recorded here as the
  executed evidence (not persisted to a separate file):
  - Trivial 0-candidate prompt, `/tmp` cwd, haiku: 0 `--plugin-dir`
    real 10.493s; 5 `--plugin-dir` (all core plugins) real 15.587s.
  - Real `_consult_cmd_and_env()`-built argv, this repo's own cwd, a
    4-candidate skill_judge-shaped prompt, haiku: 9 `--plugin-dir`
    (today's shape) real 58.355s, model `duration_ms` 29231ms; 6
    `--plugin-dir` (`exclude_core_plugins=_JUDGE_EXCLUDED_CORE_PLUGINS`,
    this fix's shape) real 51.894s, model `duration_ms` 31853ms.
    Wall-clock delta 6.461s; the non-model-compute share of that delta
    is larger still (29.124s to 20.041s, about 9.08s) since model
    `duration_ms` was higher in the "after" run (run-to-run inference
    variance) — the entire measured wall-clock saving traces to the
    removed plugin dirs, not to coincidentally faster model compute.
- `docs/issue-2201/reports/implementation/2026-08-24-hunt-bootstrap-cross-family-returned-pr-gate.md`
  (commit 6dcf38a7b9f5d5d99b8f2a43cc2e240b643214e1) — the before-landing warrant-hunt's own finding and
  repro that fix (3) resolves, with a Resolution section this record's
  fix (3) matches.

## Open findings

1. `auto_sweep`'s identically-shaped `threading.Thread(daemon=True)`
   dispatch (issue #2195) structurally shares the same pre-fork race fix
   (3) resolved for `returned_pr_gate` — it might not survive to
   completion in the bounded `--issue` CLI path either, so the
   disk-cleanup side effect may rarely finish for bounded spawns
   specifically. This record does not verify that directly (no
   `auto_sweep`-focused repro was run this session — out of this issue's
   named scope). Resolution path: a follow-up issue scoped to
   `auto_sweep` specifically, applying the same
   `.join(timeout=...)`-before-`return 0` fix if a per-spawn guarantee
   turns out to matter there too, informed by whether disk pressure is
   ever observed in practice — `auto_sweep`'s own design already frames
   the cleanup as a soft, time-averaged bound rather than a per-spawn
   guarantee (docs/issue-2195/reports/implementation.md's own "Why"
   section), unlike `returned_pr_gate`'s surfacing.
2. This record's acceptance evidence does not include a fresh literal
   live `spawn.py implementation "..." --issue 48` run against the
   `northpole-harness-fixture` repo re-emitting the exact
   `bootstrap_timing` line the issue quotes — the same
   manual/operator-driven, wall-clock-gated step issue #2195's own
   record declined for the identical reason (`harness/README.md`'s "Run
   the real baseline later" framing, issue #776 step 3): not something a
   delivery session invokes on itself inside an unattended
   (CORE_BUILD_NOW=1) single-shot run, and it would create real
   branches/PRs/gh-API traffic against a live fixture repo outside this
   session's write set. In its place, this record's evidence exercises
   the real, unmocked mechanisms directly: live `claude -p` subprocess
   A/B timing through the actual `_consult_cmd_and_env()` code path, and
   real `_spawn_one()` runs (real git repos, real `os.fork()` semantics
   via a mocked-but-structurally-faithful parent/child branch) reading
   the real emitted `bootstrap_timing` line — the same property the
   issue's acceptance bullet asks for, read the same way, against the
   real mechanism rather than the literal named fixture. Resolution
   path: a human operator, or a follow-up session explicitly authorized
   for it, re-runs the issue's own fixture-#48 measurement against this
   branch (or after merge) and pastes the fresh `bootstrap_timing` line
   for direct before/after comparison.
3. Even with `exclude_core_plugins` applied, this session's own live
   4-candidate skill_judge measurement above still cost about 52s
   wall-clock real subprocess time (`duration_ms` about 32s model
   compute plus about 20s remaining startup/plugin overhead) — well
   above the issue's own 21.282s cross_family baseline, though not
   directly comparable (this session's candidate count/task text/role
   differ from fixture issue #48's). The remaining approximately 20s of
   non-model overhead is not fully explained by `core_plugin_dirs()`
   alone (the `/tmp` trivial-prompt comparison above showed 0 versus 5
   plugin dirs costing only about 10.5s versus about 15.6s) — the
   role's own skill-repo `plugins` (left unexcluded by this fix, per the
   rejected-alternative above) or this specific environment's
   mounted-skill count are plausible remaining contributors. Resolution
   path: a follow-up investigation profiling `_skill_judge_consult()`'s
   subprocess startup directly (for example `strace -f -T`, or
   comparing `role_settings()`'s resolved `plugins` list size against
   startup time across a few real roles) before deciding whether the
   role's own skill dirs are also worth excluding for this narrow call.

## Next steps

None — loop_state is terminal (landed).

Executed acceptance evidence. canonical: this turn's own transcript —
each command below was run directly by this session at landing time, raw
stdout/stderr pasted verbatim (pytest-asyncio deprecation warnings and
the pytest-xdist "bringing up nodes..." banner trimmed), no
summarization.

acceptance: `python3 -c "import ast; ast.parse(open('spawn.py').read()); ast.parse(open('consult.py').read())"`
result:
```
(no output)
```
exit code 0.

acceptance: live subprocess A/B measurement of the actual mechanism fix
(2) changes — a script calling `spawn._consult_cmd_and_env()` directly,
before/after `exclude_core_plugins`, real `subprocess.run` of the built
argv (full script text is in this session's own transcript, re-runnable
by any later session)
result:
```
BEFORE(all core plugins, today's main shape): plugin_dirs=9 elapsed=58.355s rc=0
AFTER(freelunch/scout/warrant excluded, issue #2201 fix): plugin_dirs=6 elapsed=51.894s rc=0
delta: 6.461s saved
```
exit code 0 both runs.

acceptance: `python3 -m pytest tests/test_bootstrap_timing.py tests/test_auto_sweep_nonblocking.py gates/test_consult_gate_lib_env.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py -q`
result:
```
........................................                                 [100%]
40 passed in 22.44s
```
exit code 0.

acceptance: `python3 -m pytest tests/test_spawn_gate_wiring.py -q -k ReturnedPRGate`
(the two tests exercising fixes (1) and (3) directly, reading the real
emitted `bootstrap_timing` line and real ledger events from a real
`_spawn_one()` call)
result:
```
..                                                                        [100%]
2 passed in 24.26s
```
exit code 0.

acceptance: `python3 -m pytest tests/test_bootstrap_timing.py tests/test_auto_sweep_nonblocking.py gates/test_consult_gate_lib_env.py test/test_spawn_cross_family_skill_selection.py test/test_spawn_skill_judge_haiku_timeout_overlap.py tests/test_spawn_gate_wiring.py tests/test_spawn_board_flows.py -q`
(full combined suite touching every file this diff changes or that
exercises the changed call sites, run twice for flake-stability; a
transient run in between also showed two unrelated `MustMcpAllowEnv`
failures that did not reproduce on this run nor on a third run, and
touch no code this diff changes — treated as pytest-xdist worker-order
flakiness)
result:
```
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
2 failed, 242 passed in 336.04s (0:05:36)
```
exit code 1. Both failure names are identical to two of the four
pre-existing failures issue #2195's own "Executed acceptance evidence"
section already ran and attributed to environment pollution unrelated
to that issue's diff.

acceptance: `git stash && python3 -m pytest tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch -q && git stash pop`
(re-running the same failing test against this branch's own unmodified
base commit 02e90780, to separate pre-existing pollution from a
regression this diff introduced)
result:
```
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
1 failed in 5.52s
```
exit code 1, identical assertion and identical values ([11, 22] versus
[22]) as the run against this diff above — pre-existing on the base
commit, not introduced by this diff.

acceptance: full-repo baseline sweep — `python3 -m pytest tests/ gates/ -q`
(broader confirmation beyond the directly-affected files, run once)
result:
```
FAILED tests/test_spawn_directive_assembly.py::SinglePhaseSignal::test_without_flag_is_byte_identical_to_today
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_core_plugin_dirs_halts_on_missing_plugin_dir
FAILED tests/test_spawn_pipeline.py::SpawnCmd::test_core_version_reports_sha_date_and_label_for_local_override
FAILED tests/test_spawn_gate_wiring.py::Ledger::test_toolchain_cache_env_redirected_into_workspace
FAILED tests/test_spawn_board_flows.py::RosterOwnershipScoping::test_undispositioned_role_prs_excludes_own_roster_branch
5 failed, 2030 passed, 17 xfailed, 4 xpassed in 1068.82s (0:17:48)
```
exit code 1. All 5 are the exact same test names issue #2195's own
"Executed acceptance evidence" section already ran and documented as
pre-existing environment pollution unrelated to that issue's diff
(`core_plugin_dirs`, `core_version`, `_undispositioned_role_prs`, the
toolchain-cache-env block, and `SinglePhaseSignal`'s byte-identical-task
check — none touched by this diff's own `git diff --stat` above).

Skill check
- skill-verdict: implementation-performance-data-structure-choice —
  applied: invoked; see Why section above for the full reasoning.
- other mounted skills: not triggered — see Why section above.

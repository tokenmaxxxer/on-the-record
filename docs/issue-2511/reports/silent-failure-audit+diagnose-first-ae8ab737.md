---
issue: 2511
role: silent-failure-audit+diagnose-first-ae8ab737
author: silent-failure-audit+diagnose-first-ae8ab737
skills: silent-failure-audit (skill-repository(297e350)), diagnose-first (skill-repository(297e350))
loop_state: landed
upstream:
  - path: docs/issue-2511/reports/silent-failure-audit+observability-explorability-6f5691f7.md
    sha: bffb88bc219db58f951d3515719ed7c4153252fd
---

# issue-2511 — silent-failure-audit+diagnose-first-ae8ab737 record

skill-verdict: silent-failure-audit — applied: invoked; classified the halted/superseded/resolved spawn-attempt states and traced the evidence-pruning chain that caused the silent misdiagnosis
canonical: `cat /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl` — the live ledger read directly (3 attempts, all `outcome: "halted"`, zero `session-log`) is the artifact this classification traced back to `_prune_spawn_attempts()`'s pre-fix unconditional-prune-on-success branch (old `spawn.py:1489`), cited in full in "Why" below.

skill-verdict: diagnose-first — applied: invoked; used to pin down the evidence-location root cause (retention asymmetry) before choosing a fix
canonical: `gh pr view 2608 --comments` — the review comment's own measurement (`Counter({'spawn_attempt': 3, 'spawn_attempt_outcome': 3})`, "zero `session-log`") is the diagnosis this session re-verified against the same live file before selecting the retention-symmetry fix over an external-evidence-source alternative (see "Why", evidence-location decision).

## What was done

Build-now bypass (`CORE_BUILD_NOW=1`, spawner-set) — delivered directly, no phase-1 proposal round.

This session implements the residual PR #2594 named and PR #2608 tried and failed to land: a **supersession** check, layered on top of (never replacing) #2594's class-based halt re-check, for the one shape neither the original fix nor #2608 could resolve — a halt whose blocking condition is bound to the *attempt's own recorded arguments* (`cwd-invalid`, `workspace-origin-mismatch`) or to a legacy pre-#2594 record with no `cwd` at all, where a later successful retry for the same work can never clear the original record's own re-check no matter how many times it's asked.
canonical: `gh issue view 2511 --comments` output — reopen comment ("The residual... has this (issue, slug) since been attempted successfully?") and PR #2608 review comment ("cannot resolve its own canonical fixture in production")

**Code changes** (`spawn.py`, `roster.py`, `test/test_spawn_attempt_staleness.py`):

1. `spawn.py:1310` `_LEASE_DISAMBIGUATOR_SUFFIX_RE` + `spawn.py:1313` `_role_family(role)` — strips the trailing 8-lowercase-hex-char lease disambiguator (`roster.new_lease_disambiguator()` == `secrets.token_hex(4)`) a role string carries, leaving the "role family" that identifies the work item itself rather than one specific spawn attempt at it.
   canonical: `grep -n "def new_lease_disambiguator" -A12 roster.py` — `return secrets.token_hex(4)` (roster.py:245), confirming the exact 8-lowercase-hex-char shape the regex targets.
2. `spawn.py:1322` `_attempt_superseded(attempt_id, attempt, attempts, outcomes)` — answers "has a later attempt for this same (issue, role-family) already reached `session-log`?" using only data the caller already loaded (`_load_spawn_attempts()`), conservative-`False` on any missing/malformed field.
3. `roster.py:638-651` (`spawn_attempt_sweep()`) — after `_sp._halt_condition_cleared()` returns `False`, additionally asks `_sp._attempt_superseded()`; either path resolves the halt through the exact same event/print/ledger-write machinery #2594 already built, now tagged with `resolution="class-recheck"` or `resolution="superseded"` so the two mechanisms stay distinguishable in the durable ledger.
4. `spawn.py:1598-1614` (`_prune_spawn_attempts()`) — **the evidence-location fix**: `"session-log"` outcomes are no longer pruned unconditionally at the end of every sweep; they are now retained for `SPAWN_ATTEMPTS_RETENTION_SEC` (7 days), symmetric with `"halted"` outcomes. This is the change that makes `_attempt_superseded()`'s evidence actually available in production — see "Why" below for why PR #2608 could not find it.
5. `test/test_spawn_attempt_staleness.py` — new tests added: `RoleFamilyTest`, `AttemptSupersededTest`, `SpawnAttemptSweepSupersessionTest` (end-to-end against the exact live #2576 halt message and the exact live `issue-1/implementation-af260856` fixture), `PruneSpawnAttemptsSessionLogRetentionTest` (the retention-symmetry fix in isolation).
canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `41 passed in 0.93s` (25 pre-existing #2594 tests + 16 new, all green); `python3 -m pytest test/test_spawn_attempt_staleness.py -v 2>&1 | grep -c "^test_"` — result: `41`

## Why

**Diagnosis first (why PR #2608 failed and what that implies about where to fix it).** #2608's own review comment already did the diagnosis; this session verified it empirically against the real ledger rather than re-deriving it from scratch (diagnose-first: locate the actual cause before picking a design).

The real production ledger at the location `spawn.py`'s `STATE_ROOT = MUSTER_STATE_ROOT or ROOT/"runs"` resolves to for this orchestrator process is `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl` (found by grepping for the real fixture hex suffixes across the filesystem, since neither this per-issue worktree checkout nor `/home/jwjung/tokenmaxxxer/on-the-record/runs/` contain the file — confirmed empty/absent there).
derived: `grep -n "STATE_ROOT = " spawn.py` → `STATE_ROOT = (Path(os.environ["MUSTER_STATE_ROOT"]).resolve() if os.environ.get("MUSTER_STATE_ROOT") else ROOT / "runs")` (spawn.py:652-653); `find /home/jwjung -iname "spawn-attempts.jsonl" -not -path "/tmp/*"` located it; `grep -c "af260856\|ec09cf78\|c678659a" /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl` → `4` (the only match among the candidates found)

Its content, read directly:
```
{"event": "spawn_attempt", "attempt_id": "2576:silent-failure-audit-ec09cf78:2909352:1787801373790", "issue": 2576, "role": "silent-failure-audit-ec09cf78", "pid": 2909352, "ts": 1787801373.7906659}
{"event": "spawn_attempt_outcome", "attempt_id": "2576:silent-failure-audit-ec09cf78:2909352:1787801373790", "outcome": "halted", "detail": "-C 가 존재하지 않는 디렉터리다: tokenmaxxxer/on-the-record\n  cwd 는 레포 루트를 가리켜야 한다 — 경로를 다시 확인해라.", ...}
{"event": "spawn_attempt", "attempt_id": "2587:technical-writing-structure-comprehension-de7d3bcf:2918867:1787801516833", "issue": 2587, "role": "technical-writing-structure-comprehension-de7d3bcf", ...}
{"event": "spawn_attempt_outcome", ... "outcome": "halted", "detail": "이슈 #2587 가 요구 연결이 없다: ...", ...}
{"event": "spawn_attempt", "attempt_id": "1:implementation-af260856:3000953:1787802757739", "issue": 1, "role": "implementation-af260856", ...}
{"event": "spawn_attempt_outcome", ... "outcome": "halted", "detail": "이슈 #1 가 요구 연결이 없다: ...", ...}
```
canonical: `cat /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl` — 6 lines, 3 attempts, all `outcome: "halted"`, zero `outcome: "session-log"`, none of the three `spawn_attempt` lines carry a `cwd` field at all — this is the exact "0/3 attempts carry cwd" legacy-record shape the reopen comment's second finding described and the exact "3 records, all halted, zero session-log" shape PR #2608's review comment measured.

This confirms #2608's diagnosis directly rather than trusting its prose: the evidence a "later attempt succeeded" check needs (a `session-log` outcome record) **does not exist in production at all**, because it was pruned by `_prune_spawn_attempts()` before this session ever started — that function used to drop every `session-log` outcome unconditionally at the end of the very sweep that recorded it (the comment PR #2608's reviewer cited at old `spawn.py:1489`), and that prune runs at the end of `spawn_attempt_sweep()` itself, i.e. every watchdog heartbeat.
canonical: `grep -n "_sp._prune_spawn_attempts" roster.py` → `roster.py:674: _sp._prune_spawn_attempts(now=now)`, called unconditionally at the end of `spawn_attempt_sweep()`; `grep -n "POLL_HEARTBEAT_SLEEP_SECONDS" -r . 2>/dev/null | grep -v test` → `monitors/poll-heartbeat.sh: sleep_seconds="${POLL_HEARTBEAT_SLEEP_SECONDS:-120}"` (the ~2-minute cadence cited above)

**Evidence-location decision: retention symmetry inside `spawn-attempts.jsonl` (chosen), not an external source (rejected).** Two options were on the table (per the task statement, itself echoing #2608's review):

- **(a) Chosen — extend `session-log` retention to `SPAWN_ATTEMPTS_RETENTION_SEC`, matching `halted`.** This is the minimal, symmetric fix: the same append-only, crash-safe, already-audited mechanism (`SPAWN_ATTEMPTS_PATH`, issue #2240/#2291/#2393) already retains `halted` outcomes for exactly this reason (giving an orchestrator time to notice and act); making `session-log` outcomes live exactly as long closes the asymmetry with no new file, no new TTL knob (reuses `SPAWN_ATTEMPTS_RETENTION_SEC` verbatim), and no new failure mode. Implemented at `spawn.py:1603-1614`.
- **(b) Rejected — an external durable source** (a merged-PR check via `board.py`'s existing `_merged_pr_for_branch`, or some other GitHub/board completion record). Rejected for three concrete reasons, not a vague preference: (i) this orchestrator spawns against an arbitrary target repo passed via `-C` — it is not always `on-the-record`, is not always even a GitHub-hosted repo, and branch-naming conventions are not guaranteed uniform across targets, so a GitHub-specific completion check does not generalize the way the STATE_ROOT-scoped ledger already does; (ii) it adds a network call (`gh api`/`gh pr list`) to the watchdog's re-check path, scaling with the number of currently-halted subjects on every tick, versus the in-process file read the chosen option costs nothing extra for (the sweep already loads the whole file); (iii) `_merged_pr_for_branch` matches on exact branch name, which has the identical over-narrow-matching defect #2608's `role`-exact-match had (a retry mints a fresh lease disambiguator, so its branch name differs from the halted attempt's) — reusing it would just relocate the "same work" matching problem addressed below to a different string, not solve it.
canonical: `grep -n "def _merged_pr_for_branch" -A5 board.py` — confirms it exists and matches on `branch` (exact string), the same shape defect

**"Same work" matching rule: issue number + role family (lease-disambiguator stripped), not exact role string.** #2608's `other.get("role") == role` exact match never fires for a genuine retry, because the retry's role differs by exactly the part designed to differ: `roster.new_lease_disambiguator()` mints a fresh `secrets.token_hex(4)` (8 lowercase hex chars) per spawn, appended as `f"{skill_slug}-{disambiguator}"` — the real #2576 pair is `silent-failure-audit-ec09cf78` (halted) → `silent-failure-audit-c678659a` (succeeded), confirmed live in issue #2576's own `[watch]` session-end comments.
canonical: `gh issue view 2576 --comments` — two `[watch] ... session-end` comments: `issue-2576/silent-failure-audit-c112b427: ... PR #2586` and `issue-2576/silent-failure-audit-c678659a: ... PR #2591`; `grep -n "disambiguator = new_lease_disambiguator" -A3 spawn.py` → `spawn.py:1989-1991`, `a.role = f"{skill_slug}-{disambiguator}"`

`_role_family()` (spawn.py:1313) strips exactly an `-[0-9a-f]{8}$` trailing group. `_attempt_superseded()` (spawn.py:1322) then requires **both** `other.get("issue") == issue` (exact) **and** `_role_family(other_role) == family` (family-level) **and** `other_ts > my_ts` (the candidate must be a later attempt) **and** `outcomes[other_id].outcome == "session-log"`. Over-broadening is guarded on both axes deliberately, not just the family axis: `AttemptSupersededTest.test_success_on_a_different_issue_does_not_supersede` and `.test_success_on_a_different_role_family_does_not_supersede` (test/test_spawn_attempt_staleness.py) assert a same-family success on a *different* issue, and a same-issue success on a *different* family, both leave the halt unresolved — this is exactly the over-broadening the task named `issue-1/implementation-af260856` as the guard against.
canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py::AttemptSupersededTest -v` — result: `7 passed`

## What did not work

None.

## Upstream basis

`docs/issue-2511/reports/silent-failure-audit+observability-explorability-6f5691f7.md` (commit `bffb88bc219db58f951d3515719ed7c4153252fd`, already landed on `main`) — the #2594 record this session's supersession check is layered on top of, per the constraint that its class-based re-check "stays exactly as a first-class mechanism." The reopen and PR #2608 review comments on issue #2511 are the other upstream input (not a docs-tree artifact — read via `gh issue view`/`gh pr view`, cited inline above at each claim they support).
canonical: `gh issue view 2511 --comments`; `gh pr view 2608 --comments`

## Open findings

None outstanding for this session's scope — five items verified below, each with its own execution citation.

1. Verified — evidence-location fix is real, not cosmetic. Ran the exact real production ledger (a copy, since the watchdog process itself was not stopped for this session — see the process note below) through the pre-fix code (`git stash` of this session's `spawn.py`/`roster.py`/test changes) and the post-fix code:
   - Pre-fix, real ledger: `count: 3` — all three attempts (`issue-1/implementation-af260856`, `issue-2576/silent-failure-audit-ec09cf78`, `issue-2587/technical-writing-structure-comprehension-de7d3bcf`) print as live halts.
   - Post-fix, **same unmodified** real ledger (no reconstruction): `count: 3` — identical output. This is the honest limitation stated plainly: the fix cannot resurrect evidence already destroyed by the pre-fix pruning before this session started (the c678659a `session-log` record was already gone, per the "Why" section's direct read of the file above). The fix is prospective — from this point forward, `session-log` outcomes survive long enough for the next genuinely-superseded halt to resolve.
   - Post-fix, real ledger **plus the real historical c678659a `session-log` event reconstructed from issue #2576's own `[watch]` comment** (role `silent-failure-audit-c678659a`, log path and `2026-08-27T12:31:16Z` timestamp taken verbatim from that comment, not invented): `count: 2` — `issue-2576/silent-failure-audit-ec09cf78` now prints `halt RESOLVED at ... (class=cwd-invalid, resolution=superseded, ...)` and is gone from the live-halt count; `issue-1/implementation-af260856` and `issue-2587/...` print unchanged.
   canonical (pre-fix run): `git stash push -- spawn.py roster.py test/test_spawn_attempt_staleness.py && MUSTER_STATE_ROOT=/tmp/otr2511-demo/before python3 -c "import time,spawn,roster; roster.spawn_attempt_sweep(now=time.time())"` — result: 3 `[spawn-attempt] ... spawn halted pre-workspace` lines, `---count: 3`; `git stash pop` restored the fix afterward.
   canonical (post-fix, unmodified ledger): `MUSTER_STATE_ROOT=/tmp/otr2511-demo/after-nofix-evidence python3 -c "import time,spawn,roster; roster.spawn_attempt_sweep(now=time.time())"` — result: 3 lines, `---count: 3`, byte-identical set of subjects to the pre-fix run.
   canonical (post-fix, reconstructed real evidence): `MUSTER_STATE_ROOT=/tmp/otr2511-demo/after-with-reconstructed-evidence python3 -c "import time,spawn,roster; roster.spawn_attempt_sweep(now=time.time())"` — result: `[spawn-attempt] issue-1/implementation-af260856: spawn halted pre-workspace ...`, `[spawn-attempt] issue-2576/silent-failure-audit-ec09cf78: halt RESOLVED at 2026-08-27T05:56:14Z (class=cwd-invalid, resolution=superseded, originally attempted at 2026-08-27T03:29:33Z) — no longer a live halt: -C 가 존재하지 않는 디렉터리다: tokenmaxxxer/on-the-record`, `[spawn-attempt] issue-2587/technical-writing-structure-comprehension-de7d3bcf: spawn halted pre-workspace ...`, `---count: 2`; durable resolution record captured before cleanup: `{"event": "spawn_attempt_resolved_reported", "attempt_id": "2576:silent-failure-audit-ec09cf78:2909352:1787801373790", "issue": 2576, "role": "silent-failure-audit-ec09cf78", "class": "cwd-invalid", "resolution": "superseded", "attempted_ts": 1787801373.7906659, "ts": 1787810174.7947056}`.
   Process note: the real ledger file itself was only ever *copied* for these three runs (`cp` into `/tmp/otr2511-demo/*`, pointed at via `MUSTER_STATE_ROOT`) — the actual production file at `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/spawn-attempts.jsonl` was read but never mutated by this session. This is not the isolated/hand-built-fixture mistake #2608 made: the copies are byte-identical snapshots of the real file, and the one addition in the third run reconstructs a real historical event (role/log-path/timestamp taken verbatim from `gh issue view 2576 --comments`) rather than an invented one.

2. Verified — `issue-1/implementation-af260856` (the "nobody will ever tag this" fixture) is unaffected by the supersession mechanism under both real-ledger conditions above, and under the synthetic over-broadening guard tests.
   canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py::SpawnAttemptSweepSupersessionTest -v` — result: `2 passed` (`test_halt_superseded_by_a_later_successful_retry_stops_replaying`, `test_unrelated_halt_on_a_never_tagged_issue_keeps_reporting_unchanged`)

3. Verified — every reported line already carries the attempt's timestamp (constraint 4 in the task). This was already true from #2594 (`roster.py`'s report `print(f"[spawn-attempt] {subject}: spawn halted pre-workspace (attempted at {_iso(a.get('ts', now))}): {reason}")` is the single print statement both the "still-blocked" and "no-outcome" branches fall through to) — no code change was needed for this bullet; confirmed unchanged by re-running the pre-existing timestamp test, still green.
   canonical: `grep -n "attempted at" roster.py` → `roster.py:660` (the shared print site); `python3 -m pytest test/test_spawn_attempt_staleness.py::SpawnAttemptSweepReplayFixTest::test_report_line_carries_the_original_attempt_timestamp -q` — result: `1 passed`

4. Verified — the tag-added → no-longer-reported acceptance criterion, reusing #2594's own established test-harness pattern (`HaltConditionClearedGhBackedClassesTest`'s `mock.patch.object(requirement_linkage, "check", ...)` shape) rather than mutating a real GitHub issue:
   ```
   tag NOT yet added -> halt_condition_cleared = False
   tag added        -> halt_condition_cleared = True
   ```
   and end-to-end through the sweep itself (temp ledger, mocked `requirement_linkage.check`, real `roster.spawn_attempt_sweep()` call — same harness shape as `SpawnAttemptSweepReplayFixTest`):
   ```
   --- tick 1 (tag not yet added) ---
   [spawn-attempt] issue-2587/technical-writing-demo: spawn halted pre-workspace (attempted at 2026-08-27T04:57:04Z): 이슈 #2587 가 요구 연결이 없다: ...
   --- tick 2 (tag added) ---
   [spawn-attempt] issue-2587/technical-writing-demo: halt RESOLVED at 2026-08-27T05:57:04Z (class=requirement-tag, resolution=class-recheck, originally attempted at 2026-08-27T04:57:04Z) — no longer a live halt: 이슈 #2587 가 요구 연결이 없다: ...
   ```
   canonical: ad-hoc script run via `python3 -c "..."` using `mock.patch.object(rl, 'check', ...)` against `spawn._halt_condition_cleared` and `roster.spawn_attempt_sweep`, both invocations shown verbatim above; this exercises the pre-existing `resolution="class-recheck"` path (unchanged by this session except for the new `resolution` field name added alongside it), not the new supersession path — the supersession path's own live-ledger demonstration is finding 1 above.

5. Verified — no regressions. Full suite before this session's changes (this branch's `spawn.py`/`roster.py`/test file stashed back to their state after #2594 but before this session) vs. after:
   ```
   before: 15 failed, 318 passed in 1.88s
   after:  15 failed, 334 passed in 2.23s
   ```
   the delta (334 - 318 = 16) is exactly the 16 new tests added; the 15 failing test names are byte-identical in both runs (pre-existing, unrelated — same set the #2594 record documented).
   canonical: `git stash push -- spawn.py roster.py test/test_spawn_attempt_staleness.py && python3 -m pytest test/ tests/test_tmp_resource_gc.py -q 2>&1 | tail -3` → `15 failed, 318 passed in 1.88s`; `git stash pop && python3 -m pytest test/ tests/test_tmp_resource_gc.py -q 2>&1 | tail -3` → `15 failed, 334 passed in 2.23s`

## Staleness determination per failure class (acceptance criterion, full picture)

Five classes still use **re-check** exactly as #2594 left them (`spawn._halt_condition_cleared`, unchanged in this session): `requirement-tag`, `acceptance-format`, `enospc`, `workspace-origin-mismatch`, `cwd-invalid` — none of them use elapsed time, all documented in the upstream #2594 record's "Why" section (still accurate, not restated in full here to avoid drift between two records describing the same code).

This session adds a sixth mechanism, **supersession**, layered strictly after re-check returns `False` (never instead of it — `roster.py:638-651`): "did a later attempt at the same (issue, role-family) reach `session-log`?" This is not elapsed-time-based either — a halt with no later successful retry stays reported forever regardless of how old it is (`issue-1/implementation-af260856` is the standing proof, per Open Finding 2 above), and a halt whose retry exists but also failed is likewise not touched (`AttemptSupersededTest.test_later_attempt_that_also_halted_does_not_supersede`, part of the 7-test class cited in "Why" above). The only thing that resolves a halt through this path is a positively-confirmed later success for the identified same work — never a guess based on how much time has passed.

Why neither mechanism can mark a still-broken spawn resolved: class re-check only returns `True` on a positive, freshly-re-run confirmation of the underlying condition (files exist, gh-backed check reports clean, disk usage below threshold) — every ambiguous/unparseable/exception case returns the conservative `False` (unchanged from #2594). Supersession only returns `True` on a positive `session-log` outcome for a *later*, *same-issue*, *same-role-family* attempt — every other input (missing field, earlier/same-time candidate, wrong issue, wrong family) returns `False`, per the `AttemptSupersededTest` suite cited above. Both mechanisms fail closed toward "still reporting," never toward silence.
canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `41 passed in 0.93s`

## Next steps

None — `loop_state` is terminal (`landed`).
canonical: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` — result: `41 passed in 0.93s` (full suite for this issue's scope, re-cited here as the terminal-state evidence)

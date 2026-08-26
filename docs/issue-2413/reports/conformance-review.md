---
issue: 2413
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2413/reports/implementation.md
    sha: 335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8
  - path: docs/issue-2413/reports/implementation/2026-08-25-hunt-issue-2413-prune-fix.md
    sha: 335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8
  - path: docs/issue-2413/reports/implementation.md
    sha: bd3036dba91db953184f484bc9381eb8ed0b617f
subject: PR #2418 (issue-2413/implementation, head bd3036dba91db953184f484bc9381eb8ed0b617f, prior review pinned 335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8) — spawn.py, roster.py, tests/test_watch_hardening.py
test: issue #2413 Acceptance section, five bulleted checks
result: passed
assertedBy: conformance-review session for issue-2413, builder-blind review of PR #2418, 2026-08-25 — CORE_BUILD_NOW=1 build-now bypass, delivered directly; re-review of the CHANGES-round missing-ts fix, 2026-08-25, same bypass
---

# issue-2413 — conformance-review record

## What was done

canonical: `gh issue view 2413`, `gh pr view 2418`, `gh pr diff 2418`
(all run this session, quoted/paraphrased throughout this record) —
first reads before any check began.

Builder-blind conformance review of PR #2418
(`https://github.com/tokenmaxxxer/on-the-record/pull/2418`, branch
`issue-2413/implementation`, head `335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8`,
base `2ca4b4deff619ad9d2f0f1de0f5e16442d0db8a9`) against issue #2413's
five acceptance checks. Independently re-derived every claim in
`335a0c8e:docs/issue-2413/reports/implementation.md` (that path is not
reachable on this review branch — it lives on `issue-2413/implementation`,
cited here pinned to that commit) rather than trusting it: checked out
the PR head and its base commit into two separate `git worktree add`
checkouts (`/tmp/pr2418-review` at `335a0c8e`, `/tmp/pre-fix-review` at
`2ca4b4de`), ran the shipped test suites myself, and wrote my own
from-scratch synthetic fixture (different pid scheme and attempt_id
format than the PR's own reproduction script) to independently
reproduce the live-pid demo and the before/after measurements. All
five checks below are backed by evidence this session generated
itself this turn. Full requirement-by-requirement verdicts, each with
its own `canonical:`/`derived:` tag, are in "## Findings" below.

Skills invoked this session (skill-repository issue #1955/#1758
mapping): conformance-review-requirement-extraction,
conformance-review-verification-method-selection,
conformance-review-verdict-assignment,
conformance-review-traceability-and-evidence,
conformance-review-finding-record. See "## Skill verdicts" at the
bottom.

**CHANGES-round re-review addendum (this session, same conversation,
new turn):** PR #2418's builder pushed a fix after the check-runner's
first-pass comment (`gh pr view 2418` comments) surfaced a remaining
gap: `_prune_spawn_attempts()`'s `outcome is None` branch computed
`ts = a.get("ts", now)`, so a record with no `ts` key at all (not
malformed — genuinely absent) always defaulted to `now`, making
`now - ts == 0` and `aged_out` never trip, regardless of pid liveness
— a second instance of the exact "kept forever" failure class this
issue exists to fix, distinct from the string-encoded-pid bypass the
before-landing warrant-hunter already caught. Fix commit
`bd3036dba91db953184f484bc9381eb8ed0b617f`: default `ts` to `None`
instead of `now`, so a missing `ts` fails the existing
`not isinstance(ts, (int, float))` guard the same way a malformed
`ts` already did. This addendum independently re-verifies that fix
per `defect-verification-independence-from-upstream-verdicts`
(skill-repository issue #2001 cross-family addition) — built from
scratch rather than trusting the fix commit's own repro transcript in
`bd3036db:docs/issue-2413/reports/implementation.md`. See the new
finding block "A1a-2" below.

## Why

canonical: this session's own worktree checkouts and pytest/python3
invocations, transcripts quoted under "## Findings" below.

Chose independent re-derivation over trusting the implementation
record's transcripts because the role is explicitly builder-blind: a
review that only re-reads what the builder already claimed cannot
catch a fabricated or cherry-picked transcript, and this issue's own
filing is about a mechanism (#2400's prune) whose builder believed it
worked when it didn't. Concretely, this session ran the actual test
suites and functions itself rather than accepting pasted summaries,
built its own synthetic `spawn-attempts.jsonl` fixture from scratch
(different dead-pid value and attempt_id shape than the builder's
script) to see whether an independently-built reproduction lands on
the same before/after shape the record claims, and spawned a real
`sleep 120` subprocess itself to demonstrate the live-pid-kept
behavior first-hand rather than reading the builder's own live-pid
transcript. Full commands and outputs are the `canonical:`/`derived:`
tags under each finding below.

## Upstream basis

- `335a0c8e:docs/issue-2413/reports/implementation.md` (implementation
  record) — the delivered work under review. Not present on this
  review branch (`issue-2413/conformance-review`); read via
  `git show 335a0c8e:docs/issue-2413/reports/implementation.md` and
  `gh pr diff 2418` this session.
- `335a0c8e:docs/issue-2413/reports/implementation/2026-08-25-hunt-issue-2413-prune-fix.md`
  — the before-landing warrant-hunter finding (str-encoded pid bypass)
  and its fix, folded into the same PR. Same not-on-this-branch caveat.
- PR #2418, `https://github.com/tokenmaxxxer/on-the-record/pull/2418`,
  head `335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8`, base
  `2ca4b4deff619ad9d2f0f1de0f5e16442d0db8a9` (current `origin/main` tip
  at review time) — `gh pr view 2418`/`gh pr diff 2418`, this session.
- Issue #2413 — `gh issue view 2413`, this session.

## Findings

Five requirement blocks, one per issue #2413 acceptance bullet, split
per conformance-review-requirement-extraction rule 1 where a bullet
bundled more than one obligation (bullet 1 bundles: the prune behavior
itself, the liveness test being stated-with-reasoning, and the bound
being stated-with-reasoning — three independently checkable clauses).

---
requirement: "A1a — an attempt with no outcome whose process is provably gone (pid not running AND/or older than a stated bound) is pruned rather than kept forever" [dimension: functional behavior]
spec_ref: issue #2413, Acceptance bullet 1, clause 1
verdict: Present
evidence: |
  335a0c8e:spawn.py:1032-1073 (`_prune_spawn_attempts`, outcome-is-None
  branch at 1060-1069: `prune = NOT _pid_is_alive(pid) AND aged_out`,
  `aged_out` = age >= `SPAWN_ATTEMPTS_RETENTION_SEC`),
  335a0c8e:spawn.py:1002-1030 (`_pid_is_alive`).

  canonical: `cd /tmp/pr2418-review && python3 -m pytest
  tests/test_watch_hardening.py -v` (this session, PR head 335a0c8e) —
  `tests/test_watch_hardening.py::SpawnAttemptPruneLiveness::test_dead_pid_past_retention_is_pruned
  PASSED`, full run `32 passed in 0.95s`.

  derived: independent from-scratch fixture run this session (fork+reap
  dead pid, aged past `SPAWN_ATTEMPTS_RETENTION_SEC`) —
  ```
  MY INDEPENDENT CHECK -- dropped: 1 remaining: ['live-real']
  ```
  (the companion `dead-real` id, not printed, is the one line dropped
  — confirmed by its absence from `remaining`). Full command in this
  session's own transcript, reproduced again at scale in the A3/A4
  431-line fixture below (305 issue-31 + 114 issue-7 dead/aged orphans
  fully pruned).
rationale: Code path, an independently re-run existing test, and an independently-built (not the builder's own) fixture all agree a dead-pid-plus-aged-out record is pruned.
---
requirement: "A1a-2 (CHANGES round) — a record with no `ts` key at all (not just malformed) whose process is provably gone is pruned rather than kept forever" [dimension: functional behavior / edge case; verification method: Test + independent Demonstration, per defect-verification-independence-from-upstream-verdicts rule 2 (deliberate edge case, not only happy path)]
spec_ref: issue #2413, Acceptance bullet 1, clause 1 (missing-`ts` sub-case, not covered by A1a's original evidence — A1a's own fixture always wrote a numeric `ts`)
verdict: Present
evidence: |
  bd3036dba9:spawn.py:1067-1069 (`ts = a.get("ts")`, no default —
  changed from the pre-fix `a.get("ts", now)` at
  335a0c8e:spawn.py:1063, which this review's own A1a pass did not
  independently exercise with a `ts`-less record). A missing `ts`
  yields `None`, which fails `isinstance(ts, (int, float))`, forcing
  `aged_out = True` immediately, subject to the same
  `_pid_is_alive(pid)` override as every other record in the branch.

  canonical: `cd /tmp/pr2418-review2 && python3 -m pytest
  tests/test_watch_hardening.py -v` (this session, PR head
  `bd3036dba9`) —
  `SpawnAttemptPruneLiveness::test_missing_ts_with_dead_pid_is_pruned`
  and
  `SpawnAttemptPruneLiveness::test_missing_ts_with_live_pid_still_kept`
  both `PASSED`, full run `34 passed in 0.87s` (32 prior + 2 new).

  derived: independent from-scratch repro this session (own script,
  not the builder's — different attempt_id naming
  `review-missing-ts-*` vs. the builder's `a5`/`a6`, dead pids obtained
  by this session's own fork+reap rather than a hardcoded pid number,
  tested at 4 simulated ages instead of the builder's 3, plus a
  separate live-pid-with-missing-ts case): built two isolated worktrees
  (`/tmp/pr2418-review2` at `bd3036dba9`, `/tmp/pre-fix-review2` at the
  prior reviewed head `335a0c8e`) and ran `spawn._prune_spawn_attempts()`
  against a record with the `ts` key entirely absent (`assert "ts" not
  in record` in the script itself, not just "no value set") —
  ```
  POST-FIX (bd3036dba9):
  dead pid +0y: dropped=1 remaining_lines=0
  dead pid +1y: dropped=1 remaining_lines=0
  dead pid +3y: dropped=1 remaining_lines=0
  dead pid +10y: dropped=1 remaining_lines=0
  live pid +10y, missing ts: dropped=0 remaining_lines=1

  PRE-FIX (335a0c8e, the prior review's own pinned commit):
  dead pid +0y: dropped=0 remaining_lines=1
  dead pid +1y: dropped=0 remaining_lines=1
  dead pid +3y: dropped=0 remaining_lines=1
  dead pid +10y: dropped=0 remaining_lines=1
  live pid +10y, missing ts: dropped=0 remaining_lines=1
  ```
  Also confirmed the fix's stated out-of-scope claim: `grep -n
  'outcome_ts = outcome.get' bd3036dba9:spawn.py` still shows
  `outcome.get("ts", now)` unchanged on the sibling `halted` branch (a
  different, out-of-scope code path per the fix commit's own
  reasoning — `_record_spawn_outcome()` always writes a real `ts`, so
  that branch cannot hit this failure class in practice). Collateral
  suites re-run: `python3 -m pytest tests/test_spawn_pipeline.py
  tests/test_standing_red_watch.py` — `97 passed`. Diff scope check:
  `git diff --stat 335a0c8e4e bd3036dba9 -- . ':!docs'
  ':!.orchestrate-hook-fires'` — `spawn.py` (+10/-1) and
  `tests/test_watch_hardening.py` (+29) only, no other production file
  touched.
rationale: |
  Independently confirms, against this reviewer's own prior pinned
  commit (`335a0c8e`, which this same record marked A1a Present without
  ever testing a `ts`-less record), that a genuinely-missing `ts` key
  used to defeat aging entirely (0 dropped across 4 simulated ages up
  to +10 years) and now ages out on the very first prune pass at any
  simulated age, while a live pid with the same missing `ts` is still
  correctly kept — satisfying defect-verification-independence rule 2
  (edge case, not just the dead-pid happy path) and rule 1 (treating
  the fix commit's own "34 passed" claim as a claim to re-derive, not a
  settled fact). Present, not a revision of A1a's prior Present verdict
  — A1a covered the malformed/aged-numeric-`ts` case correctly at the
  time; this is additional coverage for a distinct sub-case the fix
  commit itself identified and this review independently corroborates.
---
requirement: "A1b — the liveness test used is stated with the reasoning" [dimension: functional behavior / documentation]
spec_ref: issue #2413, Acceptance bullet 1, clause 2
verdict: Present
evidence: |
  335a0c8e:spawn.py:1002-1030 (`_pid_is_alive` docstring — states the
  test is `os.kill(pid, 0)`, that only `ProcessLookupError` means dead,
  and that `PermissionError`/other `OSError` are conservatively treated
  as alive "because an inconclusive check must never prune a live
  spawn"); 335a0c8e:docs/issue-2413/reports/implementation.md "## Why",
  "Liveness test" paragraph, same reasoning restated for the record.
  canonical: `git show 335a0c8e:spawn.py | sed -n '1002,1030p'`, this
  session — docstring text confirmed present at that exact commit.
rationale: Both the code's own docstring and the implementation record state the chosen probe and justify the conservative-on-uncertainty policy, not just name it.
---
requirement: "A1c — the bound (age) chosen is stated with the reasoning" [dimension: functional behavior / documentation]
spec_ref: issue #2413, Acceptance bullet 1, clause 3
verdict: Present
evidence: |
  335a0c8e:spawn.py:1060-1069 (reuses `SPAWN_ATTEMPTS_RETENTION_SEC`,
  defined 335a0c8e:spawn.py:999 as `7 * 24 * 3600` = 604800s, the same
  constant the pre-existing `halted` branch already used — no new
  constant introduced); 335a0c8e:docs/issue-2413/reports/implementation.md
  "## Why", "Age bound" paragraph (explains reuse over a new knob).
  canonical: `git show 335a0c8e:spawn.py | grep -n
  SPAWN_ATTEMPTS_RETENTION_SEC`, this session — one definition
  (line 999), reused at line ~1068, no second constant defined.
rationale: The bound is not merely named — the record explains why this specific existing constant was reused rather than a new one invented, satisfying "stated with the reasoning."
---
requirement: "A2 — a genuinely in-flight attempt (process alive, no outcome yet) is still kept, demonstrated live with a real running spawn, not asserted" [dimension: edge-case; verification method: Demonstration required by the requirement's own wording]
spec_ref: issue #2413, Acceptance bullet 2
verdict: Present
evidence: |
  335a0c8e:spawn.py:1067-1069 (`if _pid_is_alive(pid) or not aged_out:
  keep`).

  canonical: `cd /tmp/pr2418-review && python3 -m pytest
  tests/test_watch_hardening.py -v` (this session) —
  `SpawnAttemptPruneLiveness::test_live_pid_survives_regardless_of_age
  PASSED`.

  canonical: independent live demonstration run this session (not the
  builder's transcript) — spawned a real
  `subprocess.Popen(["sleep", "120"])`, wrote its real pid into a
  synthetic spawn-attempts record aged past retention, alongside a
  separately forked-and-reaped dead pid aged the same amount, and ran
  `spawn._prune_spawn_attempts()` from PR head 335a0c8e against it:
  ```
  MY INDEPENDENT CHECK -- dropped: 1 remaining: ['live-real']
  ```
  the live subprocess's record (`live-real`) survived; the dead one
  (`dead-real`) was the sole drop.
rationale: The requirement explicitly demands demonstration over assertion; this session generated its own real running process and its own dead process rather than re-reading the builder's sleep-120 transcript, and got the same outcome.
---
requirement: "A3 — after the fix, runs/spawn-attempts.jsonl drops to only real, current entries — before/after line counts and per-issue breakdown in the record (currently 434 total: 305 issue 31, 114 issue 7)" [dimension: functional behavior]
spec_ref: issue #2413, Acceptance bullet 3
verdict: Present
evidence: |
  canonical: `ls runs/` in this review's own working directory, this
  session — `ls: cannot access 'runs/': No such file or directory`;
  `.gitignore` line 1 is `runs/`. Confirms independently that the
  literal path `runs/spawn-attempts.jsonl` the acceptance text names
  does not exist in any worktree available to this review — the same
  environmental constraint `335a0c8e:docs/issue-2413/reports/implementation.md`
  names, not a builder-side omission unique to their environment.

  derived: independent from-scratch 431-line fixture built this
  session (dead pid `999999`, not the builder's pid choice; 305
  issue-31 + 114 issue-7 orphan `spawn_attempt` records aged 10 days
  with no outcome, 2 live in-flight records on this session's own real
  pid, 3 `halted`-outcome records, 2 `session-log`-outcome records —
  431 total lines) — ran `spawn_attempt_sweep()`/`_prune_spawn_attempts()`
  from PR head 335a0c8e against a copy of it, ledger reset first via
  `rm runs/reconcile_ledger.json` and `ledger_check_and_stamp`/
  `ledger_write` mocked to a clean state:
  ```
  POST-FIX: before: 431 watchdog lines tick1: 5 sweep count: 5
  POST-FIX: dropped: 0 after: 8
  remaining spawn_attempt per issue: {2500: 1, 2501: 1, 2600: 1, 2601: 1, 2602: 1}
  ```
  before=431, after=8; per-issue breakdown of what remains has no
  issue 31 or issue 7 key at all — both zeroed, matching the 305/114 →
  0/0 the implementation record claims. (`dropped: 0` on the explicit
  second `_prune_spawn_attempts()` call is expected, not a
  discrepancy: `spawn_attempt_sweep()` already prunes internally as
  its last step, per its own docstring, so nothing is left for the
  second, separate call to drop.)
rationale: |
  The requirement names a specific real file that is structurally
  unavailable in any git-based review environment (gitignored, and no
  live muster daemon has run in this fresh worktree to populate it) —
  independently reconfirmed above via `ls runs/`, not just taken on
  the builder's word. The code path that would operate on the real
  file (`SPAWN_ATTEMPTS_PATH` defaults to exactly
  `runs/spawn-attempts.jsonl`, 335a0c8e:spawn.py) is unchanged by the
  substitution; only the review evidence is synthetic. Present rather
  than Unverifiable because a same-shape, independently-reconstructed
  fixture (different pid, different attempt_id strings than the
  builder used) reproduces the exact claimed before/after counts from
  scratch — corroboration a cherry-picked or fabricated number would
  be unlikely to survive. Flagged under "Open findings" below for
  visibility, since the literal artifact named by the acceptance text
  was never directly measured by anyone in this review chain.
---
requirement: "A4 — the watchdog stops re-emitting the orphaned halts — before/after count of 'spawn halted pre-workspace' lines in one tick" [dimension: functional behavior]
spec_ref: issue #2413, Acceptance bullet 4
verdict: Present
evidence: |
  335a0c8e:roster.py:435-505 (`spawn_attempt_sweep`).

  derived: independent before/after run this session against the
  same from-scratch 431-line fixture described under A3. Pre-fix code,
  checked out at base commit `2ca4b4de` in a separate worktree
  (`/tmp/pre-fix-review`), ledger reset and mocked to a fresh state:
  ```
  PRE-FIX: watchdog lines tick1: 422 sweep count: 422
  PRE-FIX: dropped: 0 before: 427 after: 427
  ```
  (orphans kept forever, `dropped: 0` — the bug reproduced against
  base commit `2ca4b4de`, unmodified stock code, not a stub). Post-fix
  code at PR head `335a0c8e`, same fixture regenerated fresh, ledger
  reset:
  ```
  POST-FIX: before: 431 watchdog lines tick1: 5 sweep count: 5
  ```
  and a second `spawn_attempt_sweep()` call immediately after (same
  tick cadence) emitted 0 further lines (checked in this session's own
  run, not quoted from the builder's transcript).
rationale: |
  422→5 independently reproduced against a fixture this session built
  from scratch (different pid, different attempt_id shape than the
  builder's own script) matches the implementation record's claimed
  422→5 almost exactly — strong evidence the number is a real property
  of the code change, not a number picked to match the issue's
  filing-time count. Same file-availability caveat as A3 (real
  `runs/spawn-attempts.jsonl` independently confirmed absent in this
  environment too, see A3's `ls runs/` evidence).
---
requirement: "A5 — repeated identical lines for one attempt within a single tick are collapsed, or the record states why the repetition is correct" [dimension: edge-case]
spec_ref: issue #2413, Acceptance bullet 5
verdict: Present
evidence: |
  335a0c8e:roster.py:478 (`reported_subjects: set[str] = set()`,
  scoped to one `spawn_attempt_sweep()` call), 335a0c8e:roster.py:496-500
  (subject already reported this tick → `continue`, checked before the
  per-attempt_id ledger gate).

  canonical: `cd /tmp/pr2418-review && python3 -m pytest
  tests/test_watch_hardening.py -v` (this session) —
  `SpawnAttemptSweepDedup::test_many_attempt_ids_same_subject_prints_once_per_tick
  PASSED`.

  derived: same A3/A4 fixture — the printed-lines transcript quoted
  under A4 (`POST-FIX ... watchdog lines tick1: 5`) contains exactly
  one line for `issue-31/implementation` despite 305 distinct
  `attempt_id`s naming that subject in the fixture, and exactly one
  line for `issue-7/implementation` despite 114 distinct attempt_ids —
  visible directly in that transcript's line count (5 lines total
  covering 7 distinct subjects worth of records, not 424).
rationale: Both the independently re-run existing test and the independent fixture with hundreds of same-subject attempt_ids confirm at most one printed line per subject per tick.
---

## Open findings

1. **Residual PID-reuse risk in the liveness check (not a failure of
   any of the five acceptance checks above — a forward-looking note).**
   canonical: 335a0c8e:spawn.py:1002-1069, read this session.
   `_pid_is_alive()` checks OS pid existence via `os.kill(pid, 0)`, not
   process identity. If a dead attempt's pid number is later
   reassigned by the OS to an unrelated, long-running process,
   `_prune_spawn_attempts()` would read that pid as "alive" and keep
   the orphaned record forever (`if _pid_is_alive(pid) or not
   aged_out: keep` has no age ceiling on the alive branch) —
   recreating the exact "kept forever" pattern this issue was filed to
   fix, via a different mechanism (pid recycling) than the one this PR
   closes (unconditional `outcome is None` retention). This is a
   narrow window in practice (requires the OS to reuse a specific pid
   number before `SPAWN_ATTEMPTS_RETENTION_SEC`, 7 days, elapses) and
   is not contradicted by anything the issue's acceptance text asked
   for (which only requires "pid not running" as one liveness signal,
   not pid-reuse-proofing), so this is not scored against any of the
   five checks above — recorded here as a residual-risk note for
   whoever next touches this code, not as a defect in PR #2418.
   Resolution path: none required for issue #2413's acceptance to
   pass; a future fix (if ever warranted) would need to record and
   check a process-start-time or similar identity token alongside the
   pid, not just the pid number.

## Next steps

None. All five acceptance checks verdict Present, independently
re-derived this session (canonical tags under each finding above).
The CHANGES-round missing-`ts` fix (commit `bd3036dba9`) is
independently re-verified in finding A1a-2 — the gap the check-runner
flagged is closed, corroborated by an independently-authored repro,
not just the fix commit's own transcript.

canonical: this session's own run, `/tmp/pr2418-review2` worktree at
`bd3036dba9` — `python3 my_missing_ts_repro2.py /tmp/pr2418-review2` —
`dead pid +0y: dropped=1 remaining_lines=0` through `+10y` (all four
simulated ages dropped=1), `live pid +10y, missing ts: dropped=0
remaining_lines=1`; same script against `/tmp/pre-fix-review2` at
`335a0c8e` (this review's own prior pinned head) — `dead pid +0y..+10y:
dropped=0 remaining_lines=1` every time, confirming the gap existed at
the commit this record previously marked Present and is now closed at
`bd3036dba9`. Full transcript under finding A1a-2 above.

loop_state set to `reported` (terminal for a review-record).

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2413's bundled Acceptance bullet 1 (prune behavior + liveness-test-stated + bound-stated) into findings A1a/A1b/A1c per rule 1, and dimension-tagged all five findings.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; selected Demonstration (not Inspection/Analysis) for A2 per the requirement's own "demonstrated live... not asserted" wording, and reused the existing repo test suite as Test-method evidence for A1a/A2/A5 per rule 4 rather than re-deriving a parallel manual check.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present to A3/A4 rather than Unverifiable, reasoning through rule 3 (evidence "lives somewhere the review session cannot read") — concluded the literal file's absence is an environmental constraint independently confirmed (via `ls runs/` this session) rather than an inaccessible-to-this-reviewer-only gap, and that an independently-reconstructed matching fixture is sufficient corroboration.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited file:line ranges pinned to the PR head sha (335a0c8e4e8b8eff6b9997ce517d879f6b72f2f8) for every finding's evidence, and recorded roster.py and spawn.py as separate evidence lines per contributing file (rule 2) rather than one bundled citation.
skill-verdict: conformance-review-finding-record — applied: invoked; wrote the five `---`-delimited requirement blocks above with the full field list (requirement, spec_ref, verdict, evidence, rationale), sourced every verdict from this session's own artifact reads and independently-run reproductions rather than the builder's account.
other mounted skills: not triggered (conformance-review-sampling-derivation — full enumeration of all five acceptance bullets was feasible, no sampling needed; conformance-review-severity-classification — review scope was not extended into risk-weighting, and no finding here needed a severity band since all five checks verdict Present).

### Skill verdicts — CHANGES-round re-review (this turn)

canonical: this session's own run — `cd /tmp/pr2418-review2 && python3
-m pytest tests/test_watch_hardening.py -v` — `34 passed in 0.87s`,
including `SpawnAttemptPruneLiveness::test_missing_ts_with_dead_pid_is_pruned
PASSED` and
`SpawnAttemptPruneLiveness::test_missing_ts_with_live_pid_still_kept
PASSED`; and `python3 my_missing_ts_repro2.py /tmp/pr2418-review2` /
`python3 my_missing_ts_repro2.py /tmp/pre-fix-review2` transcripts
quoted in full under finding A1a-2 and under "## Next steps" above —
the basis for every skill-verdict line below.

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; treated the fix commit's own "34 passed" / "dropped=1 remaining=0" transcript in `bd3036db:docs/issue-2413/reports/implementation.md` as a claim to re-derive (rule 1), not a settled fact — built an independently-authored repro script (own attempt_id naming, own fork+reap dead-pid source, 4 simulated ages instead of the builder's 3) and deliberately added the live-pid-with-missing-`ts` negative case (rule 2) alongside re-running the builder's own two new tests independently rather than citing them.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; reused the two new `test_missing_ts_with_*` cases in `tests/test_watch_hardening.py` as Test-method evidence per rule 4, and additionally ran an independently-authored Demonstration (fresh worktree, fresh script) per rule 3 rather than trusting Test evidence alone for a requirement the original A1a finding had not exercised.
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present to the new A1a-2 finding as additional coverage rather than editing A1a's existing Present verdict, since A1a's original evidence (malformed/aged-numeric `ts`) was and remains correct — the missing-`ts` case is a distinct sub-case the CHANGES round introduced coverage for, not a correction of a prior wrong verdict (rule 5 — named the specific missing sub-case rather than a bare re-affirmation).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; cited the new evidence against the new head sha `bd3036dba91db953184f484bc9381eb8ed0b617f` (rule 1), and added a second `upstream:` frontmatter entry for `implementation.md` pinned to that sha alongside the original 335a0c8e-pinned entries rather than overwriting them (preserves both review passes' basis shas).
skill-verdict: conformance-review-finding-record — applied: invoked; wrote finding A1a-2 as a new `---`-delimited block with the full field list (requirement, spec_ref, verdict, evidence, rationale) rather than mutating A1a's existing block, per finding-record's dispute/re-examination guidance to record re-examination inline rather than silently editing a prior entry.

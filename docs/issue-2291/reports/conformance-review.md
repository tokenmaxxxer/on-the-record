---
issue: 2291
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: spawn.py
    sha: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d
  - path: roster.py
    sha: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d
  - path: watchdog.py
    sha: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d
  - path: board.py
    sha: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d
subject: PR #2366 (issue-2291, durable spawn-attempt trace + watchdog pre-workspace halt visibility), head commit 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d, base main d27977b77c10c9515a11c9a4a86cc0c3dda16d84
test: issue #2291 `## Ask` (3 bullets), `## Acceptance` (gate/empty-state/provenance), and its Frozen constraint paragraph
result: failed
assertedBy: conformance-review (issue-2291/conformance-review session, builder-blind)
---

# issue-2291 — conformance-review record

## What was done

Builder-blind conformance review of PR #2366 against issue #2291's own
`## Ask`/`## Acceptance` text and Frozen constraint. Independent of PR
#2366's own claims: this session read the diff and the code directly on
a fresh `git worktree` of PR #2366's head (3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d),
derived its own requirement list from the issue text, chose a
verification method per requirement, and re-executed every acceptance
check itself (own scratch paths, own synthetic issue number 31337,
distinct from the implementation record's 538 and PR #2362's 777)
before reading the builder's own record for comparison.

canonical: `gh pr view 2366 --json title,body,additions,deletions` (this
session) — title "issue-2291: durable spawn-attempt trace + watchdog
pre-workspace halt visibility", 697 additions / 70 deletions, files
`spawn.py`, `roster.py`, `watchdog.py`,
`tests/_spawn_test_support.py`, `tests/test_spawn_pipeline.py`,
`docs/issue-2291/reports/implementation.md` (untracked on this record's
own branch — see below), `docs/reports/deviation-log.md`.

**Result: `failed` (12, derived: counted directly from the 12
`---`-delimited blocks in `## Findings` below, requirements R1-R12).**
Summary: R1, R3, R5, R6, R9, R10, R11, R12 `Present`; R2, R4 `Incorrect`;
R7, R8 `Surface`.

**Process context, not itself a requirement verdict:** PR #2366's own
record states it read prior review PR #2365's terminal state but not
its finding content before porting the identical mechanism from PR
#2305.

canonical: PR #2366 head commit 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d,
`docs/issue-2291/reports/implementation.md` (untracked on this record's
own branch `issue-2291/conformance-review`, which is based on `main` —
that file exists only on the PR #2366 branch; read via `git show
pr-2366:docs/issue-2291/reports/implementation.md`, this session), "##
Why" section: "Neither this session nor the cited PR bodies were
re-read line-by-line for defects beyond their title/state (out of scope
for this redelivery...)". `gh pr view 2365 --json state,title` (this
session) — result: state `CLOSED`, title "issue-2291: builder-blind
conformance review of PR #2305". The R1/R3 `Incorrect` finding PR #2365
recorded against the identical, unchanged mechanism is independently
re-derived in this record as R2/R4 below (not carried forward from
#2365's record by citation — re-checked live against #2366's own code,
per finding-record checklist item "the verdict came from looking at the
artifact, not the builder's account").

## Why

Builder-blind method, applied in this order: (1) extracted a checkable
requirement list from issue #2291's own text before reading PR #2366's
diff in full; (2) picked a verification method per requirement (Test for
the gate, Demonstration with this session's own scratch fixtures for
empty-state/provenance, Inspection for structural placement claims,
Analysis plus a live reproduction for the pre-existing-gates ordering
question); (3) rendered a verdict per requirement from evidence located
in this session; (4) only then read `docs/issue-2291/reports/implementation.md`
(untracked on this branch, read via `git show pr-2366:...`, this
session) to check for undisclosed deviations from the issue.

Full enumeration of issue #2291's Ask/Acceptance was feasible at this
scope — derived: `gh pr view 2366 --json files` (this session) listed 7
changed files, and the Ask names exactly 2 mechanisms — so no sampling
was required; see `conformance-review-sampling-derivation` skill-verdict
below.

## Upstream basis

`docs/issue-2291/reports/implementation.md` — present on PR #2366's own
branch (commit 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d), untracked on
this record's own branch (`issue-2291/conformance-review`, based on
`main`) — is the claimed delivery this review checks; read via `git show
pr-2366:docs/issue-2291/reports/implementation.md`, this session. Prior
art consulted for context only, not trusted as evidence for this PR's
own verdicts (different commits than #2366's head):

canonical: `gh pr view 2305 --json state,mergedAt` (this session) —
result `{"mergedAt":null,"state":"CLOSED"}`; `gh pr view 2362 --json
state,mergedAt` (this session) — result
`{"mergedAt":"2026-08-25T05:26:26Z","state":"MERGED"}`; `gh pr view 2365
--json state,mergedAt` (this session) — result
`{"mergedAt":null,"state":"CLOSED"}`.

## Findings (R1-R12)

---
requirement: Append a durable spawn-attempt record (issue, role, pid,
  ts) to a STATE_ROOT-scoped location, never the target repo.
spec_ref: issue-2291 `## Ask` bullet 1, clause 1 ("append a spawn-attempt
  record (issue, role, pid, ts) to an orchestrator-scoped location
  (STATE_ROOT per #2240 — never the target repo)"); Frozen constraint
  clause 3 ("nothing written into the consumer's tree") collapsed into
  this one entry per traceability rule 4 (same evidence location).
verdict: Present
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:861
  (`SPAWN_ATTEMPTS_PATH = STATE_ROOT / "spawn-attempts.jsonl"`),
  3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:545-546 (`STATE_ROOT`
  anchored to `MUSTER_STATE_ROOT` or `ROOT / "runs"`, never `a.cwd`),
  3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:870-887
  (`_record_spawn_attempt`, fields issue/role/pid/ts).
rationale: The trace path cannot resolve inside a caller-supplied target
  repo; independently confirmed live (see the provenance reproduction
  under R12 below, whose STEP4 `git status --porcelain` in the scratch
  target-repo clone showed no output).
canonical: source lines above, read directly in this session's `git
  worktree` of PR #2366 head, this session.

---
requirement: The spawn-attempt record is appended before any network or
  workspace work.
spec_ref: issue-2291 `## Ask` bullet 1, clause 1 ("before any network or
  workspace work, append a spawn-attempt record...")
verdict: Incorrect
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:1619
  (`require_board`), :1622 (`require_no_repo_config`), :1623
  (`require_acceptance_gate`), :1624 (`require_requirement_linkage`) —
  all four execute before `_record_spawn_attempt()` at :1652-1653.
  3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:board.py:295-351
  (`require_acceptance_gate`, `sys.exit` at :344, calls `gh api` via
  `gates/ci.py`/`gates/acceptance_gate.py`) and :352-410
  (`require_requirement_linkage`, `sys.exit` at :393, calls `gh api` via
  `gates/requirement_linkage.py`).
rationale: A halt inside either network-calling gate necessarily
  precedes attempt-record creation, so the record is not created before
  all network work — it is created after two of the four pre-existing
  gates have already run and could already have halted.
spec_vs_built: Spec requires the durable record before any network or
  workspace work in the spawn path. Built: the record is created only
  after `require_board`/`require_no_repo_config`/
  `require_acceptance_gate`/`require_requirement_linkage` have already
  run — the latter two already having made a `gh api` call and being
  capable of halting first.
canonical: source lines above, read in this session's `git worktree` of
  PR #2366 head; live reproduction confirming this ordering is real
  (not merely line-order coincidence) is under R4 below.

---
requirement: Append the outcome (halt reason or session-log path) when
  known.
spec_ref: issue-2291 `## Ask` bullet 1, clause 2
verdict: Present
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:892-903
  (`_record_spawn_outcome`), called with `"halted"` + reason at
  :1683-1687 (inside the `except (SystemExit, Exception)` wrapping
  `require_doctor()`.._spawn_one()`), and with `"session-log"` + the
  live-log path at :3079.
rationale: Both outcome kinds have a real call site firing at the point
  each becomes known, for the window this PR's `try/except` actually
  wraps (see R4 for the earlier window it does not wrap).
canonical: source lines above, read in this session's `git worktree` of
  PR #2366 head; independently exercised live under R10/R12 below.

---
requirement: Every `_fetch_or_halt`-class halt (issue's own
  generalization — read together with its root-cause framing — covers
  the whole pre-log bootstrap window, not literally only the one named
  function) must land its reason in the durable trace even when stdout
  is swallowed.
spec_ref: issue-2291 `## Ask` bullet 1, clause 3, read with the issue's
  own "## Consumer report" framing ("`_fetch_or_halt()`... and the rest
  of workspace preparation run before the session log... exist")
verdict: Incorrect
evidence: 'This session, own scratch dir, synthetic issue 99001,
  `MUSTER_STATE_ROOT=/tmp/otr-2366review-state/linkage`, `gates/ci.py`''s
  `_approved_roles_on_issue` and `gates/requirement_linkage.py`''s
  `check` monkeypatched to force the same `bad`-list branch
  `board.py:352-410` takes in production:'
acceptance: 'python3 -c "board.require_requirement_linkage(''.'', 99001)"
  against a monkeypatched `gates.requirement_linkage.check` — result:'
```
SystemExit raised by require_requirement_linkage (spawn.py:1624 call site, board.py:393 sys.exit) — BEFORE _record_spawn_attempt at spawn.py:1652:
  이슈 #99001 가 요구 연결이 없다:
  - 이슈 #99001 본문이 요구 ID를 인용하지 않는다 (synthetic, this review's own monkeypatch)
  세션을 안 띄운다 — 요구 ID(`R\d+` 또는 'northpole req#<n>')를 인용하거나 'infrastructure/no-direct-requirement' 태그를 달아야 한다(issue #1017, northpole req#6).
  R-ID 목록은 docs/specs/requirement-digest.md 에 있다(없으면 `spawn.py init` 이 스텁을 만든다).
  예시 — 이슈 본문에 이런 한 줄이면 된다: Targets R1.
  'infrastructure/no-direct-requirement' 태그는 이슈가 어떤 제품 요구에도 직접 닿지 않는 순수 기반 작업(빌드·CI·게이트·리팩터링 등)일 때만 적절하다.
spawn-attempts.jsonl existed before this halt: False / after: False
```
rationale: The durable trace file was never created by this halt (`False
  / False` above) — a halt from `require_requirement_linkage` (or the
  other three gates at the same ordering) produces zero bytes anywhere,
  reproducing live the exact swallowed-stdout/zero-trace failure class
  issue #2291 was filed to fix.
spec_vs_built: Spec requires every fail-closed halt in the pre-log
  bootstrap window to land its reason durably. Built: only halts from
  `require_doctor()` onward (spawn.py:1654-1688) are caught and
  recorded; a halt from any of the four gates at spawn.py:1619-1624 is
  outside any try/except that knows `attempt_id` and leaves no trace at
  all, confirmed by direct execution above.
canonical: reproduction command and raw output pasted verbatim above,
  this session, this turn.

---
requirement: A spawn-attempt record with no matching roster entry after
  a grace period is a reportable state.
spec_ref: issue-2291 `## Ask` bullet 2, clause 1
verdict: Present
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:roster.py:432
  (`SPAWN_ATTEMPT_GRACE_SEC = 180 + 60 + 60`), :435-493
  (`spawn_attempt_sweep`) — an attempt with no recorded outcome becomes
  reportable once `now - ts >= SPAWN_ATTEMPT_GRACE_SEC` and no roster
  entry exists for `lease_key(issue, role)`; a `"halted"` outcome is
  reportable immediately, ungated by the grace period.
rationale: Both named triggers (a recorded halt, or grace-period elapsed
  with no roster match) are wired to the same reportable branch.
canonical: source lines above, read in this session's `git worktree` of
  PR #2366 head, this session; exercised live under R6/R10/R12.

---
requirement: The watchdog surfaces "spawn halted pre-workspace:
  <reason>" for an unresolved spawn attempt, rather than silently having
  nothing to report (or misleadingly surfacing an unrelated entry as
  HEALTHY).
spec_ref: issue-2291 `## Ask` bullet 2, clause 2
verdict: Present
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:roster.py:483
  (`print(f"[spawn-attempt] {subject}: spawn halted pre-workspace:
  {reason}")`), 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:watchdog.py:1486
  (`anomaly_count += _sp.spawn_attempt_sweep(d_all=d_all)`) called
  unconditionally right after `lease_reconcile_sweep` (:1482) and
  strictly before the `if not d:` early return (:1517), so an empty
  roster never skips this sweep.
acceptance: 'MUSTER_STATE_ROOT=<scratch>/state/halt
  SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py watchdog -C .
  (this session''s own scratch state root, synthetic issue 31337) —
  result:'
```
[spawn-attempt] issue-31337/implementation: spawn halted pre-workspace: 신규 워크스페이스: fetch 실패 — fatal: '/no/such/otr-review-remote-xyz' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
돌고 있는 역할 세션 없음
```
rationale: The sweep is unconditional (runs before any roster-empty
  early return) and this session's own live watchdog tick, against its
  own scratch state root and synthetic issue number, surfaced exactly
  the named message shape.
canonical: source lines and reproduction output above, this session,
  this turn.

---
requirement: Systemic for all consumer sessions.
spec_ref: issue-2291 Frozen constraint, clause 1
verdict: Surface
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:1652-1653
  (`attempt_id = (_record_spawn_attempt(...) if a.issue is not None else
  None)`) — the entire mechanism (R1-R6) is gated on `a.issue is not
  None`.
rationale: An ad-hoc consumer spawn (`spawn.py <role> "<task>"`, no
  `--issue`) receives no durable trace and no watchdog visibility at
  all. The mechanism is correct for issue-scoped spawns (its own
  in-code comment reasons that ad-hoc spawns never register in the
  roster, so there is nothing to sweep against), but "systemic for all
  consumer sessions" as literally stated is not met.
canonical: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:spawn.py:1650-1651
  (in-code comment stating this exclusion), read in this session's `git
  worktree` of PR #2366 head, this session; issue #2291's own first
  comment (`gh issue view 2291 --comments`, this session) — the
  originally-reported incident (issue-538 spawn) was itself an ad-hoc,
  `--issue`-less spawn, per the reporter's own correction.

---
requirement: No added overhead/conflict/stall surfaces.
spec_ref: issue-2291 Frozen constraint, clause 2
verdict: Surface
evidence: 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d:roster.py:905-919
  (`_load_spawn_attempts` reads and parses the entire
  `spawn-attempts.jsonl` on every call) and :435-493
  (`spawn_attempt_sweep`, called every watchdog tick per
  watchdog.py:1486) — no pruning, rotation, or size cap exists anywhere
  in the diff. Append-only writes use the existing `open(..., "a")`
  pattern (spawn.py:864-868), no new locking added.
rationale: No new locking/blocking surface was added, but a concrete
  unbounded-growth mechanism exists with no stated numeric threshold in
  the issue to check it against.
canonical: source lines above, read in this session's `git worktree` of
  PR #2366 head, this session; `gh pr view 2365 --json body` (this
  session) — PR #2365's own body flagged the identical, unbounded-growth
  mechanism against #2305 (there labelled R6, non-blocking); #2366 ports
  the same mechanism unchanged, confirmed by the absence of any
  pruning/rotation code in the source lines cited above.

---
requirement: 'Gate: `tests/test_spawn_pipeline.py` passes.'
spec_ref: issue-2291 `## Acceptance`, "gate" line
verdict: Present
evidence: independently rerun this session, isolated `git worktree` of
  PR #2366 head (3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d)
acceptance: 'python3 -m pytest tests/test_spawn_pipeline.py -q (this
  session, `/tmp/wt-2366`) — result:'
```
bringing up nodes...
........................................................................ [ 83%]
..............                                                          [100%]
86 passed in 9.28s
```
acceptance: 'python3 -m pytest tests/test_state_root_scoping.py
  tests/test_watch_hardening.py test/test_roster_role_field.py
  tests/test_standing_red_watch.py tests/test_poll_watchdog_log.py
  tests/test_spawn_pipeline.py -q (this session, `/tmp/wt-2366`) —
  result:'
```
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                       [100%]
145 passed in 1.42s
```
rationale: Both counts independently rerun this session (not taken from
  the PR's own pasted output) — 86 and 145 respectively, matching the
  PR's own claimed counts.
canonical: raw pytest output pasted verbatim above, this session, this
  turn.

---
requirement: 'Empty state: a successful spawn — the attempt record gains
  its session-log path.'
spec_ref: issue-2291 `## Acceptance`, "empty state" clause 1
verdict: Present
evidence: this session's own scratch `MUSTER_STATE_ROOT`, synthetic
  issue 31337 (distinct from the implementation record's 538 and PR
  #2362's 777)
acceptance: 'MUSTER_STATE_ROOT=<scratch>/state/empty python3 -c
  "spawn._record_spawn_attempt(31337, ...); spawn._record_spawn_outcome(attempt_id,
  ''session-log'', ...); roster.spawn_attempt_sweep(d_all={},
  now=time.time())" (this session) — result:'
```
empty-state anomaly count (expect 0): 0
```
rationale: The outcome-write call for the success path exists and was
  independently exercised, distinct scratch/synthetic-id from every
  prior session's reproduction.
canonical: raw output pasted verbatim above, this session, this turn.

---
requirement: 'Empty state: a successful spawn — the watchdog reports
  nothing new.'
spec_ref: issue-2291 `## Acceptance`, "empty state" clause 2
verdict: Present
evidence: same reproduction as the entry immediately above
rationale: roster.py's sweep explicitly `continue`s (skips reporting)
  for any outcome other than `"halted"` (roster.py:472-473,
  3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d); the independent live run
  above confirms zero anomalies (`empty-state anomaly count (expect 0):
  0`) for a successful spawn.
canonical: source line and reproduction output above (same fence as R10),
  this session, this turn.

---
requirement: 'Provenance (executed-live): force a real `_fetch_or_halt`
  halt against an unreachable remote, with spawn stdout piped through
  `tail` exactly as the consumer''s report describes; show the halt
  reason present in the durable trace despite the pipe, and the
  watchdog''s next tick naming the pre-workspace halt.'
spec_ref: issue-2291 `## Acceptance`, "provenance" clause
verdict: Present
evidence: this session's own scratch clone
  (`/tmp/otr-2366review-clone`, `git remote add origin
  /no/such/otr-review-remote-xyz`), own scratch `MUSTER_STATE_ROOT`
  (`/tmp/otr-2366review-state/halt`), synthetic issue 31337
acceptance: 'python3 -c "spawn._record_spawn_attempt(31337, ...);
  pipeline._fetch_or_halt(''.'', ''신규 워크스페이스'')" 2>&1 | tail -15
  (this session, own scratch clone) — result:'
```
### consumer-equivalent halt, piped through tail ###
```
acceptance: 'cat <scratch>/state/halt/spawn-attempts.jsonl (this
  session, immediately after the piped halt above) — result:'
```
{"event": "spawn_attempt", "attempt_id": "31337:implementation:995669:1787641534807", "issue": 31337, "role": "implementation", "pid": 995669, "ts": 1787641534.8071394}
{"event": "spawn_attempt_outcome", "attempt_id": "31337:implementation:995669:1787641534807", "outcome": "halted", "detail": "신규 워크스페이스: fetch 실패 — fatal: '/no/such/otr-review-remote-xyz' does not appear to be a git repository\nfatal: 리모트 저장소에서 읽을 수 없습니다\n\n올바른 접근 권한이 있는지, 그리고 저장소가 있는지\n확인하십시오.", "ts": 1787641534.829702}
```
acceptance: 'MUSTER_STATE_ROOT=<scratch>/state/halt
  SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1 python3 spawn.py watchdog -C .
  (this session, same scratch clone/state root) — result:'
```
[spawn-attempt] issue-31337/implementation: spawn halted pre-workspace: 신규 워크스페이스: fetch 실패 — fatal: '/no/such/otr-review-remote-xyz' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
돌고 있는 역할 세션 없음
```
acceptance: 'git status --porcelain (this session, in the scratch
  target-repo clone, immediately after the reproduction above) —
  result:'
```
(no output)
```
rationale: End-to-end reproduced this session with its own scratch
  paths and synthetic issue number — not a replay of the PR's own 538
  demo or PR #2362's 777 demo — for the window this PR's `try/except`
  actually wraps (`require_doctor()` onward; see R4 for the earlier
  window it does not wrap).
canonical: raw output pasted verbatim above, this session, this turn.

## Open findings

1. **R2/R4 `Incorrect`** — the four pre-existing phase gates
   (`require_board`, `require_no_repo_config`, `require_acceptance_gate`,
   `require_requirement_linkage`, spawn.py:1619-1624) run before
   `_record_spawn_attempt()` (spawn.py:1652), and two of them can
   `sys.exit()` after a real `gh api` call — a halt there is exactly as
   traceless as the failure issue #2291 was filed to fix, one layer
   earlier than the window PR #2366 instruments. This is the identical,
   unaddressed defect PR #2365 already recorded (as R1/R3) against the
   unchanged mechanism in PR #2305 — resolution path: move
   `_record_spawn_attempt()` to the very top of `main()`'s non-dry-run
   path (before spawn.py:1619) and wrap `require_board()` through
   `require_requirement_linkage()` in the same
   `try/except (SystemExit, Exception)` already used for
   `require_doctor()`/`ensure_target_remote()`/`_spawn_one()`
   (spawn.py:1654-1688).
2. **R7 `Surface`**, non-blocking on its own but compounds finding 1 —
   ad-hoc (`--issue`-less) consumer spawns get no durable trace or
   watchdog visibility at all, and were the actual shape of the incident
   that first prompted this issue (issue #2291's own first comment).
   Resolution path: a future issue amendment scoping whether ad-hoc
   spawns should also get a (necessarily roster-less) durable trace, or
   an explicit narrowing of "all consumer sessions" to "all
   `--issue`-scoped consumer sessions" in issue #2291's own text.
3. **R8 `Surface`**, non-blocking — `spawn-attempts.jsonl` has no
   pruning/rotation; every watchdog tick reads/parses the whole file.
   Same gap PR #2365 flagged against #2305, carried forward unaddressed
   in #2366. Resolution path: prune once an entry's outcome has been
   swept and reported once, or cap/rotate the file.
4. **Process gap, not itself a requirement verdict**: PR #2366's own
   record documents reading PR #2365's terminal state but not its
   finding content before porting the identical mechanism — the R1/R3
   defect this record reconfirms as R2/R4 was therefore never carried
   forward into this redelivery. Resolution path: a redelivery that
   explicitly supersedes a design already subject to a prior conformance
   review should read that review's findings, not only its PR state,
   before re-porting the same mechanism.

## Next steps

None — `loop_state: reported` (terminal for `review-record`). The four
open findings above are for whichever session next takes up issue #2291
(or a follow-up issue) to resolve; this record's own verdicts stand as
delivered.

## skill-verdict

skill-verdict: conformance-review-requirement-extraction — applied:
  invoked; used to split issue #2291's `## Ask`/`## Acceptance`/Frozen
  constraint prose into the requirement list in `## Findings` above
  (count and derivation already stated under "What was done") — rule 1:
  split "before any network..." and "every halt..." into separate
  R2/R4; rule 3: dropped Acceptance's "paste real output of both" as a
  summary line restating R11/R12's own sub-points; rule 6:
  dimension-tagged each item, folded into the spec_ref/rationale text
  above.
skill-verdict: conformance-review-sampling-derivation — not-applicable:
  full enumeration of both issue #2291 mechanisms and all 7 changed
  files was feasible at this scope; no sampling scope was derived.
skill-verdict: conformance-review-verification-method-selection —
  applied: invoked; Test method reused for the gate (rerunning
  `tests/test_spawn_pipeline.py`), Demonstration for empty-state/
  provenance (own live scratch reproductions), Inspection for
  structural claims (STATE_ROOT placement, watchdog call ordering),
  Analysis plus a live reproduction for the pre-existing-gates ordering
  defect — canonical: traced spawn.py:1619-1652 (this session's `git
  worktree` of PR #2366 head), confirmed via the monkeypatched
  `require_requirement_linkage` call under R4 above.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
  Surface (not Present) for R7/R8 where the mechanism exists but does
  not fully satisfy the named condition; Incorrect (not Absent) for
  R2/R4 where the artifact actively contradicts "before any network
  work" rather than merely omitting the trace; re-checked the R2/R4
  evidence once via a live reproduction (rule 6) before finalizing;
  no finding above was carried forward from PR #2365's record by
  citation alone (different commit/PR) — every finding was
  independently re-derived against #2366's own code this session.
skill-verdict: conformance-review-traceability-and-evidence — applied:
  invoked; every verdict above cites file:line plus the commit sha
  actually read (3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d); R1 collapses
  the Ask-bullet-1 STATE_ROOT clause and the Frozen-constraint
  "nothing written into the consumer's tree" clause into one entry per
  rule 4 (same evidence location); backward-traced each requirement's
  source line to issue #2291's own text (quoted inline in `spec_ref`)
  before checking its implementation, per rule 3.
skill-verdict: conformance-review-finding-record — applied: invoked;
  every Present/Surface/Incorrect verdict above carries both an
  `evidence` pointer and a `spec_ref`; `spec_vs_built` filled for both
  `Incorrect` entries (R2, R4); no verdict rendered without a citable
  evidence pointer.
skill-verdict: conformance-review-severity-classification —
  not-applicable: this review's scope was not explicitly extended into
  risk-weighting the findings above; severity is not assigned.

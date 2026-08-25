---
issue: 2291
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: spawn.py
    sha: 300a07249b9032fe56ef684f2a2e86374a681c2a
  - path: roster.py
    sha: 300a07249b9032fe56ef684f2a2e86374a681c2a
  - path: watchdog.py
    sha: 300a07249b9032fe56ef684f2a2e86374a681c2a
  - path: board.py
    sha: 300a07249b9032fe56ef684f2a2e86374a681c2a
subject: PR #2366 (issue-2291, durable spawn-attempt trace + watchdog pre-workspace halt visibility), re-review round after CHANGES-round fix commit 300a07249b9032fe56ef684f2a2e86374a681c2a (prior reviewed head 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d, this record's own PR #2371, MERGED), base main 46da1c8a199048b380c363a936e92bca1c7c5393
test: this record's own prior R2/R4 `Incorrect` findings (PR #2371), re-derived independently against PR #2366's fix commit rather than cited
result: failed
assertedBy: conformance-review (issue-2291/conformance-review session, builder-blind re-verification of R2/R4 only; R1/R3/R5/R6/R9-R12 carried forward per verdict-assignment rule 4, evidence unchanged by this commit)
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
Summary (post-CHANGES-round-fix, this round): R1-R6, R9-R12 `Present`
(R2/R4 corrected from round 1's `Incorrect` — see `## CHANGES round`
below); R7, R8 `Surface`, unchanged and still open — `result` stays
`failed` per this repo's own convention (Surface findings, not only
Incorrect ones, keep a record `failed`; derived: `grep -c "^verdict:
Surface" docs/*/reports/conformance-review.md` across this repo's
records this session showed every record with ≥1 `Surface` verdict
also carries `result: failed`, none `passed`).

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

## CHANGES round — re-review of R2/R4 after PR #2366's fix

This record's own PR #2371 (the round above, reviewed head
3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d) merged with `result: failed`
on R2/R4 `Incorrect` plus R7/R8 `Surface`. PR #2366 then took a
CHANGES-round fix, commit
300a07249b9032fe56ef684f2a2e86374a681c2a ("issue-2291: CHANGES-round
fix — record spawn attempt before phase gates (#2371 R2/R4)"): moved
`_record_spawn_attempt()` to the top of `main()`'s non-dry-run branch
and moved all four gate calls (`require_board`,
`require_no_repo_config`, `require_acceptance_gate`,
`require_requirement_linkage`) inside the same
`try/except (SystemExit, Exception)` already wrapping
`require_doctor()`/`ensure_target_remote()`/`_spawn_one()`.

canonical: `gh pr view 2366 --json headRefOid` (this session) — result
`300a07249b9032fe56ef684f2a2e86374a681c2a`; `git show 300a0724 --stat`
(this session, `git worktree` at `/tmp/wt-2366b`) — 2 files changed,
`docs/issue-2291/reports/implementation.md` (present on PR #2366's own
branch, untracked on this record's own branch, same situation as `##
Upstream basis` above) and `spawn.py` (36 insertions, 15 deletions).

Per `defect-verification-independence-from-upstream-verdicts` rule 1 (a
prior verdict — including this record's own round-1 verdict — is a
claim to re-test, not a settled fact) and rule 3 (re-derive rather than
cite against a stale sha): this round re-derived R2 and R4 directly
against the fix commit's own code and three fresh live reproductions in
a fresh `git worktree` of PR #2366's new head, rather than citing the
fix commit's message or the builder's own CHANGES-round narrative in
`docs/issue-2291/reports/implementation.md` (untracked on this
record's own branch, same as above) as evidence.

canonical: `MUSTER_STATE_ROOT=/tmp/otr-2371review-state/linkage`
(own scratch state root, this session), three fresh synthetic issue
numbers (77002, 88003, 99009) chosen ad hoc for the three
reproductions below — derived: none collide with round 1's own issue
numbers (`grep -oE "3[0-9]{4}|9[0-9]{3}" docs/issue-2291/reports/conformance-review.md`
against this file's own round-1 text above, this session) or the
untracked `docs/issue-2291/reports/implementation.md`'s issue numbers
(as above, read via `git show pr-2366:...`, this session), confirmed
before choosing them.

Per rule 2 (deliberately include an edge case/negative path, not only
the path the fix commit's own repro covers): the fix commit's own
evidence exercises only a halt from `require_requirement_linkage` (a
`gh api`-backed gate — the same one round 1's R4 reproduction used).
This round additionally forced a halt from `require_board` — the
*first* gate in the chain, purely local, no network call — to confirm
the durable record now precedes the earliest possible halt point, not
only the `gh api`-backed gates R2/R4 originally named. This round also
re-confirmed `--dry-run` remains unaffected (no attempt record
written), since `--dry-run` never spawns a session and was never in
R2/R4's own scope.

canonical: reproduction commands and raw output pasted verbatim in the
updated R2/R4 finding blocks below, this session, this turn.

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
verdict: Present
evidence: 300a07249b9032fe56ef684f2a2e86374a681c2a:spawn.py:1658-1659
  (`attempt_id = (_record_spawn_attempt(...) if a.issue is not None else
  None)`) now precedes the `try:` block at :1660 that wraps
  `require_board()` (:1661), `require_no_repo_config()` (:1662),
  `require_acceptance_gate()` (:1663), `require_requirement_linkage()`
  (:1664), `require_doctor()` (:1665), and `ensure_target_remote()`
  (:1666) — all six now run after the attempt record, inside the same
  `try/except (SystemExit, Exception)` at :1686. Diff:
  `git show 300a0724 -- spawn.py` (this session) — the pre-fix ordering
  (round-1 R2/R4's own evidence, `require_board` through
  `require_requirement_linkage` before `_record_spawn_attempt()`) is
  replaced with attempt-record-first.
rationale: Independently re-verified this session, not cited from the
  fix commit's message: an end-to-end `spawn.main()` invocation forced
  through `require_board` — the first gate, purely local, no network
  call — with no `docs/specs/approvers.md` marker in the target repo,
  showed the attempt record exists (`before main(): False` /
  `after halt, file exists: True`) even though the halting gate is the
  very first line of the non-dry-run branch and makes no network call
  at all — a stronger confirmation than the fix commit's own repro
  (which only exercised the `gh api`-backed
  `require_requirement_linkage`). `--dry-run` re-confirmed unaffected
  (own copy of the four gates outside the attempt-record path,
  `spawn.py:1617-1626`, no attempt file written).
spec_vs_built: Spec required the durable record before any network or
  workspace work. Pre-fix built: record created only after two
  `gh api`-backed gates had already run (round-1 finding). Post-fix
  built: record now created before all four contract gates and before
  `require_doctor()`/`ensure_target_remote()` — matches the spec
  clause; this record's own round-1 `Incorrect` verdict against this
  same requirement is superseded, not silently dropped (see `## CHANGES
  round` above and `## Open findings` below).
canonical: `git show 300a0724 -- spawn.py` (this session,
  `/tmp/wt-2366b`); end-to-end reproduction command and raw output
  pasted verbatim under R4 below (same reproduction covers both R2 and
  R4 — one live spawn.main() invocation demonstrates both the ordering,
  R2, and the durable capture, R4).

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
verdict: Present
evidence: 'This session, own scratch clone/state root, three fresh
  synthetic issue numbers (own choice this round, distinct from every
  prior round''s — see `## CHANGES round` above), fix commit
  300a07249b9032fe56ef684f2a2e86374a681c2a, two independent end-to-end
  `spawn.main()` invocations (not a monkeypatched direct gate call like
  round 1''s R4 reproduction — this round drives the real CLI entry
  point):'
acceptance: 'Reproduction 1 — `require_requirement_linkage` halt
  (`gh api`-backed gate, the same one the fix commit''s own repro
  covers), `gates.requirement_linkage.check` and
  `gates.ci._approved_roles_on_issue` monkeypatched to force the halt
  branch, `MUSTER_STATE_ROOT=/tmp/otr-2371review-state/linkage`, issue
  88003, target repo `/tmp/otr-2371review-repo` (fresh scratch git
  init, `docs/specs/approvers.md` present so `require_board` passes and
  the halt is isolated to `require_requirement_linkage`) — `spawn.main()`
  invoked directly with `sys.argv` set, this session — result:'
```
before main(): False
main() raised SystemExit as expected: '이슈 #88003 가 요구 연결이 없다:\n  - 이슈 #88003 가 요구 연결이 없다 (synthetic, end-to-end main() re-verify)\n  세션을 안 띄운다 — 요구 ID(`R\\d+`
after main() halt, file exists: True
{"event": "spawn_attempt", "attempt_id": "88003:implementation:3150871:1787644748905", "issue": 88003, "role": "implementation", "pid": 3150871, "ts": 1787644748.905134}
{"event": "spawn_attempt_outcome", "attempt_id": "88003:implementation:3150871:1787644748905", "outcome": "halted", "detail": "이슈 #88003 가 요구 연결이 없다:\n  - 이슈 #88003 가 요구 연결이 없다 (synthetic, end-to-end main() re-verify)\n  세션을 안 띄운다 — 요구 ID(`R\\d+` 또는 'northpole req#<n>')를 인용하거나 'infrastructure/no-direct-requirement' 태그를 달아야 한다(issue #1017, northpole req#6).\n  R-ID 목록은 docs/specs/requirement-digest.md 에 있다(없으면 `spawn.py init` 이 스텁을 만든다).\n  예시 — 이슈 본문에 이런 한 줄이면 된다: Targets R1.\n  'infrastructure/no-direct-requirement' 태그는 이슈가 어떤 제품 요구에도 직접 닿지 않는 순수 기반 작업(빌드·CI·게이트·리팩터링 등)일 때만 적절하다.", "ts": 1787644748.9079735}
```
acceptance: 'Reproduction 2 — `require_board` halt (the *first* gate,
  purely local, no `gh api`/network call — an edge case the fix
  commit''s own repro did not cover, added this round per
  `defect-verification-independence-from-upstream-verdicts` rule 2),
  fresh scratch git-init target repo with no
  `docs/specs/approvers.md`, issue 99009, same state root — `spawn.main()`
  invoked directly, this session — result:'
```
before main(): False
main() raised SystemExit (require_board, no approvers.md, no network): '대상 레포에 docs/specs/approvers.md 가 없다: /tmp/otr-2371review-repo2\n  이 파일이 보드 opt-in 이자 승인자 allowlist 
after halt, file exists: True
{"event": "spawn_attempt", "attempt_id": "99009:implementation:3164907:1787644858375", "issue": 99009, "role": "implementation", "pid": 3164907, "ts": 1787644858.375075}
{"event": "spawn_attempt_outcome", "attempt_id": "99009:implementation:3164907:1787644858375", "outcome": "halted", "detail": "대상 레포에 docs/specs/approvers.md 가 없다: /tmp/otr-2371review-repo2\n  이 파일이 보드 opt-in 이자 승인자 allowlist 다. 만들려면:\n    python3 spawn.py init -C /tmp/otr-2371review-repo2\n  보드를 안 쓸 작업이면 --no-contract 로 건너뛴다.", "ts": 1787644858.375198}
```
acceptance: '`--dry-run` regression check (same target repo/state root
  as Reproduction 2, issue 99009) — result:'
```
attempts file exists after dry-run: NO
```
rationale: Both reproductions show the durable trace file created
  (`before main(): False` / `after..., file exists: True`) *before* the
  halting gate ever ran, for gates spanning the full range named in
  round 1's R2 evidence (`require_board` through
  `require_requirement_linkage`) — including `require_board`, which
  makes no network call at all, closing the "one layer earlier" gap
  round 1 identified. This directly reverses round 1's own
  `False / False` result for the identical
  `require_requirement_linkage` halt shape (compare this block's
  Reproduction 1 to round 1's now-superseded evidence, preserved in
  `## CHANGES round` context above). `--dry-run` unaffected, confirming
  no regression on the one path this requirement explicitly excludes.
spec_vs_built: Spec required every fail-closed halt in the pre-log
  bootstrap window to land its reason durably. Pre-fix built (round 1):
  only halts from `require_doctor()` onward were caught; a halt from
  any of the four contract gates left zero bytes anywhere. Post-fix
  built: `_record_spawn_attempt()` runs before all four gates and
  `require_doctor()`/`ensure_target_remote()`, all wrapped in the same
  `except (SystemExit, Exception)` — confirmed by two independent live
  reproductions above, one per gate class (network-backed and local).
  This requirement's `Incorrect` verdict is corrected to `Present`;
  the correction is recorded here, not by deleting or silently
  overwriting round 1's evidence above.
canonical: reproduction commands and raw output pasted verbatim above,
  this session, this turn; `git show 300a0724 -- spawn.py` (this
  session, `/tmp/wt-2366b`) for the underlying code change.

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
evidence: independently rerun this session against PR #2366's
  CHANGES-round fix head (300a07249b9032fe56ef684f2a2e86374a681c2a,
  `git worktree` at `/tmp/wt-2366b`) — round 1's evidence (against the
  since-superseded head 3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d) is
  carried forward as prior confirmation, not relied on alone; this
  round re-ran both suites fresh against the new head.
acceptance: 'python3 -m pytest tests/test_spawn_pipeline.py -q (this
  session, `/tmp/wt-2366b`) — result:'
```
bringing up nodes...
bringing up nodes...

........................................................................ [ 83%]
..............                                                           [100%]
86 passed in 10.10s
```
acceptance: 'python3 -m pytest tests/test_state_root_scoping.py
  tests/test_watch_hardening.py test/test_roster_role_field.py
  tests/test_standing_red_watch.py tests/test_poll_watchdog_log.py
  tests/test_spawn_pipeline.py -q (this session, `/tmp/wt-2366b`) —
  result:'
```
........................................................................ [ 49%]
........................................................................ [ 99%]
.                                                                       [100%]
145 passed in 1.36s
```
rationale: Both counts independently rerun this session against the new
  head (not taken from the PR's own pasted output) — 86 and 145
  respectively, matching both the PR's own claimed counts and round 1's
  prior independent run against the pre-fix head — no regression from
  the CHANGES-round fix.
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

## What did not work

Nothing in this round's own reproduction attempts failed to reproduce —
both the `require_requirement_linkage` halt and the `require_board`
halt landed in the durable trace as the fix commit's diff predicts, and
the `--dry-run` regression check showed no attempt file written, also
as predicted. No monkeypatch, scratch-state setup, or `spawn.main()`
invocation needed retrying this round.

## Open findings

1. **R2/R4, resolved this round** — round 1 recorded `Incorrect`: the
   four pre-existing phase gates ran before `_record_spawn_attempt()`,
   and two of them could `sys.exit()` after a real `gh api` call. Fix
   commit 300a07249b9032fe56ef684f2a2e86374a681c2a moved the attempt
   record to the top of `main()`'s non-dry-run path and wrapped all
   four gates in the existing `try/except`, matching the resolution
   path round 1 named verbatim. Independently re-verified `Present` this
   round (see updated R2/R4 blocks above and `## CHANGES round` above)
   — no longer an open finding.
2. **R7 `Surface`**, non-blocking on its own, unchanged this round —
   ad-hoc (`--issue`-less) consumer spawns get no durable trace or
   watchdog visibility at all, and were the actual shape of the incident
   that first prompted this issue (issue #2291's own first comment).
   PR #2366's own record (this round's `git show
   pr-2366:docs/issue-2291/reports/implementation.md`, this session)
   assessed R7 and explicitly left it open, citing the need for a scope
   decision rather than a same-shape low-risk edit. Resolution path
   unchanged: a future issue amendment scoping whether ad-hoc spawns
   should also get a (necessarily roster-less) durable trace, or an
   explicit narrowing of "all consumer sessions" to "all
   `--issue`-scoped consumer sessions" in issue #2291's own text.
3. **R8 `Surface`**, non-blocking, unchanged this round —
   `spawn-attempts.jsonl` has no pruning/rotation; every watchdog tick
   reads/parses the whole file. Same gap PR #2365 flagged against
   #2305, carried forward unaddressed in #2366's original delivery and
   in this CHANGES round (PR #2366's own record cites needing new
   already-reported tracking state before pruning is safe — a larger
   change than this round's fix). Resolution path unchanged: prune once
   an entry's outcome has been swept and reported once, or cap/rotate
   the file.
4. **Process-gap finding from round 1, now moot** — round 1 noted PR
   #2366's original delivery read PR #2365's terminal state but not its
   finding content before porting the identical mechanism from PR
   #2305. This CHANGES round explicitly closes that gap: the fix
   commit's own message names PR #2371 (this record's round-1 PR) and
   its R2/R4 finding by number, and the resolution path applied is
   verbatim what round 1's finding 1 recommended. No longer flagged as
   open process risk for this issue; left here only as resolved
   context, not deleted, per finding-record's "record re-examination
   inline rather than treat a dispute as a request to fix/delete
   anything."

## Next steps

None — `loop_state: reported` (terminal for `review-record`). R7/R8
above remain open for whichever session next takes up issue #2291 (or a
follow-up issue) to resolve; R2/R4 are resolved and no longer require
follow-up. This record's own verdicts stand as delivered.

## skill-verdict

Round 1 (this file's own prior PR) already carries its own
skill-verdict lines above for
`conformance-review-requirement-extraction`,
`conformance-review-sampling-derivation`,
`conformance-review-verification-method-selection`,
`conformance-review-verdict-assignment` (round-1 scope),
`conformance-review-traceability-and-evidence` (round-1 scope), and
`conformance-review-finding-record` (round-1 scope) — not repeated
here; those verdicts still stand for the requirements they covered.

canonical: `gh pr view 2371 --json number,state -q '.number,.state'`
(this session) — result `2371`, `MERGED`.

This CHANGES round invoked three skills fresh, for the R2/R4
re-verification specifically:

skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked;
  rule 1 (treated this record's own round-1
  `Incorrect` verdict on R2/R4 as a claim to re-test against the fix
  commit's actual code, not as settled once the fix commit's message
  claimed resolution); rule 2 (added the `require_board` local-halt
  reproduction as a deliberate edge case beyond the fix commit's own
  `require_requirement_linkage`-only repro); rule 3 (re-derived from
  `git show 300a0724 -- spawn.py` and live `spawn.main()` runs rather
  than citing the fix commit's message or PR #2366's own untracked
  `docs/issue-2291/reports/implementation.md` narrative — see `##
  CHANGES round` above for the untracked/`git show pr-2366:...` note —
  as evidence); rule 7 (both reproductions recorded with full raw
  output, not a bare "reproduced" label, matching this round's own
  "What did not work" rigor above).
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
  corrected R2/R4 from `Incorrect` to `Present` per rule 6
  (re-checked the evidence once via two independent live reproductions,
  not the fix commit's own claim alone, before finalizing); `spec_vs_built`
  on both updated blocks states what changed between the pre-fix and
  post-fix built state, not just the new verdict label, per rule 5's
  same discipline applied to a correction rather than an initial
  Incorrect/Absent call.
skill-verdict: conformance-review-finding-record — applied: invoked;
  R2/R4 verdict correction recorded inline in the existing requirement
  blocks (updated `evidence`/`rationale`/`spec_vs_built`, verdict
  changed in place) rather than as a new duplicate block, per this
  skill's own dispute-resolution guidance ("record its re-examination
  inline rather than treating the dispute as a request to fix/delete
  anything"); both updated blocks retain a citable `evidence` pointer
  and `spec_ref`, no verdict left unsupported.
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked;
  rule 1 (both updated R2/R4 evidence blocks cite file:line
  plus the new head's commit sha, 300a07249b9032fe56ef684f2a2e86374a681c2a,
  not a bare path); rule 2 (R4's evidence records both live
  reproductions — `require_requirement_linkage` and `require_board` —
  as separate `acceptance:` entries, one per contributing halt path,
  rather than one link standing in for both); rule 5 (evidence pinned
  to the CHANGES-round fix commit specifically, distinguished
  throughout from the superseded pre-fix head
  3cdfc4c52d4459c13f6d150b0ed126f06a7fc73d that round 1's own R2/R4
  evidence was checked against).

other mounted skills: not triggered this round
  (conformance-review-requirement-extraction,
  conformance-review-sampling-derivation,
  conformance-review-verification-method-selection,
  conformance-review-severity-classification — no new requirement
  extraction, sampling, or severity-weighting was needed for a
  two-requirement re-verification reusing round 1's own extraction; the
  verification methods used this round (Analysis plus live
  reproduction) were the same methods round 1's
  `conformance-review-verification-method-selection` invocation already
  selected for R2/R4, so no new method-selection judgment was made).

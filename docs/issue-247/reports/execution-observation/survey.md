---
kind: survey
subject: issue-247
role: execution-observation
date: 2026-08-14
phase: 1
---

# Survey — execution-observation of PR #256 (issue #247)

## Trigger

- canonical: `gh pr list --search 247 --state all` (this session) — result: PR #256 "issue-247: self-triggered abandoned-work respawn" (`issue-247/implementation` -> main), state `MERGED`.
- canonical: `gates/spawn_on_pr.py` read this session, function `spawn_missing_for_pr` — result: its task-string template (the line building `이슈 #{issue}: {role} — {subject}/implementation 브랜치에 랜딩된 커밋에 대해 아직 기록이 없다. PR 생성 시 자동 스폰됨 (spawn_on_pr.py).`) matches this session's own assigned task text verbatim.
- canonical: `gates/spawn_on_pr.py` read this session, function `backfill_closed` — result: its task-string template carries an extra `(닫힌 이슈 백필, backfill_closed() 로 opt-in 스폰됨)` clause that this session's task text lacks; this session was spawned by `spawn_missing_for_pr`, not `backfill_closed`.

## What landed (PR #256)

- canonical: `gh pr view 256 --json state,mergedAt,mergeCommit,headRefName,files` (this session) — result: merged 2026-08-04T05:11:39Z, merge commit `1d7df88329a97c8d2c4d0928e057a07b65a3dbb2`, files touched: `spawn.py`, `test_spawn.py`, `docs/handbooks/operations.md`, plus the `docs/issue-247/` report and proposal files.
- canonical: `git log --oneline -1 -- tests/test_spawn.py` (this session) — result: `74e40109` relocated `test_spawn.py` to `tests/test_spawn.py` in a later, unrelated commit.
- canonical: `git log --oneline 9d1394f1^..1d7df883` (this session) — result: the branch carries commit `cd48c333` (phase 1) then `9d1394f1` (phase 2), squash-merged as `1d7df883`.
- canonical: `docs/issue-247/reports/implementation.md` read in full this session — result: the delivered mechanism is a second, in-process trigger (`_self_trigger_respawn()`) for the existing capped auto-respawn machinery (issue #132), firing at the point `_spawn_one()` already knows its own `uncommitted-work`/`failed-no-commit` outcome — the gap issue #247's body describes.

## Independent reproduction this session

- canonical: `spawn.py` read this session on the current `origin/main` checkout (commit `bc53410e`), the lines around the `if bounded and issue is not None:` block — result:
```
$ sed -n '6864,6866p;6880,6881p' spawn.py
        _append_event(events_path, "session-end",
                      {"outcome": outcome, "reason": push_reason}
                      if push_reason is not None else outcome)
        _self_trigger_respawn(outcome, roster_key, cwd, issue, role,
                              str(log_path), session_start_ts)
```
canonical: spawn.py:6864-6881 (this session, commit bc53410e)
The `session-end` append precedes the `_self_trigger_respawn()` call — matching the implementation record's claimed fix for its Hunt finding 1, still standing on the current checkout.

- Command run this session (`origin/main`, commit `bc53410e`):
```
$ python3 -m pytest tests/test_spawn.py -k "SelfTriggeredRespawn or SessionEndVerdict" -q
16 passed, 487 deselected in 21.69s
```
canonical: python3 -m pytest tests/test_spawn.py -k "SelfTriggeredRespawn or SessionEndVerdict" -q
The self-trigger claim/cap/ordering tests the implementation record describes still pass on the shipped code, reproduced independently this session.

- Command run this session (same checkout):
```
$ timeout 300 python3 -m pytest tests/test_spawn.py -q
[exit 143, terminated]
```
canonical: timeout 300 python3 -m pytest tests/test_spawn.py -q
Did not finish within 300 seconds. `wc -l tests/test_spawn.py` this session reports the file at 10829 lines today. The full-file run the implementation record's own claim rests on could not be independently reproduced to a finish in this session — carried as an open item into phase 2 rather than silently substituted with the targeted run above.

## What has not yet been checked (left for phase 2's verdict)

1. **Outcome** — does the shipped self-trigger fire in a real headless `claude -p` session end to end, not just the mocked unit-level `_spawn_one()` integration test the implementation record describes? Deferred to phase two — needs a `runs/ledger.jsonl` check for a real production firing.
2. **Trajectory** — did the phase-one-to-phase-two path on this PR follow contract v3 s19 (survey before proposal, a real approval comment before phase-two work starts, phase-two output confined to the approved write set)? Deferred to phase two — needs the issue's own comment trail and commit timestamps.
3. canonical: gh issue view 247 --json state,closedAt
Result this session: `state: CLOSED`, `closedAt: 2026-08-04T05:21:09Z`.
canonical: gh issue view 247 --json comments -q '.comments[]|.author.login+": "+.body'
Result this session: closing comment by `jjongkwann` reads "delivery 수용(PR #256 머지 — 인-프로세스 재스폰 안전망). 실행 계획 step 1 소진 + 예방책 축은 core 계약 §22(#106, 종결됨)로 완결 — 사람 종결." The human closed the issue at delivery time without waiting on a separate execution-observation record, and (per the Trigger citations above) this session's own spawn still arrived through `spawn_missing_for_pr`, not `backfill_closed` — read as spawn-time issue-state-index staleness rather than a finding against PR #256; carried into phase two's trajectory verdict as a process observation only.
4. **Step** — is the reordering fix (Rationale for deviations #1) and the `time.time()` float-precision fix (#2) each individually sound, judged against the actual diff rather than the record's own narrative of it?

## Skip record (scout-directive)

Skipping a dedicated scout brief this phase: the deliverable class here is the same "audit an executed change to safety-net code, against its own implementation record's claims" shape this repo has run on comparable PRs before (`docs/issue-609/reports/execution-observation.md`, `docs/issue-266/reports/execution-observation.md`) — no open design decision this survey needs external category research to resolve. The proposal below reuses the three-level verdict (outcome/trajectory/step) those prior records already establish as this role's working shape.

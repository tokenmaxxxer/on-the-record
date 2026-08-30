---
issue: 2894
role: silent-failure-audit-0c41a52b
author: silent-failure-audit-0c41a52b
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: same-commit:roster.py
    sha: same-commit
  - path: same-commit:spawn.py
    sha: same-commit
  - path: same-commit:test/test_spawn_attempt_staleness.py
    sha: same-commit
---

# issue-2894 — silent-failure-audit-0c41a52b record

## What was done

canonical: same-commit diff — `git diff --stat` on this branch before commit:

```
 roster.py                            |   7 ++
 spawn.py                             |  53 +++++++++++++++
 test/test_spawn_attempt_staleness.py | 127 +++++++++++++++++++++++++++++++++++
 3 files changed, 187 insertions(+)
```

Added `spawn._attempt_issue_closed(attempt)` (`spawn.py:1460-1502`) — a
third, additive resolution fallback in the existing resolve/prune
pipeline. Wired into `roster.spawn_attempt_sweep()` immediately after the
existing `_attempt_superseded()` fallback (`roster.py:680-686`), tried
only when class-recheck and supersession have both already returned
"not cleared":

```python
            if not cleared and _sp._attempt_issue_closed(a):
                # 이슈 #2894: 클래스 재확인도 supersession 도 이 halt 를 못
                # 풀었지만, 이슈 자체가 닫혀 이 attempt 는 다시는 재시도되지
                # 않는다 — "고쳤다"가 아니라 "이 조건을 다시 물을 미래 시도
                # 자체가 없다"는 뜻으로 resolved 처리한다.
                cleared = True
                resolution = "issue-closed"
```

It runs `gh issue view <issue> --json state -q .state` with `cwd` set to
the attempt's recorded `-C` workspace (the same posture the
`requirement-tag`/`acceptance-format` classes already use), and marks
the halt resolved with `resolution="issue-closed"` when the answer is
`CLOSED`. Conservative on every failure mode: missing `issue`/`cwd`, a
`cwd` that is no longer a directory, a non-zero `gh` exit, or an
exception from the `gh` call itself all return `False`
("still not resolved"), with the exception path printing one `stderr`
diagnostic line so a broken re-check is distinguishable from a
genuinely-still-open issue.

Added tests to `test/test_spawn_attempt_staleness.py`:
`AttemptIssueClosedTest` (6 unit tests — closed / open / missing-fields /
missing-cwd / gh-failure / gh-exception) and
`SpawnAttemptSweepIssueClosedTest` (2 end-to-end sweep tests — an
`unknown`-class halt on a closed issue stops replaying with
`resolution=issue-closed`; the identical halt shape on a still-open
issue keeps reporting unchanged). New-test count derived: `grep -c
'def test_' test/test_spawn_attempt_staleness.py` — result: 49 total
`def test_` lines on this branch, vs 41 on `origin/main` (same command,
run via `git stash`/`git stash pop` round-trip, same session) — 49 - 41
= 8 new tests.

derived: `python3 -m pytest test/test_spawn_attempt_staleness.py -q` —
result:

```
.................................................                        [100%]
49 passed in 0.89s
```

No other production code was touched — `_halt_condition_cleared()`,
`_attempt_superseded()`, `_prune_spawn_attempts()`, and
`spawn_attempt_sweep()`'s report loop are otherwise byte-identical.

## Why

### Root cause (acceptance bullet 1) — candidates checked against the code

canonical: `watchdog.py:1590-1599` (read this session):

```python
    anomaly_count += _sp.spawn_attempt_sweep(d_all=d_all)
    # 이슈 #2468: check_runner worktree / consult·spawn settings.json 이
    # SIGKILL/하드크래시로 orphan 되는 걸 지운다 — 위 spawn_attempt_sweep
    # 과 같은 틱(살아있는 로스터와 무관하게 매번, 워치독이 도는 한 언젠가는
    # 반드시 돈다는 게 이 체크포인트를 고른 이유 — spawn 시작 시점이었다면
    # 크래시 이후 다음 스폰이 있을 때까지, 어쩌면 영원히 안 돌 수 있다).
    # 이상 신호가 아니라 정상적인 자기치유라 anomaly_count 에는 안 얹는다
    # (`_prune_spawn_attempts()`의 반환값을 spawn_attempt_sweep 이 버리는
    # 것과 같은 이유).
    _sp.tmp_resource_sweep()
```

Candidate 2 — *"`_prune_spawn_attempts()`'s retention window may not
apply to halts"* — is false. canonical: `spawn.py:1703-1707` (read this
session):

```python
        elif outcome.get("outcome") == "halted":
            outcome_ts = outcome.get("ts", now)
            if not isinstance(outcome_ts, (int, float)) or \
                    now - outcome_ts < SPAWN_ATTEMPTS_RETENTION_SEC:
                keep_ids.add(aid)  # halted — 재보고 TTL 창 동안 유지
```

The 7-day `SPAWN_ATTEMPTS_RETENTION_SEC` window is applied to `"halted"`
outcomes exactly as it is to `"session-log"` outcomes.

Candidate 3 — *"`spawn_attempt_sweep` discards `_prune_spawn_attempts()`'s
return value at `watchdog.py:1597`"* — is false, and a red herring. The
line quoted above discards the *count* `spawn_attempt_sweep()` itself
already returns and folds into `anomaly_count` one line earlier
(`watchdog.py:1590`); the actual pruning is `spawn_attempt_sweep()`'s own
internal call to `_prune_spawn_attempts(now=now)` (`roster.py:734`,
unchanged by this fix), which runs unconditionally regardless of whether
any caller reads the return value. The discarded value only affects an
observability metric — the comment quoted above states this is
deliberate, the same posture as the immediately-preceding
`tmp_resource_sweep()` call's own discarded return.

Candidate 1 — *"the resolution condition may require something these
halts can never satisfy (their issues are closed, their skill names will
never become valid)"* — **confirmed; this is the actual root cause.**
The pre-fix resolve pipeline had exactly two escape hatches:

canonical: `spawn.py:1236-1256` (read this session):

```python
_HALT_CLASS_PATTERNS = (
    ("requirement-tag", re.compile(r"^이슈 #\d+ 가 요구 연결이 없다")),
    ("acceptance-format", re.compile(r"^이슈 #\d+ 는 phase-2 승인")),
    ("enospc", re.compile(r"^스폰을 거부한다: .+ 에 여유 (?:공간|inode)")),
    ("workspace-origin-mismatch",
     re.compile(r"^작업 경로에 다른 레포가 있다 \(origin 불일치\): ")),
    ("cwd-invalid", re.compile(r"^-C 가 (?:존재하지 않는 디렉터리다|"
                                r"git 레포 안이 아니다|레포 루트가 아니라)")),
)


def _classify_halt_reason(reason: str) -> str:
    ...
    for name, pat in _HALT_CLASS_PATTERNS:
        if pat.search(reason):
            return name
    return "unknown"
```

The `"skill X not found"` shape (the issue's `issue-614`, `issue-488`,
`issue-489` examples) matches none of these five patterns, so it
classifies `"unknown"`. canonical: `spawn.py:1368-1369` (read this
session):

```python
        return False
    return False  # unknown class
```

`_halt_condition_cleared()` structurally cannot clear an `"unknown"`-class
halt — every code path for that class falls through to this final line.
The `"no requirement ID"` shape (`issue-645`) *does* classify as
`requirement-tag`, but its re-check queries the issue's current body
live via `gh` (`gates/requirement_linkage.py:61-73`, `requirement_linkage.check()`
→ `gh_rest.fetch_issue_body`) — a closed issue's body is never edited
again, so a halt recorded before closure keeps re-checking "still
missing" forever.

canonical: `spawn.py:1427-1457` (read this session):

```python
def _attempt_superseded(attempt_id: str, attempt: dict, attempts: dict,
                         outcomes: dict) -> bool:
    ...
    issue = attempt.get("issue")
    skill = attempt.get("skill")
    my_ts = attempt.get("ts")
    if issue is None or not skill or not isinstance(my_ts, (int, float)):
        return False
    family = _skill_family(skill)
    for other_id, other in attempts.items():
        if other_id == attempt_id:
            continue
        if other.get("issue") != issue:
            continue
```

Supersession (the mechanism that resolved the three #2876 halts on
2026-08-30) requires a *later* attempt to exist at all for the same
(issue, skill-family). canonical: `board.py:417-422` (read this session):

```python
    if issue is None:
        return
    root = Path(cwd).resolve()
    if not (root / _sp.MARKER).is_file():
        return
    sys.path.insert(0, str((Path(__file__).parent / "gates").resolve()))
```

`require_requirement_linkage()` (this function) and the rest of this
orchestrator's spawn gating never target a closed issue in the normal
flow, so once `issue-614`/`488`/`489`/`645` closed, no later attempt —
successful or not — will ever be recorded for them, and the
`for other_id, other in attempts.items()` loop quoted above has nothing
to find, now or after the retention window resets again.

Both escape hatches are gated on the world changing (a tag gets added, a
retry succeeds); a closed issue is a world that, for this orchestrator's
purposes, has permanently stopped changing. This is the same shape found
three times on 2026-08-30 in #2876: a mechanism that reports a clean
result only for the population that still gets exercised, leaving out
the population that structurally never will — here, closed-issue halts,
in whatever class they happen to carry.

**Field that differs from the #2876 halts.** The #2876 halts had a live
later attempt (`outcome == "session-log"`) for the same (issue,
skill-family) inside the retention window, so supersession fired. These
four have no such later attempt and never will, because their issue is
closed — the field that differs is the existence of any future attempt
at all for that issue, which the pre-fix sweep had no way to ask about.

**Why this fix, not a second suppression layer.** `_attempt_issue_closed()`
is wired into the same place and the same style as the existing
`_attempt_superseded()` fallback shown in "What was done" above —
additive, tried only after class-recheck already returned `False`,
marking the same `spawn_attempt_resolved` ledger event with a
distinguishing `resolution` value. It reaches every halt class
(including `unknown`) for exactly the population the issue names,
without a parallel filter, a time-based cutoff, or a verbosity knob.

### Must-not compliance

canonical: `test/test_spawn_attempt_staleness.py` —
`SpawnAttemptSweepIssueClosedTest.test_unknown_class_halt_on_open_issue_keeps_reporting`
(added this session, quoted in "Open findings" below) exercises this
directly: `_attempt_issue_closed()` returns `False` whenever `gh` reports
anything other than `CLOSED`, including every failure mode, so a live
blocking condition keeps reporting exactly as before — a fresh halt gets
its own new `attempt_id` and is unaffected by this change's report loop,
since this change does not touch `spawn_attempt_sweep()`'s own
reportability gate (`roster.py:651-660`, unmodified).

## What did not work

None.

## Upstream basis

Issue #2894 body (root-cause candidates, the four example halt lines,
the must-not clause) — canonical: `gh issue view 2894` output (read this
session, state: OPEN, quoted verbatim in the "Root cause" section above)
— and the pre-existing code at `roster.py:613-734`
(`spawn_attempt_resolved`, `spawn_attempt_halt_reported`,
`_prune_spawn_attempts()` call site) and `watchdog.py:1580-1599`, both at
`same-commit` since this record cites the code these changes build on
directly, in the same commit. #2876's PRs (#2882, #2887, #2889, #2891)
are cited in the issue as evidence the resolve/prune path itself works;
none of that code was modified by this change.

## Open findings

None — the fix reaches every halt class exercised by the issue's four
examples (`unknown` and `requirement-tag`). derived: `python3 -m pytest
test/test_spawn_attempt_staleness.py -q` — result: `49 passed in 0.89s`
(quoted in full under "What was done" above) — all three acceptance
checks below pass, executed live this session.

### Acceptance bullet 2 — before/after sweep diff

derived: `python3 /tmp/issue2894_demo_output.txt` harness — a scratch
`spawn-attempts.jsonl` ledger with four halts shaped like the issue's own
example lines (`issue-614` `"skill frontend-ui-engineering not found"`,
`issue-488`/`issue-489` `"skill implementation not found"`, `issue-645`
`"이슈 #645 가 요구 연결이 없다"`), all on issues stubbed `CLOSED`, run through
`roster.spawn_attempt_sweep()` with the new fallback first disabled
(pre-fix baseline) then enabled (post-fix) — result:

```
=== BEFORE fix (issue-closed fallback disabled, only class-recheck + supersession active) ===
[spawn-attempt] issue-488/implementation-bbbbbbbb: spawn halted pre-workspace (attempted at 2026-08-27T14:03:04Z): skill implementation not found
[spawn-attempt] issue-489/implementation-cccccccc: spawn halted pre-workspace (attempted at 2026-08-27T14:03:04Z): skill implementation not found
[spawn-attempt] issue-614/frontend-ui-engineering-aaaaaaaa: spawn halted pre-workspace (attempted at 2026-08-26T14:03:04Z): skill frontend-ui-engineering not found
[spawn-attempt] issue-645/requirement-tag-dddddddd: spawn halted pre-workspace (attempted at 2026-08-27T14:03:04Z): 이슈 #645 가 요구 연결이 없다: ...
emitted live-halt lines this tick: 4

=== AFTER fix (issue-closed fallback active, same ledger, next tick) ===
[spawn-attempt] issue-488/implementation-bbbbbbbb: halt RESOLVED at 2026-08-30T14:03:04Z (class=unknown, resolution=issue-closed, originally attempted at 2026-08-27T14:03:04Z) — no longer a live halt: skill implementation not found
[spawn-attempt] issue-489/implementation-cccccccc: halt RESOLVED at 2026-08-30T14:03:04Z (class=unknown, resolution=issue-closed, originally attempted at 2026-08-27T14:03:04Z) — no longer a live halt: skill implementation not found
[spawn-attempt] issue-614/frontend-ui-engineering-aaaaaaaa: halt RESOLVED at 2026-08-30T14:03:04Z (class=unknown, resolution=issue-closed, originally attempted at 2026-08-26T14:03:04Z) — no longer a live halt: skill frontend-ui-engineering not found
[spawn-attempt] issue-645/requirement-tag-dddddddd: halt RESOLVED at 2026-08-30T14:03:04Z (class=requirement-tag, resolution=issue-closed, originally attempted at 2026-08-27T14:03:04Z) — no longer a live halt: 이슈 #645 가 요구 연결이 없다: ...
emitted live-halt lines this tick: 0

=== Following tick: confirm no replay ===
emitted live-halt lines this tick: 0
```

Before/after halt-line count pair (population: the four stale halt
entries matching the issue's own example): **4 → 0**, derived directly
from the `roster.spawn_attempt_sweep()` return value printed above, not
a summary.

unverifiable: two stray `RecursionError` diagnostic lines appeared in the
raw capture ahead of the section headers — the demo harness's own
`mock.patch.object(spawn.subprocess, "run", ...)` patches the
process-global `subprocess` module object, so the real
`requirement_linkage.check()` gh call made during `issue-645`'s
legitimate class-recheck attempt also hit the mock's fallback branch,
and stdout/stderr buffering in the redirected capture reordered the
lines ahead of the buffered stdout prints — this is an artifact of the
ad hoc demo harness's global mock, not reproducible against the shipped
code path in isolation, so its exact interleaving mechanism is not
independently re-verified here.

### Acceptance bullet 3 — new failure still reports

derived: same harness, continued — after the four resolved halts stayed
silent on a further tick, one new attempt was appended (`issue-999`,
stubbed `OPEN`) with a halt reason of the same unclassifiable shape
(`"skill brandnew not found"`) — result:

```
=== A genuinely new spawn failure (issue #999, still OPEN) ===
[spawn-attempt] issue-999/brandnew-eeeeeeee: spawn halted pre-workspace (attempted at 2026-08-30T14:02:34Z): skill brandnew not found
emitted live-halt lines this tick: 1
```

It appears on the very next `spawn_attempt_sweep()` call, unaffected by
the four already-resolved entries. The same guard is covered by an
isolated unit test — canonical: `python3 -m pytest
test/test_spawn_attempt_staleness.py::SpawnAttemptSweepIssueClosedTest -q`
— result:

```
..                                                                        [100%]
2 passed in 0.02s
```

### Invariant checks

- **No return of the retired `role` axis**: derived: `python3
  gates/retirement_count.py` — result: 1136 matched lines on this branch
  and 1136 matched lines on `origin/main` (`git stash` / `git stash pop`
  round-trip, same session); `diff` of the two full outputs shows only
  line-number drift from this change's insertions, zero new matched
  lines added or removed.
- **No new bug — failing-test set vs `origin/main`, as sets of names**:
  derived: `python3 -m pytest . -q` from the repo root, run on this
  branch and on `origin/main` (`git stash` / `git stash pop`, same
  session) — 17 failed on both runs; `diff` of the sorted `FAILED ...`
  line sets between the two runs is empty (identical set — command:
  `diff <(grep '^FAILED' before.txt | sort) <(grep '^FAILED' after.txt |
  sort)`, no output). Passed count went 651 → 659 (exactly the 8 new
  tests added to `test/test_spawn_attempt_staleness.py`); `3 xfailed`
  unchanged on both runs.
- **No overhead increase**: partial hold, reported as such rather than
  claimed clean. `_attempt_issue_closed()` adds one `gh issue view` call
  per tick for each halt still unresolved after class-recheck and
  supersession both already ran. For the two classes that already call
  `gh` (`requirement-tag`, `acceptance-format`) and `unknown` (which
  never called `gh` before), the marginal cost is one additional call
  while that specific halt stays unresolved; for the three classes that
  never called `gh` at all (`enospc`, `cwd-invalid`,
  `workspace-origin-mismatch`), this is a net-new call, bounded by the
  shrinking population of still-open halts rather than unbounded or
  per-subject-multiplicative. A resolved halt is pruned on its very next
  sweep and stops costing anything at all, so sustained per-tick cost
  over the 7-day retention window goes down, not up — but the marginal
  first-tick cost for the three previously-gh-free classes is real and
  new, so this is not claimed as strictly zero.
- **Watch/monitor machinery unbroken and not quieter**: this is the
  deliverable itself, demonstrated live in acceptance bullets 2 and 3
  above — the four stale halts stop replaying, and a fresh failure (same
  reason shape, open issue) still reports on the next tick.

skill-verdict: silent-failure-audit — applied: invoked; audited
`_attempt_issue_closed()`'s own failure path (missing issue/cwd,
nonexistent cwd, non-zero `gh` exit, `gh` exception) against the
Handled/Silently-Absorbed/Unreachable classification before shipping —
canonical: `spawn.py:1460-1502` (quoted in "What was done" above) —
every branch returns `False` (conservative "still live") rather than
raising or silently returning `True`, and the exception branch prints an
explicit stderr diagnostic instead of absorbing the exception with no
trace.
skill-verdict: work-in-english — applied: invoked; new docstrings/comments
in `spawn.py`/`roster.py` were written in Korean to match this file's
existing convention — every neighboring function in the same
class-recheck/supersession block (`_halt_condition_cleared`,
`_attempt_superseded`, their surrounding module comments, quoted in
"Root cause" above) is Korean, and splitting one function's language
from its immediate siblings would read as inconsistent, the skill's own
"project convention conflicts: follow the project" edge case applies;
this record, commit messages, and the PR body are in English per the
skill's default routing.

## Next steps

None — delivered under the build-now bypass (`CORE_BUILD_NOW=1`) as a
single-session build; code, tests, and this record land in one commit
and one PR.

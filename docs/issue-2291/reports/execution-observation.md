---
issue: 2291
role: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2291/reports/implementation.md
    sha: 53347a118202acfddd7024ab1e88d511019b694f
subject: PR #2305 (branch issue-2291/implementation, untracked on this
  branch — not yet merged to main) — spawn.py durable spawn-attempt trace
  + roster.py/watchdog.py spawn_attempt_sweep, and the CHANGES-round
  role_model.txt pytest-xdist race fix in tests/_spawn_test_support.py
test: independent re-execution of tests/test_spawn_pipeline.py (three
  repeats) and an independently-scripted re-derivation of the
  Provenance (executed-live) acceptance — own scratch paths, own
  synthetic issue number, not a replay of the record's own transcript
result: passed
assertedBy: execution-observation, this session, independent re-execution
---

# issue-2291 — execution-observation record

## What was done

Independently re-executed, against a fresh `git worktree` of PR #2305's
head commit (`53347a118202acfddd7024ab1e88d511019b694f`, branch
`issue-2291/implementation` — untracked on this
`issue-2291/execution-observation` branch since the PR has not yet
merged to main), the two claims named in the task assignment: the
role_model regression-repair claim (`tests/test_spawn_pipeline.py`
deterministic after the CHANGES-round fix) and the pre-log halt
durable-trace acceptance (durable trace + watchdog visibility), per
`defect-verification-independence-from-upstream-verdicts` — each figure
below was re-derived first, in a worktree removed at the end of this
session, and the implementation record's own text was consulted only
afterward to compare.

**1. role_model regression repair.**

derived: `python3 -m pytest tests/test_spawn_pipeline.py -q`, repeated
three separate times in the worktree — result (each repetition):

```
86 passed in 10.47s
86 passed in 1.21s
86 passed in 1.17s
```

Zero failures across three independent invocations — matches the
implementation record's post-fix claim ("86 passed", repeated;
canonical: `docs/issue-2291/reports/implementation.md` — untracked on
this `execution-observation` branch, read via the worktree of PR
#2305's head commit — "Rationale for deviations" section, "Post-fix
verification" acceptance block). The record attributes the pre-fix
flake to a shared mutable `spawn.ROLE_MODEL_CONFIG` path racing across
`pytest-xdist` workers; this session did not re-run the pre-fix state
(the CHANGES-round fix is already committed on the branch, so there is
no pre-fix state left to observe on this head commit) — only the
post-fix determinism claim was re-derived, three times, as the task
assignment asked ("confirm the role_model tests pass on the branch";
derived: the three pytest runs immediately above, this session).

**2. Pre-log halt durable-trace acceptance (Provenance, executed-live).**

Re-scripted independently rather than replaying the record's own
transcript: own scratch paths (`/tmp/otr-2305-demo`,
`MUSTER_STATE_ROOT=/tmp/otr-2305-state`, both distinct from the
record's `/tmp/otr-2291-demo`), and a different synthetic issue number
(777, vs. the record's 538) to keep this run's trace lines
distinguishable from the record's own reproduction rather than
overwriting or reusing them:

derived: a short Python script calling the real
`spawn._record_spawn_attempt(777, "implementation", os.getpid())` then
the real `pipeline._fetch_or_halt()` against a real unreachable git
remote (`git remote add origin /no/such/eo-check-path`, a fresh local
repo distinct from the record's own fixture path) — result:

```
### STEP 1: consumer-equivalent spawn attempt, piped through tail exactly as the consumer's report describes ###
(swallowed exit code as the consumer's shell would see it: 0)

### STEP 2: durable trace, STATE_ROOT-scoped — never in the target repo ###
{"event": "spawn_attempt", "attempt_id": "777:implementation:1575176:1787634697269", "issue": 777, "role": "implementation", "pid": 1575176, "ts": 1787634697.2694817}
{"event": "spawn_attempt_outcome", "attempt_id": "777:implementation:1575176:1787634697269", "outcome": "halted", "detail": "신규 워크스페이스: fetch 실패 — fatal: '/no/such/eo-check-path' does not appear to be a git repository\nfatal: 리모트 저장소에서 읽을 수 없습니다\n\n올바른 접근 권한이 있는지, 그리고 저장소가 있는지\n확인하십시오.", "ts": 1787634697.2936397}
```

The durable trace survives the halt: `_fetch_or_halt()` raised
`SystemExit`, was caught, and `_record_spawn_outcome(attempt_id,
"halted", reason)` landed the reason in `SPAWN_ATTEMPTS_PATH`
(`STATE_ROOT / "spawn-attempts.jsonl"`) before re-raising — matching
the implementation record's mechanism claim (canonical: `spawn.py:
1597-1632`, read in the worktree before running the script — the
`try/except` wraps the bootstrap window and calls
`_record_spawn_outcome` on halt).

derived: `ls /tmp/otr-2305-demo/work` and `git status --porcelain --
runs/` in the worktree, immediately after — result: both empty — no
file landed in the fixture's target-repo tree or this checkout's own
`runs/`, matching the "nothing written into the consumer's tree"
constraint.

derived: the real `spawn.py watchdog -C .` CLI, same
`MUSTER_STATE_ROOT`, same worktree
(`SPAWN_WATCHDOG_ALLOW_NONCANONICAL=1` only to satisfy the unrelated
canonical-checkout guard for a throwaway worktree) — result (relevant
line):

```
[spawn-attempt] issue-777/implementation: spawn halted pre-workspace: 신규 워크스페이스: fetch 실패 — fatal: '/no/such/eo-check-path' does not appear to be a git repository
fatal: 리모트 저장소에서 읽을 수 없습니다

올바른 접근 권한이 있는지, 그리고 저장소가 있는지
확인하십시오.
```

The watchdog's next tick named the pre-workspace halt using this
session's own synthetic issue number (777) — the exact state the issue
says the system could not previously express, independently confirmed
rather than assumed from the record's own transcript (canonical:
`roster.py:422` `spawn_attempt_sweep` and `watchdog.py:1486`
`anomaly_count += _sp.spawn_attempt_sweep(...)`, read in the worktree
before running the CLI, confirming the sweep is wired into every
`roster_watchdog()` tick unconditionally).

## Why

canonical: the pytest re-runs and independently-scripted live-fire
reproduction quoted in "What was done" above (this session, executed
live in the worktree) — this section bounds those results, it does not
add new claims of its own.

Scope was the task assignment's two named items — re-execute the
pre-log halt durable-trace mechanism and re-derive role_model test
determinism on the branch (derived: see "What was done" above, three
pytest repetitions plus the live-fire script) — not a full re-audit of
the implementation record's other Acceptance-section claims (the
empty-state sweep, the broader regression sweeps, the `py_compile`
check, or the `amendments-reconciled` correction of the issue's
original 538 misattribution; canonical:
`docs/issue-2291/reports/implementation.md` — untracked on this
`execution-observation` branch, read via the worktree of PR #2305's
head commit `53347a118202acfddd7024ab1e88d511019b694f` — "Open
findings"/"Next steps" sections), which this record does not re-derive
and makes no claim about either way.

Per `defect-verification-independence-from-upstream-verdicts`, this
record re-executed the tests and re-scripted the live-fire
reproduction directly against the PR's own code first — reading the
relevant `spawn.py`/`roster.py`/`watchdog.py` source (canonical:
`spawn.py:1597-1632`, `roster.py:422`, `watchdog.py:1486`, all cited
above) to confirm the mechanism before running it — rather than
treating the implementation record's Acceptance section as ground
truth going in; that section's prose was read afterward only to
compare the independently-derived results against what was claimed.

## Upstream basis

canonical: `gh pr view 2305 --json headRefName,baseRefName` (this
session) — result: `headRefName=issue-2291/implementation
baseRefName=main`, state OPEN — PR #2305 is still open against main, so
its branch's files are untracked on this `execution-observation`
branch.

- `docs/issue-2291/reports/implementation.md` (untracked on this
  `execution-observation` branch, per the `gh pr view` result above),
  `sha: 53347a118202acfddd7024ab1e88d511019b694f` — PR #2305's head
  commit on branch `issue-2291/implementation`, hence the real
  40-character sha rather than `same-commit`; read via a `git worktree`
  of that commit this session (`/tmp/otr-2305-check`, removed at the
  end of this session), and the record whose Acceptance-section claims
  were independently re-derived above.
- `spawn.py`, `pipeline.py`, `roster.py`, `watchdog.py` at the same
  commit, in that same worktree — the source of
  `_record_spawn_attempt`/`_record_spawn_outcome`/`_fetch_or_halt`/
  `spawn_attempt_sweep`, read and exercised directly above.
- `tests/test_spawn_pipeline.py` at the same commit, same worktree —
  re-executed three times above.

## Open findings

None.

derived: the three pytest runs quoted in "What was done" above (this
session, executed live in the worktree) — result: 86 passed, zero
failures, all three repetitions (canonical: pytest summary lines quoted
verbatim above).

derived: the independently-scripted live-fire reproduction quoted in
"What was done" above (own scratch paths, own synthetic issue number
777) — result: durable trace landed the halt reason, watchdog's next
tick surfaced `spawn halted pre-workspace: ...` for that same synthetic
issue, and no file landed in the fixture's target-repo tree or this
checkout's own `runs/` (canonical: `ls`/`git status --porcelain`
output, both empty, quoted above) — corroborating the implementation
record's Provenance acceptance claim under an independently-chosen
fixture.

Resolution path: none required — nothing open.

## Next steps

None — `loop_state` is terminal (`handed-off`).

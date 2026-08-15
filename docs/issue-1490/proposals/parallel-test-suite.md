---
status: proposed
files:
  - pytest.ini
  - conftest.py
  - tests/test_spawn.py
  - tests/test_gates.py
  - tests/test_watchdog_freshness.py
  - tests/test_poll_watchdog_log.py
  - requirements-dev.txt
  - docs/handbooks/operations.md
  - docs/issue-1490/reports/implementation.md
---

## Request

Make the default `pytest` run fast (issue #1490): run tests in
parallel via `pytest-xdist`, fix any test that shares mutable state so
parallel execution stays correct, split real-subprocess/git
lifecycle tests into an opt-in `slow` tier excluded by default, and
record before/after timings plus every per-test isolation fix. Target:
default (non-slow, parallel) run under 300s.

## Constraints

- No test may be deleted or weakened (issue body, Requirement 4).
- Both tiers together (`pytest -q --ignore=bench`, no `-m` filter) must
  still produce the same pass/fail set as today's single-threaded
  baseline — recorded as a diff of test IDs (issue body, Acceptance).
- No dependency manifest exists in this repo today (survey finding);
  adding one is itself in-scope since `pytest-xdist` has no other place
  to be declared, but the pin must not touch anything unrelated to
  testing.
- Any operational-surface file (a new dependency manifest qualifies)
  needs a same-commit `docs/handbooks/*.md` touch (contract v3 s21).
- Per-test isolation fixes must be individually named in the delivery
  record (issue body, Acceptance).

## Rationale

Considered leaving parallelization to CI-level test sharding (splitting
`tests/*.py` files across N separately-invoked `pytest` processes in
the harness/CI config, no `pytest-xdist` dependency) instead of
in-process `-n auto`. Rejected: this repo's test invocation is a single
`python3 -m pytest` command with no CI/harness wrapper the survey found
that could own a sharding split — introducing one would be a second,
larger surface change (new orchestration logic) for the same effect
`pytest-xdist`'s `-n auto` gets in one `addopts` line, and it would
lose xdist's automatic load-balancing across differently-sized test
files (`tests/test_spawn.py` alone is 10861 lines vs. `tests/test_gates.py`'s
1674 — a static N-way file split would leave some shards far emptier
than others, undermining the wall-clock target more directly than
`-n auto`'s dynamic work-stealing would).

Considered marking the `slow` tier by file path (`--ignore` on
`tests/test_spawn.py`, `tests/test_poll_watchdog_log.py`, etc.) instead
of a `pytest.ini` `markers =` + per-test `@pytest.mark.slow` decorator.
Rejected: `tests/test_spawn.py` (10861 lines) mixes real-subprocess
lifecycle tests with plenty of pure-logic tests in the same file (the
survey's grep found only 12 files touching `subprocess.` at all, and
even those files are not uniformly slow) — a path-level `--ignore`
would exclude far more coverage from the default run than the issue's
"non-slow" framing intends, which risks violating the "no test
weakened" constraint by silently dropping fast tests from the default
tier's effective coverage.

## What will be done

1. Add `requirements-dev.txt` declaring `pytest-xdist` (pin to the
   version resolved at install time) as this repo's first dependency
   manifest; document the new file and the `-m "not slow"` default-run
   convention in `docs/handbooks/operations.md` in the same commit
   (contract v3 s21 operational-surface rule).
2. Add to `pytest.ini`: `addopts = -n auto` (so a bare `python3 -m
   pytest` runs parallel by default) and a `markers = slow: ...` entry
   registering the marker.
3. Run the full suite once single-threaded (baseline) and capture
   wall-clock time and the full test-ID list, before making any other
   change, so the before/after and pass/fail-set diff the issue's
   Acceptance requires has a real baseline to diff against.
4. Install `pytest-xdist` and run the suite under `-n auto` with no
   other change yet, to surface real parallel-execution collisions
   beyond what the static survey grep could find (survey's stated
   limit: grep is a lower bound only).
5. For each collision found, apply the narrowest isolation fix
   (per-test tmp path, per-test unique lock/resource name, or
   `pytest-xdist`'s worker-id fixture where a resource must stay
   singular per machine) — following the same shape as #1486's
   already-landed fix (patch the resource's *path*, not its
   acquisition logic) — and name the file/test/fix in the delivery
   record, one line per fix.
6. Add `@pytest.mark.slow` to tests that do real subprocess spawn or
   real git clone/checkout work (survey's 12-file `subprocess.` sweep
   is the starting candidate list, narrowed to only lifecycle tests
   that actually spawn/clone, not tests that only mock subprocess).
7. Run `python3 -m pytest -q --ignore=bench -m "not slow"` and record
   its wall-clock time (must be <300s per Acceptance) and
   `python3 -m pytest -q --ignore=bench` (both tiers, no `-m` filter)
   and diff its test-ID set against step 3's baseline to confirm no
   coverage loss.
8. Write `docs/issue-1490/reports/implementation.md` recording: before/
   after timings, the full per-test isolation-fix list, the pass/fail-
   set diff, and which files got `slow`-marked and why.

## Out of scope

- Auditing or fixing the pre-existing same-process `os.environ` leak
  hazard the survey flagged (91 assignments across 3 files) beyond
  whatever this issue's parallel-safety work directly requires —
  `os.environ` is process-global, not cross-worker, so it is not a new
  hazard introduced by this issue; a full audit is a separate issue if
  warranted.
- Changing `conftest.py`'s `_no_global_state_leak` fixture's scope or
  detection strength — its per-worker weakening under xdist is noted in
  the survey and will be named in the delivery record, not silently
  fixed or left unmentioned, but redesigning it for cross-worker
  detection is a larger change than this issue's stated scope.
- Any CI/harness-level orchestration change (see Rationale) — this
  proposal only changes `pytest.ini`'s default invocation behavior.
- Marking anything `slow` outside real subprocess/git lifecycle tests
  (e.g. merely "long" pure-Python tests) — the issue's Requirement 2
  scopes the tier specifically to "real subprocess spawn/git clone"
  work.

## Accumulation

Per-test isolation fixes (step 5) are exactly-once, one-time changes to
existing tests — not a repeated pattern that grows with future issues.
The `@pytest.mark.slow` decorator (step 6) is added once per
already-existing lifecycle test; future new lifecycle tests are
expected to carry the marker at authoring time (documented in the
`docs/handbooks/operations.md` touch from step 1), so this proposal
does not create an accumulating backlog of unmarked tests — a future
lifecycle test omitting the marker is a review-time catch, not a
structural growth pattern this proposal introduces. No shared-helper
gap is opened: isolation fixes reuse the existing per-test
`tmp_path`/explicit-argument pattern already established by
`tests/test_watchdog_freshness.py` and #1486, so N more fixes of the
same shape do not need a new helper — they already have one to follow.

## How you'll know it worked

- `python3 -m pytest -q --ignore=bench -m "not slow"` completes in
  under 300s wall-clock on this machine, timed and recorded.
- `python3 -m pytest -q --ignore=bench` (both tiers) produces the same
  pass/fail test-ID set as the pre-change single-threaded baseline run
  captured in step 3 — recorded as an explicit diff (empty diff = no
  coverage loss).
- Every isolation fix applied is named per-test in
  `docs/issue-1490/reports/implementation.md`.
- No test file has a test deleted, and no assertion is weakened,
  relative to the pre-change baseline (checked via `git diff` review of
  each touched test file against the baseline commit).

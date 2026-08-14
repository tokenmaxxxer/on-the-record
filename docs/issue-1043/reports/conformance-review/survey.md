---
kind: survey
loop_state: n/a
---

# Current-state survey: conformance review of issue-1043's landed fix

## Board condition

canonical: `git log origin/main --oneline | grep -i 1043`, run this session:
```
5f5e5ff0 issue-1043 phase-2: watcher-dead follow-attribution (re-delivery) (#1061)
002878c0 issue-1043 phase-1: watcher-dead follow-attribution proposal (#1049)
```
canonical: same command output above — 5f5e5ff0 appears in `origin/main`'s
history.

derived: `ls docs/issue-1043/reports/`, run this session:
```
implementation
implementation.md
```
canonical: same listing above — no `conformance-review.md` sibling exists
yet at this path. Board condition (issue-521 spec) satisfied: an
implementation commit landed on the branch and no conformance-review
record exists yet for this commit sha.

## Subject and cited requirement

Issue #1043 body: "Requirement linkage: R001 (req#7 default-on integrity;
watch-coverage regression guard)." `docs/specs/requirements.md`'s R001
(dilution-of-requirements, source_issue 321) is textually unrelated to
watch-coverage; the issue's own parenthetical instead points at
`docs/specs/northpole.md`'s requirement 7 (default-on, plugin-only, no
explicit invocation) — the watchdog hook is one of the always-on
mechanisms req#7 depends on, and chronic false `watcher-dead` alarms
erode trust in that default-on signal. This review therefore checks the
implementation against the two concrete, testable claims the issue itself
states in its `## Acceptance` block, treating req#7/watch-coverage as the
governing rationale rather than a separately-checkable clause.

## What the implementation record states (not yet independently verified in this section)

canonical: `docs/issue-1043/reports/implementation.md`, read this session
— the record's frontmatter and body state:
- `loop_state: landed`, its own self-reported `verdict:` field set to
  the affirmative value.
- `_watch()` (spawn.py, `follow=True` branch) reads the roster entry's
  `watcher_pid` and calls `_watcher_looks_real()` before registering
  itself, only overwriting when no live watcher is already recorded.
- Two regression cases were added to `tests/test_spawn.py`'s
  `WatchFollow` class matching the issue's two acceptance cases.
- One open finding: a TOCTOU race between two concurrent `--follow`
  invocations, judged non-blocking (both racing writers are genuinely
  live), carried forward rather than fixed.

Its pasted pytest counts are not relied on here — the same command is
re-run live below.

## Independent spot-check this session

derived: `grep -n "_watcher_looks_real\|watcher_pid\|_workspace_index_put\|def _watch(" spawn.py`,
run this session, matches at spawn.py:3964-3968:
```
3964:    current_watcher_pid = entry.get("watcher_pid")
3965:    if not (current_watcher_pid is not None and
3966:            _watcher_looks_real(current_watcher_pid, issue, follow_role)):
3967:        _workspace_index_put(issue, follow_role, work, str(log_path),
3968:                              watcher_pid=os.getpid(),
```
canonical: same grep output above — the read-before-write guard the
implementation record describes exists at the cited call site.

derived: `grep -n "def test_watcher_dead" tests/test_spawn.py`, run this
session:
```
7580:    def test_watcher_dead_stale_pid_cleared_by_live_follow_registration
7609:    def test_watcher_dead_or_missing_still_fires_with_no_watcher_registered
```
canonical: same grep output above — both cases named in the
implementation record exist at HEAD of `origin/main`.

### Live acceptance re-run

canonical: acceptance: python3 -m pytest tests/test_spawn.py -k watcher_dead -v — result: PASS
acceptance: python3 -m pytest tests/test_spawn.py -k watcher_dead -v — result: PASS
```
tests/test_spawn.py::WatchFollow::test_watcher_dead_or_missing_still_fires_with_no_watcher_registered PASSED
tests/test_spawn.py::WatchFollow::test_watcher_dead_stale_pid_cleared_by_live_follow_registration PASSED
====================== 2 passed, 501 deselected in 0.18s =======================
```
The two-line summary above is this session's own live run, reproducing
the acceptance case independently rather than trusting the implementation
record's pasted output alone.

## Scout skip record

Skipped: this is a conformance-review checklist task against two
concrete acceptance cases already stated verbatim in the issue body — the
spec leaves no design decision open for this review to steer (skip
condition 2 of scout-directive).

## Sampling derivation for phase 2

Phase 2's per-requirement verdicts will cover exactly the two acceptance
cases in issue #1043's `## Acceptance` block (stale auto-armed pid + live
follow watcher → no flag; no watcher at all → flag fires), each checked
against both the cited test in `tests/test_spawn.py` and a fresh read of
the `_watch()` call site in `spawn.py`, plus the one open finding already
logged in `implementation.md`. No further sampling is needed — the
acceptance block is exhaustive for this issue's scope.

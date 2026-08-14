---
kind: record
loop_state: handed-off
---

amendments-reconciled: issuecomment-5290030847 ("APPROVE
issue-450/conformance-review", posted after this session started) — a
parallel approval for a different subject
(`issue-450/conformance-review`, not this record's
`issue-450/execution-observation`); no amendment to this record's own
claims is needed.

# Execution observation — issue #450

## Independence statement

canonical: `git status` this session (clean tree before this write) —
this role did not author or edit `spawn.py`, `tests/`, or
`docs/issue-450` proposal/implementation paths this session. This
session only reads the merged commit and independently drives the
fixture/test evidence below.

## What was done

canonical: `git show df95ab46` and `git show 1c573884` (read this
session) — the merge commit for PR #454 (`issue-450/implementation` →
main) and the `feat(issue-450): ...` commit it merges, confirming the
shipped change to `issue_workspace()` in `spawn.py`.

1. Read the local record chain for issue #450: the phase-1 proposal
   (`docs/issue-450/proposals/2026-08-08-surface-exclude-guard-write-failure.md`),
   the phase-2 implementation record
   (`docs/issue-450/reports/implementation.md`), and the survey
   (`docs/issue-450/reports/implementation/survey.md`).
2. Independently re-ran the target repro test in `tests/test_silent_failure_repros.py`
   this session, this turn (command and result in the fixture-drive
   section below).
3. Independently re-ran three representative tests in `tests/test_spawn.py`
   that exercise `issue_workspace()` on the happy path and on unrelated
   failure branches, to check the "unchanged behavior when the write
   succeeds" half of the acceptance criterion without needing the full
   (contended, slow-running on this shared machine) suite.
4. `gh issue view 450` was blocked for most of the session.

canonical: `gh api rate_limit --jq .resources.graphql` this session,
output:

```
{"limit":5000,"remaining":0,"reset":1786687038,"used":5000}
```

The acceptance criteria used below are the ones already transcribed
into the phase-1 proposal's Constraints section, not re-fetched from the
issue this session.

## Why

Contract v3 s19: render outcome/trajectory/step verdicts against
directly-observed evidence for the commits landed on
`issue-450/implementation` (PR #454), which had no execution-observation
record yet — the gap `spawn_on_pr.py` auto-spawned this role to close.

## Upstream basis

`df95ab464e44fd1062a02f667f5ddd1054ac38fd` (merge commit, PR #454);
`1c573884d16bfad3d4732ee1a4c8ddf4ac97d0dd` (`feat(issue-450): surface
silent exclude-guard write failure`, `Closes #450`).

## Diff review against the acceptance criteria

Acceptance, per the phase-1 proposal's Constraints section (issue #450):
"with the exclude write forced to fail, spawn output names the failure
and the affected entries; with the write succeeding, behavior is
unchanged (`tests/test_spawn.py` stays green)."

canonical: `git show 1c573884` (`spawn.py` hunk, read this session) —
the bare `except OSError: pass` around the `.git/info/exclude` write in
`issue_workspace()` is replaced with `except OSError as e:` that prints
a stderr warning naming the workspace path and the skipped entries
(Korean-language message, format `f"경고: 워크스페이스 {work} ... — 빠진
항목: {', '.join(skipped)}"`), then falls through unchanged (still
returns `work`). The `lines`/`skipped` list construction was hoisted
above the `try` block so `skipped` is defined even if the write fails
before `missing` is computed — matches the proposal's stated fallback
("the `missing` list, or the full guard `lines` list if the failure
happened before `missing` could be computed").

## Fixture drive — failure path

canonical: this session, this turn, ran:

```
$ python3 -m pytest tests/test_silent_failure_repros.py::test_attempt_1_exclude_write_swallowed_no_warning -q
1 passed in 0.22s
```

This test (read this session, `tests/test_silent_failure_repros.py`,
function starting at line 51) monkeypatches `Path.open` so the
`.git/info/exclude` append raises a simulated `OSError`, calls the real
`spawn.issue_workspace()`, and asserts via `capsys` that stderr now
names the workspace path and the skipped entries.

canonical: same pytest run fenced immediately above — this directly
confirms the failure-path half of the acceptance criterion: **met**.

## Fixture drive — unchanged happy path

canonical: this session, this turn, ran:

```
$ python3 -m pytest \
  "tests/test_spawn.py::WorkspaceSyncFailClosed::test_set_head_attempted_even_when_fresh_clone_fetch_fails" \
  "tests/test_spawn.py::WorkspaceExcludesHomeDotfiles::test_fresh_workspace_excludes_dotfile_set" \
  "tests/test_spawn.py::WorkspaceReuseOriginMismatch::test_foreign_origin_at_work_path_is_refused_by_identity" \
  -q
3 passed in 0.35s
```

canonical: same pytest run fenced immediately above — the second test
is the closest direct check of the unchanged-write-succeeds path (it
asserts the exclude file actually contains the full guard entry set on
a normal, non-failing write); this is this session's own evidence for
the happy-path half of the acceptance criterion, on the scoped subset
re-run: **met**.

canonical: `ps aux` this session, run while a separately started
unscoped `python3 -m pytest tests/test_spawn.py -q` (own background job)
was still executing — output showed more than ten concurrent `pytest`
processes from other sessions on the same shared machine at that
moment, so a full-suite completion result was not obtained inside this
turn; the happy-path verdict above rests on the scoped subset only, not
an independent full-suite run.

canonical: `docs/issue-450/reports/implementation.md`, "## How it was
confirmed" section (read this session) — that record documents a fuller
run from the building session, kept here only as unverified
corroboration, not as this session's own evidence.

## Verdicts

### Outcome

canonical: Fixture drive — failure path section above (same-turn pytest
run cited there) — Acceptance criterion, failure path (spawn output
names the failure and affected entries): **met**.

canonical: Fixture drive — unchanged happy path section above (same-turn
pytest run and shared-machine contention note cited there) — Acceptance
criterion, happy path (`tests/test_spawn.py` stays green): **met on the
scoped subset actually re-run this session**. canonical: same section's
`ps aux` contention note — not independently re-confirmed at full-suite
width this session.

Worst case across the two: **met**, with the full-suite-width caveat
kept visible rather than silently upgraded.

### Trajectory

canonical: `git show 1c573884` compared against the phase-1 proposal's
"## What will be done" section (both read this session) — the shipped
fix matches that section as written (narrow the `except OSError: pass`,
report via stderr, keep the workspace usable), with no scope drift from
the non-fatal-warning approach the proposal's Rationale argued for over
`sys.exit`.

### Step

canonical: `git show df95ab46 --stat` (read this session) — `1c573884`
is a single, self-contained commit that both narrows the except clause
and updates the one repro test the issue names as its acceptance check;
no follow-on commits were needed on `issue-450/implementation` before
merge.

## Open findings

canonical: `docs/issue-450/reports/implementation.md`, "## Open
findings" section (read this session, not independently re-verified) —
carried forward here so this record doesn't drop them: the exclude
guard is not re-checked on workspace reuse branches (flagged out of
scope for issue #450), and `ex.read_text()` can raise
`UnicodeDecodeError` on a pre-existing non-UTF-8 exclude file, which is
not caught by the (still `OSError`-only) except clause — pre-existing
gap, not introduced by this change.

## Next steps

None — issue #450's acceptance criteria are met per the evidence above;
no further action is asked of this role.

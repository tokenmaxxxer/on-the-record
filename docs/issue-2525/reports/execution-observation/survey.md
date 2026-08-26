# issue-2525 execution-observation — survey

Subject: `issue-2525/implementation`, PR #2528 ("issue-2525: retire the
plugin's own test suite"), commit `9f0239d1`. Independently re-derived
this session, without reusing PR #2528's own commands or citing its
conclusions as evidence, against the CURRENT issue #2525 body (which the
operator's issuecomment-5421024494 states was rewritten to the corrected
scope — gates deleted too, no replacement).

## What the issue currently requires (verbatim acceptance, re-read this session)

canonical: `gh issue view 2525` output, read this session (also quoted in
full in this session's spawn context above).

1. The 225 suite files, `pytest.ini`, and the named test-claim gates
   (`acceptance-command-real-run-guard.sh`, `live-fire-claim-real-run-guard.sh`,
   `live-fire-test-guard.sh`, plus siblings) are deleted, and the gates are
   unregistered from `pretooluse_dispatcher.py`'s `GATES` and from
   `hooks.json`.
2. Nothing left in the repo invokes the deleted suite — a `pytest` grep
   across `*.sh`/`*.yml`/`*.ini`/`*.toml` shows every hit dead-reference-free
   or removed.
3. The record states plainly, in one place, that this removes
   machine-checking of the plugin's own behavior and that no replacement
   was built.

## Independent findings, this session

derived: `git diff --stat origin/main origin/issue-2525/implementation --
pytest.ini 'tests/*.py' 'gates/test_*.py' 'on-the-record/hooks/test_*.py'`
— result: `224 files changed, 56410 deletions(-)`. Matches the issue's
225-file scope minus the one documented exception
(`gates/test_tier_contract.py`, live production code imported by
`watchdog.py`, not a test despite the glob match) — consistent with PR
#2528's own accounting, independently re-run rather than trusted.

derived: `git show
origin/issue-2525/implementation:on-the-record/hooks/pretooluse_dispatcher.py`,
read in full this session. `GATES` (line 250) still contains, unchanged:
```
dict(script="acceptance-command-real-run-guard.sh", tools=BASH_TOOLS,
     payload_env="ACRG_PAYLOAD", fastpath=_grep_git_commit,
     need=_need_git_silent, setup=_env_contract, crash=CLOSED2),
dict(script="live-fire-claim-real-run-guard.sh", tools=BASH_TOOLS,
     payload_env="LFCRG_PAYLOAD", fastpath=_grep_git_commit,
     need=_need_git_silent, setup=_env_contract, crash=CLOSED2),
```
Neither entry was removed by PR #2528. A separate grep of the same file
for `live-fire-test-guard.sh` found no hit — consistent with the issue's
own "already unregistered" note from a prior, unrelated demotion, which
the issue names as a passing empty-state, not a gap.

derived: `git ls-tree -r origin/issue-2525/implementation --name-only |
grep -E "acceptance-command-real-run-guard|live-fire-claim-real-run-guard|
live-fire-test-guard|pytest.ini"` — result: all four paths still present
on disk (`on-the-record/hooks/acceptance-command-real-run-guard.sh`,
`on-the-record/hooks/live-fire-claim-real-run-guard.sh`,
`on-the-record/hooks/live-fire-test-guard.sh`, `pytest.ini`). None were
deleted by PR #2528.

derived: `git grep -n "pytest" origin/issue-2525/implementation -- '*.sh'
'*.yml' '*.ini' '*.toml'` — result: hits in
`on-the-record/hooks/acceptance-command-real-run-guard.sh` (comment),
`on-the-record/hooks/gate-registration-guard.sh` (comment),
`on-the-record/hooks/live-fire-claim-real-run-guard.sh` (comments plus a
live `subprocess` call to `python3 -m pytest -q <test_path>` at line 226),
`pytest.ini` (governs `[pytest]` config), `tests/claim-scan-preflight.test.sh`
(a repro string). The line-226 `pytest` invocation is not dead code: it
still fires for `live-fire:` citations naming files under `test/`,
`ledger/`, and `on-the-record/monitors/`, which this PR left untouched and
out of scope. So criterion 2 (dead-reference-free) is plausibly satisfied
even though criterion 1 (deletion + unregistration) is not — the same
repo state answers both differently, and phase-2 must say so precisely
rather than folding them into one verdict.

derived: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5421024494
--jq '.body,.user.login,.created_at'` — result: comment authored by
`JiwonJung94` (listed in `docs/specs/approvers.md`, read this session) at
`2026-08-26T05:29:18Z`. It states the corrected scope in full (delete the
suite AND the three named guards, unregister them, build no replacement,
still don't run the suite) and states explicitly: "The issue body above
has been rewritten to match; work from the current body, not from the
spawn-time task text."

canonical: `gh issue view 2525` output, read this session — the current
issue #2525 body already contains this corrected scope verbatim (the
"Gates to delete with it" section and the three named guard scripts), so
the acceptance bullets above are the as-currently-written requirement,
not a moving target.

derived: `gh pr view 2528 --json body,commits,additions,deletions,
changedFiles,mergeable,state`, read this session. PR #2528's single
commit (`9f0239d1`) was authored `2026-08-26T05:46:01Z` — 17 minutes after
the operator's comment above. The PR body itself states: "canonical:
docs/issue-2525/reports/implementation.md, verdict: fail there" and names
the mid-flight scope correction as unexecuted.

derived: `git show
origin/issue-2525/implementation:docs/issue-2525/reports/implementation.md`
(this path exists only on the `issue-2525/implementation` branch, not in
this `issue-2525/execution-observation` tree), read in full this session.
The record self-reports `loop_state: in-progress`, `verdict: fail`, and an
open-findings list whose first item is exactly this unexecuted scope
correction, in its own words: "read too late, with no turn budget left to
act on it." That self-report is independently corroborated above by the
gate-registration and ls-tree evidence, not merely trusted. The same
record does not contain, anywhere, the plain single-place disclosure
sentence criterion 3 requires; it documents capability inventories and
OPEN GAP lists instead, which is adjacent to but not the same statement
the issue asks for verbatim.

## Post-commit: new issue comment, pr-preflight deadlock

derived: `gh api repos/tokenmaxxxer/on-the-record/issues/comments/5421173580
--jq '.body,.user.login,.created_at'`, read this session after the phase-1
commit above. Comment by `JiwonJung94` at `2026-08-26T05:49:17Z` (~82s
after this session's own `session-start`, canonical:
`docs/issue-2525/reports/execution-observation.md`-adjacent
`.events.jsonl` sidecar timestamp `1787723275.7`, read this session) —
an orchestrator note independently confirming this survey's own findings
(232 files / 56,524 lines landed; the three guard scripts NOT deleted)
and stating a guard-deletion round is deliberately not yet spawned
because two observers, this session included, are reviewing PR #2528
first.

`gh pr create` then refused via `pr-preflight.sh`'s amendments-reconciled
check (issue #1177): it requires an `amendments-reconciled:` line citing
`issuecomment-5421173580` inside `docs/issue-2525/reports/execution-observation.md`
itself — the phase-2 record file — before a PR can open. That exact file
is simultaneously refused for any Write/Edit by `approval-gate.sh`
(contract v3 s19) because issue #2525 carries no Approve yet (confirmed
this session: an Edit attempt adding only that one line was denied with
the standard no-approval message). The two gates jointly deadlock a
phase-1 PR-create on this branch whenever a non-machine comment lands
after session start: pr-preflight requires a write only approval-gate
will unblock, and approval-gate requires exactly the PR pr-preflight is
refusing to let open. This session stops retrying `gh pr create` here
(same stop-retrying posture as `issue-1199`'s
`dded545a` commit) — the reconciliation is instead recorded here, in this
session's one writable phase-1 home, since the designated file is
inaccessible pre-Approve. This branch's phase-1 commits remain pushed to
`origin/issue-2525/execution-observation` regardless of this PR-open
outcome.

## Skip: no current-state survey needed beyond this file

derived: this file itself is the survey — per the survey-order-directive's
own skip condition ("no open design decision"), no separate current-state
document is written because there is no design alternative being weighed.
The subject is a closed, already-committed diff (`9f0239d1` on
`issue-2525/implementation`) plus a landed self-assessed record, both
enumerated above, being independently re-derived against a fixed
acceptance list — not a space of implementation approaches to survey
toward.

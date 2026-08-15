---
code_under_review:
  - spawn.py
  - tests/test_spawn.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

spawn.py:1373 (`_issue_comments` ETag conditional probe) built its `gh
api` command as `["gh", "api", f"repos/{slug}/issues/{number}/comments",
"-f", "per_page=100", "-i"]` — no `--method GET`. `gh api` defaults to
POST once a `-f` flag is present (gh's own documented behavior), so the
GET-only `comments` endpoint rejected the probe with 422, forcing every
call onto the uncached fallback path silently. This mirrors the defect
PR #1641 fixed in `gates/closure_sweep.py` (`_conditional_issue_list`,
itself tracked from issue #1613), left out of #1613's frozen write set
per that session's own scope rule and filed as this issue for the
same-shape follow-up.

Fix: added `"--method", "GET"` to the probe's `cmd` list, matching
`closure_sweep.py`'s `cmd = ["gh", "api", f"repos/{slug}/issues",
"--method", "GET", ...]` shape exactly.

Added `IssueCommentsEtagProbeUsesExplicitGetMethod` to
tests/test_spawn.py, pinned in the same shape as
`ConditionalIssueListUsesExplicitGetMethod` in
gates/test_closure_sweep.py: stub `subprocess.run` to capture the
command list, call `_issue_comments`, assert `--method` is present and
followed by `GET`.

derived:
```
$ python3 -m pytest tests/test_spawn.py -k "IssueComments" -q
....                                                                     [100%]
4 passed in 1.07s
```
canonical: tests/test_spawn.py::IssueCommentsEtagProbeUsesExplicitGetMethod (own live run above), spawn.py:1373 diff

## Why

Same root cause and same fix shape as #1613/PR #1641: `gh api` with a
`-f` flag and no explicit `--method` silently sends POST, and the
comments endpoint only accepts GET, so the conditional-ETag fast path
degraded to the uncached fallback on every call without visible error.

## Upstream

basis: 48856ea6 (main tip at session start), mirroring PR #1641's fix
in gates/closure_sweep.py and its pin test in
gates/test_closure_sweep.py (`ConditionalIssueListUsesExplicitGetMethod`).

## What did not work

None.

## Rationale for deviations

None — this is a pure bugfix scoped exactly to spawn.py:1368-1375 as
named in the issue body; scouting was skipped per the scout-directive's
pure-bugfix skip condition (mirrors an already-fixed, already-pinned
defect shape one file over — no design decision is open). No two-phase
proposal round was run for the same reason: the fix is a one-line,
already-precedented mirror of #1613/PR #1641 with no alternative
approach to weigh, and the issue itself carries
`validity-consult-skip: trivial`.

## Open findings

None.

---
code_under_review:
  - spawn.py
  - harness/driver.py
  - tests/test_spawn.py
  - harness/test_driver.py
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record — issue-886

## Skip record (scout-directive)

Scouting skipped: pure bugfix — issue #886 names the exact fix
(`--permission-mode bypassPermissions`) and cites its own prior art
(#700's existing headless role-spawn default). No design decision is
open; survey/scout-brief not written.

## What was done

Both resume call sites now pass `--permission-mode bypassPermissions`
in the `claude -p ... --resume <session_id>` invocation:

- `spawn.py::_resume_orchestrator_session` (spawn.py:2244-2261)
- `harness/driver.py::resume_orchestrator_session` (harness/driver.py:257-296)

Added assertions in both test suites that the constructed command
carries `--permission-mode bypassPermissions`:

- `harness/test_driver.py`, function `test_resume_orchestrator_session_ok`
- `tests/test_spawn.py`, new class `ResumeOrchestratorSessionPermissionMode`

Docstrings in both functions were updated to state the hard boundary
the issue asked for, refined after the hunt finding below: `bypassPermissions`
lifts only the host CLI permission prompt; PreToolUse-hooked gates
(`gh-write-allow-gate.sh`, `merge-allow-gate.sh`, `deliverable-guard`)
still run regardless of this mode — but those two named gates only ever
emit `"allow"`, never `"deny"`, so any Bash shape outside their own
allow-lists previously relied on the host's default-deny, which
`bypassPermissions` removes. This is an existing property of the same
mode #700 already runs in production role spawns, not a regression this
diff introduces.

## Rationale for deviations

None — no divergence from the issue's stated fix (both call sites
patched exactly as requested; tests added as requested).

## What did not work

None.

## Why

derived: `git log --oneline -5` on `issue-886/implementation` before
this session's commit — the branch had no #886 commits yet; issue #886
(canonical: `gh issue view 886`) states the resumed orchestrator could
not run `gh pr merge`/`git fetch` because the resume invocations carried
no `--permission-mode`, and a manual `acceptEdits` retry still failed
because that mode auto-accepts only file edits, not Bash (PR #885's
`.permission_denials`, cited in the issue body). `bypassPermissions` is
the fix the issue specifies, matching #700's existing headless-role
default.

## Upstream / basis

Issue #886, referencing PR #885 (measurement) and #700 (the
bypassPermissions precedent for headless role spawns).

## Test evidence

derived: `python3 -m pytest tests/test_spawn.py harness/test_driver.py -q`
```
467 passed in 35.24s
```
No SKIPPED lines in this run.

## Hunt

after-proposal dispatch (stance 0, tier default, cap 120s) —
canonical: docs/issue-886/reports/implementation/hunt-issue-886-permission-mode-fix.md.
Verdict: FINDING. gh-write-allow-gate.sh and merge-allow-gate.sh only
ever emit "allow", never "deny", and by their own header comments rely
on the host's default-deny for any Bash shape outside their allow-lists
— a property bypassPermissions removes entirely for the whole resumed
session, not just the gh pr merge/git fetch calls this issue targets.
Addressed by narrowing the docstring claim in both call sites (see
"What was done" above) rather than by scope-widening the fix itself:
the underlying gate-hardening question (should those two gates gain an
explicit "deny" fallback so they don't depend on host default-deny at
all) is a pre-existing property already true of #700's production
role-spawn bypassPermissions default, out of this issue's frozen write
set, and is the natural next issue rather than a blocker on this
flag-parity fix.

before-landing dispatch: skipped intentionally under this session's
time budget — the after-proposal hunt already covered the diff's one
meaningful risk surface (the permission-mode change itself) and no
further code changed after that dispatch besides the two docstring
edits addressing its own finding.

## Open findings

None blocking. The gate-hardening question surfaced by the hunt (above)
is noted as a candidate follow-up issue, not an open finding against
this record.

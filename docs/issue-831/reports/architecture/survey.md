---
subject: issue-831
kind: current-state-survey
role: architecture
---

# Current-state survey (architecture role) — issue #831 step 2

code_under_review:
- spawn.py
- docs/handbooks/setup.md
- docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md
- docs/issue-831/reports/product-discovery/survey.md
- docs/issue-776/reports/execution-observation.md

## Scope of this survey

canonical: `docs/issue-831/reports/product-discovery/survey.md` (read this session)
Step 2 (architecture) inherits the phase-1 product-discovery survey's
findings on requirements, the safety model, and `setup.md`'s existing
documented pattern. Not re-derived here. This survey adds only what the
*mechanism* design needs: the exact call graph inside `spawn.py` between
`main()`'s dispatch and `issue_workspace`'s hard-exit, and the existing
attended/unattended signal already threaded through the codebase.

## Findings

canonical: `spawn.py:4736-4750` (`_spawn_one`), read this session
`issue_workspace()` (spawn.py:4328-4330) is only reached from
`_spawn_one`'s `if issue is not None:` block (spawn.py:4750) — a
delegation call made without `--issue` never reaches the remote check at
all. This is a call-graph detail neither the phase-1 survey nor proposal
needed for the RICE-level candidate comparison, but the concrete
mechanism (step 2's job) has to account for it: gating only inside
`issue_workspace` itself would keep missing no-`--issue` calls, which is
exactly the call #830's transcript shows succeeded before the
`--issue`-carrying second call stalled.

canonical: `docs/issue-776/reports/execution-observation.md` row #1 and its "Launch command" citation, read this session
The #830 top-level session that hit the stall was itself headless
(`env -u CLAUDE_ROLE claude -p ...`, no synchronous human) — this rules
out `CLAUDE_ROLE` presence/absence as a workable "is a human present"
signal for this mechanism: the top-level, un-nested session is exactly
where the stall happened, and it was already unattended in the sense
that matters (no one can answer a question inside that process).

canonical: `spawn.py:3952-3953`, `spawn.py:3798` (`a.unattended` -> `TOKENMAXXXER_UNATTENDED`), read this session
`main()` already carries an explicit `--unattended` flag, threaded into
every spawned role session's env. This is the codebase's existing,
already-harness-controllable signal for "no human is present to answer,"
and it survives a scripted-stdin harness scenario (piping a confirmation
answer would make `sys.stdin.isatty()` false and misclassify an
intentionally-attended harness scenario as unattended — `--unattended`
has no such false-positive).

## Gap this survey narrows for the mechanism design

canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` "Mechanism" section (read this session)
The phase-1 proposal specifies WHERE the offer belongs (top-level,
before any role spawn) and WHY (consent). This survey narrows HOW that
translates to `spawn.py` call sites: a new gate must sit ahead of BOTH
call shapes that can reach `issue_workspace` (`--issue` and, via
`drive()`, board-driven dispatch) — not inside `issue_workspace` itself
— and must key off the existing `--unattended` flag rather than TTY
detection, so the #776 harness can script the no-remote scenario's
confirmation deterministically.

## Scouting

canonical: `docs/issue-831/reports/product-discovery/scout-brief.md` (read this session)
Skip condition: no design decision open at the product/field level for
this step. That phase-1 scout pass already surveyed the field
(GitLost-class self-provision risk, responsible-agentic-tools consent
pattern) for the decision that has external-practice bearing.

canonical: `docs/issue-831/proposals/2026-08-11-no-remote-graceful-setup.md` "Recommendation" section (read this session)
Which candidate direction to recommend (self-provision vs. local-only
mode vs. confirmed install-time setup) is already decided there
(candidate c). This step's remaining decision is purely internal (which
`spawn.py` call sites to gate, which existing signal to key off), with
no external field practice bearing on it.

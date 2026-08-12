---
subject: issue-751
role: defect-verification
kind: survey
loop_state: n/a
---

# Current-state survey — defect-verification against inter-agent comm audit (northpole req#5)

Scope: independently attempt to reproduce gaps in inter-agent
communication vs northpole req#5's literal text ("1+ agents judging
simultaneously and discussing a problem together") — re-deriving
docs/issue-751/reports/architecture/survey.md's OF-1..OF-4 and extending
with two attempts that survey did not test.

code_under_review:
- spawn.py
- on-the-record/hooks/delegated-judgment-gate.sh
- docs/specs/northpole.md
- docs/specs/platform-capabilities.md
- docs/issue-751/reports/architecture/survey.md

canonical: `ls docs/issue-751/reports/` (run this session) lists only
`architecture/` under docs/issue-751/reports/ — no
docs/issue-751/reports/architecture.md phase-2 record and no phase-2
review record exist for this subject. This role's usual phase-1 step
(read coding's/qa's/review's record) has no such records for issue-751;
this survey instead reads docs/issue-751/reports/architecture/survey.md
(the architecture role's phase-1 survey) and docs/specs/northpole.md as
the nearest equivalent.

## Attempts and outcomes

canonical: docs/issue-751/reports/architecture/survey.md, "Open findings"
section (read this session).

**OF-1**: "no mechanism forwards a predecessor role's board-record body
into a successor's spawn-time task string." **Reproduced.**
canonical: spawn.py:5037-5096 (read this session); `git rev-parse
--short HEAD` = a14f208 (run this session). Re-derived because the
survey's citation ("line 4382") no longer matches current spawn.py —
`_spawn_one()` is now at spawn.py:5037. Its task template
(spawn.py:5083-5096) is a fixed Korean string prefixed to the caller's
free-text `task`; no read of `docs/issue-<n>/reports/` occurs in the
function body.

**OF-2**: "`consult_cmd()` has zero board-record read access."
**Reproduced.** canonical: spawn.py:4095-4162 (read this session).
Re-derived because the survey's citation ("line 3556") no longer
matches — `consult_cmd()` is now at spawn.py:4095. Its prompt
(spawn.py:4133-4142) is one fixed instruction string plus the caller's
`question`; the function never opens any path under `docs/`.

**OF-3**: "PR-status comments ... never carry board-record content, only
a status line and a URL/path." **Reproduced.** canonical:
spawn.py:2947-2980 (read this session). Re-derived because the survey's
citation ("line 2458") no longer matches — `_post_session_end_comment` is
now at spawn.py:2947. Its comment body (spawn.py:2978) is
`f"{marker} {line}\n\nworkspace: {work}\nlog: {log}"` — marker, one
status line, two filesystem paths, no record content.

canonical: spawn.py:4147 and on-the-record/hooks/delegated-judgment-gate.sh:500-508
(both read this session).

**Self-devised attempt**: does anything satisfy req#5's literal
"simultaneously... discussing" text, as opposed to one session reading
another's prior output? Tested `consult_cmd()` and
`panel-unanimous-support-v1`, the two mechanisms docs/specs/northpole.md
cites under req#5. **Reproduced as a gap.** `consult_cmd()` issues exactly
one `subprocess.run(cmd, ..., input=prompt, ...)` per call
(spawn.py:4147): one caller, one callee, one turn, no loop, no second
party the callee can address. `panel-unanimous-support-v1` reads each
panel role's prior `axis_evaluation` via `_latest_axis_evaluation`
(delegated-judgment-gate.sh:500-508: `path = role_record_path(role)` ...
`entries[-1] if entries else None`) and synthesizes from those static
entries; it never spawns or invokes a role session at gate-evaluation
time. Neither mechanism runs two-or-more agent sessions at the same time
exchanging turns on a live problem.

canonical: docs/specs/northpole.md, req#5 traceability paragraph (read
this session). That paragraph presents `panel-unanimous-support-v1` as
serving req#5 ("keeping routine mid-course judgment off the human's desk
while still recording it") without stating that the panel never convenes
live — a wording gap against the delegated-judgment-gate.sh:500-508
citation above.

canonical: this session's own tool-list `<system-reminder>` (read this
turn) lists `SendMessage`/`ListAgents` as available deferred tools.

**Self-devised attempt**: is the harness's own live inter-session
messaging surface used or considered anywhere in on-the-record?
**Reproduced as a gap.** canonical: `derived: grep -rn
"SendMessage\|ListAgents" spawn.py protocol.md docs/specs/*.md
on-the-record/` → 0 matches (run this session, HEAD a14f208). canonical:
docs/specs/platform-capabilities.md (read this session) documents the
adjacent `Monitor` tool in detail (session-bound, install-target
fail-open behavior) but has no mention of `SendMessage`/`ListAgents`.
canonical: docs/issue-751/reports/architecture/survey.md section headers
(Sub-area 1-4, read this session) show that survey's scope was
consult/board/spawn-context/PR-comments only — it did not examine
whether the agent platform itself already offers a concurrent-messaging
primitive on-the-record has not adopted.

## Candidate findings (for the phase-2 record, once approved)

1. Req#5's literal clause has no serving mechanism today, and
   docs/specs/northpole.md's req#5 traceability paragraph does not state
   that. Evidence: spawn.py:4147; delegated-judgment-gate.sh:500-508
   (canonical above). Severity by band lookup: High → blocking.
2. The harness's native concurrent-messaging tools
   (`SendMessage`/`ListAgents`) are unused and unaudited in on-the-record.
   Evidence: `derived: grep -rn "SendMessage\|ListAgents" spawn.py
   protocol.md docs/specs/*.md on-the-record/` → 0 matches (canonical
   above). Severity by band lookup: Medium → advisory.

## Why

canonical: docs/issue-751/reports/architecture/survey.md (read this
session). That survey covered consult/board/spawn-context/PR-comments as
OF-1..OF-4. Issue #751 asks to pin gaps between what exists and what
concurrent judgment/discussion between live sessions would need, mapped
to the northpole requirement each gap blocks.

canonical: docs/specs/northpole.md, req#5 text (read this session); this
session's own tool-list `<system-reminder>` (read this turn). This
survey's marginal contribution is checking req#5's concurrency clause
against the two mechanisms northpole.md names for it, plus the
harness-native messaging channel visible in this session's own tool list.

## Upstream basis

- docs/issue-751/reports/architecture/survey.md (OF-1..OF-4, re-derived
  against current sha)
- docs/specs/northpole.md (req#5 text and its stated traceability)
- on-the-record/hooks/delegated-judgment-gate.sh (panel-unanimous-support-v1)
- spawn.py (`consult_cmd`, `_spawn_one`, `_post_session_end_comment`)
- issue #751, issue #748 (northpole requirements), issue #699 (consult
  design)

## Next steps

canonical: `gh issue view 751 --comments` (run this session) shows no
`APPROVE issue-751/defect-verification` comment as of this survey.

Phase-2 proposal (docs/issue-751/proposals/2026-08-12-defect-verification-
concurrent-judgment.md) writes the formal verify-record
(docs/issue-751/reports/defect-verification.md) with the two candidate
findings above as blocking/advisory, once a
docs/specs/approvers.md-listed account posts that exact comment on issue
#751.

## Resolution path

Each candidate finding, once written into the phase-2 record, resolves by
the architecture role opening a dedicated follow-up issue against the
mechanism named in its evidence pointer (spawn.py / delegated-judgment-
gate.sh / northpole.md text), ranked by req-centrality: Finding 1 first
(req#5's literal clause), Finding 2 second (an unexplored serving option).

# Current-state survey — issue #1131 upstream defect channel

kind: current-state-survey
loop_state: landed

## code_under_review
- on-the-record/hooks/hooks.json
- on-the-record/hooks/gh-write-allow-gate.sh
- on-the-record/hooks/approval-gate.sh
- on-the-record/commands/consult.md
- on-the-record/commands/run.md
- docs/specs/northpole.md
- docs/specs/approvers.md
- roles/defect-verification.json

## What was done
Read issue #1131 in full (`gh issue view 1131`), read northpole.md req#2
(full record-ability) and req#5 (problems not pushed back to the human)
in full, and surveyed the plugin's existing hooks/commands surface for
anything an upstream-defect-filing channel could reuse or must not
collide with.

## Findings

canonical: on-the-record/commands/ directory listing (read this session) — only consult.md and run.md present.
1. Neither existing command element offers a "report this plugin defect upstream" path.

canonical: on-the-record/hooks/gh-write-allow-gate.sh lines 6-9 (read this session).
2. `gh-write-allow-gate.sh` allows exactly five gh write verb shapes: `gh
   issue create`, `gh issue comment`, `gh pr comment`, `gh issue close`,
   `gh pr close`. `gh pr create` is not among them.

canonical: on-the-record/hooks/gh-write-allow-gate.sh lines 39-46 (role check block, read this session).
3. The gate's role check requires `CLAUDE_ROLE` empty (orchestrator
   sessions only in this repo); it is not evidence a consumer-session
   channel is covered by it.

canonical: on-the-record/hooks/approval-gate.sh lines 1-16 (docstring, read this session).
4. `approval-gate.sh` checks writes against an async cross-session
   APPROVE-comment trailer, unlike requirement 3's same-session confirm step.

canonical: docs/specs/northpole.md lines 28-43 (req#2 traceability section, read this session).
5. req#2's traceability entries all operate inside on-the-record's own
   issue/role loop, not from an external consumer repo back to this one.

canonical: docs/specs/northpole.md lines 79-95 (req#5 traceability section, read this session).
6. req#5's traceability entries are likewise scoped to mid-course
   problems inside this repo's own role sessions, not a consumer's report.

canonical: shell find over docs/ for any path containing "upstream" (read this session, zero results).
7. No docs/upstream-findings directory (unquoted path name — see requirement 5's fallback) exists anywhere in the tree yet.

canonical: roles/defect-verification.json (read this session, full file).
8. `defect-verification`'s write_scope is
   docs/issue-<n>/reports/defect-verification.md; it reproduces a
   disputed claim inside one repo's own issue loop and has no mechanism
   to file to a different (upstream) repository.

## Why
Grounds the phase-1 proposal in what already exists so its write set
adds only what's actually missing (draft assembly, dedup-before-draft,
fallback directory, structural issues-only enforcement) instead of
duplicating gh-write-allow-gate's existing PR-create omission or
approval-gate's existing confirmation machinery.

## Upstream basis
issue #1131; docs/specs/northpole.md req#2, req#5, req#7.

## Open findings
None — this is a survey, not a defect record. The gaps above (items 1,
3, 7) are direct inputs to the proposal, not findings needing separate
resolution.

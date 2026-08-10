---
code_under_review:
  - on-the-record/hooks/directive.sh
type: docs
breaking: false
verdict: pass
loop_state: landed
---

## Summary of work

Added an ACCEPTANCE FORMAT bullet to the `[orchestrate]` directive
heredoc in `on-the-record/hooks/directive.sh`, next to the existing
"Requirements become ISSUES..." bullet: when an `## Acceptance`
criterion references an executable artifact (backtick `test/` or
`gates/` path, or a `gate:`/`check:` line), write
`check:`/`empty state:`/`provenance:` each on its own line, never
inline — with a note that `gates/acceptance_gate.py` enforces this
post-hoc as a backstop.

## Why

`gates/acceptance_gate.py` only checked this shape after the issue was
posted, so the orchestrator (which drafts issues) wrote fields inline
and got rejected post-hoc, causing rewrite/re-spawn round-trips
(#649/#650/#651). Stating the contract at the authoring point closes
the gap, mirroring the precedent for role-record shape
(tokenmaxxxer-core#195).

## Basis

docs/issue-670/proposals/2026-08-10-acceptance-format-in-directive.md
(approved via issue comment `APPROVE issue-670/implementation`, single-
account mode, JiwonJung94 listed in docs/specs/approvers.md).

## What did not work

None.

## Rationale for deviations

None — implementation matches the approved proposal's "What will be
done" exactly.

## Doc placement

- [x] Change confined to `on-the-record/hooks/directive.sh` per the
  proposal's frozen write set; no handbook/decision/report doc
  required (no new env var, config key, dependency, migration, or
  public-signature change).

## How it was verified

derived: `bash on-the-record/hooks/directive.sh` (CLAUDE_ROLE and
ORCHESTRATE_OFF unset) piped to `grep -n "ACCEPTANCE FORMAT\|check:\|empty"`

```
8:- ACCEPTANCE FORMAT: when an `## Acceptance` criterion you draft
10:  path, or a `gate:`/`check:` line), write `check:`/`empty
```

Red state (pre-change) had no match; green state (post-change, shown
above) matches — confirms the format-rule text renders in the
orchestrator session's directive output, per the proposal's "How
you'll know it worked" (`check:` / provenance: executed-unit).

## Open findings

None.

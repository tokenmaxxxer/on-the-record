---
status: proposed
files:
  - on-the-record/hooks/directive.sh
---

## Request

The orchestrator drafts GitHub issue Acceptance clauses, but
`gates/acceptance_gate.py` only checks their shape *after* the issue is
posted — it requires `check:`/`empty state:`/`provenance:` each on its
own line once an executable artifact is referenced. Because the
orchestrator's directive never states this contract, it writes fields
inline and gets rejected post-hoc, causing rewrite/re-spawn round-trips
(#649/#650/#651). Fix: state the format contract at the authoring
point — the `[orchestrate]` directive in `directive.sh` — so it is
known before the issue is drafted, not discovered after.

## Constraints

- The directive heredoc is injected on every prompt; the addition must
  stay short (the issue's own text asks for "짧은 ACCEPTANCE FORMAT
  절").
- `acceptance_gate.py`'s post-hoc rejection stays in place as backstop
  — this proposal does not change the gate.
- Only `on-the-record/hooks/directive.sh` is in scope; no other file
  needs to change for the orchestrator to see the new section (it is
  injected fresh every prompt, no caching/build step involved).

## Rationale

Chosen: add a short ACCEPTANCE FORMAT section to `directive.sh`'s
existing `[orchestrate]` heredoc, next to the "Requirements become
ISSUES..." bullet.

Rejected alternative: put the format contract in `/orchestrate:run`
(the on-demand slash-command doc `directive.sh` already defers to for
PR-relay wording) instead of the always-injected heredoc. Rejected
because `/orchestrate:run` is read on demand, not injected every
prompt — the issue's own failure mode is that the orchestrator invents
Acceptance wording *before* consulting any on-demand doc, so a fix
living only there would not close the gap the issue reports. This
mirrors the precedent already applied for role-record shape
(tokenmaxxxer-core#195): that fix landed the format inside the
always-injected role directive, not in a doc the role would have to
remember to open.

Rejected alternative: change `acceptance_gate.py` to auto-fix or
soften its rejection. Rejected because the issue text explicitly asks
to keep the gate as a backstop and fix authorship instead — changing
the gate's behavior is out of scope for what was requested.

## What will be done

Add a short paragraph to the `[orchestrate]` heredoc in
`on-the-record/hooks/directive.sh`, near the existing "Requirements
become ISSUES you draft..." bullet, stating: when an `## Acceptance`
criterion references an executable artifact (a backtick `test/` or
`gates/` path, or a `gate:`/`check:` line), write `check:`/`empty
state:`/`provenance:` each on its own line — never inline in one
sentence — and that `acceptance_gate.py` enforces this post-hoc as a
backstop.

## Out of scope

- Changing `gates/acceptance_gate.py` itself.
- Changing `/orchestrate:run` or any other slash-command doc.
- Any code path outside the orchestrator directive heredoc.

## How you'll know it worked

check: capture `directive.sh`'s rendered stdout (`CLAUDE_ROLE` unset,
`ORCHESTRATE_OFF` unset) and grep for the added format-rule text —
red before the change (no match), green after.
empty state: not applicable — the directive heredoc renders
unconditionally into the orchestrator session; there is no corpus/empty
state to check.
provenance: executed-unit — verified by running
`on-the-record/hooks/directive.sh` directly and grepping its stdout,
not through a live orchestrator session.

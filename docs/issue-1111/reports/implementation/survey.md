# Survey: gate ownership of docs/product/ (issue #1111)

## The deadlock, read from the two hooks

canonical: on-the-record/hooks/deliverable-guard.sh (read in full)
`deliverable-guard.sh` (PreToolUse, Write|Edit|MultiEdit|NotebookEdit)
denies any write to a deliverable-shaped path inside a git-repo-rooted
target when the session carries no `CLAUDE_ROLE` (i.e. the
orchestrator). Its only carve-outs today: `docs/specs/approvers.md` by
exact suffix match, and `scratch`/`tmp`/`.git`/`plugin-cache` path
segments. A `docs/product/*.md` path matches neither — the
orchestrator's write there is denied.

canonical: on-the-record/hooks/product-capture-stopgate.sh (read in full)
`product-capture-stopgate.sh` (Stop) no-ops when `CLAUDE_ROLE` is set,
so it only ever fires in the orchestrator session — the same session
`deliverable-guard.sh` blocks from the write it asks for. It walks the
session transcript for four category patterns (requirements,
priorities, philosophy, goals), and for any category flagged with no
corresponding added line in the issue-scoped or fallback product doc
path, returns `additionalContext` nudging the orchestrator to record
it before the turn ends. It is advisory (`hookSpecificOutput`, never
`decision:"block"`) — it does not itself prevent Stop — but nothing
else resolves the nudge, so the same nudge recurs every Stop until the
file gains a line the orchestrator cannot write.

## Existing precedent inside deliverable-guard.sh

canonical: on-the-record/hooks/deliverable-guard.sh, the
`n.endswith("docs/specs/approvers.md")` check
The `docs/specs/approvers.md` exemption is the one precedent already
carved into this exact gate for "orchestrator scribing" — same hook,
same denial branch, same `n.endswith(...)` check ahead of the
git-repo-root probe. No comparable precedent exists on the
`product-capture-stopgate.sh` side for accepting a non-file capture
form (e.g. a GitHub issue comment) as satisfying its cross-check: that
check (`git diff --unified=0` / `git log -1 -p` against the tracked
target path) only ever inspects the working tree, never GitHub API
state.

## Current state of the product-docs directory

derived: `ls -la docs/product`
```
ls: cannot access 'docs/product': No such file or directory
```
No such directory exists in this tree yet — no prior capture has ever
landed through it, consistent with the issue's own account that the
interim record for the pending priority statement was left as an
issue comment instead.

## The pending entry to capture

canonical: gh issue view 745 --comments (close-out comment by
JiwonJung94, 2026-08-12, tagged `priority-record`)
> this issue is deliberately deprioritized (`infrastructure/
> no-direct-requirement`) behind #1110, the 7-scenario harness
> re-measurement, and the user's fresh-session E2E test. docs/product/
> priorities.md capture is role work — to be routed via
> product-management next session (orchestrator deliverable-guard
> blocks direct write).

## consult

canonical: docs/reports/consult-log.md (2026-08-12T17:29:46+00:00
entry cited in the issue body)
The issue states validity-consult was attempted twice and the
pipeline itself failed, tracked as a companion consult-regression
issue separate from #1111. A re-run for this proposal is attempted
below; the issue's own text treats the consult step as best-effort
here ("consult to be re-run by the phase-1 role"), not as gating —
#1111's acceptance criterion names only the test, not a consult
transcript.

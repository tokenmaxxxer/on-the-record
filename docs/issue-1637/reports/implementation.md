---
code_under_review:
  - docs/issue-466/reports/implementation/survey.md
  - docs/issue-501/reports/implementation/survey.md
type: fix
breaking: false
verdict: pass
loop_state: landed
---

# Issue #1637 — Implementation Record

## What was done

Issue #1637 was re-scoped 2026-08-16 after the earlier denial recorded
below (original target `docs/issue-85/reports/coding.md` is owned by the
retired `coding` role — cross-ROLE write, denied by R5; see `## What did
not work`). New scope: two genuine broken citations in records owned by
the implementation role itself (cross-issue, same-role — R4
maintenance-targets exception applies, R5 satisfied), fixed via plain
`Edit` from this issue's own branch (issue-1637/implementation), no
heredoc/python -c/tee:

1. `docs/issue-466/reports/implementation/survey.md:35` — changed the
   literal string "docs/issue-374/proposals/2026-08-07-...md" (unresolvable,
   literal ellipsis) to
   `docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md`.
2. `docs/issue-501/reports/implementation/survey.md:79` — changed the
   literal string "docs/issue-501/proposals/implementation.md" (does not
   exist) to
   `docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md`.

Both `Edit` calls were allowed by the repo's `board-gate.sh` PreToolUse
hook (same-role cross-issue write under the R4 maintenance-targets
exception declared in issue #1637's body: `maintenance-targets:
docs/issue-466/, docs/issue-501/`) — no denial, no bypass shape used.

canonical: both `Edit` tool calls this session against
`docs/issue-466/reports/implementation/survey.md` and
`docs/issue-501/reports/implementation/survey.md`, each returning success
with no PreToolUse hook error.

## Why

Issue #1637 (updated body) requires both fixes to land from this issue's
own branch via plain `Edit`, gate-allowed under the R4 maintenance-targets
exception (same-role, cross-issue), with the record citing the allowed
writes — exactly what was performed.

## Upstream basis

- Issue #1637 (this issue), re-scoped 2026-08-16.
- Target lines: `docs/issue-466/reports/implementation/survey.md:35` and
  `docs/issue-501/reports/implementation/survey.md:79`, on branch
  issue-1637/implementation at commit_sha 1076908a217b7e768bfa8afe8c5ddeef78e8f614
  (branch tip at session start).

## What did not work

- (From the prior session, original scope) Direct `Edit` on
  `docs/issue-85/reports/coding.md` — expected: the R4 maintenance-targets
  allow would let this issue's session write outside its own record;
  actual: `board-gate.sh` refused the write unconditionally for any path
  outside `implementation.md`/`implementation/**`, citing contract v3 s11
  (R5 own-record-only), because that path is owned by a different ROLE
  (`coding`), not a same-role cross-issue path — the exact R4∩R5 shadowing
  tracked in #1633. That denial was recorded honestly and no bypass was
  attempted; the docs/issue-85 defect remains open under #1633.
- This session's two Edits (new scope) — both succeeded on the first
  attempt; nothing failed.

## Open findings

None. The original open finding (board-gate has no maintenance-targets
carve-out for cross-ROLE writes) is superseded by the issue's own
re-scope, which routes future cross-role record fixes through #1633
instead of asking this gate to be changed.

## Acceptance verification

acceptance: test -f docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md && test -f docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md — result:

```
$ test -f docs/issue-374/proposals/2026-08-07-decision-queue-stop-hook-nudge.md && test -f docs/issue-501/proposals/2026-08-08-session-latency-breakdown.md; echo exit=$?
exit=0
```

acceptance: both Edits performed cross-issue from this issue's own branch by plain Edit with the gate allowing (no bypass shapes) — canonical: the two `Edit` tool calls in this session's transcript against `docs/issue-466/reports/implementation/survey.md` and `docs/issue-501/reports/implementation/survey.md`, each returning "has been updated successfully" with no PreToolUse hook error.

acceptance: the record cites the allowed writes — canonical: `## What was done` above, this record's own text.

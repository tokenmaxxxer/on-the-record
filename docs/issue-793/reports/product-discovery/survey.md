# Survey — issue #793 (verify-before-claim)

## Scout skip record

Skipped. Reason: this is an internal mechanism-design task constrained
entirely by the existing repo's hook/gate architecture
(`gates/record_lint.py`, `on-the-record/hooks/record-claim-guard.sh`,
issue #791's file:line-context rule) — there is no external product
category to benchmark against, and the issue text leaves no
market-facing design decision open.

## Background / context

`derived: docs/issue-793` — no prior work on this issue exists (empty
directory before this session).

A consumer session self-reported 2026-08-11: five wrong judgments (a
bad-instruction halt, a false-premise issue close) traced to one root
cause — asserting on a role-summary or partial observation without
confirming the canonical source. The same pattern recurred in the
reporting session itself: mistaking a role's phase-1 plan PR for the
actual baseline result, and misreading a filtered `ps` grep as "all
sessions gone."

Issue #791 already covers one narrow slice: a defect claim must cite
actually-read source content, not a grep keyword hit. #793 asks for the
general rule underneath it, covering three claim types, not just
defect claims.

## Current mechanical surface (derived: gates/record_lint.py, on-the-record/hooks/record-claim-guard.sh)

Two claim-shape checks already exist and both fire only on
`docs/issue-*/reports/**` writes:

- `bare_count_claim_check` (#333): a bare "N of M" / "N items" count
  needs a `derived:` tag or a code-fence reproduction.
- `orphaned_path_reference_check` (#330): a backtick-quoted path must
  resolve in the working tree.
- `unverifiable_reason_check` / `checked_claim_reason_check` (#310/#331):
  an `unverifiable:`/`unverifiable` result line needs a stated reason.

None of these check WHAT KIND of source backs a claim — only that a
count has *some* citation and a path *exists*. A claim cited as
`derived: role X's self-summary` currently passes the gate exactly like
`derived: gh pr view 790 --json files`. That gap is what #793 asks to
close.

## JTBD (problem stated without a solution attached)

- Job performer: an agent role (product-discovery, implementation, an
  orchestrating/consumer session) mid-task, about to take a
  consequential action.
- Job: decide whether a state (a role finished X, a PR/session is in
  state Y) or a defect (file:line causes Z) is true, then act on that
  belief — file/close an issue, halt/merge a session, write a record
  that asserts the state or defect.
- Circumstance: the information at hand is a role's own self-report, a
  watcher/event log, a truncated or filtered tool output (grep over
  `ps`, a summary paragraph) — cheap to read, and it FEELS like enough
  to decide from.
- Desired outcome: the agent only acts on a claim it has confirmed
  against the thing the claim is actually about, so a false premise
  never survives past the moment before the consequential action, not
  discovered afterward as a bad halt or a wrongly-closed issue.

The issue text already states the problem source-attached
("role-summary or partial observation") rather than naming a solution
up front, so no restatement gap.

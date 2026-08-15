# Patrol Channel Contract

Issue #1586. Operator decision 2026-08-15 (recorded in the consumer
repo's docs/reports/product/goals.md). This spec is EARS-pattern (Easy
Approach to Requirements Syntax): each requirement states its pattern,
a verification method, and a verification condition — same shape as
[docs/specs/upstream-defect-channel.md](upstream-defect-channel.md).

This change is tagged `infrastructure/no-direct-requirement`: it is a
governance/capability-scope amendment, not an operator-quote-sourced
requirement, so it carries no `R###` id in
[docs/specs/requirements.md](requirements.md) and is cross-referenced
here from [docs/specs/requirement-digest.md](requirement-digest.md)
rather than appended into that auto-generated file (per
`gates/requirement_digest.py`'s own stated invariant: the digest is a
byte-exact render of `requirements.md`'s numbered entries — hand-adding
a synthetic entry there would misrepresent this change as an operator
quote it is not).

Precedes the patrol-board implementation (issue #1582's tier-1 queue,
issue #1584's trigger guard) — this spec amends the contract those
pieces will build against; it does not itself build the board.

## Scope of the waiver

For the judgment-patrol channel ONLY, the per-issue scribe confirmation
step (the standing contract requiring a human-confirmed step before an
autonomous session creates a per-issue write) is waived. This waiver
never extends to any other issue-creation path — every non-patrol
channel keeps the existing scribe contract unchanged.

## Requirements

### PCC-1 (ubiquitous)
The patrol filer SHALL be permitted to autonomously create and
edit-in-place exactly one living "patrol board" issue per active role
(Renovate dependencyDashboard pattern: one issue, edited in place,
never re-created), batching verified queue findings from
`gates/patrol_queue.py`.
- verification_method: gate test (shape-level permission check)
- verification_condition: `on-the-record/hooks/test_gh_write_allow_gate.py`
  asserts an orchestrator-session `gh issue edit` call gets
  `permissionDecision: allow`
- source: issue #1586 requirement 1

### PCC-2 (event-driven)
WHEN a human ticks a finding's checkbox on the patrol board issue, the
tick SHALL be treated as the operator's work-start approval, and ONLY
that tick MAY trigger creation of the real per-finding issue and spawn
work on it.
- verification_method: design invariant, enforced at the patrol-board
  implementation layer (issue #1586 explicitly precedes that build);
  this spec records the semantics the board-implementation issue must
  satisfy
- verification_condition: UNVERIFIABLE at this layer — no board-edit or
  tick-detection code exists yet to test against; the patrol-board
  implementation issue must add its own gate test asserting no
  per-finding issue is created except in direct response to a tick
- source: issue #1586 requirement 2

### PCC-3 (ubiquitous)
Untriaged findings (queue entries with no tick recorded on the board)
SHALL NOT become standalone issues.
- verification_method: same as PCC-2 — design invariant for the
  patrol-board implementation layer
- verification_condition: UNVERIFIABLE at this layer; deferred to the
  patrol-board implementation issue's own gate test
- source: issue #1586 requirement 2

### PCC-4 (ubiquitous)
The patrol channel's autonomous issue-creation and board-edit paths
SHALL NOT extend the scribe-confirmation waiver to any non-patrol issue
or PR write.
- verification_method: gate test (caller-identity + verb-shape check)
- verification_condition: `on-the-record/hooks/test_gh_write_allow_gate.py`
  asserts a role session (`CLAUDE_ROLE` set) never receives `allow` for
  any `gh` write verb regardless of shape, and that `gh-write-allow-gate.sh`
  grants `allow` only to the specific recognized verb shapes, never by
  inspecting `--body`/`--title` content
- source: issue #1586 requirement 3

### PCC-5 (ubiquitous)
The patrol channel SHALL be bounded by four hard caps:
1. Max 2 tick-promoted issues per hour per role.
2. Max 10 open patrol issues per role.
3. Board edits batched to one edit per role per patrol run.
- verification_method: gate test, enforced at the patrol-board
  implementation layer (rate/count state is runtime data, not
  something a shape-only permission gate can check)
- verification_condition: UNVERIFIABLE at this layer; deferred to the
  patrol-board implementation issue's own gate test, which must assert
  each of the three caps independently
- source: issue #1586 requirement 4

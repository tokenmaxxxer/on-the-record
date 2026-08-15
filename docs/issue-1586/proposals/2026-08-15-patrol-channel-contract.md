---
status: proposed
files:
  - docs/specs/patrol-channel-contract.md
  - on-the-record/hooks/gh-write-allow-gate.sh
  - on-the-record/hooks/test_gh_write_allow_gate.py
---

## Request

Operator decision (2026-08-15, recorded in the consumer repo's
docs/reports/product/goals.md): for the judgment-patrol channel only,
waive the per-issue scribe confirmation step. The patrol filer may
autonomously create and edit-in-place one living "patrol board" issue
per active role, batching verified queue findings; ticking a finding's
checkbox on the board is the operator's work-start approval and is the
only thing that may create the real per-finding issue. Everything else
keeps the existing scribe contract. Hard caps: 2 tick-promoted issues/
hour/role, 10 open patrol issues/role, board edits batched to one per
role per patrol run.

## Constraints

- The waiver applies to the patrol channel only — it must not read as
  a general relaxation of the scribe-confirmation contract for any
  other issue-creation path.
- `gh-write-allow-gate.sh`'s existing design invariant — decision keyed
  on command shape only, never on argument text — must not be broken to
  implement this; the gate cannot itself enforce the hourly/open-count
  caps (those are runtime state, not shape) or which specific issue is
  "the" board issue.
- The spec doc must be cross-referenced from the requirement digest per
  its own stated conventions, without hand-editing the digest file
  itself (it is strictly auto-generated from docs/specs/requirements.md
  by gates/requirement_digest.py) and without inventing a synthetic
  R-id for a change the issue itself tags
  `infrastructure/no-direct-requirement`.

## Rationale

Considered content-inspecting `gh issue edit`'s `--body`/`--title` for
a "patrol board" marker so the gate itself enforces "only the board
issue, only batched edits." Rejected: this is exactly the argument-text
inspection `gh-write-allow-gate.sh`'s own header comment rules out by
design (issue #810 SCOPE EXTENSION 2's measured failure mode — a
`--body` argument carrying sensitive-looking literals must never flip
the decision). The gate is deliberately shape-only and keys "who may
write at all" off caller identity (`CLAUDE_ROLE` resolving empty);
content-level policy (which issue is the board, whether caps are
respected) belongs in the patrol code path that constructs the `gh`
call, not in the permission gate. Chosen instead: add the one missing
verb shape (`gh issue edit`) the gate needs to stop blocking a
legitimate board-edit-in-place call, and leave the cap/board-identity
enforcement to be built in the patrol-board implementation this issue
explicitly precedes.

## What will be done

- Write `docs/specs/patrol-channel-contract.md`: an EARS-pattern spec
  (same shape as `docs/specs/upstream-defect-channel.md`) stating (1)
  the waiver scope — patrol channel only, (2) tick-is-approval
  semantics — a checkbox tick on the board issue is the sole trigger
  for creating a real per-finding issue, untriaged findings never
  become standalone issues on their own, (3) the four hard caps
  verbatim from the issue body. Its header cross-references
  `docs/specs/requirement-digest.md` (mirroring
  `upstream-defect-channel.md`'s own cross-reference to
  `docs/specs/northpole.md`) and states plainly that no R-id covers
  this change (`infrastructure/no-direct-requirement`, per the issue's
  own validity-consult line) rather than fabricating one.
- Add `("gh", "issue", "edit")` to `gh-write-allow-gate.sh`'s
  `VERB_SHAPES` tuple — the one verb shape the board-edit-in-place step
  needs that is not already covered. No other line of the gate's logic
  changes: the `cd DIR &&` prefix handling, the heredoc-substitution
  carve-out, and the operator-token check all apply to the new shape
  identically to the existing five.
- Add test cases to `on-the-record/hooks/test_gh_write_allow_gate.py`
  covering: orchestrator `gh issue edit` gets allow; role-session `gh
  issue edit` still gets no allow; chained/substitution variants of
  `gh issue edit` still fall through denied — mirroring the existing
  coverage pattern for the other four verbs.

## Out of scope

- The patrol-board implementation itself (which issue is "the" board,
  the tick-detection/promotion code path, the hourly/open-count cap
  enforcement) — this issue is explicitly the contract amendment that
  precedes that build, not the build itself.
- Any change to the scribe-confirmation contract outside the patrol
  channel.

## How you'll know it worked

- `docs/specs/patrol-channel-contract.md` exists, states the waiver
  scope/caps/tick-is-approval semantics, and cross-references the
  requirement digest.
- `python3 on-the-record/hooks/test_gh_write_allow_gate.py` passes,
  including the new `gh issue edit` cases, and the pre-existing cases
  for the other four verbs and role-session denial still pass
  unchanged.

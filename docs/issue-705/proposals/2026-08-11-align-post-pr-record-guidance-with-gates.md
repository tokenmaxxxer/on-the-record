---
status: proposed
files:
  - docs/issue-705/reports/implementation/survey.md
  - docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md
---

## Request

Four implementation sessions on 2026-08-11 opened their PRs cleanly, then
lost their remaining turns to `board-gate`, `record-claim-guard`, and
`record-fields-gate` failures while writing the post-PR hunt record and
the phase-2 record. Survey what currently instructs those writes — the
`warrant` plugin's hunt-record path template, and the `coding`/
`record-shape` rulebooks' record-shape guidance — and propose how to
align that authoring-time text with what the gates actually check, so a
fresh session's first write attempt already lands in scope and in shape.
This is phase 1 only: survey plus proposal, no code changes.

## Constraints

- The fix belongs at authoring time, in the deployed directive text —
  same root-cause class as core#195 — not as a post-hoc retry loop or a
  gate softening.
- The three sources that need correcting (`warrant`, `coding`,
  `record-shape` plugin directives) live in different repos
  (`tokenmaxxxer-core`, `tokenmaxxxer-implementation`) than this one
  (`on-the-record`). This phase-1 session's write set stays inside
  `docs/issue-705/**` in `on-the-record` per warrant's own rule; the
  actual plugin-file edits are out of scope for this PR and become the
  phase-2 (or a separate cross-repo) unit once this proposal is approved
  and the plugin repos' own role sessions pick it up.
- The corrected hunt-record path must satisfy `role_scope`'s in-scope
  globs (`docs/issue-<n>/reports/<role>.md` or
  `docs/issue-<n>/reports/<role>/**`) for every role that dispatches a
  warrant-hunter, not just `implementation`.
- The correction must not introduce a second hardcoded copy of the
  role-scope rule that can drift from `gates.py` again.

## Rationale

Two shapes were possible for the hunt-record path fix:

1. **Hardcode the corrected literal path** in `warrant/hooks/directive.sh`
   (`docs/issue-<n>/reports/<role>/hunt-<slug>.md`, substituting `<role>`
   textually per dispatch). Simplest, but recreates exactly the drift this
   issue is about: the survey found this file already went through one
   partial fix (issue segment added, role segment forgotten) precisely
   because the path lives as duplicated literal text instead of derived
   logic.
2. **Have the calling role's rulebook supply the record directory** (the
   `coding` plugin already declares
   `docs/issue-<n>/reports/implementation.md` as its record home) and have
   `warrant`'s directive interpolate that value rather than writing a
   literal path of its own.

This proposal picks (2): the hunt-record path is derived from the same
fact `role_scope` already derives structurally (the role owns exactly one
record directory), instead of being retyped a third time in a
role-agnostic plugin that cannot know the role. (1) was rejected because
it repeats the failure mode the issue reports, just with a corrected
string that will drift again the next time someone edits `warrant`
without also checking `gates.py`.

For the claim-guard and record-fields-gate findings, the alternative
considered was leaving `record-claim-guard.sh`/`record-fields-gate.sh` to
catch and reject bad phrasing as today (status quo) versus adding
authoring-time template lines to `coding`/`record-shape`'s directives that
pre-satisfy the checks. Status quo was rejected because it is the
observed failure: four sessions already hit the gate after the fact with
no template to reach for, burning their last turns on gate-driven retries
instead of writing the record correctly the first time.

## What will be done

Scoped to this repo's phase-1 deliverable (survey + this proposal); the
concrete plugin-text edits it authorizes are:

- `warrant/hooks/directive.sh` (and `warrant/agents/warrant-hunter.md`,
  `warrant/README.md`): replace the hardcoded hunt-record path text with
  a role-derived directory. Every rulebook surveyed declares its record
  as a flat `docs/issue-<n>/reports/<role>.md` *file*, not a directory —
  `role_scope`'s second in-scope glob (`docs/issue-*/reports/{role}/**`)
  is the actual hunt-record home, a sibling of that file, not a
  subdirectory carved out of it. The directive must derive
  `docs/issue-<n>/reports/<role>/` from the role name directly (the same
  way `role_scope` builds its glob), never by appending a path segment
  onto the record file's own `.md` path — appending onto the file path
  produces a broken `...reports/<role>.md/hunt-<slug>.md` (a directory
  named `<role>.md`), which the after-proposal hunt on this issue's own
  survey-and-proposal transition caught as a bypass in the first draft of
  this section. The hunt record then lands at
  `docs/issue-<n>/reports/<role>/hunt-<slug>.md`, falling back to the
  existing non-issue-scoped path only when no issue segment is present.
- `coding/hooks/directive.sh`: add one line to the `HAND_OFF` block naming
  the `derived: <command or path>` tag as required immediately before any
  count claim, and one line stating that any `unverifiable:` line or
  `unverifiable` Acceptance-verification result must carry a reason after
  it — the two shapes `record_lint.py` actually checks.
- `record-shape/hooks/directive.sh`: add a line stating that a
  non-terminal `loop_state` with an open finding must carry a `next
  steps` line and a `resolution path` line, matching contract v3 §20 and
  what `record-shape-gate.sh` mechanically checks.

## Out of scope

- Editing the plugin files themselves in this PR (they live in other
  repos; this proposal documents and authorizes the change, the actual
  edit is a separate cross-repo unit once approved).
- Any change to the gates (`gates.py`, `record_lint.py`,
  `record-shape-gate.sh`) — the gates are already correct per the issue;
  only the guidance that precedes them is misaligned.
- Retrying or backfilling the four stranded sessions' PRs.

## How you'll know it worked

Per the issue's Acceptance section: once the plugin-text edits land, a
unit test rendering the deployed guidance/template for the implementation
role asserts (a) the hunt-record path it names matches `role_scope`'s
in-scope glob for that role, and (b) the record template's example
phrasing satisfies `record_lint.py`'s bare-count and unverifiable-reason
checks and `record-shape-gate.sh`'s terminal/non-terminal shape check.
That test is phase-2 work in the plugin repos, not this proposal — this
proposal's own "worked" bar is: the survey names each of the three
sources with the exact line/finding to fix, and the proposal's Rationale
names the derivation-based fix (not a re-hardcoded literal) as the chosen
direction, so the phase-2 session has no ambiguity left to resolve.

## Accumulation

Not accumulation-cost-shaped: this is a one-time authoring-guidance
correction, not a per-item or per-request cost that compounds with scale.

# Current-state survey — issue #1586

## Write set under consideration

- docs/specs/patrol-channel-contract.md (new) — the waiver/caps/
  tick-is-approval spec.
- on-the-record/hooks/gh-write-allow-gate.sh — the shape-only gate
  that currently grants `permissionDecision: allow` for orchestrator
  `gh issue create/comment/close` and `gh pr comment/close`.
  canonical: on-the-record/hooks/gh-write-allow-gate.sh (read in full
  this session) — the `VERB_SHAPES` tuple lists only `("gh","issue",
  "create")`, `("gh","issue","comment")`, `("gh","pr","comment")`,
  `("gh","issue","close")`, `("gh","pr","close")`; no `issue edit`
  shape exists in that tuple.
- on-the-record/hooks/test_gh_write_allow_gate.py — existing test
  file for the gate; add cases for the new `gh issue edit` shape.

## What #1582/#1584 already built (immediately prior work, same channel)

canonical: docs/issue-1582/proposals/2026-08-15-tier1-role-patrol-pilot.md
(read this session) — states the queue's own non-goal directly: "No
auto-promotion code path — queue-to-issue only via a human-confirmed
orchestrator step, not built in this pilot (issue design req 9,
explicit non-goal)." Neither `gates/patrol_queue.py` nor
`gates/patrol_trigger.py` (git log 655542ec) write to GitHub issues, so
neither prior slice touched the gh-write gate boundary. #1586 is the
first slice in this channel that reaches it, matching the issue title's
own framing ("precedes the patrol-board implementation").

## gh-write-allow-gate.sh design invariants (must not violate)

canonical: on-the-record/hooks/gh-write-allow-gate.sh header comment
(read this session) — decision is keyed on command SHAPE only: verb +
no unquoted chaining/substitution outside the one tolerated heredoc-body
substitution; "no token past the verb's own subcommand name is ever
inspected" is the file's own stated design requirement (issue #856).
This means the gate structurally cannot distinguish "board-issue edit"
from any other issue edit by content — only by verb shape.

canonical: same file, identity block (read this session) — `role`
resolving non-empty (a role session) exits 0 before any shape check
runs, so a role session's `gh issue create/edit/...` never reaches an
allow from this gate regardless of verb. This is the existing mechanism
for denying unattended issue creation from role sessions: gated by
caller identity, not by content.

canonical: same file, `VERB_SHAPES` tuple (read this session) — the
five existing shapes are all already unconditionally allowed for the
orchestrator. `gh issue edit` is absent, so a board-edit-in-place call
today falls through to the host's default classifier with no allow
signal, unlike the other write verbs the orchestrator loop relies on.

## What the acceptance requires, given the above

1. A new EARS-pattern spec doc (matching the shape of
   docs/specs/upstream-defect-channel.md, read this session, which
   itself cross-references docs/specs/northpole.md via a markdown link
   in its header) stating the waiver scope, tick-is-approval semantics,
   and the four hard caps from the issue body, and cross-referencing
   docs/specs/requirement-digest.md the same way.
   canonical: gates/requirement_digest.py (read this session) — the
   digest is strictly auto-generated, byte-exact from
   docs/specs/requirements.md's numbered R### entries
   (`render()`/`check()`); appending a synthetic R-id there would
   misrepresent a governance/capability-scope change (tagged
   `infrastructure/no-direct-requirement` in the issue body itself) as
   an operator quote it is not. The link direction that matches
   existing convention is spec-to-digest, not a hand-edit of the
   generated file.
2. gh-write-allow-gate.sh needs exactly one new verb shape:
   `("gh", "issue", "edit")` — the mechanical enabler for board-edit-
   in-place. Tick-promoted creation is already covered by the existing
   `gh issue create` shape. The "deny other unattended issue creation"
   half is already met by the existing role-session short-circuit and
   needs no change.

## Alternatives considered (feeds the proposal's Rationale)

- Content-inspect `--body`/`--title` text for a "patrol board" marker
  to scope `issue edit` more narrowly than "any issue edit from the
  orchestrator". Rejected: violates the gate's own stated design
  invariant (argument-text inspection was deliberately ruled out for
  this file per its header comment, issue #810 SCOPE EXTENSION 2's
  exact failure mode), and caller-identity already does the real
  gatekeeping.

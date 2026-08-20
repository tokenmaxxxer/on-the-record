---
status: proposed
files:
  - gates/auto_approval_class.py
  - gates/test_auto_approval_class.py
  - docs/specs/auto-approval-config.json
  - docs/specs/contract-v3-amendment-auto-approval.md
  - docs/reports/auto-approval-audit-log.md
---

# issue-1739: conditional auto-approval, shadow-mode first

## Request

Add a classifier (`gates/auto_approval_class.py`) that identifies
low-risk PR classes (docs-only, non-behavior-contract diffs;
test-only additions) via an explicit whitelist, fail-closed on any
ambiguity or on any diff touching a behavior-contract path
(`on-the-record/hooks/`, `gates/`, `docs/specs/`, or any file that
defines approval/gate semantics). Compose the classifier's verdict with
the three existing deterministic gates (scope_adherence,
stale_revert_guard, requirement_met) plus a quota (default 5/24h,
config-overridable) and a precision circuit breaker (any revert/flag of
an auto-approved PR within a rolling 4 weeks suspends the class to
human-required). Ship shadow-mode only in this delivery: the classifier
runs, labels its verdict, and writes an audit-log line, but
`approval-gate.sh` keeps requiring the human `APPROVE issue-<n>/<role>`
comment exactly as it does today — no bypass activates. Also land a
documented contract v3 s19 amendment describing the auto-approval path
as reviewable spec text.

## Constraints

- No auto-approval config present -> `approval-gate.sh` behavior stays
  byte-identical to today (human APPROVE required for every
  phase-2-shaped write). This proposal's write set therefore does not
  touch `on-the-record/hooks/approval-gate.sh` at all — the empty-state
  requirement is satisfied by construction, not by a conditional inside
  the hook.
- Auto-approval logic can never approve a change to itself
  (circular-trust ban): any diff touching `on-the-record/hooks/`,
  `gates/`, `docs/specs/`, or a file defining approval/gate semantics is
  always human-required, independent of extension or declared class.
  This proposal's own write set (a `gates/*.py` pair and a
  `docs/specs/*` pair) is itself an instance of that carve-out — a
  future PR built by this classifier would never be eligible to
  auto-approve itself or a peer file in these same directories.
- This delivery's Acceptance criteria (per the issue) are entirely
  about the classifier, shadow-mode recording, and quota/circuit-breaker
  machinery — real bypass activation is out of scope, gated behind a
  separate human decision after the shadow-mode sample window
  (>= 10 samples or 4 weeks, whichever is later) closes with zero
  human-overturned would-approve verdicts.
- Governance-contract amendment (contract v3 s19): the amendment lands
  as reviewable spec text in `docs/specs/contract-v3-amendment-auto-
  approval.md`, not folded silently into code comments.

## Rationale

**Config format: JSON file under `docs/specs/`, not prose inside the
amendment doc.** Considered keeping the quota and shadow-mode flag as
prose fields inside `contract-v3-amendment-auto-approval.md` (single
file, no new format to learn). Rejected: the Acceptance empty-state
criteria ("no auto-approval config present -> byte-identical", "no
feature flag file present -> zero shadow verdicts recorded") need a
file whose *presence* is itself the signal a test can assert on. A
markdown doc that also carries prose explanation is not a reliable
presence/absence switch — a human editing the doc's prose (fixing a
typo, adding a paragraph) would not intend to flip runtime behavior,
but a config-embedded-in-prose design makes the two indistinguishable.
A dedicated, minimal JSON file (empty/absent = feature off) keeps the
presence check trivial and keeps the human-readable amendment doc free
to change without side effects.

**Classifier composes existing gates by shelling out to their existing
callable, not by re-deriving PASS/allow status independently.**
Considered re-implementing a lightweight scope/staleness/requirement
check inside `auto_approval_class.py` itself, reasoning it would avoid
a dependency on three other modules' internals. Rejected: two
independent implementations of "does this PR's scope adhere" can drift
apart silently — a future edit to `scope_adherence.py`'s definition of
adherence would not automatically propagate to a shadow copy, and
Requirement 3 explicitly ties auto-approval eligibility to those three
gates' actual results, not to an approximation of them. Composing over
the existing modules is also the pattern the scout brief's axis 3
(composability with existing gates, Mergify's `auto_merge` firing only
when a ruleset's own conditions are already satisfied) surfaced as the
strong-exemplar behavior.

**Quota/circuit-breaker state persists in a local append-only state
file, not derived live from `gh` on every check.** Considered a
stateless design that re-queries GitHub PR/comment history on each
approval check to recompute the trailing-24h count and trailing-4-week
revert flag. Rejected for this delivery: it costs an API round trip on
every check (this repo's own consult log shows recent issues around
GraphQL/REST quota exhaustion from polling-heavy designs — see
issue-1498/1493 lineage referenced in `docs/reports/consult-log.md`),
and "was this PR reverted" has no single canonical GitHub signal to
query live (a revert is itself a separate PR/commit, not a flag on the
original). A local state file the audit-log write already touches in
the same transaction (Requirement 5) is simpler to keep consistent than
a second live-derived source of truth.

## What will be done

- `gates/auto_approval_class.py`: a `classify(diff_paths, diff_stats)`
  -type entry point returning one of `{docs_only, test_only,
  not_eligible}` plus a `reason` string. Behavior-contract paths
  (`on-the-record/hooks/`, `gates/`, `docs/specs/`, any file whose
  content defines approval/gate semantics) always return `not_eligible`
  regardless of the rest of the diff. Mixed diffs (docs + code, or
  partially out-of-scope against the PR's declared scope) return
  `not_eligible`. A `shadow_verdict(classify_result, gate_results,
  quota_state)` function composes the classification with
  `scope_adherence`, `stale_revert_guard`, and `requirement_met`
  results plus quota/circuit-breaker state (read from a local JSON
  state file, default path under `docs/reports/`) to produce a
  `would_auto_approve: bool` plus reason, and appends one line to
  `docs/reports/auto-approval-audit-log.md` in the same call — never a
  approve/deny action on its own; `approval-gate.sh` is not modified in
  this delivery, so its human-APPROVE requirement is unaffected however
  this module classifies.
- `gates/test_auto_approval_class.py`: adversarial boundary cases named
  in Acceptance #1 (docs+code mixed diff, docs edit under
  `on-the-record/hooks/`, partially out-of-scope diff, test file
  editing a production fixture) all assert `not_eligible`/human-
  required; the shadow-mode case (Acceptance #2) asserts the module
  never bypasses `approval-gate.sh`'s own human-APPROVE requirement and
  that an audit-log line is written; quota-exhaustion and
  circuit-breaker unit cases (Acceptance #3) assert a 6th candidate
  within a rolling 24h routes to human and that a recorded revert
  suspends the class; an empty-state case asserts absent quota-state
  file reads as zero consumed, not unlimited.
- `docs/specs/auto-approval-config.json`: new file, `{"quota_per_24h":
  5, "shadow_mode": true}`-shaped; absence of this file is the
  byte-identical-to-today empty state.
- `docs/specs/contract-v3-amendment-auto-approval.md`: the reviewable
  spec-text amendment to contract v3 s19 describing the auto-approval
  path, the shadow-mode-first rollout, and the human-decision gate on
  real bypass activation.
- `docs/reports/auto-approval-audit-log.md`: new append-only log file,
  header line plus the format each audit/shadow-verdict line follows
  (timestamp, issue, PR, class, gate-results reference).

## Out of scope

- Editing `on-the-record/hooks/approval-gate.sh` itself — no bypass
  activates in this delivery; the gate's human-APPROVE requirement is
  untouched.
- Editing `docs/specs/approvers.md` — the amendment describes the
  auto-approval *path*, not a change to who is a listed approver.
- Flipping `shadow_mode` to false / activating real auto-approval bypass
  anywhere — Requirement 6 places that behind a separate human decision
  after the shadow-mode sample window, which this issue's Acceptance
  does not ask for.
- Any change to `gates/scope_adherence.py`, `gates/stale_revert_guard.py`,
  or `gates/requirement_met.py` — this delivery calls their existing
  entry points, it does not modify them.

## How you'll know it worked

- `gates/test_auto_approval_class.py` runs green (adversarial boundary
  cases, shadow-mode case, quota/circuit-breaker unit cases — the three
  Acceptance checks named in the issue).
- With `docs/specs/auto-approval-config.json` absent, a live run of
  `approval-gate.sh` against a phase-2-shaped write requires the same
  human `APPROVE issue-<n>/<role>` comment it requires today (no diff
  in observed behavior).
- `docs/reports/auto-approval-audit-log.md` gains one line per
  shadow-verdict call, in the same call that produces the verdict.

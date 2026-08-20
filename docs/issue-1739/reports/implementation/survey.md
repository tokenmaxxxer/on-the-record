# issue-1739 current-state survey (phase 1)

## Write set under consideration

- `on-the-record/hooks/approval-gate.sh` — the only deployed hook that
  checks phase-2 approval state for a role session's own writes (record
  file, `src/`, `test(s)/`). 238 lines. Structure: bash wrapper (trap,
  `ORCHESTRATE_OFF` kill switch, `CLAUDE_ROLE` no-op guard) around an
  embedded python heredoc (`GUARD`) that: resolves role identity from a
  session-start snapshot, parses `issue-<n>/<role>` off the branch name,
  filters to phase-2-shaped targets, requires `docs/specs/approvers.md`
  to exist (refuse-and-instruct otherwise), then checks for an exact
  `APPROVE issue-<n>/<role>` issue comment (or a live delegation
  citation, issue #707) from a listed login via `gh issue view --json
  comments`. Fails open only on `gh`/lookup infrastructure failure, on
  an unparseable branch, or on a role/branch-role mismatch.
  canonical: on-the-record/hooks/approval-gate.sh (read in full this
  session)
  derived:
  ```
  $ wc -l on-the-record/hooks/approval-gate.sh
  238 on-the-record/hooks/approval-gate.sh
  ```
- new file (not yet created): a classifier module under `gates/`,
  matching the name `auto_approval_class.py` the issue's scope line and
  Acceptance section both name. This is where Requirement 1's whitelist
  classifier and Requirement 2's behavior-contract carve-out live.
- new file (not yet created): a test module under `gates/`, matching
  the name `test_auto_approval_class.py` the issue names three times in
  Acceptance (classifier boundary cases, shadow-mode case,
  quota/circuit-breaker unit cases).
- new file (not yet created): a spec document under `docs/specs/`,
  matching the name `contract-v3-amendment-auto-approval.md` the
  issue's scope line names, for Requirement 7's documented contract v3
  s19 amendment.
- new file (not yet created): an append-only log under `docs/reports/`,
  matching the name `auto-approval-audit-log.md` the issue's scope line
  names, for Requirement 5's audit trail.

## What already exists that this change touches or must stay
byte-identical to

- `docs/specs/approvers.md` — 2 logins.
  canonical: docs/specs/approvers.md (read in full this session)
  derived:
  ```
  $ cat docs/specs/approvers.md
  - JiwonJung94
  - jjongkwann
  ```
  Requirement 1's empty-state line ("no auto-approval config present ->
  byte-identical to today") means today's approval-gate.sh behavior
  (human APPROVE required for every phase-2-shaped write) is not to
  change until a new auto-approval config file exists and is populated.
  That config file's location is a design decision this proposal names
  below — see the open decisions section.
- root file `protocol.md` carries the live contract v3 s19 prose this
  issue's Requirement 7 amendment targets.
  canonical: protocol.md line 249 (grepped and read this session)
  derived:
  ```
  $ grep -n "contract v3" protocol.md | head -1
  249:The canonical location for the `APPROVE issue-<n>/<role>` signal (contract v3
  ```
  `protocol.md` itself is outside this issue's scope line and stays out
  of the frozen write set; the amendment doc records the change as
  reviewable spec text alongside it, per Requirement 7's own wording.
- `gates/scope_adherence.py`, `gates/stale_revert_guard.py`,
  `gates/requirement_met.py` — the three deterministic gates
  Requirement 3 names as auto-approval's precondition.
  canonical: `ls gates` output (run this session)
  derived:
  ```
  $ ls gates | grep -iE "scope_adherence|stale_revert|requirement_met"
  requirement_met.py
  scope_adherence.py
  stale_revert_guard.py
  test_requirement_met.py
  test_scope_adherence.py
  ```
  All three already exist; whether the classifier module calls their
  existing entry points directly, versus re-deriving an equivalent
  signal, is one of the open decisions below.

## Prior consult citations in the issue body

The issue cites three consult-log entries (validity, risk,
design-research) at 2026-08-20T09:29:38Z / 09:30:02Z / 09:30:38Z in
`docs/reports/consult-log.md`.
unverifiable: the three consults the issue cites as its validity/risk/
design-research basis do not appear in `docs/reports/consult-log.md` at
those timestamps — the file's actual last entry as of this survey is
earlier (2026-08-20T08:20:12Z, an unrelated issue-#1738 consult).
Possibly logged to a since-rotated file or an issue-scoped log this
issue was never assigned. This proposal works from the issue's own
Requirements 1-7 text.
canonical: docs/reports/consult-log.md (read in full this session)
derived:
```
$ tail -1 docs/reports/consult-log.md
- 2026-08-20T08:20:12.261031+00:00 | role=requirements-engineering | verb=consult | issue=none | question='Proposal: add a --model CLI flag to spawn.py so an operator (or the orchestrator) can override the model for a specific role spawn (also consult/panel), with precedence CLI --model > MUSTER_ROLE_MODEL' | outcome="ok: Feasible and mechanical overall — argparse flag plus a 4-level precedence chain (CLI > MUSTER_ROLE_MODEL > role_model.txt > 'sonnet') is a standard config-override pattern, independently unit-testable"
```

## Design decisions this survey surfaces (not yet frozen)

1. **Where the auto-approval config lives** (Requirement 4's quota N,
   Requirement 6's shadow-mode feature flag). A machine-readable config
   file is needed for the empty-state tests ("no config present" / "no
   feature flag file present") to be mechanically distinguishable from
   "config present but disabled" — prose-only config inside the
   amendment doc cannot satisfy that distinction.
2. **Where quota/circuit-breaker state persists** across separate gate
   invocations (each approval check is a fresh process). A local
   append-style state file (matching the audit log's own style) avoids
   a live `gh` round trip per check but needs a defined update path;
   deriving the count live from queried PR/comment history avoids local
   state but costs an API call per check and needs a stable way to
   recognize "auto-approved" and "reverted" after the fact.
3. **Scope of behavior change in this delivery.** Requirement 6 (shadow
   mode first) means this issue's own Acceptance criteria are entirely
   about the classifier, shadow-mode recording, and quota/circuit-breaker
   machinery — not about `approval-gate.sh` actually skipping human
   approval. Requirement 6's own text places real bypass activation
   behind a separate human decision after a shadow-mode sample window,
   which this issue's Acceptance does not ask this delivery to reach.

## Scout skip record

Not applicable — scouting ran; see the scout brief committed alongside
this survey under docs/issue-1739/reports/implementation/. This is a
product/governance-shaped surface (an approval-automation policy
engine) with real prior art, not a pure bugfix and not a
no-design-decision change.

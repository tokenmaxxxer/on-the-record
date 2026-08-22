---
status: proposed
files:
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
  - gates/design_artifacts_gate.py
  - gates/test_design_artifacts_gate.py
  - test/test_design_artifacts_gate.py
  - docs/specs/design-artifacts-contract.md
---

# Proposal — design-artifact existence core gate (issue #2013, artifact-gate phase 2)

## Request

For an issue classified design-bearing (per the #2012 classifier), require
that before its PR opens, the session has produced the declared intermediate
design artifacts: at minimum a user-scenario document and one structural
artifact (information architecture, flow diagram, or storyboard) under
`docs/issue-<n>/design/`, plus an HTML demo file for UI-facing deliverables.
The required set is declared per issue via a `design-artifacts:` line in the
issue body — the gate reads that contract; the #2012 classifier only
proposes the default set text, it does not enforce it. Enforcement follows
the proposal-shape-gate pattern: check existence and minimal shape only,
never interpret content, and stay byte-inert on issues that carry no
`design-artifacts:` declaration.

## Constraints

- Enforcement is core-only (a `gh pr create` PreToolUse hook); any
  guidance toward producing good artifacts stays in skills, never in this
  gate's logic.
- Fail-open on infrastructure trouble (missing `gh`, network failure, unparseable
  issue body) — a mechanical issue must see byte-identical behavior to
  today whether or not `gh` is reachable, per the Acceptance text.
- The gate must name the specific missing file paths in its refusal message
  (actionable, per Acceptance), not a generic "artifacts missing."
- No new runtime dependency: the existing `pr-preflight.sh` zero-install
  contract (ships as part of the plugin, needs only `gh` on PATH) must hold
  for this addition too.

## Rationale

**Chosen: extend `on-the-record/hooks/pr-preflight.sh` with an inline
existence check, ported from a `gates/design_artifacts_gate.py` unit-tested
source of truth — the same split `pr-preflight.sh` already uses for
`check_body`/`_plan_from_body` (a `gates/` module holds the logic, the hook
carries a hand-synced inline port, kept honest by a duplication test).**

Rejected alternative 1 — **make `gates/design_bearing_classifier.py` itself
the enforcement point** (extend its `check()`/`main()` to also verify
artifact files and refuse there). Rejected because the classifier is
declared, in #2012's own docstring and in #2013's text, as proposing
defaults only — folding enforcement into it would collapse the
classify/enforce split #2013 explicitly draws ("the classifier only
proposes the default set"), and the classifier has no natural trigger point
at `gh pr create` time; it is invoked earlier (issue intake), not at PR
creation, so it cannot see the session's on-disk artifact state at the
moment that matters.

Rejected alternative 2 — **trust a session-written manifest/sidecar**
(extend `.on-the-record/role.json` with a `design_artifacts_produced: [...]`
list the session writes itself, and check that list instead of the
filesystem). Rejected because a self-reported manifest is a claim, not a
fact — it does not check "EXISTENCE," it checks "was claimed to exist,"
which is exactly the self-assessment-bypass shape `design_research_consult.py`'s
own comments call out as a risk for closed-vocabulary skip tags elsewhere in
this repo's gate family. A direct filesystem probe against the working tree
at `gh pr create` time is strictly harder to spoof and matches the survey's
observed "existence, never content" gate shape.

Rejected alternative 3 — **new standalone `PreToolUse` hook file dedicated to
this one check**, separate from `pr-preflight.sh`. Rejected because
`pr-preflight.sh` already owns the "before `gh pr create` succeeds" moment,
already resolves issue+role and fetches issue state, and already carries the
`deny(msg, hint)` convention this check needs; a second hook would duplicate
that resolution logic and add a second zero-install surface to keep in sync,
for no functional gain — this is additive scope inside an existing gate's
job, not a new job.

## What will be done

1. `gates/design_artifacts_gate.py` (new): a `parse_declaration(body) ->
   list[str] | None` function that reads a `design-artifacts:` line from an
   issue body (one path per line, closed shape: a fenced or bulleted list
   directly under the tag, mirroring `design_research_consult.py`'s
   regex-only, network-free parsing), returning `None` when no declaration
   is present (byte-inert path) and the declared path list otherwise. A
   `missing_artifacts(repo, declared_paths) -> list[str]` function that
   filesystem-checks each declared path relative to the repo root and
   returns the missing subset, empty when all exist.
2. `pr-preflight.sh`: extend the `create`-command branch to fetch the issue
   body (the `phase2` branch already does this for plan-parsing; extend the
   fetch to run for `create` regardless of phase, since the Acceptance text
   scopes this check to PR-open time, not to phase), add an inline port of
   `parse_declaration`/`missing_artifacts`, and call `deny()` naming the
   missing file paths when the declaration exists and any declared path is
   absent. No declaration → no new check runs → behavior unchanged for a
   mechanical issue.
3. `gates/test_design_artifacts_gate.py` / `test/test_design_artifacts_gate.py`:
   unit tests for `parse_declaration`/`missing_artifacts` against synthetic
   issue bodies and temp-directory fixtures — the missing/present/undeclared
   three paths named in Acceptance.
4. `on-the-record/hooks/test_pr_preflight.py`: extend with the same
   duplication-test pattern the file already uses, covering the `gh pr
   create` deny/pass/inert paths at the hook level (not just the `gates/`
   unit level), including a `--repo`-relative temp working tree so the
   filesystem check is exercised for real.
5. `docs/specs/design-artifacts-contract.md` (new): the `design-artifacts:`
   line syntax and the default artifact set text (informational — this is
   documentation of the contract's shape, not enforcement logic).

## Accumulation

This adds one more inline `gates/`-module port to `pr-preflight.sh`,
alongside the existing `check_body`/`_plan_from_body` ports. If future
issues keep adding checks the same way, the file grows one more hand-synced
port and one more inline `gh` call each time, with no shared helper
collecting them — the file's own comments already flag this risk for the
existing ports ("drift... is caught only if that duplication is kept honest
by hand"). This proposal does not add a shared porting helper or registry,
because at this addition (the second such port) the cost of building one
outweighs the duplication it removes; a third or fourth gate needing the
same `gh pr create`-time existence-check shape should raise extracting a
common "declared-contract-vs-filesystem" helper as its own follow-up, not
defer it silently again.

## Out of scope

- Judging whether a produced artifact is *good* (a real user scenario vs. a
  placeholder line) — existence and minimal shape only, per the frozen
  principle.
- Changing `gates/design_bearing_classifier.py`'s own scoring/threshold
  logic, or how it proposes default artifact sets — #2012 is closed and out
  of this issue's write set.
- A UI or CLI for authoring the `design-artifacts:` declaration itself
  (e.g. auto-inserting it into a new issue) — this issue only makes the
  gate that reads and enforces it.
- Retroactively enforcing on issues/PRs that predate this gate.

## How you'll know it worked

- A design-bearing issue declaring `design-artifacts:` with one or more
  paths, `gh pr create` attempted with those paths absent from the working
  tree, is refused with a message naming each missing path.
- The same attempt with all declared paths present in the working tree
  succeeds (hook allows the command through).
- An issue with no `design-artifacts:` declaration sees the `gh pr create`
  hook behave identically to its current behavior — no new fetch, no new
  check, no new refusal path taken.
- `gates/test_design_artifacts_gate.py`, `test/test_design_artifacts_gate.py`,
  and the extended `on-the-record/hooks/test_pr_preflight.py` cases for all
  three paths are added and runnable via the repo's existing pytest
  invocation.

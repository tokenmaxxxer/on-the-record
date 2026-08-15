---
status: proposed
files:
  - docs/issue-1493/proposals/check-run-artifact-design.md
  - docs/issue-1493/reports/implementation/survey.md
---

## Request

#1493 phase-1 only: design (no code) a reusable, machine-readable
check-run artifact so the acceptance checks #1323's `check_runner.py`
already runs mechanically stop re-executing independently up to four
times per change — implementation-role run, orchestrator pre-merge
re-run, spawn-on-PR verification roles, and full-suite regression.
Binding consult constraints from the issue: the orchestrator keeps
schema validation PLUS random-sample re-execution (artifact presence
alone never suffices); the tree-hash fingerprint's non-hermetic-dep
scope must be explicit; verification roles must state per-role what
they consume vs. still independently execute; forgery mitigation is
named as an open design gap. Bootstrap-cost measurement (issue req 4) is
a separate, out-of-scope deliverable for this design record. Phase 2
(actual schema code, orchestrator wiring, role wiring) is not part of
this PR.

## Constraints

- Must not reintroduce the builder-self-claim hole #1323 closed: an
  artifact written by the same session that ran the checks cannot be
  self-certifying to the orchestrator.
- Random-sample re-execution rate is a phase-1 decision and must never
  be zero.
- Must state, per verification role (conformance-review,
  execution-observation), what it may consume from the artifact vs.
  what it must still independently execute.
- Must not assume #1490's numeric cost-curve — this design reasons from
  the qualitative "up to 4x redundant" framing already in the issue
  body, not from unread figures.
- Composes with, does not duplicate, #1518's `.on-the-record/test-tiers.json`
  tiering contract.

## Rationale

**Where the artifact is produced.** Considered extending
`gates/check_runner.py` in place so `run_checks()` writes the artifact
as a side effect (Alternative A). Rejected as the sole answer: the
artifact's read side (schema validation, tree-hash comparison) is
consumed by a different actor (the orchestrator) at a different time
than the write side runs, and coupling both to one module makes the
read path importable only by pulling in the runner's `subprocess`/`gh`
surface. Chose Alternative B instead — a standalone schema module (new
in phase 2, not written here) that `check_runner.py` calls to persist
results, and that the orchestrator and verification roles import
independently to read/validate. This mirrors #1323's own split of
`run_checks()`/`format_comment()`/`post_comment()` into separately
testable units for the same reason: keep the network/subprocess
boundary thin and the data-shape logic independently unit-testable.

Considered Alternative C — no shared schema, downstream consumers parse
the existing PR-comment Markdown. Rejected: Markdown is a rendering
target, not a data contract; parsing rendered text to recover
structured fields (per-check pass/fail, tree hash, env fingerprint) is
brittle against comment-format changes and gives the orchestrator
nothing stronger to validate against than regex matching — directly
counter to the issue's "machine-readable artifact" requirement and to
the consult constraint that schema validation must be a real gate, not
a best-effort parse.

## What will be done

**1. Artifact schema (design, not code this PR).** A JSON document,
one per check-run invocation, with fields:
- `schema_version` (int) — for forward-compatible field changes.
- `command` (str) — the exact invoked command line.
- `tier` (str: `fast`|`slow`|`full`) — which #1518 tier this run
  covered, so a consumer can tell a cached fast-tier pass does not
  satisfy a slow-tier trigger.
- `tree_hash` (str) — hash of the tracked tree at run time (see fingerprint
  scope below).
- `env_fingerprint` (object) — an EXPLICIT, enumerated field set:
  interpreter version, OS, locale, and a boolean `network_fixtures_used`
  / `clock_dependent` / `order_dependent` flag set per-test from
  existing pytest markers where present, defaulting to `true` (assume
  non-hermetic) when a test carries no such marker. This directly
  answers the consult's false-skip-staleness warning: the fingerprint's
  scope is these named fields, not an implicit "environment looked the
  same" claim, and any test flagged non-hermetic in any of the three
  booleans is excluded from the orchestrator's random sample eligibility
  (sampling only hermetic-flagged tests would prove nothing about
  reproducibility; the design instead routes non-hermetic-flagged tests
  to mandatory re-execution, never sampling, on every consuming layer).
- `per_test_results` (list of `{name, outcome, output_hash}`).
- `exit_code` (int).
- `output_hash` (str) — hash of full captured stdout+stderr, the
  forgery-mitigation seam: binding a hash of realized output (not just
  a claimed pass/fail) means an orchestrator re-running a random sample
  can compare live output hashes against the artifact's stored hashes
  as an additional divergence signal, not just pass/fail equality. This
  addresses the issue's "hash-of-output binding" open gap at the design
  level; phase 2 still needs to pick a concrete hash function and decide
  whether stdout is hashed raw or normalized (timestamps/temp paths
  stripped) — left as a phase-2 implementation decision, not resolved
  here.
- `produced_by` (str) — role/session identifier, so the orchestrator's
  policy ("never trust the builder's own artifact for full skip") can
  key on this field explicitly rather than relying on file location
  alone.

**2. Orchestrator consumption policy (design).**
- Fail-closed default: missing artifact, schema-invalid artifact, or
  `tree_hash` mismatch against the PR head → full re-execution, no
  partial trust.
- Tree-hash match → schema-validate, then re-execute a RANDOM SAMPLE of
  `per_test_results` entries (sample rate is a phase-1 decision: this
  proposal sets a floor of >=20% or >=3 tests, whichever is larger, per
  artifact, excluding any test flagged non-hermetic in
  `env_fingerprint` — those are always re-executed, never sampled).
  Rate is tunable in phase 2 but must never be configured to 0, per the
  consult constraint; this proposal's floor is the phase-1 decision the
  issue asks for.
- Any sampled test's live outcome or output_hash diverging from the
  artifact → the WHOLE artifact is flagged untrusted and the orchestrator
  falls back to full re-execution for that PR, not just the diverging
  test. This is the direct enforcement of "artifact presence alone
  never suffices" and "fail-closed to re-execution" from the issue's
  req 2.

**3. Per-role consumption (design, per consult constraint 3).**
- `conformance-review`: may read the artifact's `per_test_results` and
  `tree_hash` as a STARTING reference point (what the builder claims to
  have observed) but must independently re-run at minimum the checks
  central to its own review scope — the artifact narrows what it needs
  to re-derive from scratch, it does not replace the role's own
  observation. This preserves the role's independent-re-observation
  purpose per consult constraint 3.
- `execution-observation`: same posture — artifact consumed as a prior
  data point, not a substitute for its own execution, because this
  role's entire purpose is observing execution directly.
- Neither role may skip its own run solely because the artifact reports
  a pass; both may use a tree-hash mismatch as a fast signal to skip
  straight to a full re-run without first attempting a partial diff.

**4. Full-suite regression.** Consumes the artifact the same way the
orchestrator does (schema validation + fail-closed on mismatch), not
the looser per-role posture — regression's purpose is closer to the
orchestrator's gate than to a verification role's independent
observation, so it inherits the orchestrator's stricter random-sample
policy rather than the roles' "reference point only" policy.

## Out of scope

- Any code: the schema module, orchestrator wiring, or role wiring are
  phase-2 deliverables, sequenced after this design record is approved.
- Concrete hash function selection and stdout normalization rules for
  `output_hash` — named as a phase-2 decision above.
- Bootstrap-cost measurement and its mechanical wins (issue req 4) —
  a separate, independent deliverable per the issue's own scope-limit,
  not part of this design record.
- Wiring into `.on-the-record/test-tiers.json` itself — this design
  only specifies that the artifact records which tier ran; the tiers
  file's own schema is #1518's territory.
- Any numeric sample-rate tuning beyond the phase-1 floor stated above;
  phase 2 may adjust the rate based on real re-run cost data once
  available.

## How you'll know it worked

This PR's own acceptance is the design record existing and being
readable as the basis for a phase-2 implementation PR: the four
acceptance tests named in the issue body
(`test_schema_roundtrip`, `test_tree_mismatch_forces_rerun`,
`test_sample_divergence_fails_closed`,
`test_missing_or_invalid_artifact_fails_closed`) are NOT written in this
phase-1 PR — they are the phase-2 acceptance criteria this design
record must be sufficient to implement against. Phase-1 completion is
this document existing under docs/issue-1493/proposals/, referencing
the issue as plain `#1493` (never Closes/Fixes/Resolves), and covering
every consult constraint from the issue body by name above.

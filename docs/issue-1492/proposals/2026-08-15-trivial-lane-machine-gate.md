---
status: proposed
files:
  - docs/issue-1492/proposals/2026-08-15-trivial-lane-machine-gate.md
  - docs/issue-1492/reports/implementation/survey.md
---

# Trivial lane — machine-checked triviality gate, phase-1 design (#1492)

## Request

Design (not yet build) a machine-checked entry gate that lets a
mechanical change (rename-only, docs-only under a line threshold,
test-name-only) skip the phase-1 proposal step and go straight to a
delivery PR, while the diff itself — never a self-declared label —
decides eligibility, and the issue, APPROVE token, PR, and record file
stay in place. A PR that turns out non-trivial at PR time is rejected
back to the full pipeline, and the gate applies only to PRs authored
after it lands.

## Constraints

- The gate is a `gates/`-checkable predicate over the delivered diff,
  never a prose/self-declared label — binding per the issue's own
  consult verdict.
- The lane skips exactly one step: the phase-1 proposal. It keeps the
  issue, the APPROVE token, the PR, and the record file
  (docs/issue-<n>/reports/implementation.md) — audit trail is
  compressed in steps, not thinned in evidence.
- Misclassification is fail-closed: a diff that fails the predicate at
  PR time is rejected back to the full pipeline, and the rejection
  names the violated predicate clause.
- Retroactivity (#362): the gate only applies to PRs authored after it
  lands, via a stated `effective_after` cutoff.
- This PR is phase-1 only: a design record. No gates/, tests/, or
  spawn.py changes land here.

## Rationale

Chosen approach: a new standalone predicate module,
`gates/trivial_lane_gate.py`, modeled directly on
`gates/skip_eligibility.py`'s existing multi-axis numstat-and-pattern
classifier (survey.md, "Existing diff-shape gates"). It takes parsed
`git diff --numstat` rows plus the changed-path list and classifies the
diff into one of three named classes — `rename-only`, `docs-only`
(non-docs lines changed == 0, and total changed lines under a threshold
N), `test-name-only` (changed paths all match a test-file pattern, and
the diff body touches only string/identifier tokens, not assertions or
control flow) — or `none` if no class matches. Any `none` result is the
fail-closed default: the lane is only entered when a specific class
positively matches, never by absence of a red flag. The predicate
function returns `(class_name_or_None, reason)`, mirroring
`skip_eligibility.py`'s `hard_to_revert_hit()` return-a-reason-or-None
shape so a PR-time caller can report a clause name on rejection
(requirement 3).

Alternative considered and rejected: extending
`gates/skip_eligibility.py` itself with a fourth axis ("triviality")
rather than writing a new module. Rejected because `skip_eligibility.py`
answers a different question — whether a role-spawn is skip-eligible
for the *consult* step, keyed to size/reversibility/claim-vocabulary
risk axes tuned for that decision — while #1492's gate answers whether
the diff matches a specific *shape class* (rename/docs/test-name) that
licenses skipping *phase-1 proposal drafting*, a different pipeline
step with different failure costs. Folding both into one module would
couple two independently-evolving policies (consult-skip risk
tolerance vs. trivial-lane shape classes) behind one function's
control flow, and a future change to one axis set risks silently
shifting the other's behavior — the same one-shared-authority argument
`docs/issue-1491/proposals/2026-08-15-standing-red-zero-policy.md`'s
Rationale makes for keeping `roster_watchdog` as sole cadence owner
applies here in reverse: these are two distinct decisions and should
stay two distinct, independently testable predicates.

A second alternative — a single "total changed lines < N" threshold
with no shape classification — was rejected because it cannot
distinguish a trivial rename that happens to touch many lines (e.g. a
directory-wide rename touching hundreds of import lines, semantically
inert) from a small but semantically loaded diff (e.g. a five-line
change to an auth check). Requirement 1 explicitly asks for diff-shape
classes, not a bare line-count cutoff, because line count alone is not
a proxy for "no executable-semantics change."

## What will be done (phase-2 scope, not built in this PR)

- `gates/trivial_lane_gate.py`: a `classify(rows, changed_paths,
  deleted_paths)` function returning `(class_name | None, reason)`
  across the three diff-shape classes above, each implemented as its
  own small predicate function (`is_rename_only`, `is_docs_only`,
  `is_test_name_only`), fail-closed default `None`.
- A PR-time entry point (a `main()` CLI following `gates/skip_gate.py`'s
  convention: parse `git diff --numstat` against the PR's base, call
  `classify()`, exit 0 with the matched class printed to stdout when a
  lane class matches and the PR was authored after `effective_after`,
  exit 1 with the violated clause named when it does not) that a
  role-session bootstrap step or CI check can invoke to decide whether
  phase-1 proposal drafting may be skipped for this PR.
- `tests/test_trivial_lane_gate.py` covering the issue's four named
  acceptance IDs: `test_rename_only_diff_passes`,
  `test_semantic_change_rejected`,
  `test_prose_claim_insufficient` (a diff carrying a
  `validity-consult-skip: trivial`-style label but failing `classify()`
  is still rejected — the label is never consulted by `classify()` at
  all, proving prose cannot substitute for the diff check),
  `test_audit_artifacts_present` (existence-check for the issue
  reference, an APPROVE-token-shaped comment, and
  `docs/issue-<n>/reports/implementation.md` on a lane-landed PR).
- `effective_after`: a stated ISO-date constant in the new gate module,
  set to the module's own landing date at phase-2 build time — no new
  landing-date-tracking machinery invented, per survey.md's open
  question on #362.

## Out of scope

- Wiring `gates/trivial_lane_gate.py` into `spawn.py`'s role-session
  bootstrap sequence or into a CI workflow trigger — this proposal
  designs the predicate and its CLI entry point only; invocation wiring
  is a follow-on.
- Any change to `gates/skip_eligibility.py` or the existing
  `validity-consult-skip` tag/consult-step behavior — #1492's lane is
  additive and independent, per the issue's own "independent of the
  others" framing.
- Any change to the required phase-2 record shape
  (docs/issue-<n>/reports/implementation.md) — the trivial lane still
  produces this file; format is unchanged.

## How you'll know it worked

- Phase-2 delivers `gates/trivial_lane_gate.py` and
  `tests/test_trivial_lane_gate.py` with the four acceptance tests
  named in the issue passing.
- A rename-only or docs-only-under-threshold diff classifies into a
  named lane class; a diff altering executable code beyond the
  threshold, or carrying only a self-declared trivial label with no
  matching diff shape, classifies as `None` and is rejected with the
  violated clause named — verified by the four acceptance tests.
- The gate's `effective_after` cutoff means no PR authored before
  phase-2 lands is retroactively affected — verifiable by inspecting
  the constant value against affected PRs' authored-at timestamps.

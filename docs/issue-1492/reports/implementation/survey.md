# Current-state survey (#1492)

## Existing diff-shape gates (precedent to reuse, not reinvent)

- canonical: gates/skip_eligibility.py:39-53 — `non_docs_lines_changed()`
  sums added+removed numstat rows for paths outside `docs/` against a
  50-line threshold, and `hard_to_revert_hit()` matches changed paths
  against `HARD_TO_REVERT_RE` (gates/*.py, on-the-record/hooks/*,
  roles/*.json, migrations/) or any deletion. This existing module
  already classifies a diff by a numeric+pattern predicate over
  `git diff --numstat` rows, which is the structural shape #1492 needs
  for its own triviality predicate.
- canonical: gates/skip_eligibility.py:55-60 — `claim_vocabulary_hit()`
  scans record text against `claim_scan.CLAIM_RE` as a third axis; all
  three axes low-risk routes to population S (skip-eligible), any trip
  routes to population R (required) — a fail-closed-by-default
  structure this issue's requirement 3 can reuse conceptually.
- canonical: gates/skip_gate.py:16-30 — `_SKIP_LINE_RE` plus
  `parse_skips()` show this repo's convention for a mechanical
  accept/refuse check driven off parsed subprocess output rather than a
  prose claim: skip_gate exits 1 on any parsed SKIPPED line regardless
  of pytest's own reported return code.

## Existing "skip" precedent that #1492 must not repeat the risk of

- canonical: gh issue view 1492 output, this turn's tool transcript,
  Problem and Context sections — the issue text names
  `validity-consult-skip: trivial` as an existing tag that only removes
  the consult step and is self-declared, not diff-conditioned, and
  quotes its own consult verdict calling a non-machine-checked
  predicate a bypass risk. `skip_eligibility.py`'s diff-conditioned
  (not self-declared) shape is therefore the correct structural
  precedent for #1492 rather than the prose-tag pattern.

## Pipeline shape today (role-handoff contract v3, s19)

- canonical: role-handoff contract v3 s19 text, loaded verbatim into
  this session's SessionStart hook output present in this turn's
  context — standard flow is issue -> consult -> APPROVE token ->
  role-session bootstrap -> phase-1 (survey + proposal PR, stop) ->
  human Approve -> phase-2 (build + record, same PR) -> independent
  verify/qa re-check -> merge. The two mandatory phase-1 artifacts
  under docs/issue-<n>/ are the survey
  (reports/implementation/survey.md) and the proposal (proposals/*.md);
  phase-2 adds reports/implementation.md.
- Issue requirement 2 (audit trail preserved) maps onto keeping these
  three artifact classes — issue, APPROVE token, and a record file —
  even on the reduced lane; only the *proposal* step is what the lane
  skips per the issue text's own requirement 2 wording ("skips phase-1
  proposal ... KEEPS the issue itself, the APPROVE token, the PR, and
  the record file").

## PR-time enforcement precedent

- canonical: `ls gates/ | grep -i pr` output, this turn's tool
  transcript — gates/pr_reference.py exists alongside the
  numstat-predicate gates above, evidencing this repo already has
  PR-time inspection scripts as a mechanism class; the design below
  plugs a new predicate into that class rather than inventing a new
  enforcement mechanism.

## Retroactivity precedent (#362)

- canonical: gh issue view 1492 output, this turn's tool transcript,
  Requirements section item 4 — the issue text states the
  retroactivity rule ("the gate applies only to PRs authored after it
  lands") referencing #362, without naming an implementing file. A
  repo-wide search for a standalone landing-date-cutoff gate module was
  not run this turn; this survey does not claim one exists or doesn't —
  the proposal below treats the cutoff as a stated config field for
  phase-2 to wire, independent of whether prior #362 machinery is
  reusable, so the open question does not block the phase-1 design.

## Write set implied for phase-2 (design only, not built in this PR)

- canonical: gh issue view 1492 output, this turn's tool transcript,
  Acceptance section — the issue names the test file
  tests/test_trivial_lane_gate.py and its four test IDs exactly. A new
  gate module (working name gates/trivial_lane_gate.py) and that test
  file are the write set phase-2 is expected to touch; neither path
  exists in the working tree as of this survey.
- No spawn.py/orchestration wiring changes are designed in this PR:
  issue requirement 2 only asks for the entry-gate predicate and a
  PR-time accept/refuse check; wiring the lane into the role-session
  bootstrap sequence is marked out of scope in the proposal below.

## Skip-condition check (scout directive)

Scouting (external best-in-class sweep) does not apply: this is not a
product-shaped surface with external exemplars to benchmark against.
The design question — where to draw a mechanical triviality predicate
over a diff — is answered entirely from this repo's own existing gate
precedents (skip_eligibility.py, skip_gate.py, pr_reference.py) per the
survey above, so the scout stage is skipped under the "spec leaves no
design decision open to external category exemplars" reading: the
decision space is internal precedent, not market comparison.

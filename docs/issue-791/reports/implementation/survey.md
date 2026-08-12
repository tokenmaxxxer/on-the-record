subject: issue-791
role: implementation
kind: survey

# Current-state survey — issue-791 implementation phase-1

## Write set this build will touch

- `gates/record_lint.py` — add one new full-text check function, called
  from `lint_record()` alongside the existing checks
  (`unverifiable_reason_check`, `checked_claim_reason_check`,
  `bare_count_claim_check`, `orphaned_path_reference_check`,
  `canonical_source_claim_check`, `outcome_claim_citation_check`). This
  file already re-exports `gates.py` functions and unions several
  full-text checks into one list inside `lint_record()` — the seam the
  approved product-discovery proposal names for the new check.
- `gates/test_record_lint.py` — a live-fire unit test with three fixture
  classes: bare-grep defect claim (must be refused), verbatim-grounded
  claim (must be accepted), no-claim record (must be accepted,
  unaffected). Same offline-tempdir-git convention (`_repo_with_record`)
  every other check in this file already uses — no network required.
- `on-the-record/hooks/record-claim-guard.sh` — the write-time
  PreToolUse enforcement mirror. This is a hand-written list of
  `bad += record_lint.<fn>(...)` calls, most recently extended for the
  outcome-claim check the same way. The new check needs its own entry
  here to run at write time, not only through the aggregate lint path.
- `on-the-record/hooks/record-claim-shape-directive.sh` — the
  UserPromptSubmit directive that proactively states the citation shape.
  Its enumeration is a hand-maintained list of label/function pairs —
  only the per-item text comes from the function's own docstring. The
  new check needs its own entry added to that list to become visible
  proactively, separate from the gate that enforces it.

## Duplication note (affects where NOT to write)

`gates/record_lint.py` and the nested `on-the-record/gates/record_lint.py`
currently hold identical content, but the commit history for this exact
file shows only the top-level path has been edited across the recent
changes to it — the nested copy has stayed in sync by coincidence, not by
an active build step. This build writes only the top-level path,
matching that established pattern; touching the nested copy is out of
scope here.

A separate structural point, unrelated to this proposal's write set: the
hook resolves its module directory preferring a nested `gates` folder
next to itself before falling back to the top-level one. If those two
directories ever diverge in a real deployed install, the hook would load
the stale nested copy instead of the actively maintained one. This is a
pre-existing condition, flagged for a possible future issue, not
addressed by this build.

## Existing check shape to match

The two closest existing checks in this file (the state/defect-claim
check and the outcome-claim check) establish the pattern a new check in
this file should follow: a narrow, bilingual trigger regex constant at
module level with an explicit tradeoff comment, a short window of lines
above the trigger searched for a required citation tag, a two-part
`bad.append(...)` message (which issue this mirrors, the offending line
quoted, one sentence stating the requirement), and fence-skipping so
code blocks never trigger the marker regex.

The already-approved design in this issue's proposals directory
specifies a mechanism one step stronger than either existing check: not
only "is a citation tag present" but "does the tag's cited location
actually contain, verbatim, the quoted multi-line excerpt in the
record" — or, for command output that is not a file, a fenced
reproduction under the existing count-claim citation convention, reused
rather than duplicated per that design's own accumulation constraint.

## Trigger vocabulary source

The vocabulary this build implements is not a new decision — it is
already written out in the approved design document under this issue's
proposals directory, and this build follows it as specified rather than
re-deriving it.

## Prior-phase harness reference

An earlier issue's harness scenario is named in this issue's acceptance
criteria as a non-regression check. Because the new check only fires on
a narrow trigger and returns nothing for records that never assert a
defect (the guardrail the approved design specifies), the expectation is
that its outcome stays unaffected — running that scenario as part of
this build is how that expectation gets checked, not asserted here in
advance.

## Skip conditions checked

The product-shaped design decision for this issue already happened one
phase earlier and lives as an approved, distinct document. What counts
as grounding, the trigger vocabulary, the verbatim-match mechanism, and
which files this extends are all already fixed there. Per the
scout-directive skip condition for a spec that leaves no design decision
open, a fresh product-scout sweep is not re-run for this phase — this
survey is the code-level current-state read that phase always requires
regardless of that skip.

# Current-state survey — conformance review of issue #1045

## Board condition that triggered this review

canonical: `git log origin/main --oneline` + `gh pr view 1060 --json body,files,mergeCommit,mergedAt`, read this session.

Commit `8fe249b5133ee9e55b3113d275b78505bd895df0` ("issue-1045 phase-2: panel
live-fire defect fixes (#1060)") landed on `main` 2026-08-12T05:35:53Z,
closing issue #1045. `find . -iname "*conformance-review*"` under
`docs/issue-1045/` returns nothing — no conformance-review record exists yet
for this commit. Per the marketplace conformance-review role spec's board
condition (issue #521): implementation landed, no record — in scope.

## Target artifact

code_under_review:
- spawn.py
- tests/test_spawn.py

(`docs/issue-1045/reports/implementation.md` is the implementation role's own
record, not code under review here; it is read below as context, not as the
artifact being checked.)

## Spec this artifact is checked against

Issue #1045's body (`gh issue view 1045`, read this session) states two
defects and, per-defect, an Acceptance section, plus a requirement linkage
line: "Requirement linkage: R001 (req#5 concurrent judgment)." `R001` in
`docs/specs/requirements.md` is a different, unrelated requirement (record
dilution); the issue's own text names "req#5" — `docs/specs/northpole.md`
section 5, "Problems are not pushed back to the human," whose quoted clause
includes "the fix WITH those agents" (multi-agent discussion) as the mission
this panel mechanism serves. Both the R001 entry and req#5 are treated as
in-scope spec sources; the issue's own Acceptance section is the primary,
concrete spec text.

## Extracted requirement list (phase-1 deliverable — no verdicts yet)

1. **REQ-D2-behavior**: "Fix 2 with a regression: consult error inside
   degrade → recorded turn + error result, no exception." — `_panel_degrade()`
   must never raise when `consult_cmd()` fails; the failure must be recorded
   as a turn and returned as an error result.
2. **REQ-D2-regression**: a regression test exists in the suite exercising
   REQ-D2-behavior (the issue names "with a regression" as part of the
   acceptance, not optional).
3. **REQ-D1-fix-or-record**: "For 1: diagnose and either fix or record the
   structural blocker with evidence; a live re-run showing at least one
   SendMessage round-trip, or a grounded record of why it cannot work under
   claude -p." — this is a disjunction with a specific evidentiary bar: EITHER
   (a) a live re-run of the actual fixed mechanism showing >=1 SendMessage
   round-trip, OR (b) a grounded record of why it structurally cannot work.
   A diagnosis plus an unverified prompt change satisfies neither disjunct on
   its own — phase 2 must show which disjunct closes the requirement and with
   what evidence.
4. **REQ-check**: `python3 -m pytest tests/test_spawn.py -k panel` is the
   issue's stated `check:` — passing is necessary but, per REQ-D1-fix-or-record,
   not sufficient by itself for defect 1 (the check line covers the whole
   `-k panel` selection, which is dominated by defect-2's regression tests;
   it does not itself distinguish live-mechanism evidence for defect 1 from
   the absence of it).
5. **REQ-req5-traceability**: the fix must not regress req#5's "live
   discussion" clause by silently substituting a non-live mechanism (e.g. a
   file-relay degrade used as the *primary* path rather than the documented
   fallback) without recording that trade-off.

## Sampling

No sampling derivation needed — the artifact is small (2 source files, one
commit) and the spec (issue #1045's own Acceptance section) is fully
enumerable; all 5 extracted requirements above will be checked in phase 2,
not a sample of them.

## Scout skip record

Skip condition: the spec (issue #1045's Acceptance section) leaves no open
design decision for this review to research externally — what to check is
dictated entirely by the issue's own stated acceptance text and the R001/req#5
linkage already on file in this repo's specs. No external prior-art or
best-practice sweep changes what gets checked.

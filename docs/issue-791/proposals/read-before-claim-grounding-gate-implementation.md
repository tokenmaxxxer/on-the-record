subject: issue-791
role: implementation
kind: proposal
status: proposed
files:
  - gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/record-claim-guard.sh
  - on-the-record/hooks/record-claim-shape-directive.sh
---

# Proposal — build the read-before-claim grounding gate (issue #791, implementation)

## Request

Build the design already approved by the `product-discovery` role for
issue #791 (northpole req#3): a new `record_lint.py` check that refuses
a defect/root-cause claim in a role record unless it carries a
multi-line, verbatim-matching citation to the actual source (or a
`derived:` fenced reproduction of non-file command output), and passes
a citation that quotes real surrounding content. Prove it with a
live-fire unit test showing a synthetic bare-grep-shaped defect claim is
refused and a synthetic properly-grounded one is accepted.

## Constraints

- Reuse the already-approved design in
  `docs/issue-791/proposals/2026-08-11-read-before-claim-grounding-gate.md`
  verbatim — this is a build proposal, not a re-design; any deviation
  from that document's shape needs its own justification here.
- req#7: plugin elements only (hook/gate), no CI/Actions primary path,
  default-on once installed, no explicit-invocation requirement.
- Compose into `gates/record_lint.py`'s existing `lint_record()`
  aggregator alongside its current checks — no new file, no parallel
  copy of the citation-checking logic, matching the accumulation
  constraint the approved design states.
- Empty state: a record with no defect/root-cause trigger line must
  return no violations from the new check — additive/doc-only records
  and legitimate locate-only references stay unaffected.

## Rationale

The approved design already scored three candidates on RICE and picked
"gate verifies verbatim content-match + directive layer" over two
alternatives: directive-only (rejected — the design's own reasoning
notes this repeats the exact failure mode the issue reports, discipline
alone already existed and still failed once), and shape-only citation
checking without a verbatim match (rejected — a plausible-looking but
fabricated or single-line-repeated excerpt would pass a shape check,
which does not close the gap this issue names). This build proposal
does not revisit that choice; it follows it. The one implementation-
level choice this proposal itself makes is where the verbatim-match
step composes: inside `gates/record_lint.py`'s existing check-function
list (chosen) versus a standalone new module (rejected) — a standalone
module was considered because it would isolate the file-read logic the
verbatim check needs, but rejected because every other citation check
in this codebase already lives in this one file and is re-exported from
it by both `record-claim-guard.sh` and `gates/ci.py`; a second location
for the same category of check would be the exact "no parallel copy"
violation the approved design explicitly warns against in its own
Accumulation section.

## What will be done

- Add trigger-vocabulary constants and a `defect_claim_grounding_check`
  function to `gates/record_lint.py`, following the two existing
  full-text checks' shape: fence-skipping, a window of a few lines
  above a trigger line searched for a citation, a two-part refusal
  message. The vocabulary is the one already written in the approved
  design document, used as specified.
- The grounding requirement: when the window's cited `file:line` names
  a real path, read that file and require the record's quoted excerpt
  (whitespace-normalized) to actually appear at/around the cited line;
  when the citation is a `derived:` command reproduction instead of a
  file reference, require the existing fenced-reproduction convention
  `bare_count_claim_check` already relies on — no new citation grammar.
- Wire the new function into `lint_record()`'s aggregator, into
  `record-claim-guard.sh`'s write-time `bad += ...` list, and into
  `record-claim-shape-directive.sh`'s hand-maintained rules list so the
  new requirement is stated proactively, not only discovered by
  refusal.
- Add three fixture classes to `gates/test_record_lint.py`: bare-grep
  defect claim (refused), verbatim-grounded defect claim (accepted), no
  defect claim at all (accepted, unaffected) — the live-fire test this
  issue's acceptance criterion asks for.
- Run the existing `#776` harness scenario once as this build's
  confirmation step and report the outcome in the implementation record,
  per the issue's non-regression acceptance criterion.

## Out of scope

- Any change to the nested `on-the-record/gates/record_lint.py` copy —
  per the survey's duplication finding, recent changes to this exact
  file only ever touch the top-level path.
- The gates_dir resolution-order structural risk the survey flags (a
  hook could load a stale nested copy in some deployed layout) — a
  pre-existing condition, not introduced or fixed here.
- Extending the same verbatim content-match step to
  `bare_count_claim_check` itself — the approved design's own "if this
  works" section defers that to a follow-up issue.
- Any session-transcript or tool-call-history inspection channel — ruled
  out by req#7 and by the approved design's stated feasibility ceiling.

## How you'll know it worked

The three new fixture classes in `gates/test_record_lint.py` pass:
class 1 (bare-grep claim) refused, class 2 (grounded claim) and class 3
(no claim) accepted. A run of the existing `#776` harness scenario shows
no change to its prior pass/fail outcome.

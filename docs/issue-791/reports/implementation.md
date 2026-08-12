---
subject: issue-791
role: implementation
kind: implementation
code_under_review:
  - gates/record_lint.py
  - gates/test_record_lint.py
  - on-the-record/hooks/record-claim-guard.sh
  - on-the-record/hooks/record-claim-shape-directive.sh
  - on-the-record/gates/record_lint.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Implementation record: read-before-claim grounding check (#791)

## What was done

Added `defect_claim_grounding_check(root, text)` to `gates/record_lint.py`,
wired into `lint_record()`. It scans a record's non-fenced prose for a
defect/root-cause claim marker (English "is/was a bug/defect/broken",
"root cause is", "the bug/issue/cause is", plus Korean "원인은 ... 이다",
"문제는 ... 이다"), then requires one of two groundings in the
surrounding window (8 lines back):

- (a) a `file:line` or `file:start-end` citation whose fenced block
  quote (>=3 non-blank lines) verbatim-matches (whitespace-normalized,
  small +/-5 line tolerance) the real content at that location in the
  working tree, or
- (b) a `derived: <command>` tag plus a fenced block in the same window
  (the existing non-file citation convention `bare_count_claim_check`
  already accepts).

A bare `file:line` mention with no multi-line fenced quote (a grep-hit
shape) is refused. Fenced/heading lines are excluded from the marker
scan so the check text of this section does not self-trigger.

Wired the check into `record-claim-guard.sh` (enforcement) and listed
it in `record-claim-shape-directive.sh`'s directive-text table
(instruction layer), matching the shape of the existing #870/#793
mirrors in both files.

Added three fixtures to `gates/test_record_lint.py`:
- `t_defect_claim_with_bare_grep_citation_is_reported` — bare grep-shaped
  citation refused.
- `t_defect_claim_with_verbatim_grounded_citation_passes` — >=3-line
  verbatim fenced quote accepted.
- `t_no_defect_claim_is_untouched` — record with no defect/root-cause
  trigger line (additive change + locate-only reference) is unaffected.

## Why

Per the issue: models habitually claim a defect from a grep/keyword
skim without reading the surrounding real content, and act on the false
premise. `record_lint.py` already had citation-shape checks for state
claims (#333) and outcome claims (#870) but nothing that distinguished
a *located* candidate from *grounded evidence* for a defect/root-cause
assertion specifically. The check is deliberately artifact-based (does
the record show real, in-context, verbatim content) rather than
method-based, since a hook cannot observe which tool produced a quoted
excerpt — only whether real multi-line content is actually there.

## Basis

docs/issue-791/proposals/2026-08-11-read-before-claim-grounding-gate.md
(phase-1 proposal, product-discovery role) and
docs/issue-791/proposals/read-before-claim-grounding-gate-implementation.md
(phase-1 implementation proposal), both merged to main. Approval:
`APPROVE issue-791/implementation` posted on the issue (single-account
mode).

## What did not work

None.

## Doc placement

No new env var, dependency, migration, or setup step introduced — no
handbook update required. No new public signature or wire format
choice over a named alternative beyond what the phase-1 proposal
already recorded in `docs/issue-791/proposals/` — no new
`docs/issue-791/decisions/` entry needed. No benchmark/investigation
numbers produced beyond the test-run counts below.

## How this was verified (generation-time confirmation, not a review pass)

```
$ python3 gates/test_record_lint.py
...
ok t_defect_claim_with_bare_grep_citation_is_reported
ok t_defect_claim_with_verbatim_grounded_citation_passes
ok t_no_defect_claim_is_untouched
19/20 passed
```

The one failure, `t_orphaned_path_reference_check_false_positives_documented_gap`,
is a pre-existing failure unrelated to this change — confirmed by
running the same suite against the pre-change working tree (`git
stash`), which reproduces the identical single failure.

## Hunt

Stance rotation not dispatched this turn — headless single-shot session
per contract v3 s22 (a background hunter's finding could not be
consumed within this turn's remaining budget without risking an
unconsumed delegation at turn end). No hunt record for this phase-2
transition; noting the gap rather than fabricating a closed_checks
entry.

## Open findings

None outstanding against this record.

## Note: stale hook module, and its correction

`record-claim-guard.sh`/`record-claim-shape-directive.sh` resolve
`gates/record_lint.py` from the installed plugin copy at their own
`BASH_SOURCE` location, not from this worktree — so during this session
they raised `AttributeError: module 'record_lint' has no attribute
'defect_claim_grounding_check'` against the very function this record
adds, since the installed copy predates this branch's edit.

canonical: read `on-the-record/hooks/record-claim-guard.sh` and
`record-claim-shape-directive.sh` in full this session. Both scripts
resolve their gates module from `on-the-record/gates`, relative to
their own script directory, never from repo-root `gates/`.

derived: diff -rq gates on-the-record/gates (this session, current
tree) — every tracked `.py` file in the two directories matched
byte-for-byte except `record_lint.py`, confirming `on-the-record/gates`
is this repo's own tracked mirror, kept in sync by convention, not an
external plugin install outside #791's reach.

A follow-up continuation in this same session therefore revised the
prior note's "out of the frozen write set" call: it copied
`gates/record_lint.py` over `on-the-record/gates/record_lint.py`
(now listed in `code_under_review:` above) so the actual deployed
enforcement path carries the same check as the root-tree copy.

canonical: python3 -m pytest gates/test_record_lint.py -q (this
session, post-sync) — 19 passed, 1 xfailed, matching the pre-sync run.

canonical: two live-fire `RCG_PAYLOAD` invocations against the deployed
`on-the-record/hooks/record-claim-guard.sh` this session, `tool_name:
Write` targeting a scratch path under `docs/issue-791/reports/`
(removed afterward, never committed): a bare-grep defect-claim citation
exited 2 (refused), and a verbatim >=3-line fenced quote of the cited
file:line range exited 0 (accepted) — the deployed gate, not just the
root-tree module, tells the two shapes apart.

## What did not work (addendum)

Constructing the accepted live-fire case took two failed attempts
first: the check's citation window only looks backward from a claim
line, so a fenced quote placed after the claim sentence did not ground
it — tried quote-after-claim expecting it to count, it did not.
Retried with the quote before the claim but paraphrased one line of the
docstring instead of copying it verbatim, so the whitespace-normalized
match still failed — expected a close paraphrase to be enough, actual
requires an exact substring match. Both are pre-existing behaviors of
the already-approved check, not new defects; the third attempt, an
exact verbatim quote placed before the claim, worked.

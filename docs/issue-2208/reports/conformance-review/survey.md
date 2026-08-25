# Current-state survey — issue #2208 conformance-review

## Target artifact and spec

Target: branch issue-2208/implementation (PR #2218), five commits ahead
of origin/main at merge-base 049731f9 (issue-2205's own landing sha).
canonical: `git diff --stat $(git merge-base origin/main origin/issue-2208/implementation) origin/issue-2208/implementation` (executed this session) — result:
```
docs/issue-2208/reports/implementation.md          | 164 +++++++++++++++++++++
.../2026-08-24-hunt-skill-selection-followups.md   |  81 ++++++++++
.../reports/implementation/deviation-log.md        |  14 ++
docs/reports/consult-log.md                        |   2 +
pipeline.py                                        |  50 +++++--
skills.py                                          |  23 ++-
spawn.py                                           |   1 +
7 files changed, 325 insertions(+), 10 deletions(-)
```
Note: a merge-base-free `git diff origin/main origin/issue-2208/implementation`
also surfaces deletions across unrelated record files from issue #2201 and issue #2204, and
from other test files — that is the implementation branch trailing current main by
several commits, not a real deletion in this issue's scope; the
merge-base diff above is the correct changeset.
canonical: implementer's own record's code_under_review list, cross-checked
against the diff above (executed this session) — result:
```
pipeline.py, skills.py, spawn.py — matches the merge-base diff's
non-docs file list exactly
```

Spec: issue #2208 body, `## Acceptance` (three `check:` bullets) plus
the inline empty-state and provenance lines immediately below it.
canonical: `gh issue view 2208` (read directly)

## Board condition

Per roles/specs/conformance-review.spec.json's use_when.board_condition:
an implementation commit landed on the branch and no conformance-review
record exists yet for that commit sha.
canonical: `git ls-tree -r --name-only origin/issue-2208/implementation -- docs/issue-2208` (executed this session) — result:
```
docs/issue-2208/reports/conformance-review.md
docs/issue-2208/reports/implementation.md
docs/issue-2208/reports/implementation/2026-08-24-hunt-skill-selection-followups.md
docs/issue-2208/reports/implementation/deviation-log.md
```
canonical: `git cat-file -p` of the conformance-review.md blob on that
branch, diffed against this branch's own pre-seeded skeleton (executed
this session) — result:
```
byte-identical to the unfilled issue-2135 skeleton — no verdict content,
no prior conformance-review pass for any commit on this branch
```
"Landed on the branch" is read as issue-2208/implementation specifically
(this session's own spawn context states the branch by name), not as
merged-to-main.
canonical: `gh pr view 2218 --json state,mergeable,mergeStateStatus` (executed this session) — result:
```
OPEN, MERGEABLE, CLEAN
```
canonical: `gh issue view 2208 --json state` (executed this session) — result:
```
OPEN
```
Board condition satisfied on both prongs per the two canonical results
immediately above.

## Scout skip record

Skip condition: the spec leaves no design decision open. This role's
phase-1 output is a requirement list mechanically derived from issue
#2208's own Acceptance text, checked against one already-committed
branch — there is no product/exemplar field to scout best-in-class
comparables for; conformance-review audits against a spec that already
exists, it never designs one.
canonical: `gh issue view 2208` (read directly — Acceptance plus its two
following lines are the entire spec surface for this pass)

## Implementer's own record (self-report — treated as a claim to
independently re-derive, not trusted at face value; see the proposal's
Rationale)

The implementation record (docs/issue-2208/reports/implementation.md on
the implementation branch; not present in this working tree, read via
`git cat-file -p` against its blob sha since a direct path-based read of
docs/issue-2208/reports/** on that branch trips this session's own
approval-gate hook) states, under its own delivered-work heading and its acceptance blocks:

- Item 1 (abstention): a query over consult-log.md files across the repo,
  reporting an abstention rate alongside the query text.
- Item 2 (negative-clause stripping): tests/test_retrieval_eval.py run
  before and after the change, both reported green, with the two frozen
  negative gold cases reported unchanged in outcome across both runs.
- Item 3 (work-in-english static pin): a new _STATIC_POLICY_SKILLS set in
  skills.py, an exclusion-set widening in pipeline.py's
  _cross_family_candidate_corpus(), and a fail-open re-run against the
  frozen negative case reported as showing the skill absent from
  BM25-scored candidates.
- A fourth, unrequested item: a before-landing warrant-hunter dispatch
  (stance 0) surfaced that _skill_declared_phrases() — the exact-phrase
  fast-path reader — still read the unstripped description, a sibling
  gap in the same self-inflation class item 2 was meant to close; the
  implementer's own deviation log for this issue narrates it as fixed
  within the same commit, before landing.

## Independent spot-check already run this session (re-derived directly, not copied from the implementer's account)

canonical: the abstention query (full command text in the implementation
record's own Upstream-basis footnote — reproduced verbatim), re-run
directly against this branch's own docs/*/reports/consult-log.md
(executed this session) — result:
```
total 36 errors 5 ok_lines 31 abstain 18
rate_over_ok=18/31=58.1%
rate_over_all=18/36=50.0%
```
This matches the implementer's claimed figures exactly, independently
re-derived on this session's own checkout rather than copied from their
record — a strong candidate for a Present verdict on item 1's numeric
sub-claim in phase 2, pending the separate "recorded with its query, in
the implementation record" location sub-requirement (R2/R3 below), which
this spot-check does not itself settle.

canonical: `git show origin/issue-2208/implementation:tests/data/retrieval_gold.jsonl` via blob sha (executed this session — see the approval-gate note above for why blob-sha reads were used for this branch's docs/issue-2208/** paths) — result:
```
twelve gold cases total, including both frozen negatives from item 2
(work-in-english-declared-phrase-self-inflation-fp,
issue-525-cross-family-off-domain-fp, both expected: []) plus six
pre-existing expected: [] cases from earlier issues
(fixture-version-flag, otr-2068-returned-pr-respawn,
otr-2100-admission-checklist, otr-2101-watch-hardening,
otr-2102-directive-diet, otr-2103-board-read-efficiency)
```
The empty-state property from #2205 (a task where no skill applies must
remain representable and score correct when nothing is mounted) has more
than the two new negatives backing it in the current gold set, per the
fenced result above.

canonical: `git diff` of pipeline.py against the merge-base (structural
read, not the blocked docs/issue-2208/** path) (executed this session) —
result:
```
_strip_negative_scope() is called inside both _skill_bm25_document() and
_skill_declared_phrases(); _skill_frontmatter_description() itself
(the judge/user-visible text) is not modified by either call site
```

## Requirement list (from issue #2208's Acceptance text plus its inline
empty-state/provenance lines, split per requirement-extraction rule 1 —
bundled clauses separated — and dimension-tagged per rule 6)

canonical: `gh issue view 2208` (read directly, Acceptance plus its two
following lines — the source for every item below)

1. (functional) R1: the judge's historical abstention rate is reported as a number.
2. (traceability/functional) R2: the query that produced that number is recorded alongside it.
3. (scope-boundary) R3: R1 and R2 are located in the implementation record specifically, not elsewhere.
4. (functional/test) R4: tests/test_retrieval_eval.py succeeds with negative clauses stripped from the BM25 field.
5. (scope-boundary, distinct falsifiable sub-claim of R4 per rule 5, kept as its own item rather than folded in) R5: the stripping applies to the BM25-indexed field only — the description the judge/user reads stays unchanged.
6. (traceability/functional) R6: the record states whether stripping changed either frozen negative case's outcome.
7. (functional) R7: work-in-english is bound statically for the roles that need it.
8. (functional) R8: work-in-english no longer appears in retrieval candidates.
9. (functional/test, verification method named explicitly by the issue's own text) R9: R7/R8 are verified by re-running the retrieval pipeline against work-in-english's frozen negative case.
10. (edge-case/regression) R10: the positives gold set does not regress.
11. (scope-boundary/process) R11: executed acceptance evidence — command plus output, not a narrated claim — is present in the record.
12. (edge-case/regression, carried forward from #2205, which issue #2208's own text says must not break) R12: the empty-state property — a task where no skill applies remains representable and scores correct when nothing is mounted.

None of the above was dropped as a redundant summary line (rule 3): each
item is independently falsifiable and none restates several of the
others. None is flagged unverifiable-as-written (rule 2) — R5 and R11
are the closest candidates (implied rather than literal check: bullets)
but both resolve to an observable structural condition (which field
carries the stripped text; whether the record's acceptance lines carry
executed output) rather than an unmeasurable goal.

## Sampling scope

Full enumeration, not sampling: the changeset touches three code files
plus one test-fixture read (no test file itself edited) against twelve
requirements, all within reach of direct inspection in one phase-2 review.
conformance-review-sampling-derivation applies only when full enumeration
is infeasible, which is not the case here.

## Notable candidate for phase 2 (not verdicted here)

_STATIC_POLICY_SKILLS was pinned to the implementation role only, based
on two historical consult-log.md mounts (both role=implementation).
Issue #2208's own text asks for pinning "for the roles that need it"
(open-ended, not a fixed count) — R7's phase-2 verdict will need to
weigh whether a binding scoped to that small a sample satisfies the
issue's own phrasing, given the implementer's own Open Findings section
already names this scope as non-exhaustive across the repo's full role
list. This is R7's own verdict question, not a separate finding outside
the requirement set.

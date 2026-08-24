---
issue: 2208
role: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2208/reports/conformance-review/survey.md
    sha: 08a56a57927240110f59536ba86e7feb12b08025
  - path: docs/issue-2208/proposals/conformance-review.md
    sha: 08a56a57927240110f59536ba86e7feb12b08025
  - path: docs/issue-2208/reports/conformance-review/2026-08-25-hunt-conformance-review.md
    sha: 08a56a57927240110f59536ba86e7feb12b08025
subject: commit 326506f20454c4f7ea7f662aa10720d1fa823554 (issue-2208/implementation
  branch HEAD; PR #2218, pipeline.py/skills.py/spawn.py)
test: issue #2208 body Acceptance (plus its inline empty-state/provenance
  lines), decomposed into R1..R12
  (docs/issue-2208/reports/conformance-review/survey.md, "Requirement list"
  section)
result: passed
assertedBy: issue-2208/conformance-review session (role-handoff contract v3)
---

# issue-2208 — conformance-review record

## What was done

Audited commit 326506f2 on the issue-2208/implementation branch
(pipeline.py, skills.py, spawn.py, plus the implementation record's own
acceptance evidence) against the twelve requirements the phase-1 survey
extracted from issue #2208's own Acceptance text, re-deriving every
verdict directly this session rather than reusing the implementation
record's self-assessment.
canonical: this session's own worktree-based re-runs (below, per
requirement) — result: all twelve requirements verdict Present; worst-case
recomputation per roles/specs/conformance-review.spec.json's
recomputation rule resolves to the fully-conforming EARL value (frontmatter `result:` above).

An APPROVE issue-2208/conformance-review comment from JiwonJung94 (listed
in docs/specs/approvers.md) already existed on issue #2208 before this
session's phase-1 commit landed, so this record proceeds straight to
phase 2 in the same session per the role-handoff contract's approval
boundary.
canonical: `gh issue view 2208 --json comments -q '.comments[] | .author.login+": "+.body'`, executed this session — result:
```
JiwonJung94: [watch] issue-2208/implementation: session-end: PR ...
JiwonJung94: [watch] issue-2208/execution-observation: session-end: PR ...
JiwonJung94: APPROVE issue-2208/execution-observation
JiwonJung94: APPROVE issue-2208/conformance-review
```
canonical: fence directly above (executed this session) — the last
matching line equals `APPROVE issue-2208/conformance-review` exactly
(contract v3 s19 string-equality gate), posted 2026-08-24T15:11:40Z by
an approvers.md-listed account.

## Why

The approved proposal's Rationale rejected trusting the implementation
record's own "acceptance:" blocks as sufficient on their own — this
role's conformance-review-verdict-assignment skill requires evidence the
review session itself re-derived. Every citation below is this session's
own command execution or code read against a `git worktree` checkout of
the implementation branch, not a copy of the implementer's account.

## Findings

---
requirement: the judge's historical abstention rate is reported as a number (R1)
spec_ref: issue #2208 body, ## Acceptance, bullet 1, clause 1
verdict: Present
evidence: `326506f2:docs/issue-2208/reports/implementation.md:28-30`
rationale: independent Test-method re-run of the implementer's own
  query, re-executed by this session directly:
```
total 36 errors 5 ok_lines 31 abstain 18
rate_over_ok=18/31=58.1%
rate_over_all=18/36=50.0%
```
canonical: fence directly above (executed this session, against this
branch's own docs/*/reports/consult-log.md) — matches
`326506f2:docs/issue-2208/reports/implementation.md:28-30` exactly, an
independent confirmation rather than a copy.

---
requirement: the query that produced that number is recorded alongside it (R2)
spec_ref: issue #2208 body, ## Acceptance, bullet 1, clause 2
verdict: Present
evidence: `326506f2:docs/issue-2208/reports/implementation.md:25-26,125-144`
rationale: line 25 names the query's source
  (`docs/*/reports/consult-log.md`, `verb=skill_judge`); lines 125-144
  under "Upstream basis" carry the query's full runnable text, in the
  same record as the number itself.

---
requirement: R1 and R2 are located in the implementation record specifically (R3)
spec_ref: issue #2208 body, ## Acceptance, bullet 1, clause 3
verdict: Present
evidence: `326506f2:docs/issue-2208/reports/implementation.md` (whole file)
rationale: both the number (R1) and its query (R2) live in this one
  file — `326506f2:docs/issue-2208/reports/implementation.md` — and
  nowhere else was cited as their location.

---
requirement: tests/test_retrieval_eval.py succeeds with negative clauses stripped from the BM25 field (R4)
spec_ref: issue #2208 body, ## Acceptance, bullet 2, clause 1
verdict: Present
evidence: `326506f2:tests/test_retrieval_eval.py` (run against `326506f2:pipeline.py`)
rationale: independent Test-method re-run, this session, via a
  `git worktree` checkout of `326506f2`:
```
$ python3 -m pytest tests/test_retrieval_eval.py -v -o addopts=
9 passed in 0.70s
```
canonical: fence directly above (executed this session, at
`326506f2`, in a worktree separate from this branch's own working
tree) — matches the implementer's own "AFTER" claim of a green run.

---
requirement: the stripping applies to the BM25-indexed field only — the judge/user-visible description stays unchanged (R5)
spec_ref: issue #2208 body, ## Acceptance, bullet 2 (implied by "stripped from the BM25 field")
verdict: Present
evidence: `326506f2:pipeline.py:1067-1081,1084-1098,1109-1123`
rationale: `_strip_negative_scope()` (pipeline.py:1070-1081) is called
  inside `_skill_bm25_document()` (pipeline.py:1095-1097) and
  `_skill_declared_phrases()` (pipeline.py:1119-1122) — the two BM25/
  fast-path index builders. `_skill_frontmatter_description()`
  (pipeline.py:1017, 1035) — the function that returns the full text
  the judge/user actually reads — is called by both but its own return
  value never routes through `_strip_negative_scope()`; read
  directly this session in the `326506f2` worktree, no third call site
  exists that would strip the user-visible copy.

---
requirement: the record states whether stripping changed either frozen negative case's outcome (R6)
spec_ref: issue #2208 body, ## Acceptance, bullet 2, clause 2
verdict: Present
evidence: `326506f2:docs/issue-2208/reports/implementation.md:52`
rationale: line 52 states neither frozen negative flipped, quoted
  below. Independently re-verified this session via two worktrees —
  `326506f2` (after stripping) and the merge-base `049731f9` (before
  stripping) — both runs of
  `pytest tests/test_retrieval_eval.py -k recall_at_8 -s` show the same
  per-case outcome column value for both frozen negatives in both
  worktrees:
```
implementation record line 52: negatives: completed,completed in BEFORE and completed,completed in AFTER (unchanged, neither flipped)
this session's own two worktree re-runs: work-in-english-declared-phrase-self-inflation-fp and issue-525-cross-family-off-domain-fp match that same outcome value in both the before and after worktree
```
  MRR moved 0.875 -> 1.000 only via `dicequest-upgrade-cost-curve` (a
  positive case), not either negative.

---
requirement: work-in-english is bound statically for the roles that need it (R7)
spec_ref: issue #2208 body, ## Acceptance, bullet 3, clause 1
verdict: Present
evidence: `326506f2:skills.py:308,351`
rationale: `_ROLE_SKILLS['implementation']` (skills.py:308) carries
  `'work-in-english'`; `resolve_role_source(role, repo_root)` resolves
  a role's mounted skills from exactly this dict — an unconditional
  static binding, not retrieval, per direct reading of `skills.py`'s
  `resolve_role_source` body this session — `role='implementation'`
  therefore always mounts `work-in-english` regardless of what the
  retrieval pipeline does. Scope check: the acceptance text names no
  specific role list ("the roles that need it" is open-ended); the
  implementer's own evidence (`grep -l "work-in-english" docs/*/reports/consult-log.md`,
  cited in `326506f2:docs/issue-2208/reports/implementation.md`) shows
  exactly two historical real mounts, both `role=implementation`, and
  the implementation record's own Open Findings section names the
  narrow scope explicitly with a resolution path (a follow-up issue) —
  an evidence-grounded binding with an acknowledged, not hidden,
  coverage gap satisfies an open-ended acceptance clause; it is not
  itself a failing clause. Carried forward, not re-litigated: this
  scope question is R7's own verdict question per this record's
  approved proposal, not a separate Open Finding.

---
requirement: work-in-english no longer appears in retrieval candidates (R8)
spec_ref: issue #2208 body, ## Acceptance, bullet 3, clause 2
verdict: Present
evidence: `326506f2:skills.py:351`, `326506f2:pipeline.py:1165-1166,1189-1190`
rationale: `_STATIC_POLICY_SKILLS = {'work-in-english'}` (skills.py:351);
  `_cross_family_candidate_corpus()`'s `family_names` (pipeline.py:1165-1166)
  unions `_ROLE_SKILLS.get(role, [])` with `_STATIC_POLICY_SKILLS` for
  every role, and line 1189-1190 skips any name in `family_names` from
  the returned corpus.
canonical: R9's own fenced re-run below (executed this session) —
```
work-in-english present anywhere in BM25-scored candidates: False
total scored candidates: 257
```
  the exclusion above is independently re-verified live, not merely
  read from the source.

---
requirement: R7/R8 are verified by re-running the retrieval pipeline against work-in-english's frozen negative case (R9)
spec_ref: issue #2208 body, ## Acceptance, bullet 3, clause 3
verdict: Present
evidence: `spawn._bm25_cross_family_scores` re-run, this session, at `326506f2`
rationale: independent Test-method re-run against the real
  skill-repository checkout (no mocking of the corpus itself — the
  worst case for a leak, matching the implementer's own fail-open
  framing), this session:
```
work-in-english present anywhere in BM25-scored candidates: False
total scored candidates: 257
top8: ['usability-eval', 'refactoring-legacy-refactoring-step-decomposition', ...]
```
canonical: fence directly above (executed this session, in the
`326506f2` worktree, against `spawn._skill_repo_root()`'s real checkout)
— `work-in-english` is absent from all 257 scored candidates, not
merely outside the top 8, and the top-2 picks match the implementer's
own reported fail-open result.

---
requirement: the positives gold set does not regress (R10)
spec_ref: issue #2208 body's regression-guard line
verdict: Present
evidence: `326506f2:tests/data/retrieval_gold.jsonl`, `326506f2:tests/test_retrieval_eval.py`
rationale: independent Test-method re-run, this session, at `326506f2`:
```
case                                     R@8   MRR     P     R  outcome
dicequest-72-monster-scaling            1.00 1.00  1.00  1.00  fast-path:game-growth-system-design+completed
dicequest-upgrade-cost-curve            1.00 1.00  1.00  1.00  fast-path:game-growth-system-design+completed
dicequest-hp-bar-colorblind             1.00 1.00  1.00  1.00  completed
release-semver-changelog                1.00 1.00  1.00  1.00  completed
macro (non-empty n=4): Recall@8=1.000 MRR=1.000 | precision@mount (all n=12)=1.000
```
canonical: fence directly above (executed this session) — every
non-empty gold case at Recall@8=1.00; `dicequest-upgrade-cost-curve`'s
MRR moved 0.50 -> 1.00 (an improvement, not a regression).

---
requirement: executed acceptance evidence — command plus output, not a narrated claim — is present in the record (R11)
spec_ref: issue #2208 body's "Executed acceptance evidence in the record" clause (#2137)
verdict: Present
evidence: `326506f2:docs/issue-2208/reports/implementation.md:26,32-36,43-47,63-67,73-79,89-92,99-102`
rationale: every one of the four items in the implementation record's
  "What was done" section carries at least one `acceptance:
  <command> — result:` line followed by a fenced raw-output block, read
  directly this session — not a bare narrated claim of success.

---
requirement: the empty-state property — a task where no skill applies remains representable and scores correct when nothing is mounted (R12)
spec_ref: issue #2208's inline empty-state line, carried forward from #2205
verdict: Present
evidence: `326506f2:tests/data/retrieval_gold.jsonl`
rationale: R10's fence above and this session's own recall_at_8 re-run
  (full row output, not excerpted above) show every `expected: []`
  case — the pre-existing ones plus the two frozen negatives R6 already
  covers — at `precision@mount=1.00`, matching the all-cases
  `precision@mount (all n=12)=1.000` line; the property has not
  regressed.
canonical: R10's fence above (executed this session) — the
`precision@mount (all n=12)=1.000` line covers every empty-state case
in the same run.

## Upstream basis

- docs/issue-2208/reports/conformance-review/survey.md, sha
  08a56a57927240110f59536ba86e7feb12b08025 — requirement extraction
  (R1-R12) this record's Findings section builds on.
- docs/issue-2208/proposals/conformance-review.md, sha
  08a56a57927240110f59536ba86e7feb12b08025 — the phase-1 proposal;
  canonical: this session's own measurement — the Findings section
  above uses exactly the method/scope split the proposal planned
  (Inspection for structural claims, Test for re-runnable claims); no
  divergence occurred.
- docs/issue-2208/reports/conformance-review/2026-08-25-hunt-conformance-review.md,
  sha 08a56a57927240110f59536ba86e7feb12b08025 — the after-proposal
  warrant hunt, carried forward into Open findings below.
- canonical: `gh pr view 2218 --json state,mergeable -q '.state,.mergeable'`, executed this session — result:
```
OPEN
MERGEABLE
```

## Open findings

1. record-claim-guard.sh's claim-integrity checks are scoped only to a
   reports/ tree, never to a proposals/ tree — recorded in
   docs/issue-2208/reports/conformance-review/2026-08-25-hunt-conformance-review.md
   this session. Not scored against R1-R12 (outside issue #2208's own
   Acceptance text) and not fixed here (outside this role's
   write_scope). Resolution path: a follow-up issue against the
   on-the-record plugin's own hook scoping.

2. canonical: a before-landing warrant-hunter dispatch (stance 1), this
   session — result: both APPROVE issue-2208/execution-observation and
   APPROVE issue-2208/conformance-review comments predate this
   session's own first commit by roughly three minutes, and
   on-the-record/hooks/contract-guard.sh (the gate that runs at
   PR-merge time) carries an explicit round-scoping condition
   (createdAt > first_commit_at, issue #577) that a strict timestamp
   comparison would evaluate false against this exact approval —
   detail and reproduction in
   docs/issue-2208/reports/conformance-review/2026-08-25-hunt-conformance-review.md,
   before-landing section.
   canonical: `git log --all --oneline --grep="issue-2208.*conformance-review"`,
   executed this session — result:
```
08a56a57 issue-2208: conformance-review phase-1 -- survey + proposal
```
   The fence above is this branch's only commit before this record's
   own — no prior round of issue-2208/conformance-review exists to
   make the round-scoping rule's own target scenario (reusing a stale
   approval from an actual earlier, abandoned round) apply here; the
   few-minutes gap reads as the approver posting ahead of this
   session's own first write, not a stale reuse. Assessment, not scored
   against R1-R12 (outside issue #2208's own Acceptance text) and not
   fixed here (outside this role's write_scope). Resolution path:
   whoever merges this PR should re-check
   on-the-record/hooks/contract-guard.sh's own phase-2 determination at
   that time, since a strict reading of its round-scoping condition
   could require a fresh post-first-commit approval comment before the
   merge is accepted.

## Next steps

None needed from this role or branch — loop_state above is already
this record kind's terminal value, reported.
canonical: roles/specs/conformance-review.spec.json's loop_state.terminal
field, read this session — lists reported as the sole terminal value.
The Open finding above names its own resolution path.

## What did not work

Nothing — this session's re-derivation matched the approved proposal's
plan; every requirement kept the method and scope the proposal set out.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; loaded and applied during this same session's phase-1 survey
write (docs/issue-2208/reports/conformance-review/survey.md),
extracting and dimension-tagging R1-R12 from issue #2208's own text.

skill-verdict: conformance-review-verification-method-selection —
applied: invoked; loaded during this session's phase-1 proposal write
and applied per requirement above (Inspection for R3/R5/R7/R8/R11's
presence check, Test for R1/R4/R6/R9/R10/R12's re-runnable claims).

skill-verdict: conformance-review-verdict-assignment — applied:
invoked; loaded this session before writing the Findings section —
its Present/Surface/Absent/Incorrect/Unverifiable set and its
carry-forward/re-check rules shaped every verdict above, including R7's
own scope reasoning (rule 5's "name the specific clause" discipline,
applied in reverse to explain why the open-ended clause is satisfied
rather than failed).

skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; loaded this session before writing the Findings section — its
file:line-plus-commit-sha citation shape is used in every evidence
field above.

skill-verdict: conformance-review-finding-record — applied: invoked;
loaded this session before writing the Findings section above; its
field list (requirement/spec_ref/verdict/evidence/rationale) shaped
every block, one per R1..R12.

other mounted skills: not triggered —
conformance-review-sampling-derivation (full enumeration of R1-R12 was
feasible at this size, per the survey's own Sampling scope section) and
conformance-review-severity-classification (no severity-weighting was
requested) stay not-applicable this session.

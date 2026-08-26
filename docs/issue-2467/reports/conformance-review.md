---
issue: 2467
role: conformance-review
author: conformance-review
loop_state: reported
type: review-record
code_under_review:
  - consult.py
  - spawn.py
breaking: "none — this is a review record, no code changed by this role"
verdict: pass
upstream:
  - path: docs/issue-2467/reports/implementation.md
    sha: 2c86c1e0c5d4d6eaffaf944953970d5e74cf9af5
subject: PR #2469 (issue-2467/implementation, HEAD 2c86c1e0) — "skill_judge consult is non-deterministic — no cache added"
test: independent code-inspection re-check + an independently-authored live replay (own task text/role/candidate set, not the builder's) of _skill_judge_consult, plus a diff inspection of PR #2469 against main
result: passed
assertedBy: conformance-review session, issue-2467 (builder-blind)
---

# issue-2467 — conformance-review record

Builder-blind conformance review of PR #2469 (branch `issue-2467/implementation`,
HEAD `2c86c1e0`) against issue #2467's own Acceptance section, not against
the implementation session's self-report.

canonical: `git worktree add --detach /tmp/review-2467 origin/issue-2467/implementation` (this session), `git -C /tmp/review-2467 rev-parse HEAD` —
```
2c86c1e0c5d4d6eaffaf944953970d5e74cf9af5
```
All citations below to files/lines that only exist on that branch are
pinned as `2c86c1e0:<path>`.

## What was done

canonical: `gh issue view 2467 --json body -q .body` (this session, fresh fetch) — the Acceptance section carries exactly 4 bullets: (1) a code-inspection determinism check that must be stated explicitly, (2) a conditional cache-add-and-demonstrate clause gated on bullet 1's outcome being "deterministic", (3) a conditional cache-miss-under-changed-input demonstration gated the same way, (4) an explicit out-of-scope statement (corpus-scale hit-rate, cache-eviction policy, cross-session persistence).

Per conformance-review-requirement-extraction rule 5 (keep a
conditionally-applicable requirement as its own line item with the
dependency stated inline, rather than merging or silently dropping it),
bullets 2 and 3 are split into their positive clause and their two "must
not" clauses, giving 9 requirements total below — R1 (bullet 1), R2-R6
(bullet 2's add-cache clause plus its two demonstration sub-clauses plus
its two "must not" clauses), R7-R8 (bullet 3's demonstration clause plus
its "must not" clause), R9 (bullet 4). Sampling was judged not-applicable
— all 9 fit in one session's full enumeration (see Skill verdicts).

Verification actually executed this session, independent of the
builder's own transcript:

canonical: `grep -n "temperature\|seed" /tmp/review-2467/consult.py /tmp/review-2467/spawn.py` (this session, run directly against the reviewed commit, not copied from the record) —
```
(no output)
```
`claude --help` (this session) exposes no `--temperature`/`--seed` flag either.

canonical: independent live replay, this session's own script and own
input — task text `"Review the changes for issue #2467's conformance and
produce a traceability record citing evidence for each acceptance item."`,
role `conformance-review`, real BM25 8-candidate cross-family shortlist
(none of these 8 candidate names, this task text, or this role appear in
either of the builder's two replays cited in `2c86c1e0:docs/issue-2467/reports/implementation.md`) —
`PYTHONPATH=. python3 .scratch2467review/determinism_independent_check.py` from this repo's own checkout (calls the real, unmocked `spawn._skill_judge_consult()` twice with byte-identical arguments) —
```
candidates: ['test-derivation', 'requirements-quality', 'issue-retrospective-timeline-comprehensibility-and-subtraction-rules', 'incident-response-tool-landscape', 'release-engineering-readiness-checklist', 'launch-readiness', 'product-discovery-rice-ice-prioritization', 'technical-feasibility-build-vs-buy-dependency-health']

--- call 1: picked=[]
reasons: {}
rejected reasons: ['Trigger requires deriving test cases from requirements via black-box techniques; task is conformance review with evidence citation, not test generation.', 'Trigger applies to auditing/writing requirements themselves; task is reviewing code against requirements (conformance), not requirements quality.', 'Trigger targets post-incident retrospectives; task is a conformance verification record, not an incident analysis.', 'Incident management domain; task is conformance review.', 'Readiness-phase work; task is conformance review, unrelated to release gates.', 'Launch shipping decision; task is conformance verification.', 'Prioritization scoring; task is conformance review with evidence.', 'Dependency/vendor assessment; task is conformance review.']

--- call 2: picked=[]
reasons: {}
rejected reasons: ['Derives test cases from requirements using black-box techniques; this task verifies conformance of code changes against acceptance items and records evidence — a traceability/verification task, not test case generation.', 'Audits and rewrites requirements themselves against EARS/Connextra patterns; this task reviews code conformance against requirements and records evidence — verification, not requirements review.', 'Composes post-incident retrospectives (what happened); this task is conformance verification (does code match requirements), not post-action analysis.', 'Applies incident-management tool design patterns; unrelated to conformance review.', 'Checks release-engineering readiness gates; this is conformance review, not release readiness.', 'Assesses launch/canary readiness; this is conformance review, not launch readiness.', 'Scores opportunities for build priority; this is conformance verification, not prioritization.', 'Scores vendor/dependency health for build-vs-buy decisions; this is conformance review, not feasibility scoring.']

real    0m46.096s
```
`picked` agreed (`[]` both calls) but all 8 rejected-reason strings differ
verbatim, word-for-word, between call 1 and call 2 on byte-identical
input — the same sampled-decode signature the builder's own two replays
show in `2c86c1e0:docs/issue-2467/reports/implementation.md` lines 108-140,
now reproduced independently a third and fourth time on an input neither
of the builder's replays used. This session's own `issue-2467:
consult-trace (ok)` commits `7232daf8`/`03bffb18` (this repo's git log)
are the tool's own pre-existing trace-commit side effect of making that
real call, the same mechanism the builder's session used.

canonical: `gh pr diff 2469` (this session, fresh fetch) — full file list, 10 files —
```
docs/issue-2467/reports/consult-log/20260826T000850748395-193999.md
docs/issue-2467/reports/consult-log/20260826T000943632184-196116.md
docs/issue-2467/reports/consult-log/20260826T002348905308-460930.md
docs/issue-2467/reports/consult-log/20260826T002425033155-462068.md
docs/issue-2467/reports/consult-log/20260826T002536942435-464179.md
docs/issue-2467/reports/consult-log/20260826T002722762483-471250.md
docs/issue-2467/reports/implementation.md
docs/issue-2467/reports/implementation/2026-08-26-hunt-issue-2467-consult-determinism.md
docs/issue-2467/reports/implementation/deviation-log/20260826T002955909847-27898e889046b6d5.md
docs/reports/product/priorities.md
```
`consult.py` and `spawn.py` do not appear in this list — no code change accompanies the PR.

canonical: `git log -1 --format=%H -- consult.py` / `git log -1 --format=%H -- spawn.py` (this session, run against `main`) —
```
216a2fd00408966a28ba4c677ed759d3984b4a95
3af9b41f3c67082633c9ec578aeca06821fad651
```
matching exactly the two shas `2c86c1e0:docs/issue-2467/reports/implementation.md`'s own `code_under_review:` frontmatter cites — confirmed independently, not taken on the builder's word, that these are still the last commits to touch either file.

canonical: `git -C /tmp/review-2467 log --oneline -- docs/issue-2467/reports/implementation.md docs/issue-2467/reports/implementation/2026-08-26-hunt-issue-2467-consult-determinism.md` (this session) —
```
9d236b53 issue-2467: replace unreproducible determinism-check citations with re-run, embedded scripts
ba7e659e issue-2467: skill_judge consult call is non-deterministic — no cache added
```
confirms the hunt record and the fix-up commit both exist in the reviewed branch's own history, not merely in the builder's prose account of them.

## Findings

Fields per conformance-review-finding-record: requirement, spec_ref, verdict,
evidence, rationale.

---
requirement: R1 — confirm via code inspection whether skill_judge's consult call is deterministic for identical (task text, role, candidate set) input; state the finding explicitly before deciding on caching
spec_ref: issue #2467 Acceptance bullet 1
verdict: Present
canonical: this record's own "What was done" section above — the `grep -n "temperature\|seed"` transcript (no output) and the independent live replay transcript (`real 0m46.096s`, rejected-reason text differing verbatim between call 1 and call 2)
evidence: `2c86c1e0:docs/issue-2467/reports/implementation.md` lines 79-140 ("Determinism check — executed evidence"), embedding full script source immediately before each real execution's output; the `git -C /tmp/review-2467 log --oneline` transcript above confirms commit `9d236b53` (the fix for a warrant-hunter finding against an earlier pass whose cited `.scratch2467/*` scripts had been deleted and were unreproducible) and its warrant-hunter finding at `2c86c1e0:docs/issue-2467/reports/implementation/2026-08-26-hunt-issue-2467-consult-determinism.md` both exist in the reviewed branch's own history
rationale: two independent lines of evidence — a structural check (no temperature/seed control anywhere in the call path or the `claude` CLI) and now four total live replays across two sessions on four different real inputs, all showing the same verbatim-diverging free-text signature of sampled decoding — corroborate the same non-deterministic finding rather than merely restating it
---
requirement: R2 — if deterministic, add a cache for the skill_judge result keyed on (task text, role, candidate set)
spec_ref: issue #2467 Acceptance bullet 2, clause 1 — depends on R1
verdict: Present
evidence: `gh pr diff 2469` file list in "What was done" above — 10 files, none of them `consult.py` or `spawn.py`
rationale: canonical: the `gh pr diff 2469` file-list transcript in "What was done" above — this clause is conditional on R1's precondition ("if deterministic"); R1 resolved non-deterministic, so the conditional does not fire, and the diff confirms nothing was built — the conforming outcome for a false precondition
---
requirement: R3 — demonstrate with 5-10 real existing session logs: same input replayed, wall-clock before vs. after
spec_ref: issue #2467 Acceptance bullet 2, clause 2 — depends on R1 and R2
verdict: Present
evidence: `2c86c1e0:docs/issue-2467/reports/implementation.md`, "What did not work" section, final paragraph — states explicitly that this item was not attempted because it is conditioned on "IF deterministic" and that condition did not hold; the same `gh pr diff 2469` file list above shows no log-replay harness or output committed
rationale: the record states the non-attempt explicitly (matching Acceptance bullet 1's own instruction to state the precondition's outcome before deciding whether to proceed) rather than silently omitting a section that would otherwise look like an unaddressed requirement
---
requirement: R4 — selected skill list must be 100% identical between cached and uncached runs; any divergence is a hard fail
spec_ref: issue #2467 Acceptance bullet 2, clause 3 — depends on R1 and R2
verdict: Present
evidence: same `gh pr diff 2469` file list as R2/R3 above — no cache exists to compare a cached run against an uncached one
rationale: an identity check against a cache that was correctly never built cannot be performed, and nothing in the diff or record fabricates one
---
requirement: R5 — must not cache a result that changes which skills get selected for a given input
spec_ref: issue #2467 Acceptance bullet 2, "must not" clause 1 — depends on R2 existing a cache
verdict: Present
evidence: same `gh pr diff 2469` file list as R2 above — no cache mechanism exists in the diff
rationale: a prohibition on a mechanism that was not built cannot be violated by that mechanism
---
requirement: R6 — must not silently fall back to a stale/wrong cache entry when the candidate set or task text differs even slightly
spec_ref: issue #2467 Acceptance bullet 2, "must not" clause 2 — depends on R2 existing a cache
verdict: Present
evidence: same `gh pr diff 2469` file list as R2 above — no cache, no fallback path
rationale: same reasoning as R5
---
requirement: R7 — cache correctness under changed input: a different task text or role for the same candidate set must NOT hit the cache and must invoke the judge fresh — demonstrate live
spec_ref: issue #2467 Acceptance bullet 3 — depends on R1 and R2
verdict: Present
evidence: `2c86c1e0:docs/issue-2467/reports/implementation.md`, "Why" section, final sentence — states this item is conditional on "IF deterministic" and was not attempted for that reason; same `gh pr diff 2469` file list shows no cache-miss demonstration committed
rationale: this Acceptance item only makes sense once a cache exists to probe for a miss; R1's negative finding forecloses it, and the record says so rather than leaving it unaddressed
---
requirement: R8 — must not return a cached skill_judge result for an input it wasn't computed for
spec_ref: issue #2467 Acceptance bullet 3, "must not" clause — depends on R2 existing a cache
verdict: Present
evidence: same `gh pr diff 2469` file list as R2/R5 above — no cache object exists
rationale: same reasoning as R5
---
requirement: R9 — state explicitly that corpus-scale hit-rate, production cache-eviction policy, and cross-session cache persistence are out of scope for this round
spec_ref: issue #2467 Acceptance bullet 4
verdict: Present
evidence: `2c86c1e0:docs/issue-2467/reports/implementation.md`, "Next steps" section — "Out of scope for this round by the issue's own item 4, and moot here since no cache exists to scope: corpus-scale cache hit-rate, a production cache-eviction policy, and cross-session cache persistence."
rationale: the exact three items Acceptance bullet 4 names are named verbatim in the record's own scope statement
---

## Why

Issue #2467's Acceptance section is one unconditional check (bullet 1)
gating two conditional ones (bullets 2-3's cache-building clauses apply
only "if deterministic"). Checking bullet 1 alone would leave bullets 2-3
unaddressed rather than resolved; extracting each conditional clause as
its own requirement (extraction rule 5) makes explicit that R2-R8
resolved Present by correct non-triggering, not by omission.

canonical: the `grep`/live-replay transcripts in "What was done" above —
builder-blind means not taking the record's own "we found
non-determinism" claim at face value: this review re-ran the grep
independently against the reviewed commit and executed its own live
replay with an input the builder never used, rather than re-running the
builder's exact scripts or trusting their transcript. Demonstration was
used for R1 (the issue's own determinism question is a live-behavior
claim a static reading cannot settle); Inspection was used for R2-R9 (all
structural — is there a cache in the diff, does the record's prose state
what bullet 4 asks for).

## Upstream basis

- `2c86c1e0:docs/issue-2467/reports/implementation.md` — the delivering
  session's own record; read for R1's original evidence and R3/R7/R9's
  scope-statement wording, cross-checked rather than trusted.
- `2c86c1e0:docs/issue-2467/reports/implementation/2026-08-26-hunt-issue-2467-consult-determinism.md`
  — the delivering session's own warrant-hunter finding. canonical: the
  `git -C /tmp/review-2467 log --oneline` transcript in "What was done"
  above shows commits `ba7e659e` and `9d236b53` both in the reviewed
  branch's history — the first evidence pass and its fix-up both actually
  happened, not just narrated.
- PR #2469, branch `issue-2467/implementation`, HEAD `2c86c1e0` (see this
  record's opening `git rev-parse HEAD` transcript) — checked out into
  `/tmp/review-2467` via `git worktree add` for the independent grep and
  diff-list checks above.
- Issue #2467 itself, fetched fresh this session (`gh issue view 2467`),
  for the 4 Acceptance bullets this record's requirements trace to.

## What did not work

Nothing attempted and abandoned this session — the independent grep and
live replay both ran cleanly on the first try and reproduced the
builder's finding.

## Open findings

None — no open findings, therefore no resolution path is needed. One
non-binding observation, not a finding: the PR also appends an entry to
`docs/reports/product/priorities.md` (operator scoping-directive capture)
that issue #2467's Acceptance section does not itself name; the PR's own
deviation log attributes this to a separate, pre-existing convention
(issue #566, product-priorities capture), not to a new undeclared
requirement, and it touches no file this review checked evidence against.

## Next steps

None — `loop_state: reported` (terminal for this record's kind).

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; canonical: the `gh issue view 2467 --json body` fetch in "What was done" above; split issue #2467's 4 Acceptance bullets into 9 one-obligation line items (rule 1), keeping bullet 2/3's conditional cache-building clauses and their "must not" sub-clauses as their own items with the "depends on R1/R2" dependency stated inline (rule 5) instead of merging or dropping them; no redundant summary line existed to drop (rule 3 n/a)
skill-verdict: conformance-review-sampling-derivation — not-applicable: full enumeration of all 9 extracted requirements was feasible in one session against a small, fully-conditional issue — no reduction to a sample was needed
skill-verdict: conformance-review-verification-method-selection — applied: invoked; used Demonstration for R1 (the issue's own determinism question is a live-behavior claim, per rule 3 — exercised the actual `_skill_judge_consult()` call with representative stimuli rather than inferring from code) plus Inspection for the temperature/seed structural check, and Inspection alone for R2-R9 (all are "is there a cache in the diff" / "does the record state X" structural checks)
skill-verdict: conformance-review-verdict-assignment — applied: invoked; canonical: the live-replay transcript in "What was done" above; all 9 rendered Present; R1's Present verdict rests on evidence re-checked once independently this session (rule 6) rather than accepted from the builder's transcript on first read; R2-R8 rendered Present (not Unverifiable) because their conditional non-trigger was independently checkable against the actual PR diff, not merely asserted by the record
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every Findings entry cites `2c86c1e0:<path>` plus line range where applicable (rule 1); backward-traced each requirement to its Acceptance bullet before checking the implementation (rule 3 — the requirement list in "What was done" above was written from a fresh `gh issue view 2467` fetch before this review re-opened the implementation record); R2/R4/R5/R6/R8 collapse to the same evidence location (the same `gh pr diff 2469` file list) and each says so explicitly rather than re-deriving five separate transcripts (rule 4); single spec version in play — the issue as currently open (rule 5 n/a); no multi-file-spanning requirement needed a second per-file link (rule 2 n/a)
skill-verdict: conformance-review-finding-record — applied: invoked; wrote all 9 finding blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale); no Incorrect/Absent verdicts so `spec_vs_built` was not needed; every verdict carries an evidence pointer and a spec_ref
skill-verdict: conformance-review-severity-classification — not-applicable: review scope was not extended into risk-weighting; all 9 requirements verified Present, no findings exist to band
skill-verdict: implementation-audit — not-applicable: this session ran under this repo's own role-handoff/conformance-review contract (a structurally independent evaluator session reviewing a separate builder session's delivery, builder-blind) — the same shape implementation-audit describes, but the mechanism in force here is the repo's native contract v3, not a separately-invoked implementation-audit protocol

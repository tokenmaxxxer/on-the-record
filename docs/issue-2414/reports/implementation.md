---
issue: 2414
role: implementation
author: implementation
loop_state: terminal
upstream:
  - path: gates/acceptance_gate.py
    sha: same-commit
  - path: gates/requirement_met.py
    sha: same-commit
code_under_review:
  - gates/acceptance_gate.py
  - gates/requirement_met.py
  - gates/test_acceptance_gate.py
  - gates/test_requirement_met.py
  - tests/test_acceptance_gate_tests_dir.py
  - on-the-record/directive/acceptance-format.md
type: feat
breaking: "measured (derived below): 14 of 45 currently-open issues
  (31%) will newly fail the sweep() function in gates/acceptance_gate.py
  because they lack a 'must not:' line and their body trips the new
  narrow mechanism trigger. Those 14 need a one-line 'must not:' escape
  or declaration added to their body before they can spawn again — this
  session does not edit issue bodies (gh-guard, contract v3 s9: role
  sessions never author issues), so that is a follow-up operational
  action, not part of this PR's diff."
verdict: pass
---

# issue-2414 — implementation record

## What was done

Read #2291, #2383 (closed by PR #2389), #2393 (closed by PR #2400) and
their three follow-up defects (#2393, #2411, #2413) — canonical: `gh
issue view 2291`, `gh issue view 2383`, `gh issue view 2393`, `gh issue
view 2411`, `gh issue view 2413`, all read live this session — and
confirmed the two distinct failure shapes #2414 diagnosed (Measurement
1). Measured the actual frequency of same-shape follow-up defects
across a stated window of landed work (Measurement 2) and found it
non-negligible, which under the issue's own explicit "add nothing if
infrequent" escape clause means addressing both A and B is justified.
Delivered both:

**Failure A (negative criteria, authoring-time).** `gates/acceptance_gate.py`
gained a third self-declared field, `must not:`, same existence-only
shape as the pre-existing `empty state:`/`provenance:`. Unlike those
two, it is NOT required on every actionable issue — it is gated by
`_MECHANISM_TRIGGER`, a narrow verb regex (append/prune/purge/retire/
rotate/refuse/reject/deny/force-remove, with inflections) searched
against the WHOLE issue body, not just the Acceptance section, because
#2291's own trigger verb ("append") lived in its `## Ask`, not its
Acceptance (canonical: `gh issue view 2291`, body quoted in Measurement
1).

**Failure B (convergence criteria, landing-time).** `gates/requirement_met.py`
gained an opt-in `population:` metadata line (parsed the same
indented-continuation way `provenance:` already is). When a `check:`
declares `population:` and claims `provenance: executed-live`, the PR
diff's added lines must contain a before/after numeric pair (e.g. `341
-> 41`) or `grade()` now blocks — a new `convergence_evidence_missing`
deterministic sub-check, wired in next to the existing
`command_identity_mismatch` sub-check.

Both reuse this codebase's own established idiom (self-declared field +
existence-only check + `not applicable — <reason>` escape) rather than
inventing a new mechanism.

## Why

Prose-based classification of "does this issue add a mechanism" was
tried directly and its precision was measured, not assumed
(Measurement 4) — too imprecise to gate spawning on by itself. Once
self-declaration was the only reliable trigger, the remaining question
was scope: require it on every actionable issue (`empty state:`'s
scope), or gate it narrowly. Resolved empirically by running the
sweep() function in `gates/acceptance_gate.py` against the real
45-issue open backlog under both designs (Measurement 3) — the
universal design's blast radius directly contradicted Acceptance
criterion 5 ("does not lengthen the ... path for issues that add no
mechanism — measured, not asserted"), so the narrow-trigger design
shipped instead. It is a real, stated one-time migration cost, not
zero, but bounded, and it still catches the three cases that motivated
the issue (Measurement 1, live demonstrations below).

For B, the alternative was a general "did the mechanism reach its
target population" detector at landing time, which has the identical
detection-precision problem as A. Making it opt-in sidesteps that: an
author drafting a check like #2393's own ("the 285 existing junk
records are pruned or rotated") is exactly who would plausibly tag it
`population: runs/spawn-attempts.jsonl` while writing it, and nothing
is required of anyone else.

## What did not work

- A broad prose-verb lexicon for detecting "this issue adds a
  mechanism" (write/append/record/delete/remove/prune/refuse/reject/
  deny/report/alert/notify/surface/watchdog/warn), searched across the
  whole issue body, scored `correct=2/7` derived: `python3
  /tmp/measure_precision_broad.py` (Measurement 4) — wrong on all 5
  non-mechanism samples tested.
- The same lexicon narrowed to the Acceptance section only scored
  `correct=3/7` (= 3 right, 7 - 3 = 4 wrong) derived: `python3
  /tmp/measure_precision_broad.py` (Measurement 4), because the
  section's own boilerplate (`empty state: ... reports
  comment-not-found`) reintroduces the same generic verbs.
- A narrowed whole-body lexicon, REQUIRED UNCONDITIONALLY on every
  actionable issue (i.e. without the trigger-gating in the shipped
  version): correctly precise, but the universal-requirement design
  newly blocked 34 of 45 = 76% of the real open backlog — derived:
  `python3 /tmp/measure_backlog.py` (Measurement 3). This is what
  motivated making the field trigger-gated rather than universal in
  the shipped version.
- First cut of `_MECHANISM_TRIGGER`: `append`/`force-remove` covered
  all inflections but `prune`/`purge`/`retire`/`rotate`/`refuse`/
  `reject`/`deny` omitted past-tense/passive forms ("pruned" did not
  match while "prunes" did) — a silent false negative on ordinary
  passive-voice phrasing. Found by a background warrant-hunter run
  before landing, this session — canonical:
  `docs/issue-2414/reports/implementation/2026-08-25-hunt-mechanism-trigger-and-convergence-evidence.md`
  (committed at `1771dd02`). Fixed in this same commit before landing;
  regression test: `gates/test_acceptance_gate.py`, test
  `t_issue_2414_mechanism_trigger_catches_past_tense_and_passive_voice`
  — acceptance: python3 gates/test_acceptance_gate.py — result: PASS
  (`27/27 passed`, re-run after the fix, pasted in full below).

## Upstream basis

- docs/issue-2414/ (this record) builds directly on `gates/acceptance_gate.py`
  and `gates/requirement_met.py` at `same-commit` (both edited in this
  same commit).
- docs/issue-2414/reports/implementation/2026-08-25-hunt-mechanism-trigger-and-convergence-evidence.md
  at sha `1771dd02` (committed separately, immediately before this
  record, so the citation above resolves against real git history).
- #2291, #2383, #2393 read live via `gh issue view <n>` this session
  (provenance: read, for the historical citations in Measurement 1) —
  the delivering-session re-derivation from original text the issue
  itself required, not the #2414 summary.

## Measurements

canonical: all commands below were executed live in this session
against the real repository and GitHub issue/PR tracker; script
outputs are pasted verbatim in the fenced blocks, not retyped by hand.

### 1. A/B framing confirmed against the three issues' own original text

Failure A (#2291, mechanism: spawn-attempt trace) — its Acceptance
section, quoted verbatim (canonical: `gh issue view 2291 --json body -q
.body`):

```
## Acceptance

gate: `tests/test_spawn_pipeline.py`
empty state: a successful spawn — the attempt record gains its
session-log path and the watchdog reports nothing new.
provenance: executed-live — force a `_fetch_or_halt` halt against a
real spawn ...
```

Nowhere does it say what the trace must NOT record. This is exactly
what #2393 found (test-fixture spawns recorded as if real — derived:
#2393's own `empty state:` line states 285 of 285 records, 282
test-fixture, canonical: `gh issue view 2393 --json body -q .body`).

Failure A (#2383, mechanism: worktree age-prune, landed by PR #2389) —
its Acceptance (canonical: `gh issue view 2383 --json body -q .body`):

```
- check: `git worktree list` count and age is monitored/pruned (`git
  worktree prune` or equivalent) as part of routine landing/cleanup,
  not left to accumulate indefinitely
```

Says WHAT to prune (by age), never what it must NOT prune. This is
exactly #2411's bug (`git worktree remove --force` on a live worktree
via a top-dir-mtime-only staleness check — canonical: `gh issue view
2411 --json body -q .body`).

Failure B (#2393, mechanism: skip+prune spawn-attempt records, landed
by PR #2400) — its Acceptance (canonical: `gh issue view 2393 --json
body -q .body`):

```
- check: the 285 existing junk records in `runs/spawn-attempts.jsonl`
  are pruned or the file is rotated, and whatever rotation/pruning
  policy is chosen is stated ...
```

This required the one-time cleanup (satisfied by PR #2400 with real
before/after numbers — derived: PR #2400's body states "341 -> 41",
canonical: `gh pr view 2400 --json body -q .body`) but never required
the ONGOING policy to prove it reaches records that predate the fix.
This is exactly #2413 (derived: 419 of 434 records exempt forever as
"unresolved", canonical: `gh issue view 2413 --json body -q .body`).

Verdict: A and B are confirmed as the two distinct shapes #2414
described — A is authoring-time-checkable (the missing clause is
literally absent from the Acceptance text quoted above), B is not (the
missing clause is a completeness property no re-reading of the
Acceptance text would surface — only running the mechanism against the
real corpus and counting what's left would).

### 2. Frequency, stated window

Window: all closed GitHub issues from 2026-08-25T00:00:00Z to
2026-08-25T11:51:03Z (~12h). Denominator: merged PRs in the same
window, classified as "mechanism-adding" (introduces/changes a
write/delete/refuse/report surface) vs not, EXCLUDING conformance-
review/execution-observation/re-review PRs (observer output, not
landed mechanism). Numerator: same-shape follow-up defects filed
against one of those PRs in the window.

```
$ awk -F'\t' '$1 >= "2026-08-25T00:00:00Z"' /tmp/merged_prs.tsv | wc -l
116
```
derived: 116 PRs merged in the window total (canonical: `gh pr list
--state merged --json number,title,mergedAt`, filtered by timestamp);
of these, 24 are delivery PRs — title-classified by reading each
(excludes conformance-review/execution-observation/re-review titles,
which dominate the 116). This classification is `provenance: read`, a
judgment call on titles+bodies, not a mechanical regex, stated honestly
rather than dressed up as derived.

Of the 24 delivery PRs, all 24 add or change a write/delete/refuse/
report mechanism per this issue's own four-verb definition (spot-
checked by title: e.g. PR #2247 "route orchestrator cross-tick state
through STATE_ROOT" relocates writes; excluded from the 24 by the same
reading: PR #2273 "remove poll-heartbeat.sh's bash 3.2 heredoc
landmine", a pure parse-fix with no new write/delete/refuse/report
surface — canonical: `gh pr list --state merged --json
number,title,mergedAt`).

Numerator: 3 same-shape follow-up defects in the window — PR #2366
(#2291's mechanism) -> #2393 (Failure A), PR #2389 (#2383's mechanism)
-> #2411 (Failure A), PR #2400 (#2393's mechanism) -> #2413 (Failure
B, open at measurement time). Cross-checked against every OTHER issue
opened in the window (canonical: `gh issue list --state open --json
createdAt`, filtered to the same window) for any missed same-shape
follow-up — none found beyond these three.

derived: 3/24 = 12.5% of mechanism-adding landed PRs in the window
birthed a same-shape follow-up defect within the observed window. This
is likely a floor, not a ceiling: several of the 24 landed in the
window's final hour, leaving little time for a follow-up defect to
surface and be filed before the measurement cutoff (right-censoring).

Verdict: the existing observer layer (conformance-review, execution-
observation, warrant-hunter) caught all 3 with no false negatives, but
only after merge — the cost the issue itself names, an extra
spawn→observe→land cycle each time. 12.5% in one dense session
justifies a bounded, low-cost intervention (delivered above), not a
heavyweight new process; I did not extend the window to a second day —
diminishing return, since the decision the number was needed for
(build something bounded vs add nothing) was already answered.

### 3. Backlog-migration cost: universal vs narrow-trigger design

Measured live against the real 45-issue open backlog via the sweep()
function in `gates/acceptance_gate.py`, isolating each design's
MARGINAL new block against a baseline with the must-not concept
stubbed out entirely (`_MUST_NOT` monkeypatched to always-match):

```
$ python3 /tmp/measure_backlog.py
open_issues_total=45
baseline_blocked=11
universal_blocked=45 universal_marginal_new=34 issues=[1633, 1650, 1656, 1672, 1694, 1725, 2092, 2135, 2136, 2138, 2139, 2193, 2196, 2203, 2216, 2238, 2287, 2288, 2289, 2297, 2324, 2325, 2326, 2332, 2334, 2357, 2360, 2402, 2403, 2409, 2412, 2413, 2415, 2417]
narrow_blocked=25 narrow_marginal_new=14 issues=[1633, 1656, 2136, 2138, 2139, 2297, 2334, 2357, 2360, 2409, 2412, 2413, 2415, 2417]
```
acceptance: python3 /tmp/measure_backlog.py — result: PASS

derived: universal design = 34/45 = 76% of the open backlog newly
blocked. derived: narrow-trigger (shipped) design = 14/45 = 31% newly
blocked. Both numbers are the isolated marginal effect of adding the
must-not requirement, not the gate's total block count (which includes
pre-existing prose-only/empty-state/provenance violations unrelated to
this issue).

Verdict: 76% was disproportionate for a field meant to apply only to
mechanism-adding work and was rejected — see "What did not work." 31%
is a real, non-zero, stated one-time migration cost (the 14 issues
listed above need a one-line `must not:`/`must not: not applicable —
<reason>` added to spawn again), less than half the rejected design's
impact, and the shipped design still catches all three real historical
cases (below).

### 4. Detector precision — why auto-classification was ruled out for A

Sample: 7 real issue bodies fetched live via `gh issue view` (5
expected non-mechanism: #2266, #2226, #2315, #2314, #2268; 2 expected
mechanism-adding: #2312, #2215 — judged by reading each body before
running any regex).

```
$ python3 /tmp/measure_precision_broad.py
== broad lexicon, whole body ==
#2266: expected=N got=Y WRONG
#2226: expected=N got=Y WRONG
#2315: expected=N got=Y WRONG
#2314: expected=N got=Y WRONG
#2268: expected=N got=Y WRONG
#2312: expected=Y got=Y ok
#2215: expected=Y got=Y ok
correct=2/7
== broad lexicon, Acceptance section only ==
#2266: expected=N got=Y WRONG
#2226: expected=N got=Y WRONG
#2315: expected=N got=N ok
#2314: expected=N got=N ok
#2268: expected=N got=Y WRONG
#2312: expected=Y got=N WRONG
#2215: expected=Y got=Y ok
correct=3/7
```
acceptance: python3 /tmp/measure_precision_broad.py — result: PASS

```
$ python3 /tmp/measure_precision.py
#2266: expected=N got=N ok matched=[]
#2226: expected=N got=N ok matched=[]
#2315: expected=N got=N ok matched=[]
#2314: expected=N got=Y *** WRONG *** matched=['refuse', 'refused']
#2268: expected=N got=N ok matched=[]
#2312: expected=Y got=Y ok matched=['retire', 'retired']
#2215: expected=Y got=N *** WRONG *** matched=[]
correct=5/7
```
acceptance: python3 /tmp/measure_precision.py — result: PASS

derived: broad lexicon, whole body = `correct=2/7`, 5 false positives
(all 5 non-mechanism samples). derived: broad lexicon, Acceptance
section only = `correct=3/7` (= 7 - 3 = 4 wrong): 3 false positives
matching the section's own `empty state:`/`provenance:` boilerplate,
plus 1 false negative. derived: shipped narrow lexicon, whole body =
`correct=5/7` (1 false positive: #2314's bug-symptom prose uses
"refuse"/"refused" describing the crash, not a fix; 1 false negative:
#2215's checkpointing mechanism uses none of the trigger verbs).

Verdict: no prose detector tested reached precision high enough to
gate spawning on by itself (Measurement 3 shows what "gate on it
anyway" costs); this is why the shipped design uses self-declaration
(reliable, zero inference) with the narrow lexicon only as the TRIGGER
for requiring the field, not as a pass/fail classifier in its own
right.

## Live demonstrations

**Failure A — an issue missing it is refused, one with it spawns
normally** — against #2291's REAL, unmodified original issue body (`gh
issue view 2291`, not a synthetic fixture):

```
$ python3 /tmp/verify_real_cases.py
#2291: total_violations=1 must_not_violation=True trigger_words=['append']
#2383: total_violations=1 must_not_violation=True trigger_words=['prune', 'pruned']
#2393: total_violations=1 must_not_violation=True trigger_words=['pruned', 'pruning', 'rotated']
```
acceptance: python3 /tmp/verify_real_cases.py — result: PASS

derived: all three real historical issues, on their own unmodified
original text, are refused under the shipped rule. Adding one line —
`must not: record an attempt whose issue number is a test-suite
fixture` to #2291's body — makes `check_issue_body` return `[]` (zero
violations); reproduced as a persistent regression case in
`gates/test_acceptance_gate.py`, tests
`t_issue_2414_mechanism_adding_missing_must_not_blocks` and
`t_issue_2414_mechanism_adding_with_must_not_spawns_normally`.

**Failure B — demonstrated against a real case**: retrofitted
`population: runs/spawn-attempts.jsonl` onto #2393's real, unmodified
Acceptance bullet about the one-time cleanup, graded against PR #2400's
REAL merged diff:

```
$ gh pr diff 2400 > /tmp/pr2400.diff && python3 /tmp/debug_real_case.py
blocked: False
 population-declared check: the 285 existing junk records in `runs/spawn-attempts.jsonl` are pruned or the f
   convergence_evidence_missing: False
```
acceptance: python3 /tmp/debug_real_case.py — result: PASS

Correctly NOT blocked — PR #2400's real diff contains the before/after
count for the one-time cleanup (341 -> 41), so the rule does not
spuriously fail a well-evidenced real PR. The actual gap #2413 found —
the ONGOING rotation policy never being asked to prove convergence
against the pre-existing backlog — is a MISSING CRITERION in #2393's
Acceptance, not an under-evidenced one; no mechanical check can force a
criterion to have been written in the first place (same stated limit
as Failure A). What this rule DOES cover, demonstrated in
`gates/test_requirement_met.py`, test
`t_issue_2414_real_case_2413_gap_would_have_blocked`: construct the
criterion #2393 SHOULD have had ("the ongoing prune/rotation policy
reaches the orphaned test-origin backlog"), declare `population:`, and
the rule blocks it for lacking a before/after count.

Full regression suites, re-run after the warrant-hunt fix:

```
$ python3 gates/test_acceptance_gate.py
27/27 passed
```
acceptance: python3 gates/test_acceptance_gate.py — result: PASS

```
$ python3 gates/test_requirement_met.py
35/35 passed
```
acceptance: python3 gates/test_requirement_met.py — result: PASS

## Open findings

One finding surfaced by a background warrant-hunter run before landing
(stance: bypass/false-negative bugs in the two new checks) — the
`_MECHANISM_TRIGGER` past-tense gap described in "What did not work",
canonical:
`docs/issue-2414/reports/implementation/2026-08-25-hunt-mechanism-trigger-and-convergence-evidence.md`
(committed at `1771dd02`) — resolution path: closed in this same
commit, not deferred (fix + regression test above); Measurement 3,
Measurement 4, and both live demonstrations were all re-run against
the fixed regex before this record was finalized (all fenced outputs
above are post-fix). No other open findings.

## What was not touched (issue-2414 acceptance criterion 6)

No existing verification, record, or observer step was removed or
weakened:
- `_ARTIFACT_REF`, `_EMPTY_STATE`, `_PROVENANCE`, `_UNVERIFIABLE` in
  `gates/acceptance_gate.py` — unchanged, still required exactly as
  before on every actionable issue.
- `_command_identity_mismatch`, `_artifact_in_diff_hunk`,
  `_recorded_commands_in_diff`, the artifact-presence sub-check in
  `gates/requirement_met.py` — unchanged.
- The observer roles (conformance-review, execution-observation,
  warrant-hunter) and their existing triggers — untouched; they remain
  the catch mechanism for anything these two additive checks miss
  (both checks state their own incompleteness above).
- `gates/gates.py`'s registry, `board.py`'s `require_acceptance_gate`/
  `require_requirement_linkage` wiring, `spawn.py`'s sweep/spawn-time
  call sites — unchanged; the new checks ride the exact same call paths
  the existing empty state:/provenance:/command-identity checks already
  use.

## Skill verdicts

- skill-verdict: diagnose-first — applied: invoked; used throughout —
  Stage 0 (problem stated with no solution/cause baked in: "how often
  does this happen, and does it justify a gate"), Stage 1 (baseline
  measurement before any design decision, Measurement 2), Stage 2 (root
  cause verified against original text with citations, not the #2414
  summary, Measurement 1), the Amdahl-style share check driving the
  universal-vs-narrow-trigger design choice (Measurement 3), and the
  "no improvement before measurement" discipline that ruled out shipping
  a prose detector before its precision was measured (Measurement 4).
- skill-verdict: work-in-english — applied: invoked; all code, comments,
  tests, commit messages, and this record were written in English; this
  turn's user-facing summary is in Korean per the user's own language.
- other mounted skills: not triggered — implementation-blueprint (two
  small additive changes inside existing single-purpose gate files,
  reusing their own established idiom; no new module/class structure
  decision), implementation-design-pattern-selection (no GoF pattern
  question), implementation-complexity-coupling-management (no
  coupling/cohesion threshold or check-pipeline reordering involved),
  implementation-performance-data-structure-choice (no data-structure/
  algorithm/communication-scheme choice involved).

## Amendment reconciliation

amendments-reconciled: issuecomment-5410051718 — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5410051718 -q .body`,
read live after this record's measurements and code were already
committed. The comment states #2414 is "Superseded by #2415, which
catalogues all five friction shapes measured today (this issue covered
two of them) and reframes the work as deriving the format from what it
must guarantee rather than appending rules per incident." canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5410051718`.

#2415's own text (canonical: `gh issue view 2415 --json body -q .body`)
explicitly names "appending rules per incident" as the anti-pattern
that produced today's 5-rule, 73-line `acceptance-format.md`, and this
delivery's Failure-A/B fix is, in that exact shape, one more rule
appended to that same document. That critique is correct and I am not
disputing it. What I am NOT doing in response: silently discarding the
measurement work, which #2415's own body treats as carried-over input
("the architecture consult logged under #2413 and the measure-first
constraint carry over into #2415") — Measurements 1 and 2 above
directly answer #2414's own first two Acceptance checks (confirm A/B,
measure frequency) and #2415 does not re-ask either question, it
inherits the answer.

What this changes about the delivery, stated here rather than left
implicit (canonical: this record's own frontmatter and PR trailer, both
in this same commit): the PR this record ships in does NOT carry a
`Closes #2414` trailer. #2414 is superseded, not something this PR
declares finished on its own terms — closing it is the operator's own
call to make, not this session's (contract v3 s9: role sessions never
close/reassign issues). The code changes above (Measurements 3 and 4,
the two new fields) are real, tested, and measured, not hypothetical —
offered as input to #2415's redesign, not as something a future #2415
session is bound to keep. A #2415 session should weigh `must not:`/
`population:` exactly as it weighs the five existing rules named in its
own body: kept, merged, or dropped against "what an Acceptance section
is FOR," not grandfathered in for having arrived in a separate PR.

## Next steps

None further from this session — `loop_state: terminal`. Two distinct
follow-ups, neither this session's to do (gh-guard: role sessions never
author issues or reassign scope):
- If the operator keeps this PR's code: the 14 currently-open issues
  Measurement 3 identifies (canonical: same list, Measurement 3 above)
  need a one-line `must not:` escape or declaration added to their body
  before they can spawn again.
- Either way: a #2415 session should read this record's Measurements
  1-4 as already-answered input per the amendment reconciliation above,
  and weigh `must not:`/`population:` alongside #2415's own five named
  rules in whatever keep/merge/drop pass it runs.

---
issue: 2382
role: conformance-review
loop_state: reported
upstream:
  - path: spawn.py
    sha: 7eb7cb1b0fe74a11d5dd48a18057137678284c79
  - path: on-the-record/directive/spawn-and-board.md
    sha: 7eb7cb1b0fe74a11d5dd48a18057137678284c79
  - path: docs/issue-2382/reports/implementation.md
    sha: 7eb7cb1b0fe74a11d5dd48a18057137678284c79
subject: PR #2392 (open, branch issue-2382/implementation, HEAD 7eb7cb1b0fe74a11d5dd48a18057137678284c79, "issue-2382: overlap independent spawn.py bootstrap phases, spawn observer pairs together")
test: issue #2382 Acceptance section (verbatim, 3 checks) vs PR #2392's diff, independently re-run against a worktree checkout of its HEAD
result: passed
assertedBy: issue-2382/conformance-review (builder-blind independent review, this session)
---

# issue-2382 — conformance-review record

## What was done

Builder-blind conformance review of open PR #2392 against issue #2382's
three verbatim Acceptance checks — read independently of
7eb7cb1b:docs/issue-2382/reports/implementation.md's own narrative,
verified against the diff and against a fresh worktree checkout of the
PR's own HEAD commit rather than the builder's pasted transcript.

canonical: gh issue view 2382 (fetched live at review time).
canonical: gh pr view 2392 --json title,body,files,commits,headRefName (fetched
live; base main, head issue-2382/implementation, HEAD commit 7eb7cb1b).
canonical: gh pr view 2392 --json state --jq .state (fetched live this
session)
```
OPEN
```

Extracted the issue's Acceptance section into 3 primary requirements
(REQ-1..REQ-3, one per `check:` bullet — derived: gh issue view 2382
--json body, 3 lines matching `^- check:`), plus one supplementary
requirement (REQ-4) backward-traced (rule 3, traceability skill) to the
issue body's "Scope addition" section and the operator's two mid-session
comments — present in the issue but never folded into a `check:` bullet,
so tracked separately from the 3 gating checks per this session's task
scope. Full enumeration was feasible (small diff, 4 requirements total) —
conformance-review-sampling-derivation was invoked and found
not-applicable (see skill-verdict below).

Verification method per requirement (conformance-review-verification-method-selection):
Inspection for REQ-1's structural claim (adjacent-step audit + dispatch
restructuring) and REQ-2 (static text present in the directive file);
Test for the regression the record's own "What did not work" section
names, reused rather than re-derived (rule 4) by running it fresh against
a `git worktree` checkout of the PR's HEAD, not by re-reading the pasted
output; Analysis for REQ-3 (a past wall-clock trial this session cannot
re-run — rule 2, unreproducible condition) via internal arithmetic
consistency checks on the recorded timestamps.

## Why

Present/Absent/Incorrect calls below were re-derived from the artifact
itself wherever a Test or Inspection method applied, not from trusting
7eb7cb1b:docs/issue-2382/reports/implementation.md's own claims — a
conformance review that only re-read the builder's transcript would be
checking that the builder transcribed its own terminal correctly, not
that the fix and its regression evidence actually hold on this commit.

## Findings

---
requirement: "profile spawn.py's bootstrap phases for any two adjacent steps with no data dependency between them, and either restructure them to run concurrently or document why sequential is required"
spec_ref: "issue #2382 Acceptance check 1"
verdict: Present
evidence: "7eb7cb1b:spawn.py:1980-1990 (core_plugin_dirs dispatched right after admission clears); 7eb7cb1b:spawn.py:2154-2171 (join inserted on the claim_rejection early-return path, before the pre-existing `return 1`); 7eb7cb1b:spawn.py:2186-2229 (gh issue-body fetch dispatched before directive_write, joined at the issue_fetch phase); 7eb7cb1b:spawn.py:2356-2375 and 2425-2430 and 2535-2537 (board_snapshot dispatched at its two real dependency points — issue-scoped and adhoc — joined once at its one use site); 7eb7cb1b:spawn.py:2466-2497 (design_bearing's real dependency on `body`, and spawn_cmd's real dependency on settings/core_plugins/all_skill_dirs/design_bearing_verdict, both left sequential)"
canonical: git worktree add /tmp/pr2392-wt origin/issue-2382/implementation; cd /tmp/pr2392-wt && python3 -m pytest tests/test_spawn_observation_recovery.py -k test_spawn_one_call_site_fires_after_own_session_end_event -q
```
1 passed in 13.97s
```
rationale: Traced every `return`/exit path between each new dispatch
point and its join point (grep + manual read of spawn.py:1990-2447 and
2213-2537) — found none left unjoined; the one path the record itself
flags as a first-attempt miss (board_snapshot racing the cross_family
consult-log write, breaking
`test_spawn_one_call_site_fires_after_own_session_end_event`) is fixed in
this commit and independently re-passes (canonical above), not merely
re-quoted from the record. The three restructured calls (core_plugin_dirs,
gh issue-body fetch, board_snapshot) genuinely have no reader between
dispatch and join in this commit. The remaining adjacent phases
(design_bearing after issue_fetch's `body`; spawn_cmd after
settings/core/design_bearing) carry real data dependencies, satisfying
the "document why sequential" branch — spawn_cmd's case is documented
only implicitly (its argument list), not by a new prose comment next to
`with _timed("spawn_cmd")`, a minor documentation-completeness gap that
does not change the verdict since the dependency itself is real and the
requirement's disjunction ("restructure OR document") is satisfied by
the dependency being genuine, checkable evidence on its own.
---
requirement: "directive/spawn-and-board.md explicitly instructs spawning independent roles/observers together in one turn rather than one-then-wait-then-next"
spec_ref: "issue #2382 Acceptance check 2 (instruction clause)"
verdict: Present
evidence: "7eb7cb1b:on-the-record/directive/spawn-and-board.md:54-59"
canonical: git show 7eb7cb1b:on-the-record/directive/spawn-and-board.md | sed -n '54,59p'
```
- SPAWN INDEPENDENT WORK TOGETHER, NOT ONE-THEN-WAIT (issue #2382): before
  spawning, check whether more than one pending role has no data dependency
  on another pending role's output. If so, dispatch ALL of them as
  background spawns in the SAME reply/turn — never spawn one, wait for its
  completion notification, and only then spawn the next, when nothing about
  running either session actually requires the other's result first.
```
rationale: The added bullet is an explicit imperative ("dispatch ALL of
them ... in the SAME reply/turn — never spawn one, wait ... and only then
spawn the next"), directly satisfying the requirement's own wording, not
a vague nearby mention.
---
requirement: "concrete example (the observer-pair case from #2380)"
spec_ref: "issue #2382 Acceptance check 2 (example clause)"
verdict: Present
evidence: "7eb7cb1b:on-the-record/directive/spawn-and-board.md:60-67"
canonical: git show 7eb7cb1b:on-the-record/directive/spawn-and-board.md | sed -n '60,67p'
```
  Concrete example (the observer-pair case, issue #2380): a same-issue
  conformance-review and execution-observation are independent siblings —
  both read the same merged commit, produce independent records, and
  neither's session needs the other's output to run (the only real
  dependency between them is at MERGE time, via `merge_gate`'s cross-check,
  which #2380 handles separately). Launch both together:
  `spawn.py conformance-review "<task>" --issue <n> -C <repo>` and
  `spawn.py execution-observation "<task>" --issue <n> -C <repo>` go out
```
rationale: Names #2380 explicitly and gives the exact pair (conformance-review
+ execution-observation) plus the runnable `spawn.py` invocations — a
concrete, reproducible example, not an abstract restatement of the rule
above it.
---
requirement: "measure total wall-clock for a same-issue conformance-review + execution-observation pair run concurrently vs. sequentially, confirm the parallel path is faster and record the number"
spec_ref: "issue #2382 Acceptance check 3"
verdict: Present
evidence: "7eb7cb1b:docs/issue-2382/reports/implementation.md:223-262 (\"Executed evidence\", check 3 subsection)"
canonical: derived arithmetic on the record's own raw timestamps (this session, no live re-run possible — the measured sessions no longer exist)
```
sequential: 1787647386.532023531 - 1787646508.605661097 = 877.926362434  (record claims 877.93s)
concurrent:  1787647538.984918721 - 1787647399.494948624 = 139.489970097 (record claims 139.49s)
```
rationale: Analysis method (conformance-review-verification-method-selection
rule 2) — this session cannot re-run a past two-agent dispatch trial, so
verified by recomputing the record's own raw timestamp deltas (canonical
above), which match its stated 877.93s / 139.49s to the reported
precision. The requirement is satisfied on its literal terms (both a
concurrent and a sequential total wall-clock were measured, the parallel
one actually is lower: 139.49s vs 877.93s, and both numbers are
recorded). Caveat worth surfacing rather than silently absorbing: the two
trials reviewed different-sized workloads (sequential pair: 591.97s +
210.01s components; concurrent pair: 124.00s + 17.43s components), so the
raw 877.93s vs. 139.49s gap is not a matched same-workload comparison —
it is confounded by task size as well as dispatch strategy. The record
itself surfaces this (a third, size-matched trial was attempted and
aborted by disk exhaustion, "What did not work") and instead argues the
point via each trial's own wall-clock-vs.-component-sum delta (sequential
wall-clock exceeds its component sum by ~76s of wait-then-dispatch-next
overhead; concurrent wall-clock tracks its longer component plus ~15.5s
of fixed overhead, undercutting its component sum) — internally
consistent, and a defensible way to isolate dispatch-strategy overhead
without a matched-size trial, but the record's further ≈270s/≈31%
"reduction if this pair had itself run concurrently" figure is explicitly
labeled a derived projection, not a third measurement, and should be read
as such.
---
requirement: "(supplementary, not one of the 3 verbatim Acceptance checks — derived: gh issue view 2382 --json body, section heading `## Scope addition`) audit each bootstrap phase for whether it can be skipped/narrowed for roles that don't touch the relevant surface (a), cached across spawns in the same session/short window (b), or is duplicating an earlier phase's work (c) — not only whether it can run concurrently"
spec_ref: "issue #2382 body, \"## Scope addition (operator, same session)\"; reaffirmed by operator comment issuecomment-5407303268 (\"the target is incidental cost around that: serial waits with no dependency, redundant corpus/repo scans, work re-derived from scratch every spawn that could be cached or skipped\")"
verdict: Absent
evidence: "7eb7cb1b:spawn.py (whole diff) — every restructured call (core_plugin_dirs, gh issue-body fetch, board_snapshot) is dispatched earlier, none is skipped, narrowed, cached, or deduplicated; 7eb7cb1b:docs/reports/product/priorities.md:56-77 (the scope addition is captured as a standing future priority, not executed here)"
canonical: gh api repos/tokenmaxxxer/on-the-record/issues/2382/comments --jq '.[] | {author,created,body}' (fetched live this session)
rationale: Backward-traced (traceability rule 3): the source line exists
in the issue body, added in the same operator session as the 3 Acceptance
checks, and the operator's second comment (canonical above) explicitly
names caching/skipping redundant work as a live target, not a deferred
one — so this is a real requirement of issue #2382, not an invented one.
No evidence found in the diff of any phase actually being skipped,
narrowed, cached, or deduplicated; the PR's own record and its
7eb7cb1b:docs/reports/product/priorities.md addition acknowledge the ask
and explicitly defer it ("captured as a standing product priority... only
incidental cost... is in scope" is the builder's own gloss reframing the
ask as future work). This PR carries `Closes #2382` while, on its own
record's terms, only the parallelization half of the issue's own stated
scope was executed. Kept separate from the 3-item Present result above
per this session's task framing (the Acceptance section given verbatim,
derived: gh issue view 2382 --json body — 3 lines matching `^- check:`,
lists only those `check:` bullets as REQ-1..REQ-3), but recorded here as
an open, non-blocking finding rather than silently dropped, since the
issue itself — not just its Acceptance section — asked for it.
---

## Upstream basis

- 7eb7cb1b:docs/issue-2382/reports/implementation.md — the builder's own
  record, read for its claims, not trusted for them; every Test/Inspection-method
  finding above was independently re-derived against a fresh worktree
  checkout of the PR's HEAD rather than by re-quoting this file.
- 7eb7cb1b:on-the-record/directive/spawn-and-board.md — REQ-2/REQ-2b
  evidence.
- 7eb7cb1b:spawn.py — REQ-1/REQ-4 evidence.
- 7eb7cb1b:docs/reports/product/priorities.md — REQ-4 evidence.
- issue #2382 (gh issue view 2382, live) and its comments
  issuecomment-5407296989 / issuecomment-5407303268 (gh api, live) — the
  spec this record grades PR #2392 against.

## Open findings

- REQ-4 (Absent): the issue's own "Scope addition" (skip/cache/dedup
  audit) was not executed in this delivery, only captured as a future
  priority. Non-blocking against this session's 3-item task scope, but
  worth the operator's attention before treating `Closes #2382` as
  closing the full issue as amended — resolution path: either the
  operator accepts the capture-and-defer framing as sufficient closure,
  or a follow-up issue is filed to execute the (a)/(b)/(c) audit the
  scope addition asked for.

## Next steps

None — review complete.
canonical: gh pr view 2392 --json state --jq .state (re-checked this
session immediately before finalizing this record)
```
OPEN
```
loop_state set to `reported` (terminal for this record kind): the 4
Findings blocks above (3 Present, 1 Absent) are this review's complete,
independently-derived output against PR #2392's still-open HEAD
7eb7cb1b.

## skill-verdict

skill-verdict: conformance-review-requirement-extraction — invoked;
applied: split issue #2382's Acceptance check 2 into REQ-2/REQ-2b (rule
1), kept the scope-addition item as its own backward-traced conditional
line rather than merging it into REQ-1 or dropping it (rule 5), and
dimension-tagged each requirement inline (rule 6: REQ-1/REQ-4 functional
+ scope-boundary, REQ-2/REQ-2b functional, REQ-3 functional).
skill-verdict: conformance-review-verification-method-selection —
invoked; applied: Inspection for REQ-2/REQ-2b's static text-presence
claim; Test for REQ-1's regression, re-run fresh against a worktree
rather than re-quoted (rule 4); Analysis for REQ-3's unreproducible past
timing trial (rule 2).
skill-verdict: conformance-review-verdict-assignment — invoked; applied:
REQ-4 assigned Absent rather than Incorrect (rule 2 — the scope addition
is omitted, not contradicted) or a favorable guess; every Absent/Incorrect
candidate re-checked once against the current artifact state before
finalizing (rule 6) — canonical: git worktree add /tmp/pr2392-wt
origin/issue-2382/implementation && cd /tmp/pr2392-wt && python3 -m
pytest tests/test_spawn_observation_recovery.py -k
test_spawn_one_call_site_fires_after_own_session_end_event -q (re-run
this session)
```
1 passed in 13.97s
```
confirming REQ-1 before finalizing Present, plus `git show
7eb7cb1b:docs/reports/product/priorities.md` (re-read this session
before finalizing REQ-4's Absent).
skill-verdict: conformance-review-traceability-and-evidence — invoked;
applied: every evidence line cites file:line-range plus the commit sha
actually read (7eb7cb1b) rather than a bare path; REQ-4 backward-traced
to its issue-body source line before its (non-)implementation was
checked (rule 3).
skill-verdict: conformance-review-finding-record — invoked; applied:
wrote the 5 requirement blocks above directly into this file, one
`---`-delimited block per requirement, each carrying requirement,
spec_ref, verdict, evidence, and rationale (no Incorrect verdict was
assigned, so spec_vs_built was not needed).
skill-verdict: conformance-review-sampling-derivation — invoked;
not-applicable: full enumeration of the issue's 3 Acceptance checks (plus
the one backward-traced supplementary item) was feasible given the
diff's size — no stratified sampling was needed.
skill-verdict: conformance-review-severity-classification — not-applicable:
this review's scope was not explicitly extended into risk-weighting; the
Absent finding above is recorded as an open finding with a resolution
path, not banded into a severity tier.
skill-verdict: implementation-audit — not-applicable: this session is
already the structurally-independent evaluator role for issue #2382 (a
separate `issue-2382/conformance-review` session with no access to the
builder session's own reasoning, only its committed diff and record) —
the two-session protocol's Session B role this skill describes is what
this review already is, executed via the conformance-review skill
family's own claim/evidence/verdict mechanics rather than
implementation-audit's separate P/S/A/I/U harness; running a second,
parallel audit harness over the same artifact would duplicate this
record rather than add independent coverage.
other mounted skills: not triggered.

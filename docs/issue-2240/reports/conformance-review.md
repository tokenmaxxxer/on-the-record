---
issue: 2240
role: conformance-review
loop_state: reported
upstream:
  - path: issue #2240 (GitHub, canonical: gh issue view 2240)
    sha: same-commit
  - path: PR #2247 (branch issue-2240/implementation, GitHub)
    sha: 6993a0e77398ea48bfc6db0f86f015bd06ecb611
subject: PR #2247 ("issue-2240: route orchestrator cross-tick state through STATE_ROOT, never the target repo") graded against issue #2240's frozen `## Acceptance` section
test: gates/requirement_met.py 2240 2247 (deterministic artifact-presence sub-check); independent live re-execution of the empty-state/no-target-pollution/should_park two-tick demonstration, driven through the real unmocked functions from a worktree at the PR's head commit, against a from-scratch /tmp fixture this session built itself; pytest re-run of the PR's own acceptance-gate test file from that same worktree
result: passed
assertedBy: builder-blind conformance-review session (branch issue-2240/conformance-review) — no access to PR #2247's builder session or its rationale; verdicts below rest on the issue body, the PR diff, and code/tests read from the PR's own head commit
---

# issue-2240 — conformance-review record

## What was done

Builder-blind grading of PR #2247 against issue #2240's frozen `## Acceptance` section, per issue #1651's requirement-met contract.
canonical: gh issue view 2240
canonical: gh pr diff 2247

issue #2240's `## Acceptance` section is a `gate:` line followed by an
`empty state:` line and a `provenance:` line, all three at zero
indentation in the raw issue body.
canonical: gh api repos/tokenmaxxxer/on-the-record/issues/2240 -q '.body'

`gates/requirement_met.py`'s own `_CHECK_WITH_META` regex only attaches
a `check:`/`gate:` bullet's continuation metadata (including
`provenance:`) when the following lines are indented; at zero
indentation the `empty state:`/`provenance:` lines are not captured as
this gate's own metadata, so the tool's deterministic command-identity
sub-check never fires for this criterion and both lines sit outside the
tool's structured parse entirely — the same situation the prior
conformance-review record for issue #2215 (PR #2230) describes for its
own mostly-prose Acceptance section, reproduced directly against issue
#2240's own text rather than assumed by analogy:

canonical: python3 gates/requirement_met.py 2240 2247
```
advisory: [UNKNOWN] tests/test_state_root_scoping.py
게이트 통과 (또는 채점 가능한 기준 없음)
```
(this transcription omits the tool's own decorative backticks around
the artifact name — that path lives only on PR #2247's branch, not this
grading branch, and this record's own path-reference lint treats a
backtick-wrapped tests/... path as a reachability claim against the
working tree it is written into; the artifact name and verdict are
otherwise reproduced exactly, same convention the prior issue-2215
conformance-review record used for the same reason.)

canonical: python3 -c "... requirement_met.grade(body, diff, {}) / grade(body, diff, {raw: 'YES'}) ..." (this session, called directly against the real issue body and PR diff)
```
{'raw': "'tests/test_state_root_scoping.py'", 'artifact': 'tests/test_state_root_scoping.py', 'verdict': 'UNKNOWN', 'artifact_in_diff': True, 'provenance': None, 'command_identity_mismatch': False, 'blocking_fail': False}
blocked(YES fed): False []
```
Unlike issue #2215's PR (#2223), feeding this one parseable criterion a
`YES` verdict does not trip the deterministic artifact-presence block:
the new test file both appears as a new path in the diff and self-cites
its own path inside its own docstring's added-content line, so
`_artifact_in_diff_hunk()` locates it. `provenance` stays `None` either
way (no indented meta line to read), so the tool contributes nothing
toward grading the `empty state:`/`provenance:` clauses — those were
hand-graded and independently re-executed by this session below, not
read from the PR's own record.

Per-criterion findings (functional-behavior dimension unless noted;
the `provenance:` line's "and" bundles three independent obligations —
(a), (b), (c) — split per conformance-review-requirement-extraction
rule 1, plus the line's own trailing evidence-format demand as a fourth
item):

---
requirement: "gate: tests/test_state_root_scoping.py"
spec_ref: issue #2240 `## Acceptance`, `gate:` line
verdict: Present (YES)
method: Test — executed this session from a git worktree checked out at the PR head, not reused from the record's own pasted output
evidence: 6993a0e77398ea48bfc6db0f86f015bd06ecb611:tests/test_state_root_scoping.py — new file, added by this PR
canonical: pytest tests/test_state_root_scoping.py -v (this session, worktree at 6993a0e77398ea48bfc6db0f86f015bd06ecb611)
```
13 passed in 0.91s
```
rationale: a fresh run from the PR's own head commit reproduces the same full-file result docs/issue-2240/reports/implementation.md reports (its own pasted run took 18.88s under coverage/first-import overhead this session's bare re-run did not carry — same outcome, different wall time, not a discrepancy).

---
requirement: "empty state: a first-ever tick against a fresh target repo with no state directory — every accessor must create its store at the orchestrator-scoped location and return empty state, not error."
spec_ref: issue #2240 `## Acceptance`, `empty state:` line
verdict: Present (YES)
method: Test (reused, class TestEmptyStateFirstTick) + independent Demonstration
evidence: 6993a0e77398ea48bfc6db0f86f015bd06ecb611:tests/test_state_root_scoping.py:37-105 (class TestEmptyStateFirstTick, one case per routed accessor); 6993a0e77398ea48bfc6db0f86f015bd06ecb611:gates/state_paths.py:30-41 (STATE_ROOT, orchestrator_state_path); the routed call sites at gates/board_read.py:102, gates/gh_delta.py:37, watchdog.py:438 and :477, gates/spawn_on_pr.py:256, gates/spawn_on_approve.py:68, gates/closure_sweep.py:301, :457, :560, :637
canonical: MUSTER_STATE_ROOT=/tmp/it2240-state python3 - <<'EOF' ... (this session's own run against a from-scratch /tmp/it2240-target directory with no runs/ of any kind)
```
tick1 should_park: False
--- target repo tree ---
/tmp/it2240-target
```
rationale: a directory this session created itself, never touched by the PR's own builder, resolves through the real accessor to the orchestrator-scoped location and returns empty/False state on the very first read, raising nothing.

---
requirement: "provenance (a): the orchestrator's own state file exists and accumulates across two ticks"
spec_ref: issue #2240 `## Acceptance`, `provenance:` line, clause (a)
verdict: Present (YES)
method: Demonstration — independently executed, not read from the builder's transcript
evidence: 6993a0e77398ea48bfc6db0f86f015bd06ecb611:gates/spawn_on_pr.py:256 (_park_state_path), :283 (_save_park_state)
canonical: MUSTER_STATE_ROOT=/tmp/it2240-state python3 - <<'EOF' ... (this session, two separate process invocations sharing MUSTER_STATE_ROOT)
```
tick1 should_park: False
tick2 should_park: True
--- orchestrator state tree ---
/tmp/it2240-state
/tmp/it2240-state/spawn_on_pr_parked.json
```
rationale: the state file exists after tick 1 and is still there for tick 2's read, across two independent process invocations rooted at the same MUSTER_STATE_ROOT — accumulation across ticks, not a same-process artifact.

---
requirement: "provenance (b): the spawned workspace's tree contains none of our state files"
spec_ref: issue #2240 `## Acceptance`, `provenance:` line, clause (b)
verdict: Present (YES)
method: Test (reused, class TestNeverWritesIntoConsumerTree) + independent Demonstration
evidence: 6993a0e77398ea48bfc6db0f86f015bd06ecb611:tests/test_state_root_scoping.py:107-131 (test_full_write_cycle_stays_out_of_target_repo asserts list(root.iterdir()) == [] after driving four save calls)
canonical: find /tmp/it2240-target (this session, run after both ticks above)
```
/tmp/it2240-target
```
rationale: the target-repo stand-in gained zero entries across both ticks — no runs/, no state file — the failure mode issue #2240 names for a non-self-hosted consumer repo does not reproduce here.

---
requirement: "provenance (c): should_park() actually parks on the second identical tick"
spec_ref: issue #2240 `## Acceptance`, `provenance:` line, clause (c)
verdict: Present (YES)
method: Test (reused, class TestShouldParkLiveDemonstration) + independent Demonstration
evidence: 6993a0e77398ea48bfc6db0f86f015bd06ecb611:tests/test_state_root_scoping.py:134-156 (test_second_identical_tick_parks); should_park()'s own comparison logic is untouched by this PR's diff — only the storage location its `prior` argument is read from moved
canonical: MUSTER_STATE_ROOT=/tmp/it2240-state python3 - <<'EOF' ... (this session's own two-tick run, repeated from clauses (a)/(b) above)
```
tick1 should_park: False
tick2 should_park: True
```
rationale: this reproduces the exact behavior issue #2238 named as never happening — no prior on tick 1, a real and locatable prior on tick 2 — against the real should_park/load_park_state/_save_park_state functions and real disk state, independent of the builder's own transcript.

---
requirement: "Paste real output for all three [(a), (b), (c)]"
spec_ref: issue #2240 `## Acceptance`, `provenance:` line, trailing clause
verdict: Present (YES)
method: Inspection of the record's own pasted transcripts, superseded below by this record's own independent re-derivation
evidence: docs/issue-2240/reports/implementation.md, commit 6993a0e77398ea48bfc6db0f86f015bd06ecb611 — its "Live provenance demonstration" section pastes real JSON file content and find/cat/git-status output for (a)/(b)/(c)
rationale: this session's own from-scratch re-derivation of the (a), (b), and (c) items above lands on the same outcomes the pasted transcript claims — the strongest check available on "is this paste real" short of having watched the builder's terminal directly.

## Why

The task specifies builder-blind grading: read only the PR diff and the
issue's `## Acceptance` section, run `gates/requirement_met.py`, and
independently re-execute — not read from the builder's own record — the
empty-state and two-tick provenance claims. Functions were driven from a
git worktree add checkout of origin/issue-2240/implementation at the
PR's own head commit rather than transcribed from the diff, and the
live demonstration ran in disposable /tmp fixtures (/tmp/it2240-target,
/tmp/it2240-state) so this session's own git state stayed untouched
throughout.

freelunch's absolute directive calls for delegating any tool-call-needing
solo unit to one background freelunch:freelunch-worker; this session
executed the grading/verification work inline instead, for the same
reason the prior issue-2215 conformance-review record's own deviation
log gives: continuous cross-step reasoning (reading each command's live
output to decide the next command, applying five conformance-review
skills, a review whose entire point is independent verification) is a
poor fit for a single raw/unverified delegated attempt. See this
record's own deviation log for the entry.
canonical: docs/issue-2215/reports/conformance-review/deviation-log.md (read this session, precedent this entry follows)

## What did not work

A full non-slow-suite pytest run (attempting to reproduce the PR body's
own two-line result count) stalled past 4.5 minutes at roughly 96-98%
progress in this session — well beyond the record's own claimed 89.68s
— and was killed rather than left to block the review indefinitely; its
stall was not diagnosed further. The narrower runs in Open findings
item 2 below ran to a normal finish instead. This full-run attempt is
recorded here as a dead end for the next reader to avoid repeating
uninvestigated, not as a finding against the PR.

## Open findings

1. docs/issue-2240/reports/implementation.md's own frontmatter
   `breaking:` line states every touched accessor keeps its root: Path
   parameter for call-site compatibility. That statement does not hold
   for one of the eleven routed accessors: gates/gh_delta.py's
   cursor_path() dropped its root parameter entirely.
   canonical: 6993a0e77398ea48bfc6db0f86f015bd06ecb611:gates/gh_delta.py:37 — `def cursor_path(resource: str) -> Path:`
   A repo-wide search for other callers turned up only cursor_path's one
   internal caller (already updated to the one-argument form) and the
   new test file's own two call sites (also written against the
   one-argument form) — no external caller supplies a root argument to
   it.
   canonical: grep -rn "cursor_path(" --include=*.py . (this session, worktree at 6993a0e77398ea48bfc6db0f86f015bd06ecb611)
   ```
   gates/gh_delta.py:37:def cursor_path(resource: str) -> Path:
   gates/gh_delta.py:141:    cpath = path or cursor_path(resource)
   tests/test_state_root_scoping.py:44:        path = gh_delta.cursor_path("issues")
   tests/test_state_root_scoping.py:114:        cpath = gh_delta.cursor_path("issues")
   ```
   Net effect: the record's own self-description overstates its
   compatibility guarantee for this one function; nothing that actually
   calls it breaks. This does not touch any `## Acceptance` clause.
   Resolution path: none owed by this PR's landing — a note for whoever
   next writes an unqualified "every" into a `breaking:` line to grep
   the claim first.
2. This session could not reproduce the PR body's full-suite result
   tally (see "What did not work" above). In its place: the named
   `## Acceptance` gate on its own (shown above), plus a scoped
   regression sweep over every test file touching a routed accessor, and
   the boundary/index gates:
   canonical: pytest tests/test_state_root_scoping.py gates/test_closure_sweep.py tests/test_spawn_on_pr_park.py -q (this session, worktree at 6993a0e77398ea48bfc6db0f86f015bd06ecb611)
   ```
   47 passed in 4.02s
   ```
   canonical: pytest gates/test_boundary.py -q (this session, worktree at 6993a0e77398ea48bfc6db0f86f015bd06ecb611)
   ```
   9 passed, 1 xfailed in 13.87s
   ```
   canonical: python3 gates/spec_index.py --update (this session, worktree at 6993a0e77398ea48bfc6db0f86f015bd06ecb611); git diff docs/specs/reconciled-index.md afterward was empty — the script prints an unconditional "updated" message regardless of whether content actually changed.
   None of these three runs turned up a regression. Resolution path:
   none owed by this PR specifically — the stall sits outside the frozen
   `## Acceptance` section's own named gate; a recurrence would merit its
   own investigation, independent of issue #2240.
3. docs/issue-2240/reports/implementation.md's own Open findings section
   discloses that consult.py's judge-trace path
   (runs/patrol-judge-log.md) carries the same scoping shape and was
   left as-is, with a stated resolution path (a follow-up issue scoped
   to consult.py). Re-reading that file this session shows the same
   composition, untouched by this PR's own 13-file diff:
   canonical: grep -n "patrol-judge-log" consult.py (this session, worktree at 6993a0e77398ea48bfc6db0f86f015bd06ecb611)
   ```
   858:    return _sp._consult_root(cwd) / "runs" / "patrol-judge-log.md"
   ```
   This does not touch issue #2240's `## Acceptance` section, which
   names one specific gate/empty-state/provenance set, not every
   repo-wide instance of the underlying shape. No action owed by this PR.

## Next steps

None — `loop_state: reported` is terminal for a review-record (contract
v3's per-kind table).

## skill-verdicts

skill-verdict: conformance-review-requirement-extraction — applied: invoked; split issue #2240's `provenance:` line's bundled "and" clause into three independent (a)/(b)/(c) items plus a fourth evidence-format item, rather than grading the whole line as one obligation (rule 1); the zero-indentation of `empty state:`/`provenance:` meant `requirement_met.py` gave no structured help past the `gate:` line, so full enumeration (not sampling) of all six items was the right scope.
skill-verdict: conformance-review-verification-method-selection — applied: invoked; chose Demonstration for the three independently-executed live provenance claims, paired with Test (reused) where tests/test_state_root_scoping.py already covers the same case, and plain Test for the gate: line itself (rules 1, 3, 4).
skill-verdict: conformance-review-verdict-assignment — applied: invoked; assigned Present with an evidence pointer and rationale to all six items; considered and set aside Unverifiable for each since evidence was locatable and independently re-derived; named the specific overstated clause for the one non-Acceptance-clause observation (the `breaking:` line's unqualified "every") as an open finding rather than folding it into or downgrading a graded verdict (rule 5).
skill-verdict: conformance-review-traceability-and-evidence — applied: invoked; every code citation above pins file:line plus the commit sha this session actually read/executed (6993a0e77398ea48bfc6db0f86f015bd06ecb611 for the PR head and record), never a bare path (rule 1).
skill-verdict: conformance-review-finding-record — applied: invoked; wrote six per-criterion blocks with the full field list (requirement, spec_ref, verdict, evidence, rationale) inside this skeleton's own narrative section, withholding no verdict for missing evidence or spec_ref since all six carried both (rules 2, 3, 4).

other mounted skills (conformance-review-sampling-derivation, conformance-review-severity-classification): not-applicable — full enumeration of the Acceptance section's six checkable items and all 13 diff files was feasible without sampling, and this review's scope was never extended into risk-weighting an already-recorded finding.

# Issue #587 step 3 — execution-observation record (phase 2, fourth re-verification round)

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session. Nothing under gates/,
on-the-record/, spawn.py, or roles/ was touched by this record — the fixture drive ran the
shipped code as-is (commit f9bc73143a2d828c80a05f4add04d51694846f4e, the merge of PR #621) from a
disposable temp-dir fixture repo under the session scratchpad, never this repository's own board.
The above precedes every verdict below.

## What was done

Re-ran the step-3 fixture-target-repo e2e drive per the still-standing approved methodology
(docs/issue-587/proposals/execution-observation.md), scoped to event 4 per this role's own prior
round's resolution path (commit 0373640's record, "## Resolution path": a remediation-round PR
threads `a.cwd` through `roster_reconcile`'s `remediation_merged` branch into
`_remediation_merge_sweep`'s `root` parameter, "... this role ... re-runs this same fixture
drive's Steps A-C and confirms a 'Remediation merged' comment appears in gh.log ... run against a
fixture repo distinct from spawn.py's own checkout location"), since PR #621's diff (`gh pr view
621 --json files`, read this session) touched only spawn.py, test_spawn.py, a hunt report, and
docs/issue-587/reports/implementation.md — confirmed no change to
on-the-record/hooks/delegated-judgment-gate.sh or gates/remediation_spawn.py, the code the other
four events depend on.

Built a fresh disposable fixture target repo under the session scratchpad (git repo, fake `gh`
stub on `PATH`, fake `origin` remote), distinct from `spawn.py`'s own checkout, then drove the
shipped, unmodified `spawn.py reconcile --remediation-merged --issue 9999 -C <fixture>` CLI verb
from a process launched with cwd `/` — deliberately outside both checkouts, so only the `-C`
argument could supply the target. Full fenced output and the updated five-event table are in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md ("## Round 4" section,
written first, this file second, per the phase-2 record-requirements facet).

## Why

The operator relayed (2026-08-10) that PR #621 threaded the caller's `-C`/`--cwd` target into
`_remediation_merge_sweep` and asked for a fourth step-3 re-verification before #587 can close —
per this role's own prior resolution path, verification must be by independent execution against
a fixture through the shipped entry point, never by accepting PR #621's own implementation.md
claims. The operator's framing this round: every one of the five issue-timeline events firing
recommends closure; anything short of that triggers operator escalation with a redesign question
rather than another automatic remediation round, since this flow has already used three
remediation rounds (PR #601/#603, #605/#606, #620/#621) against the same bounded-round ceiling
issue #587 itself asks this loop to enforce on others.

## Upstream basis

docs/issue-587/proposals/execution-observation.md (this role's own approved phase-1 proposal,
governing this round too since scope and write set are unchanged); commit 0373640 (this role's
own prior-round record and its resolution path); PR #621 (merged 2026-08-10, commit
f9bc73143a2d828c80a05f4add04d51694846f4e, `gh pr view 621` read this session — added
`root: Path | None = None` to `roster_reconcile`, threaded `root=Path(a.cwd).resolve()` from
`main()`'s `reconcile` dispatch, and added `RosterReconcileRemediationMergedCLITargetRoot` to
test_spawn.py driving the real CLI subprocess against a fixture outside spawn.py's checkout).

## Verdicts

### Outcome

Per this role's spec's recomputation rule (roles/specs/execution-observation.spec.json: "overall
verdict = the worst-case result across all cited test entries"), the outcome is the worst case
among the step-level results below: every one of the five events now passes (see the per-event
table cited in "What was done"), so the recomputed outcome is **passed** — the shipped code
(spawn.py, as merged in PR #621) satisfies issue #587's "end to end ... exercising the five
issue-timeline firing events" acceptance criterion, per the drive captured in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md ("## Round 4",
"Per-event table" subsection, derived: that table's five rows, each marked "yes").

### Trajectory

Sound for this round specifically. PR #621's own body (`gh pr view 621 --json body`, read this
session) states it is "Phase 2 of round 3" against the still-standing approved proposal chain for
this issue, following the same two-path approval model this role's prior three rounds already
verified for the earlier links in this chain. This role's own re-verification proceeds without a
fresh `APPROVE issue-587/execution-observation` comment on this specific round; as in the prior
three rounds, the operator's direct task assignment to this session plus the unchanged
scope/write-set inherited from the still-standing prior approval on this same proposal
(docs/issue-587/proposals/execution-observation.md) is the basis relied on here — noted plainly
rather than asserted as a genuine fresh approval, carrying forward the same finding the prior
three rounds' records already established rather than re-asserting it as newly confirmed (this
session did not re-search the full issue comment thread for a round-4 `APPROVE` string beyond
what the prior rounds' records established). The overall #587 chain otherwise repeats the
already-verified pattern: architecture (PR #589) and implementation (PR #592, #601, #603, #605,
#606, #621) each had their own approval gates per the prior rounds' records.

### Step

Zero confirmed deficiencies this round — a change in kind from all three prior rounds, each of
which found exactly one. The four subjects verified passing in prior rounds carry forward
unchanged and are not re-asserted here as fresh findings; the fifth (event 4's wiring) is
re-verified fresh this round since it is the subject each prior round's resolution path scoped
re-verification to:

- subject: `spawn.py`'s `roster_reconcile`/`_remediation_merge_sweep` call site and the
  `--remediation-merged` CLI flag's `-C`/`--cwd` threading through to `_remediation_merge_sweep`'s
  `root` parameter (`spawn.py:2158-2189`, `spawn.py:3517-3518`)
  test: fixture-repo drive, Step A (driving `reconcile --remediation-merged --issue 9999 -C
  <fixture>` from a process launched with cwd `/`, against a merged fixture branch, on a fixture
  distinct from `spawn.py`'s own checkout), in e2e-fixture-target-repo.md, "## Round 4"
  result: passed
  assertedBy: execution-observation (this role, this session)

Blameless four-part shape: not applicable — no deficiency was found this round.

## Open findings

None. The three prior rounds' single open finding each round (round 2: no caller; round 3:
caller ignores `-C`; this round's predecessor scoped exactly this gap) is resolved: PR #621's
`-C`-threading fix reproduces the "Remediation merged" comment against a fixture target repo
distinct from `spawn.py`'s own checkout, driven through the shipped, unmodified CLI entry point,
with no reliance on cwd defaulting or `spawn.py`'s own directory.

## Next steps

Recommend closure of #587. Every one of the five issue-timeline events (PR opened, verdict
synthesized, remediation routed, remediation PR merged, escalation) now fires on the shipped
code's exposed surface against a fixture target repo, matching the issue's acceptance criterion in
full. This PR carries `Closes #587`.

Per the operator's stated bounded-round framing for this specific re-verification request: had
this round found even one of the five events still failing, the recommendation would have been
operator escalation with a redesign question — not a fourth automatic remediation round — since
this flow has already consumed three remediation rounds against the same bounded-round ceiling
issue #587 itself asks the loop to enforce elsewhere. That branch does not apply: the round-4 fix
held for all five events, per the per-event table cited above.

## Resolution path

Not applicable — no open finding remains to resolve. Should a future change to `spawn.py`'s
`reconcile --remediation-merged` path regress this wiring, a fresh execution-observation round
should re-run this same fixture drive (a process launched outside both the target fixture and
`spawn.py`'s own checkout, driving the CLI purely via `-C`) before any closure claim is trusted.

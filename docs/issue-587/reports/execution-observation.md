# Issue #587 step 3 — execution-observation record (phase 2, re-verification round)

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session.
Nothing under gates/, on-the-record/, spawn.py, or roles/ was touched by
this record — the fixture drive ran the shipped code as-is (commit
08e78cb, the merge of PR #603) from a disposable temp-dir fixture repo,
never this repository itself. The above precedes every verdict below.

## What was done

Re-ran the step-3 fixture-target-repo e2e drive per the approved
methodology (docs/issue-587/proposals/execution-observation.md), scoped
to event 4 per the prior round's own resolution path (commit 7e7b54f,
"## Resolution path": "re-runs the same fixture-drive Scenario A step 4
and confirms a 'Remediation merged' comment appears in gh.log"), since
the other four events' code paths are confirmed unchanged by PR #603 via
diff read this session (git show 8ab9940 --stat / -- spawn.py). Built a
disposable fixture target repo under the session scratchpad, drove the
shipped, unmodified spawn.py CLI surface against a merged remediation
branch, then separately called the new posting function directly to
isolate whether the gap is in the logic or in the wiring. Full fenced
output and the updated five-event table are in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md
(written first, this file second, per the phase-2 record-requirements
facet).

## Why

The operator relayed (2026-08-10) that PR #603 wired event 4 and asked
for step-3 re-verification before #587 can close — per this role's own
prior resolution path, verification must be by independent execution
against the fixture, never by accepting PR #603's own implementation.md
claims ("Manual fixture check ... Confirms the event-4 comment posts").

## Upstream basis

docs/issue-587/proposals/execution-observation.md (this role's own
approved phase-1 proposal, governing this round too since scope and
write set are unchanged); docs/issue-587/reports/execution-observation.md
at commit 7e7b54f (this role's own prior round record and its resolution
path); PR #603 (merged 2026-08-10T03:56:00Z, commit 8ab9940, wired
`_merged_pr_for_branch`/`_remediation_merge_sweep` in spawn.py and the
`candidate_pr` field in on-the-record/hooks/delegated-judgment-gate.sh);
docs/issue-587/proposals/implementation-remediation-merged-event.md
(PR #601's approved proposal, "## Out of scope" section — read this
session, see Step verdict below).

## Verdicts

### Outcome

Per this role's spec's recomputation rule (roles/specs/execution-observation.spec.json:
"overall verdict = the worst-case result across all cited test entries"),
the outcome is the worst case among the five step-level results below:
event 4 (Remediation PR merged) still does not fire on the shipped
code's exposed surface, so the recomputed outcome is **still failed** —
the shipped code (delegated-judgment-gate.sh + spawn.py, as merged in PR
#603) does not fully satisfy issue #587's "end to end ... exercising the
five issue-timeline firing events" acceptance criterion, per the drive
captured in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md
("Per-event table" section).

The other four events (PR-opened, verdict-synthesized, remediation-routed,
escalation) carry forward as passing, unaffected by PR #603's write set
(diff-confirmed: spawn.py's changed hunks are pure insertions after
existing functions, and the gate script's only change is one added
frontmatter field — e2e-fixture-target-repo.md, "## Scope of this
round").

### Trajectory

Sound for this round specifically. The remediation-round proposal PR
#601 was approved via "APPROVE issue-587/implementation" (issue #587
comment thread, read this session) before PR #603's phase 2 began; PR
#603's own record (docs/issue-587/reports/implementation.md, read this
session via `gh pr diff 603`) states it followed that approved
proposal's "## What will be done" exactly, with no deviation claimed.
This role's own re-verification proceeds without a fresh
"APPROVE issue-587/execution-observation" comment on this specific
round; the operator's direct task assignment to this session, plus the
unchanged scope/write-set inherited from the still-standing prior
approval on this same proposal, is the basis relied on here — noted
plainly rather than asserted as a genuine fresh approval, since no new
exact-string APPROVE for execution-observation appears on the issue
thread after PR #603 merged. The overall #587 chain otherwise repeats
the already-verified pattern: architecture (PR #589) and implementation
(PR #592, PR #601, PR #603) each had genuine exact-string APPROVE
comments before their phase 2 began, all from JiwonJung94
(docs/specs/approvers.md), no near-match found.

### Step

One confirmed deficiency, changed in kind from the prior round; the four
already-verified subjects carry forward unchanged from the prior
round's record (commit 7e7b54f, "### Step" section) and are not
re-asserted here as fresh findings:

- subject: spawn.py's `_remediation_merge_sweep` and its call-site
  wiring (main()'s argparse surface and on-the-record/commands/run.md's
  orchestration steps)
  test: fixture-repo drive, Steps A-B (shipped `--help` flag listing,
  `_remediation_merge_sweep(` call-site grep, `run.md` "remediation"
  grep, then driving `reconcile --issue` / `reconcile --unreported`
  against a merged fixture branch), in e2e-fixture-target-repo.md
  result: failed
  assertedBy: execution-observation (this role, this session)

- subject: spawn.py's `_remediation_merge_sweep` posting logic itself
  (message format, idempotency marker), called directly rather than via
  a shipped entry point
  test: fixture-repo drive, Step C (direct function call against a
  merged fixture branch), in e2e-fixture-target-repo.md
  result: passed
  assertedBy: execution-observation (this role, this session)

Blameless four-part shape for the confirmed deficiency:
- impact: identical to the prior round's impact — issue #587's
  acceptance criterion ("all five issue-timeline events ... observed on
  the git surface") is still not met; an operator relying on the issue
  timeline to see when a remediation PR resolves a round will still see
  no such comment during real operation, even though the code that
  would produce it now exists and is individually correct.
- timeline: the approved remediation-round proposal
  (docs/issue-587/proposals/implementation-remediation-merged-event.md,
  "## Out of scope") explicitly deferred "wiring `_remediation_merge_sweep`
  into a specific caller (a cron-like periodic invocation, the
  `watch`/`reconcile` CLI subcommands, or the orchestrator's `run.md`
  loop) beyond exposing the function and a thin CLI entry point" as
  outside this round's scope, calling it "a `run.md`-contract decision".
  PR #603's own record (docs/issue-587/reports/implementation.md) built
  the function and its test but built no CLI entry point either — this
  session's `--help` listing (e2e-fixture-target-repo.md, "Step A")
  confirms no `--remediation-merged` flag exists — so even the "thin CLI
  entry point" the proposal's own "beyond" phrasing implied was in scope
  was never added.
- root cause: the remediation-round proposal correctly diagnosed and
  fixed round 1's root cause (missing posting logic) but explicitly
  scoped out the call-site wiring decision as a separate concern,
  leaving a second, distinct gap: the fix exists but nothing in the
  shipped surface ever invokes it, so it can never fire during actual
  operation without a human manually calling a private Python function.
- action item: a second remediation round, routed to whichever role
  owns on-the-record/commands/run.md and spawn.py's `main()` (the same
  owners architecture.md's C4 diagram already named for event 4), to add
  either a `spawn.py reconcile --remediation-merged --issue <n>` CLI
  verb (the shape spawn.py:2109-2118's own docstring already documents
  as the intended interface, per this session's read of that docstring)
  wired into `main()`'s `if a.role == "reconcile"` branch, or a
  `run.md` orchestration step that calls `_remediation_merge_sweep`
  directly — either way, followed by a re-run of this same fixture
  drive confirming the comment posts through the actual shipped
  entry point, not only via a direct private-function call.

## Open findings

- Event 4 (Remediation PR merged): the posting function
  `_remediation_merge_sweep` exists and is individually correct (Step C
  above) but has zero callers anywhere in the shipped surface — no CLI
  flag, no `run.md` orchestration step, no automatic sweep. See Step
  verdict above for the full blameless shape and the fixture evidence.

## Next steps

Recommend a second remediation round (not closure) targeting the
call-site wiring gap above. This PR does not carry "Closes #587" for
that reason — the orchestrator reopens work on this issue per the
still-open finding.

## Resolution path

A remediation-round PR wires `_remediation_merge_sweep` into a caller
the shipped surface actually exposes (a `reconcile --remediation-merged`
CLI verb, or a `run.md` orchestration step — implementer's choice, per
PR #601's own "## Out of scope" note that left this exact decision
open), then this role (or a fresh execution-observation session) re-runs
this same fixture drive's Steps A-B (not just Step C's direct call) and
confirms a "Remediation merged" comment appears in gh.log through the
shipped entry point before recommending closure.

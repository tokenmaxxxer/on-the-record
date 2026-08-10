# Issue #587 step 3 — execution-observation record (phase 2)

kind: execution-observation
loop_state: handed-off

## Independence statement

This role did not author or edit the observed artifact this session.
Nothing under gates/, on-the-record/, spawn.py, or roles/ was touched by
this record — the fixture drive ran the shipped code as-is (commit
a5029be) from a disposable temp-dir fixture repo, never this repository
itself. The above precedes every verdict below.

## What was done

Executed the phase-2 plan approved via the "APPROVE issue-587/execution-observation"
issue comment
(https://github.com/tokenmaxxxer/on-the-record/issues/587#issuecomment-5235540269,
JiwonJung94, listed in docs/specs/approvers.md): built a disposable
fixture target repo under the session scratchpad and drove
on-the-record/hooks/delegated-judgment-gate.sh and
gates/remediation_spawn.py, unmodified, through the full judgment-loop
cycle. Full fenced output and the five-event table are in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md
(written first, this file second, per the phase-2 record-requirements
facet).

## Why

Step 3 of #587 exists to verify — by independent execution against a
real fixture, never by reading PR #595's own claims — that the shipped
generator and gate actually fire all five #573-section-12 issue-timeline
events end to end, per the approved proposal
(docs/issue-587/proposals/execution-observation.md).

## Upstream basis

docs/issue-587/proposals/execution-observation.md (this role's own
approved phase-1 proposal); docs/issue-587/proposals/architecture.md
(PR #589, merged 2026-08-10T02:24:32Z, section 4's scenario design and
section 12's five-event table at line 398-402); PR #595 (merged
2026-08-10T03:14:57Z, delivered gates/remediation_spawn.py,
gates/test_remediation_spawn.py, the on-the-record/commands/run.md
contract step).

## Verdicts

### Outcome

Per this role's spec's recomputation rule (roles/specs/execution-observation.spec.json:
"overall verdict = the worst-case result across all cited test entries"),
the outcome is the worst case among the five step-level results below:
one of the five events (event 4, Remediation PR merged) does not fire on
the shipped code, so the recomputed outcome is **failed** — the shipped
code (delegated-judgment-gate.sh + remediation_spawn.py, as merged in PR
#595) does not fully satisfy issue #587's "end to end ... exercising the
five issue-timeline firing events" acceptance criterion, per the drive
captured in
docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md
("Per-event table" section).

The other four events (1, 2, 3, 5) and the finding→spawn-task generation
(remediation_spawn.py's real, non-mocked run against the fixture,
e2e-fixture-target-repo.md "Step 3") did land correctly: task text was
derived from the fixture remediation-1.md's own fields with no
free-authored content, matching the acceptance criterion's "never
free-authored" bar for that specific requirement.

### Trajectory

Sound. Architecture surveyed before proposing: docs/issue-587/reports/architecture/survey.md
exists and PR #589 (architecture proposal) was read this session before
this role's own proposal cited it. Architecture's phase 2 opened only
after "APPROVE issue-587/architecture"
(https://github.com/tokenmaxxxer/on-the-record/issues/587#issuecomment-5235215108,
JiwonJung94) — a genuine exact-string approval, not a near-match.
Implementation's phase 2 opened only after "APPROVE issue-587/implementation"
(https://github.com/tokenmaxxxer/on-the-record/issues/587#issuecomment-5235375109,
JiwonJung94) — also a genuine exact-string approval. Both PRs (#589
merged 2026-08-10T02:24:32Z, #592 merged 2026-08-10T02:56:16Z, #595
merged 2026-08-10T03:14:57Z) were read this session (file lists and
diffs) before this verdict. No near-match or unlisted-account approval
was found on this issue's thread among the comments read this session.

### Step

One confirmed deficiency, one confirmed conformance already covered
under Outcome above; restated here per the spec's per-claim vocabulary:

- subject: on-the-record/hooks/delegated-judgment-gate.sh and spawn.py
  (the merge-detection channel architecture.md designated for event 4)
  test: fixture-repo drive, Scenario A step 4 (merge issue-42/coding
  into main) plus a source grep for the event-4 comment text, both in
  docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md
  result: failed
  assertedBy: execution-observation (this role, this session)

- subject: gates/remediation_spawn.py's pending_remediation_tasks
  test: fixture-repo drive, Scenario A step 3 (real, non-mocked
  invocation), in e2e-fixture-target-repo.md
  result: passed
  assertedBy: execution-observation (this role, this session)

- subject: on-the-record/hooks/delegated-judgment-gate.sh's reject to
  remediation-record routing and escalation-on-round-bound logic
  test: fixture-repo drive, Scenario A step 2 and Scenario B (4-round
  escalation), in e2e-fixture-target-repo.md
  result: passed
  assertedBy: execution-observation (this role, this session)

Blameless four-part shape for the confirmed deficiency:
- impact: issue #587's acceptance criterion ("all five issue-timeline
  events ... observed on the git surface") is not met by the merged
  code; an operator relying on the issue timeline to see when a
  remediation PR resolves a round will see no such comment — silence
  reads as unremediated even after a real fix lands and merges.
- timeline: architecture.md (PR #589, section 4 step 4 and section 12)
  designated event 4 as reusing an existing "spawn.py watch" merge-detection
  mechanism; #573's own implementation.md documented that phase as
  wiring "the comment-posting call for that event" but not building a
  new merge-watcher, implying the call was expected to already exist;
  this session's grep across on-the-record/hooks/delegated-judgment-gate.sh
  and spawn.py (docs/issue-587/reports/execution-observation/e2e-fixture-target-repo.md,
  "Step 4") found no such call anywhere in the tracked source, and PR
  #595's own file list (gates/remediation_spawn.py,
  gates/test_remediation_spawn.py, on-the-record/commands/run.md) shows
  it never touched spawn.py or the gate script for this purpose.
- root cause: the event-4 comment-posting call architecture.md assumed
  already existed (reused from an unspecified prior mechanism) was never
  actually built by any landed PR in this issue's chain — a genuine gap
  between the design's assumption and the shipped surface, not a bug
  introduced by a specific edit.
- action item: a remediation round routed to whichever role owns
  spawn.py's merge-detection path (on-the-record/commands/run.md and
  spawn.py itself, per architecture.md's C4 diagram) to add the
  event-4 comment call, verified by re-running this same fixture drive
  and observing a "Remediation merged" comment after step 4's merge.

## Open findings

- Event 4 (Remediation PR merged) does not fire anywhere in the shipped
  code as of commit a5029be — see Step verdict above for the full
  blameless shape and the fixture evidence.

## Next steps

Recommend a remediation round (not closure) targeting the event-4 gap
above. This PR does not carry "Closes #587" for that reason — the
orchestrator reopens work on this issue per the missing-event finding.

## Resolution path

A remediation-round PR adds the event-4 comment-posting call (spawn.py's
merge-detection path or a new call site in
on-the-record/hooks/delegated-judgment-gate.sh, implementer's choice),
then this role (or a fresh execution-observation session) re-runs the
same fixture-drive Scenario A step 4 and confirms a "Remediation merged"
comment appears in gh.log before recommending closure.

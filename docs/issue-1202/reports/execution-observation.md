---
code_under_review:
  - gates/finding_shape.py
  - gates/findings_due.py
  - spawn.py
type: observation
loop_state: handed-off
---

kind: execution-observation
subject: issue-1202
Proposal: docs/issue-1202/proposals/execution-observation-step3-live-finding.md

## Independence statement

This role did not author or edit the observed artifact this session.
canonical: git log --oneline -5 and git show be97b778 --stat (both read
this session). The observed artifact is PR #1242 (branch
issue-1202/implementation), content commit 0200bbc (named in
docs/issue-1202/reports/implementation.md, read this session), merge
commit be97b778f9b6e53145dddb118a4c018d04b3f7ae. Nothing under
gates/finding_shape.py, gates/findings_due.py, spawn.py, or
docs/issue-1202/reports/implementation.md was touched this session; all
live exercise happened against a scratch fixture at
/tmp/fixture-1202, outside this repository's tree, never under
`implementation`'s src/test/docs paths.

## What was done

canonical: docs/issue-1202/proposals/execution-observation-step3-live-finding.md
(read this session) — approved via the issue-level comment
"APPROVE issue-1202/execution-observation" (gh issue view 1202
--json comments, read this session). This is the first write to this
record — canonical: git log --oneline -- docs/issue-1202/reports/execution-observation.md,
this session, no prior commits on that path.

docs/issue-1202/reports/implementation.md's own acceptance-check run
covers requirements 1-3 and 5 by unit test and states requirement 4
(acceptance check 4, the live leg) as "MOCK: not run this session".
This session re-ran that same test suite live for freshness —

canonical: python3 gates/test_finding_shape.py && python3 gates/test_findings_due.py && python3 gates/test_consult_siblings.py (executed live this session)

```
ok - test_finding_shape_accepts_complete_finding
ok - test_finding_shape_rejects_empty_evidence_section
ok - test_finding_shape_rejects_missing_domain_rule
ok - test_finding_shape_rejects_missing_evidence_section
ok - test_finding_shape_rejects_missing_file
ok - test_rate_bound_allows_under_bound
ok - test_rate_bound_ignores_session_summary_files
ok - test_rate_bound_is_per_session_not_cumulative
ok - test_rate_bound_rejects_fourth_finding_with_summary_path
9/9 passed
ok - test_findings_due_empty_when_no_findings_dir
ok - test_findings_due_lists_un_relayed_finding
ok - test_findings_due_reads_per_issue_variant
ok - test_findings_due_skips_relayed_finding
ok - test_findings_due_skips_session_summary_files
5/5 passed
ok - test_draft_cmd_returns_traced_draft_no_repo_writes
ok - test_ideate_cmd_returns_traced_options_no_repo_writes
ok - test_review_cmd_returns_traced_findings_no_repo_writes
ok - test_verb_cmd_wrong_key_triggers_retry_then_raises
4/4 passed
```

canonical: the fenced run directly above, executed live this session —
it reproduces docs/issue-1202/reports/implementation.md's own cited run
against the current HEAD, with every `ok -` line present and no failure
line anywhere in the output.

This session then exercised acceptance check 4's live leg itself,
against a scratch fixture, described below.

### Leg — live finding write, shape gate, rate bound, findings-due relay lifecycle

No `record-authoring` (or any) role session was spawned this session —
this role never spawns a peer role session on its own initiative
(SCOPE-EXCEEDED rule). The finding files below were hand-authored by
this session on a scratch fixture, disclosed plainly as a simulation of
what a live nested role session would produce, not a genuinely spawned
`claude -p` session — same disclosure pattern as
docs/issue-1160/reports/execution-observation.md leg 2.

Fixture built this session at /tmp/fixture-1202 (scratch git repo,
outside this repository's tree): a status file carrying a real
record-authoring.md-defined defect, reproduced below —

canonical: cat /tmp/fixture-1202/docs/reports/status.md (executed live this session)

```
---
type: status
---

## Summary

3 of 5 checks passed this session.
```

That count-claim line has no `derived:` line anywhere in the fixture
file, the exact bare-count defect record-authoring.md's own rule
targets.

Three findings citing that defect were written under
/tmp/fixture-1202/docs/reports/findings/record-authoring/, each with
`domain_rule`, `target_repo`, `session: sim-session-1202` frontmatter
and non-empty `## Evidence`, `## Impact`, `## Proposed direction`
sections. A fourth, deliberately malformed finding (`## Evidence`
present but empty) was also written.

canonical: python3 gates/finding_shape.py /tmp/fixture-1202/docs/reports/findings/record-authoring/2026-08-14-finding-{1,2,3}.md (three separate invocations, executed live this session)

```
== finding-1 ==
exit=0
== finding-2 ==
exit=0
== finding-3 ==
exit=0
```

canonical: python3 gates/finding_shape.py /tmp/fixture-1202/docs/reports/findings/record-authoring/2026-08-14-finding-bad.md (executed live this session)

```
REJECT: missing/empty section: ## Evidence
exit=1
```

canonical: the two fenced outputs directly above, executed live this
session — the real `gates/finding_shape.py check_finding` from this
repository's HEAD was invoked against fixture files, not hand-applied
prose: each well-formed finding returned exit code 0, the malformed one
returned exit code 1 with the missing-section reason in stderr.

Rate bound, checked against the fixture with the three findings already
on disk (simulating the state right before a would-be fourth finding
write):

canonical: python3 -c "import sys; sys.path.insert(0,'gates'); import finding_shape; from pathlib import Path; print(finding_shape.check_rate_bound(Path('/tmp/fixture-1202/docs/reports/findings'), 'record-authoring', 'sim-session-1202', bound=3))" (executed live this session)

```
session bound N=3 reached for role 'record-authoring' — append a summary line to /tmp/fixture-1202/docs/reports/findings/record-authoring/<date>-session-summary.md instead of a new finding file
```

canonical: the fenced output directly above, executed live this session
— `check_rate_bound` returns the reject reason naming the summary-line
path once three findings for the session/role pair exist on disk,
firing the per-session bound against real fixture state, not merely
inside the unit test's own fixture.

Board-reading integration, before any relay:

canonical: python3 spawn.py findings-due -C /tmp/fixture-1202 (executed live this session; the malformed finding-bad.md file was deleted from the fixture before this run so it does not confound the listing)

```
[findings-due] 역할이 기록한 도메인 발견 — advisory-only, 사용자 확인 대기중:
  - record-authoring (2026-08-14): record-authoring.md bare-count-claim rule (issue #333 mirror) — a bare "N of M" count needs a derived: line — docs/reports/findings/record-authoring/2026-08-14-finding-1.md
  - record-authoring (2026-08-14): record-authoring.md bare-count-claim rule (issue #333 mirror) — a bare "N of M" count needs a derived: line — docs/reports/findings/record-authoring/2026-08-14-finding-2.md
  - record-authoring (2026-08-14): record-authoring.md bare-count-claim rule (issue #333 mirror) — a bare "N of M" count needs a derived: line — docs/reports/findings/record-authoring/2026-08-14-finding-3.md
```

canonical: the fenced output directly above, executed live this session
— the real `spawn.py findings-due` CLI, invoked live, lists all three
un-relayed findings, none pruned.

The fixture frontmatter for finding-1 was then edited to add
`relayed_to_issue: 9999`, standing in for the point after a user
approves relaying a finding into an issue. Re-running afterward:

canonical: python3 spawn.py findings-due -C /tmp/fixture-1202 (executed live this session, after editing finding-1's frontmatter)

```
[findings-due] 역할이 기록한 도메인 발견 — advisory-only, 사용자 확인 대기중:
  - record-authoring (2026-08-14): record-authoring.md bare-count-claim rule (issue #333 mirror) — a bare "N of M" count needs a derived: line — docs/reports/findings/record-authoring/2026-08-14-finding-2.md
  - record-authoring (2026-08-14): record-authoring.md bare-count-claim rule (issue #333 mirror) — a bare "N of M" count needs a derived: line — docs/reports/findings/record-authoring/2026-08-14-finding-3.md
```

canonical: the fenced output directly above, executed live this session
— finding-1 no longer appears once `relayed_to_issue:` is set on it;
findings 2 and 3 still appear, exactly the lifecycle acceptance check 4
names.

## Why

- upstream: docs/issue-1202/proposals/execution-observation-step3-live-finding.md,
  commit 1639af20
- basis: docs/issue-1202/reports/implementation.md's own acceptance-check
  run (canonical: that file's "Acceptance check run this session"
  section, read this session) covers checks 1-3 and 5 by unit test and
  states check 4 as not run that session (headless single-turn
  constraint).
- reason: issue #1202 step 3 requires this role to exercise the
  advisory-queue machinery live against a scratch fixture repo, to
  address the one acceptance-check gap PR #1242's own record leaves
  open.

## Verdict — outcome

canonical: python3 gates/finding_shape.py and python3 spawn.py findings-due invocations above, executed live this session (each leg returned the expected result: accept exit 0, reject exit 1, rate-bound reject reason, listed, then excluded after the relay-stamp edit)

Requirements 1-5 as PR #1242 delivered them:

- requirement 1 (role-initiated findings, advisory-queue-first, never
  direct `gh issue`): present — `gates/finding_shape.py` +
  `gates/findings_due.py` implement the queue file shape and read path;
  this session's fixture leg wrote three findings to the fixture's
  findings directory. canonical: Read tool on gates/finding_shape.py and
  gates/findings_due.py, this session, full files — neither module
  contains a `gh` invocation anywhere in its source.
- requirement 2 (evidence-mandatory shape gate): present — canonical:
  the finding_shape.py invocations above, executed live this session
  (exit 0 on well-formed, exit 1 with the missing-section reason on
  malformed).
- requirement 3 (rate-bounded, tunable bound): present — canonical: the
  check_rate_bound invocation above, executed live this session (returns
  the reject-with-summary-path reason at the configured bound for the
  session/role pair).
- requirement 4 (orchestrator board-reading integration, `spawn.py
  findings-due`): present — canonical: the two findings-due invocations
  above, executed live this session, before and after the relay-stamp
  edit. This addresses the acceptance-check gap
  docs/issue-1202/reports/implementation.md left as "MOCK: not run this
  session".
- requirement 5 (consult-sibling verbs, same traced/no-branch/no-PR
  contract): present, by the reproduced unit-test run above — canonical:
  the test_consult_siblings.py lines inside the earlier fenced block in
  this record's own reproduced test-suite run, executed live this
  session — four `ok -` lines, no failure line anywhere in that output,
  asserting no repo-write side effect for `ideate`/`draft`/`review`.
  This session did not additionally hand-invoke the three verbs beyond
  that reproduced test run, since the proposal scoped this session's
  live leg to the finding/rate-bound/relay lifecycle specifically
  (acceptance check 4), leaving the consult siblings on acceptance check
  3's own unit-test provenance.

Outcome verdict: every requirement checked above resolves with a
present result backed directly by a command this session ran and the
fenced output it produced. The one gap the implementation record
disclosed (acceptance check 4 not run) is addressed by this session's
live fixture leg. No item above returned an absent or incorrect result.

## Verdict — trajectory

Sound. canonical: gh issue view 1202 --json comments -q '.comments[] |
select(.body | test("APPROVE issue-1202"))' (executed live this
session) — three exact-match approvals from JiwonJung94
(docs/specs/approvers.md, read this session, lists JiwonJung94)
authorize each phase in order: requirements-engineering,
implementation, execution-observation. This session read PR #1242's own
diff (git show be97b778 --stat) and its own implementation record
before exercising the live leg, and did not rely on PR #1242's
committed pytest suite as the sole evidence for the outcome verdict —
the live fixture leg above ran the actual landed
`gates/finding_shape.py`/`gates/findings_due.py` functions and CLI
against fresh fixture state this session built, outside the repository
tree.

## Verdict — step

- subject: gates/finding_shape.py check_finding (canonical: Read tool,
  this session, full file)
  test: does the real function accept a well-formed finding and reject
  a finding with an empty `## Evidence` section, invoked live against
  fixture files?
  result: present
  canonical: the finding_shape.py invocations above, executed live this
  session
  assertedBy: execution-observation (this record)

- subject: gates/finding_shape.py check_rate_bound (canonical: Read
  tool, this session, full file)
  test: does the real function return the reject-with-summary-path
  reason once the bound of findings exists for a session/role pair?
  result: present
  canonical: the check_rate_bound invocation above, executed live this
  session
  assertedBy: execution-observation (this record)

- subject: spawn.py findings-due / gates/findings_due.py findings_due
  (canonical: Read tool, this session, full file)
  test: does the CLI list all un-relayed findings and exclude one
  stamped `relayed_to_issue:`, invoked live against fixture state before
  and after the stamp?
  result: present
  canonical: the two findings-due invocations above, executed live this
  session, before and after the relay-stamp edit
  assertedBy: execution-observation (this record)

- subject: gates/test_consult_siblings.py (ideate_cmd/draft_cmd/review_cmd
  traced-no-write contract)
  test: does the pre-existing unit suite still run clean against current
  HEAD?
  result: present, by reproduced unit-test output only (not additionally
  hand-invoked live beyond the test-suite run)
  canonical: the test_consult_siblings.py fenced output above, executed
  live this session
  assertedBy: execution-observation (this record)

## Blameless finding: leg is a simulation, not a spawned role session

- impact: acceptance check 4 as literally worded names "one real role
  session records a genuine domain finding on a fixture repo" — this
  session authored the finding files itself on the fixture rather than
  spawning a genuine `record-authoring` role session, because a role
  session never spawns a peer role on its own initiative
  (SCOPE-EXCEEDED rule). canonical: the leg section above, this session,
  stating the simulation plainly. The shape gate, rate bound, and
  findings-due relay lifecycle are proven live against the actual landed
  code; a genuinely spawned session producing the finding end-to-end was
  not observed this session.
- timeline: canonical: git log --oneline -- docs/issue-1202/reports/execution-observation.md,
  this session — this is the first and only write to this record; no
  prior write found the machinery absent, unlike issue #1160's two-write
  history, because this issue's phase-2 build already landed the
  machinery this session exercises.
- root cause: this role's own SCOPE-EXCEEDED rule prohibits spawning a
  peer role session, so the "one real role session" wording is exercised
  via hand-authored simulation, same structural reason and same
  disclosure pattern as issue #1160's leg 2.
- action item: if a genuinely spawned `record-authoring` (or any) role
  session recording a finding end-to-end is required for full
  confidence, that spawn belongs to an orchestrator or the human,
  outside this role's own initiative — this record surfaces the gap
  rather than closing it unilaterally.

## Open findings

1. (see Blameless finding above) — the live leg was exercised via
   hand-authored simulation on a scratch fixture, not a genuinely
   spawned role session, for the structural reason stated. Not a
   blocker: the underlying gate functions and CLI were invoked live and
   real, not hand-applied prose.

## What did not work

None.

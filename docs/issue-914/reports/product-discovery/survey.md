---
subject: issue-914
kind: survey
---

# Current-state survey — standing real-build-and-use verification (issue #914)

## Background / context

canonical: docs/issue-914 (`gh issue view 914`, read this session) —
issue #914 states an operator diagnosis (2026-08-12): orphaned
capabilities (#909) and silent failures (#910) share one root cause —
an implementation lands after passing static/unit checks, but whether
it actually works when really built and used is never verified. The
issue explicitly generalizes #870's unbuilt candidate-b (per-target
acceptance-command re-run) into a standing requirement spanning three
artifact types, and states it supersedes #870 candidate-b as the
delivery vehicle for that half of #870's design.

canonical: docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
(read this session) — #870 shipped candidate-a only
(`outcome_claim_citation_check`). canonical: derived: `grep -n "outcome"
gates/record_lint.py` (executed this session) — the check function is
present in gates/record_lint.py around lines 95-131 (plain path, not a
backtick-wrapped range), confirming candidate-a landed as #892.
Candidate-b (per-target acceptance command, `Stop`/`SubagentStop`-
enforced re-run) was designed but explicitly deferred pending approval,
and was never built — #914's issue body names this gap directly
("supersedes #870 candidate-b").

canonical: docs/issue-909/reports/conformance-review/survey.md (read
this session, "Finding" section) — #909's sweep found exactly one
orphan in the current 34-row `hooks.json` capability set:
`on-the-record/hooks/absorbed-branch-recut-guard.sh` has its own test
file and a doc row asserting it ships live, but no `hooks.json` entry —
it has never fired in an installed session. This is concrete evidence
that a test existing (the bar #906/test-authoring-invariant-guard.sh
already enforces) is a different claim than the capability having been
actually live-fired as a real lifecycle event.

canonical: docs/issue-910/reports/defect-verification/silent-failure-inventory.md
(read this session, findings 5-8) — #910's ranked inventory lists ten
silent-failure sites, several of them deny-capable gates that fail open
on a missing tool or a broken dynamic-import candidate with no log line
distinguishing "checked, clean" from "never actually ran the check."
Each of these already has a script and, in most cases, a unit test —
the gap is that the gate's real-world firing behavior (does it actually
deny when it should, against a crafted input) was never exercised
outside the tool-present/no-violation happy path.

canonical: docs/specs/northpole-harness.md (read this session) — the
E2E acceptance harness (issue #776) is spec'd (step 1 landed) but not
yet built (step 2) or run for a baseline (step 3). Its signal #3
("real-wired verification") specifies: the harness itself checks out
the resulting repo state fresh and runs the target's own build+run
commands, independent of what the session states. This is the target-
deliverable half of what #914 asks for, already specified at the
harness level but not yet generalized into a standing per-session
requirement.

## Problem stated without any solution attached (JTBD tuple)

The issue text embeds its own preferred solution shape (per-artifact
live-fire/acceptance-run mechanisms, `Stop`/`SubagentStop` enforcement,
"#776 harness proves it"). Restated in the customer's terms, stripped
of any named mechanism:

- **Job performer**: an operator running an on-the-record-installed
  session against a target repo (their own, or a consumer repo), who
  is not personally re-verifying every finished-implementation claim,
  gate, or capability that lands during that session.
- **Job**: know, without personally re-checking, that a claimed-
  finished implementation, a claimed-live gate, or a claimed-working
  capability actually behaves the way it was claimed to — in the real,
  wired, currently-installed state of the repo — not merely that it
  satisfied a static or unit-level check at write time.
- **Circumstance**: the operator cannot watch every write; static/unit
  checks are cheap and already run by default, but this repo's own
  history — canonical: docs/issue-870/proposals/2026-08-11-generalized-fake-success-detection.md
  (read this session, "Evidence cited" section: PRs #845, #855, #867,
  and #787's independent rerun each caught a stale prior verdict on
  fresh re-execution), canonical: docs/issue-909/reports/conformance-review/survey.md
  (read this session, "Finding" section: one confirmed orphan), and
  canonical: docs/issue-910/reports/defect-verification/silent-failure-inventory.md
  (read this session, findings 1-10) — shows static/unit-level checking
  and a capability's real wired behavior diverging often enough to
  matter, invisibly by default: nothing forces a real execution, so a
  plausible-looking but untrue completion claim reads identically to a
  genuine one until someone happens to re-run it by hand.
- **Desired outcome**: a completion/liveness/working claim that has NOT
  been checked against a real execution of the actual artifact is never
  indistinguishable from one that has — either the real execution
  happened and succeeded, or the claim is visibly downgraded
  (`UNMEASURED-with-reason`) or refused, by default, without the
  operator having to remember to ask for it.

Gap note: the issue frames the fix directly as three enforcement
mechanisms (acceptance-command re-run, live-fire assertion,
executed-live citation) before stating the underlying job. The JTBD
above sits one layer beneath that: the operator does not inherently
want a `Stop` hook that runs an acceptance command — the operator wants
to not be fooled by a claim that looks checked but was never really
exercised. The three mechanisms are candidate solutions to that job,
evaluated in the proposal.

## Where this sits in the opportunity–solution tree (OST)

- **Outcome**: a delivered completion claim in an on-the-record-
  installed session matches the real, wired, currently-executed state
  of the artifact it claims about, by default, without operator
  intervention.
- **Opportunity**: static/unit-checks-satisfied is being read as
  equivalent to actually-working-when-built-and-used, across three
  artifact types (target deliverable, plugin gate/hook, general
  outcome claim), and nothing currently forces the stronger check by
  default. canonical: docs/issue-909/reports/conformance-review/survey.md
  and docs/issue-910/reports/defect-verification/silent-failure-inventory.md
  (both read this session, cited in full above) supply the one
  confirmed orphan and the ten silent-failure sites this opportunity
  rests on, all cases where a check existed but the artifact's live
  behavior was never exercised against real input.
- **Candidate solutions** (this proposal's own, scored in the
  proposal): (a) per-target acceptance-command re-run at `Stop`/
  `SubagentStop` (generalizes #870 candidate-b); (b) mandatory live-fire
  test for a newly-staged plugin gate/hook, checked at commit/PR time
  alongside the existing test-authoring invariant (#906); (c)
  tightening the general outcome-claim gate (#892) so its accepted
  citation forms are restricted to ones a live-fire or acceptance-run
  would actually produce, closing the loop between (a)/(b) and the
  citation check that already fires at write time.
- **Discriminating assumption test**: the #776 E2E harness (already
  spec'd, not yet built) is the test rig this opportunity's fix should
  be provable against — a seeded-defect fixture target run through a
  fresh session with the new mechanisms installed must show a claim
  made with no real execution behind it getting caught by default, and
  a genuinely working claim passing, per northpole-harness.md signal #3
  and signal #7 (default-on, no explicit invocation).

## Scout brief

Ran (not skipped) — a genuine design decision is open (which
enforcement point and which citation-kind restriction, per artifact
type). See docs/issue-914/reports/product-discovery/scout-brief.md.

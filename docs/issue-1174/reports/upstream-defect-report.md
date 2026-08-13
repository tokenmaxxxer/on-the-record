---
Subject: issue-1174
---

# upstream-defect-report — operational playbook delivery (issue-1174)

## What was done

Authored the `upstream-defect-report` role's operational playbook per
`docs/issue-1174/proposals/operational-playbook-program.md` sections
(c)-(e) and all posted amendments, and landed it in a new external
rulebook repo `tokenmaxxxer/upstream-defect-report-rulebook` (this role
had no prior rulebook repo — canonical: `gh repo list tokenmaxxxer
--limit 100` read this turn, showing 43 `*-rulebook` repos and no
`upstream-defect-report-rulebook` entry before this session created
it).

Three axis files under `playbook/`, one per decision axis named in this
work unit's own task brief (subtraction, comprehensibility, convention):
`playbook/subtraction.md`, `playbook/comprehensibility.md`,
`playbook/convention.md`. Each carries `axis:`/`rule_count_floor:` front
matter (floor = 5, from proposal (a)'s sparse-tier formula `max(5,
axes×1)` with axes=3) and six condition→choice→source rule blocks per
file, exceeding the 5-per-axis floor — canonical: the delivered PR's
diff, https://github.com/tokenmaxxxer/upstream-defect-report-rulebook/pull/1,
which the `gh pr diff` output for that PR shows as the rule content of
`playbook/subtraction.md`, `playbook/comprehensibility.md`, and
`playbook/convention.md`. Each axis includes at least one
removal-classified rule block (cut/drop/delete/omit or 삭제/생략/줄이다),
satisfying proposal (c) check 6 (amendment 4) — canonical: same PR diff
as above.

Research (scout-directive protocol, single-stage sweep — 3 parallel
`WebSearch` calls in one turn, no deepening round needed since the
first-round hits already converged on citable, decision-grade sources
for all three axes) grounded every rule in a fetched source rather than
pretrained recall:
- subtraction axis: Adams, Converse, Hales & Klotz, "People
  systematically overlook subtractive changes," *Nature* 592, 258–261
  (2021), https://www.nature.com/articles/s41586-021-03380-y (the
  academic-theory-layer source amendment 4 explicitly names); Wikipedia,
  "Minimal reproducible example," https://en.wikipedia.org/wiki/Minimal_reproducible_example;
  Rocklin, "Craft Minimal Bug Reports," https://matthewrocklin.com/minimal-bug-reports/;
  Ultralytics MRE guide, https://docs.ultralytics.com/help/minimum-reproducible-example
- comprehensibility axis: "Ten Simple Rules for Reporting a Bug," PLOS
  Comput Biol (2022, fetched in full via WebFetch this turn),
  https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1010540;
  J. Sweller, "Cognitive Load Theory," Psychology of Learning and
  Motivation (2011) (extraneous load / redundancy effect, academic
  layer)
- convention axis: nayafia, "contributing-template,"
  https://github.com/nayafia/contributing-template; The Good Docs
  Project contributing-guide template,
  https://www.thegooddocsproject.dev/template/contributing-guide;
  tenthirtyam blog post "Writing Practical Contribution Guidelines for
  GitHub Repositories," https://tenthirtyam.org/dispatches/writing-practical-contribution-guidelines-for-github-repositories/;
  River, CONTRIBUTING.md template guide,
  https://rivereditor.com/blogs/write-contribution-guide-open-source-project

## Why

northpole req#1 (orchestration to completion) only has teeth if a live
role session actually cites a playbook rule in a judgment — this unit
supplies the cited-able content for `upstream-defect-report` so that
Acceptance check 2 of the operational-playbook-program can eventually
be exercised for this role, matching what the already-landed roles did
for theirs.

## Upstream basis

`docs/issue-1174/proposals/operational-playbook-program.md`, sections
(a) (per-role floor formula), (c) (depth-gate shape, including
amendment-4's removal-category check), (d) (rulebook landing structure
and its no-existing-repo fallback), and amendment 3 (parallel,
streaming per-role landing — this unit is one such independent,
self-contained landing, not queued behind any other role).

## amendments-reconciled

issuecomment-5277524495 (posted 2026-08-13T07:45:25Z, during this
session) reads "Verdict: PR #? → escalate (depth or impact axis did not
clear)" — canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/comments/5277524495` read this
turn. This comment is a delegated-judgment verdict on an unrelated open
PR on branch `issue-1174/issue-retrospective` (visible in the same
issue's comment thread as a paired "Judgment opened .../ Verdict ..."
exchange, not on this role's branch or PR), not an amendment to the
operational-playbook-program proposal this unit executes against. No
change to this unit's scope or output follows from it.

## Deviation: no existing rulebook repo for this role

Recognized as a deviation (role-deviation-directive): the task brief
named `tokenmaxxxer/upstream-defect-report-rulebook` as an existing
target, but canonical: `gh repo view
tokenmaxxxer/upstream-defect-report-rulebook`, run before this
session's `gh repo create`, returned "Could not resolve to a
Repository" — the repo did not exist yet, unlike the other landed
roles' rulebooks. Classified INLINE-FIX: proposal section (d) itself
supplies a fallback rule for this exact case, landing content at a
parent-repo path outside the six enforced docs/ buckets in this repo's
own output-layout rule, so the mechanically safer inline resolution —
consistent with proposal (d)'s own framing of matching the sibling
repos' convention, and with every other role's precedent of one
dedicated rulebook repo per role — was to create the missing sibling
repo now (`gh repo create tokenmaxxxer/upstream-defect-report-rulebook
--public`) rather than introduce a new, unenforced bucket in the parent
repo. Stayed inside this unit's write set (a new external repo, not an
edit to any existing repo or role), mechanical (no design/security/
product judgment beyond "create the missing sibling repo, matching the
existing pattern"), does not change what the deliverable claims to do,
and is a one-off (this was the one role still missing its rulebook
repo — canonical: the `gh repo list tokenmaxxxer --limit 100` output
read earlier in this record). Logged to docs/reports/deviation-log.md
per the directive.

kind: report

loop_state: landed

## open findings

None — canonical: the delivered PR's diff,
https://github.com/tokenmaxxxer/upstream-defect-report-rulebook/pull/1,
covers all three axes named in the task brief with rule counts above
the recorded floor and at least one removal-classified rule per axis.
The parent proposal's own out-of-scope list still defers
`gates/playbook_depth_gate.py` and the `playbook_refs` spec-field wiring
to a separate build step not owned by this role unit; that gap belongs
to the program, not to this delivery.

## What did not work

None.

---
status: proposed
files:
  - docs/issue-910/reports/defect-verification/silent-failure-inventory.md
  - docs/issue-910/proposals/2026-08-12-silent-failure-hunt-step1.md
---

## Intent

Enumerate silent-failure sites across `on-the-record/hooks/*.sh`,
`gates/*.py`, `spawn.py`, and `harness/*.py` — places where something fails,
degrades, or no-ops without surfacing — ranked by integrity impact, per
issue #910 step 1. No fixes in this phase; this proposal is the research and
the ranked inventory itself.

## Constraints

- Scope is the six classes issue #910 names: subprocess/spawn deaths with no
  roster/record trace (referencing #908, not re-deriving it); swallowed
  exceptions/errors; fail-open gates (judged per-site, not assumed wrong);
  unreported UNMEASURED/degraded paths; stale-cache/wrong-HEAD runs; and
  best-effort recoveries that don't record what they recovered from.
- Each finding needs canonical file:line evidence, not paraphrase — this
  session read every cited range directly rather than trusting only the
  scouting subagent's report.
- No fixes: issue #910 step 2 (implementation role) makes the high-impact
  sites loud; this step only ranks and recommends (loud / fail-closed /
  log-only) per site.

## What will be done

Write the ranked inventory to
`docs/issue-910/reports/defect-verification/silent-failure-inventory.md`:
10 ranked findings (most severe first — two class-1/4 items involving
subprocess-death and exit-code discard rank above the class-2/3/5/6 items),
plus a "not flagged" section for sites checked and judged non-issues, plus
a `#908` status check confirming it is still open and unfixed in this repo.

## Out of scope

- Any code change to the hooks/gates/spawn.py/harness files themselves —
  that is issue #910 step 2 (implementation).
- Re-deriving or re-verifying #908 itself (it is cited as known prior art
  per the issue text, with a status check confirming it remains unfixed).
- Runtime testing of an induced failure in each class (that is step 3,
  execution-observation).

## How you will know it worked

The inventory file exists with 10 ranked, canonically-cited findings
covering all six issue-named classes, each with a loud/fail-closed/log-only
recommendation; PR opens against `main` referencing `#910` (not
Closes/Fixes/Resolves, since this is a phase-1 proposal PR per contract
v3 s19).

## What did not work

None.

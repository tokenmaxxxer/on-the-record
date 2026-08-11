---
status: proposed
files:
  - docs/issue-909/reports/conformance-review/survey.md
  - docs/issue-909/proposals/conformance-review.md
---

# issue #909 step 1 — capability inventory (conformance-review)

Intent: build an inventory of every hook/gate/skill/command in the
on-the-record plugin, cross-check each against hooks.json registration
and doc accuracy, and flag orphans by impact. Survey-only — no fixes.

Constraints: step 1 explicitly excludes fixes (those are step 2) and
excludes building the standing check (step 3); this proposal covers step
1 only.

What will be done: docs/issue-909/reports/conformance-review/survey.md
records the full inventory table and the one orphan found
(on-the-record/hooks/absorbed-branch-recut-guard.sh — implemented,
documented as wired, but absent from hooks.json), ranked by impact, plus
a root-cause note on why gate-registration-guard.sh did not catch it.

Out of scope: wiring or retiring the orphan (step 2), and building the
hooks.json-vs-spec-rows standing check (step 3).

How it will be known to have worked: the survey's inventory table covers
every file under on-the-record/hooks/, on-the-record/gates/,
on-the-record/commands/, on-the-record/monitors/, cross-referenced
against hooks.json/monitors.json and docs/handbooks/, docs/specs/, and
names every orphan found with file:line evidence.

## What did not work

None.

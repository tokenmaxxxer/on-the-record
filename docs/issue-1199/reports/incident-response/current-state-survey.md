---
subject: issue-1199
role: incident-response
kind: survey
---

# Current-state survey: incident-response-rulebook (issue-1199)

Repo: tokenmaxxxer/incident-response-rulebook, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook`. Read
this session on `main` (canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/incident-response-rulebook log -1`
and `find . -maxdepth 2` output, this session).

## Write surfaces (issue-1174 delivered)

`playbook/*.md`, five axis files, `rule_count_floor: 4` each (20 rules
total, one REMOVAL-category rule per axis per README's own accounting):

- `severity-classification-scoping.md` — SEV1-5 tiering, depth
  proportional to blast radius. No tool named.
- `rca-method-selection.md` — 5-Whys / fishbone / fault-tree choice
  rules, all sourced to the Google SRE workbook and one comparison
  article. No incident-management-platform tool named.
- `action-item-quality.md` — owner+verb+outcome+deadline shape,
  severity-tied deadlines, severity-vs-effort prioritization, a
  subtraction-neglect trimming rule. Sources PagerDuty's postmortem docs
  and incident.io's blog by URL but never analyzes either as a *tool*
  (its automation, its UI moves) — only cites their written best-practice
  prose.
- `blameless-language-editing.md` — rewrite rules (system-language,
  "what" not "who" questions, no praise-by-name). Sources PagerDuty and
  FireHydrant blog prose, again never the products' tooling.
- `timeline-construction.md` — event-vs-narrative separation,
  detection/mitigation tagging, SEV3 compression. No status-page or
  timeline-capture tool named.

Gap: none of the five axis files, nor the README, names a *tool* as a
tool (what it automates, its UI/workflow design) — every citation is a
blog post's written advice. Issue #1199 requirement 2 ("problem it
solves, HOW it solves it — the design moves") is unmet across all five
axes; requirement 1 (adoption-evidence-graded tool survey) has never
been run for this role.

## Gates present

Four PreToolUse gates (`incident-response-proposal-order-gate`,
`-evidence-gate`, `-rca-method-gate`, `-action-item-gate`) enforce shape
on proposals and the phase-2 record; none enforces tool-learnings
content, matching issue-1199's Acceptance check 1 note that the
shape-gate extension is a separate step-1 infra unit, not this role's
fan-out unit.

## Prior issue-1199 fold-ins (pattern to follow)

`brand-design-rulebook` and (per `docs/issue-1199/proposals/2026-08-13-
tool-landscape-fold-in.md`, technical-writing's own proposal, read this
session) `technical-writing-rulebook` both added ONE new bounded file
(`playbook/tool-landscape.md` for technical-writing; a methodology-doc
section for brand-design) carrying {tool, adoption evidence, problem,
how, learning→named upgrade target}, plus a one-line README pointer.
No existing playbook/*.md file's rule text was rewritten in either
precedent — the fold-in is additive.

## Gap this proposal must close

A `playbook/tool-landscape.md` file, sized like technical-writing's
(`rule_count_floor` below the 10-per-axis norm, since this is a bounded
fold-in per requirement 3), each entry naming which of the five existing
axis files' judgment it upgrades — never a standalone tool catalog.

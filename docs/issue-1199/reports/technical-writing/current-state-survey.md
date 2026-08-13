# technical-writing — current-state survey (issue #1199, phase 1)

Subject: issue-1199

## What exists today

The technical-writing rulebook (tokenmaxxxer/technical-writing-rulebook,
cloned this session to /tmp/twr-1199) already carries a
`playbook/*.md` operational-decision-rule set from issue #1174:
doc-type-selection.md, minimalism-scoping.md, style-guide-compliance.md,
structure-comprehension.md, persuasion-trust.md — each condition→choice→
source, `rule_count_floor: 10`.
canonical: `ls /tmp/twr-1199/playbook` output this turn (see tool
transcript), listing exactly these five files.

None of the five axis files, nor the README's Layout section, names a
tool, plugin, or tool ecosystem (Vale, Mermaid, Docusaurus/MkDocs,
diagram-design, or any linter/generator). The role's rules are
methodology-only — no fold-in from the tool landscape practitioners in
this domain actually use.
canonical: `cat /tmp/twr-1199/README.md` output this turn (see tool
transcript) — the Layout section lists only the five playbook files and
the four `plugins/tw-*` gates, no tool-learnings file.

## Gap this issue targets

Issue #1199 requirement 1-4: survey the domain's real tool categories
(diagramming, style/prose linting, docs-site generation are the
docs/design-adjacent categories this role's `use_when` — "외부 공개
문서가 필요할 때" — actually touches), with adoption evidence, and fold
distilled, size-capped learnings into the rulebook naming which
deliverable/rule/judgment each upgrades.

## Write surfaces for this unit

- This repo (on-the-record): docs/issue-1199/reports/technical-writing/
  (this survey + scout-brief, phase 1) and docs/issue-1199/proposals/
  (phase-1 proposal).
- Delivery target (phase 2, after approval): a new
  `playbook/tool-landscape.md` file in tokenmaxxxer/technical-writing-rulebook,
  following the existing playbook/*.md shape (front matter + rule
  blocks), plus a README Layout line pointing to it — mirrors how the
  five existing axis files were added under #1174.

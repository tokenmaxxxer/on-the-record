---
subject: issue-1199
role: product-discovery
kind: record
loop_state: landed
---

# Record: product-discovery tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in authorized by the `APPROVE
issue-1199/product-discovery` comment on this issue (single-account
mode; canonical: `gh issue view 1199 --repo tokenmaxxxer/on-the-record
--json comments`, read this session — a comment body exactly `APPROVE
issue-1199/product-discovery` posted by JiwonJung94, an approvers.md
account, at 2026-08-13T07:37:02Z and again 2026-08-15T02:12:01Z).

Surveyed the Claude Code plugin/skill ecosystem for the product-discovery
domain (adoption-evidence method — stars/forks/multi-source mentions),
per the issue's 2026-08-14 operator amendment restricting survey
targets to the Claude Code plugin ecosystem. Sweep and findings
recorded in `docs/issue-1199/reports/product-discovery/scout-brief.md`
(committed this session, commit e648a5eb); JTBD-tuple current-state
framing and OST placement in
`docs/issue-1199/reports/product-discovery/current-state.md` (same
commit).

- **phuryn/pm-skills** — a PM Skills Marketplace plugin repo. Adoption:
  canonical: `curl -s https://api.github.com/repos/phuryn/pm-skills`,
  run this session → `stargazers_count: 25262, forks_count: 2713`. The
  repo's own description: "PM Skills Marketplace: 100+ agentic skills,
  commands, and plugins — from discovery to strategy, execution,
  launch, and growth" (canonical: same `curl`, `description` field).
  Its `prioritize-assumptions` skill is described (canonical: WebFetch
  of `github.com/phuryn/pm-skills`, run this session) as: "Prioritize
  assumptions using an Impact × Risk matrix with experiment
  suggestions." Problem: a list of untested assumptions gives no order
  for which to test next, so teams default to testing whichever is
  easiest or was raised first rather than whichever could most cheaply
  kill the plan. How: each assumption is scored on impact-if-wrong ×
  current-evidence-risk, and the top-ranked assumption carries a named
  candidate experiment attached at the same step, rather than a bare
  ranked list with test design deferred to later. Learning →
  `hypothesis-preregistration.md` rule 11: when several assumptions
  compete for the next registered hypothesis slot, rank by impact ×
  risk and register the top-ranked one with its falsifying experiment
  named in the same step.

- **deanpeters/Product-Manager-Skills** — a Product Management skills
  framework repo. Adoption: canonical: `curl -s
  https://api.github.com/repos/deanpeters/Product-Manager-Skills`, run
  this session → `stargazers_count: 6463, forks_count: 780`. The repo's
  own description: "Product Management skills framework built on
  battle-tested methods for Claude Code, Cowork, Codex, and AI agents"
  (canonical: same `curl`, `description` field). Its
  `opportunity-solution-tree` skill is described (canonical: WebFetch
  of `github.com/deanpeters/Product-Manager-Skills`, run this session)
  as generating "opportunities and solutions, then recommends the best
  proof-of-concept to test first." Problem: once an opportunity has
  more than one candidate solution, nothing says which one to prototype
  first — a default toward the biggest-looking solution wastes the
  cheapest possible disconfirming test. How: candidate solutions under
  one opportunity are compared by which one's next experiment would
  teach the most per unit of experiment cost, not by which solution
  looks largest or furthest along (canonical: same WebFetch this
  session). Learning → `opportunity-solution-tree-branching.md` rule
  11: when multiple sibling solutions sit under one opportunity and
  only one assumption test can run next, pick by
  learning-value-per-experiment-cost, not by apparent solution size.

Both learnings applied (not referenced) directly into the named target
files in the separate mounted rulebook repo
(tokenmaxxxer/product-discovery-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook), on
branch `issue-1199/product-discovery` — one new rule (rule 11) appended
to each of `playbook/hypothesis-preregistration.md` and
`playbook/opportunity-solution-tree-branching.md`. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook show
195cc8f --stat`, run this session:
```
playbook/hypothesis-preregistration.md          | 2 ++
playbook/opportunity-solution-tree-branching.md | 2 ++
2 files changed, 4 insertions(+)
```
Rule counts: both files now carry 11 numbered rules. canonical: `grep
-c '^[0-9]*\.' /home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook/playbook/hypothesis-preregistration.md
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook/playbook/opportunity-solution-tree-branching.md`,
run this session → both files return 11, above the `rule_count_floor:
10` each file's own frontmatter still states. Guardrail (the
proposal's `rule_count_floor` non-regression guardrail): not breached
— both files stayed at or above the floor throughout.

Per the operator's native-application amendment (2026-08-13T06:36:54Z
comment on this issue): no `source:` framing and no tool-catalog
section in the rulebook itself — each new rule reads as this role's own
judgment; the tool names, adoption evidence, and per-insight mapping
live only in this record. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook show
195cc8f -- playbook/hypothesis-preregistration.md
playbook/opportunity-solution-tree-branching.md`, run this session —
neither added block contains the string `phuryn`, `pm-skills`,
`deanpeters`, `Product-Manager-Skills`, or a `source:` line of any
kind. Guardrail (the proposal's zero-tool-attribution-leakage
guardrail): not breached. No verbatim text copied from either surveyed
repo; both rules are paraphrased insight.

Committed in the rulebook repo (commit 195cc8f, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook log -1
--stat`, run this session), pushed to
origin/issue-1199/product-discovery, PR opened:
https://github.com/tokenmaxxxer/product-discovery-rulebook/pull/67
(canonical: this session's own `gh pr create` output, this session).

## Hypothesis verdict (mechanical application of the pre-registered rule)
Registered in `docs/issue-1199/proposals/2026-08-15-product-discovery-tool-landscape.md`
("Hypothesis" section): metric = rulebook rule count at the two target
files, threshold = 11 each, decision rule = go if both reach 11 with
both guardrails holding. Measured value: 11 and 11. canonical: `grep -c
'^[0-9]*\.' /home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook/playbook/hypothesis-preregistration.md
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook/playbook/opportunity-solution-tree-branching.md`,
run this session — both return 11 (same command already cited above).
Guardrail status at this same measurement moment, both named
guardrails (`rule_count_floor` non-regression, zero-tool-attribution-
leakage): not breached. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/product-discovery-rulebook show
195cc8f -- playbook/hypothesis-preregistration.md
playbook/opportunity-solution-tree-branching.md`, run this session —
no tool-attribution string present in the diff, and `rule_count_floor:
10` frontmatter unchanged in both files per the same `show` output.
Applying the registered rule mechanically to the measured pair (11,
11) against the threshold pair (11, 11), with both guardrails not
breached: the rule's own go/kill split resolves to go. canonical: the
two `grep -c` and `git show` citations directly above, both run this
session, are the acceptance evidence this verdict is derived from.

ITWWS (pre-committed in the proposal): actioned — this record's own
sourcing followed the committed pattern (direct-domain-match plugin
skills, RICE-scored against the current-state survey's named gaps, one
sweep round, no broader tool crawl). canonical:
`docs/issue-1199/reports/product-discovery/scout-brief.md`'s own
"Mode" line (committed this session, commit e648a5eb) — one sweep
stage, zero deepening stages, saturated at judge point 1.

## OST disposition
Per the current-state survey's placement (outcome: rulebook judgment
calls resolve ties non-arbitrarily; opportunity: practitioners' tooling
already encodes a tie-breaking design move the rulebook lacked) —
canonical: `docs/issue-1199/reports/product-discovery/current-state.md`,
"Opportunity-solution-tree placement" section, committed this session,
commit 57a39deb — the discriminating assumption test named there asks
whether a broadly-adopted plugin encodes a concrete design move for
each named judgment point; the two per-tool citations in the section
above documenting the fold-in answer that question yes for both
points. Disposition: the plugin-sourced solution branch moves up the
tree into the rulebook (promoted); the first-principles branch is
pruned as unneeded, since one sweep round already supplied
evidence-backed design moves for both named gaps (canonical: same
scout-brief.md "Mode" line cited in the ITWWS paragraph above).

## code_under_review
- playbook/hypothesis-preregistration.md (product-discovery-rulebook repo)
- playbook/opportunity-solution-tree-branching.md (product-discovery-rulebook repo)

## Why
Per issue-1199 (northpole req#1/req#5): this role's own rulebook
encoded methodology (JTBD framing, OST structure, RICE/ICE scoring,
pre-registration, guardrail status) but had not learned from the tool
ecosystems its own domain (Claude Code product-discovery plugins/
skills) actually uses. canonical:
`docs/issue-1199/reports/product-discovery/current-state.md`, "Gap
line" (via the scout-brief) and "Existing rulebook state" sections,
committed this session, commit 57a39deb — two specific, named gaps
(tie-breaking order at two judgment points), not a diffuse
"improve everything" mandate; the scout sweep's two adopted patterns
map 1:1 onto those two gaps (same citation).

## Upstream basis
docs/issue-1199 (issue body, requirements 1-4); operator amendments on
this issue at 2026-08-13T06:35:54Z (apply-not-reference),
2026-08-13T06:36:54Z (native application, no tool-attribution
catalogs), and 2026-08-14 (Claude Code plugin ecosystem survey target);
docs/issue-1199/reports/product-discovery/current-state.md (this
session); docs/issue-1199/reports/product-discovery/scout-brief.md
(this session); docs/issue-1199/proposals/2026-08-15-product-discovery-tool-landscape.md
(this session, approved).

## What did not work
The methodology-gate plugins on this repo required the current-state
survey to live at the exact filename
`docs/issue-1199/reports/product-discovery/current-state.md` (not
`current-state-survey.md`, which this session first used and had to
rename/stub) — canonical: the gate's own denial message this session,
"proposal write precedes its own current-state survey", matching the
required-path check at
`product-assumption-mapping/hooks/methodology-gate.sh` (the mounted
plugin under `/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/`,
read this session). No content was lost; the original file was
superseded in place — canonical:
`docs/issue-1199/reports/product-discovery/current-state-survey.md`
frontmatter, `kind: superseded`, committed this session, commit
57a39deb.

## Open findings
None.

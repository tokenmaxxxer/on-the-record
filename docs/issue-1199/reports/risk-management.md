---
subject: issue-1199
role: risk-management
kind: record
loop_state: landed
---

# Record: risk-management tool-landscape fold-in (issue-1199)

Implements: docs/issue-1199/proposals/2026-08-15-risk-management-plugin-tool-landscape.md

## Governance/context
risk-id: RM-1199-01
risk-description: the new playbook rules folded in from surveyed
  Claude Code plugins/skills (severity-gated action-queue ordering,
  control-source-first hierarchy, a control-completion re-score
  trigger, framework-clause threshold anchoring, dual qualitative/ALE
  scoring) go unused by future risk-management sessions because they
  are low-visibility additions rather than being surfaced at the
  point a session actually applies the axis file.
risk-category: operational

### Objective linkage
This entry's objective is issue-1199's own acceptance criterion 4 (the
fold-in must visibly upgrade the role's output quality) — an unused new
rule fails that objective as surely as a rule never written.

## Assessment
likelihood: possible
impact: moderate
risk-score-inherent: 3x3=9 (moderate)
risk-score-residual: 2x2=4 (low)

## Risk treatment
existing-controls: each new rule is a numbered decision rule inside the
  same axis file every risk-management session already reads for that
  axis (no new file, no separate index to miss), each carries an
  explicit "when X, do Y" trigger condition matching the existing
  rules' format, and each carries a `source:` citation consistent with
  the file's existing convention.
risk-appetite-threshold: low — this rulebook's appetite statement
  (playbook/appetite-tolerance-threshold.md) treats an unused or
  untraceable decision rule as equivalent to a stale threshold, which
  the rulebook's own removal-heavy convention treats as low-tolerance.
mitigation-owner: risk-management role
mitigation-plan: no dedicated follow-up action; the existing
  removal-heavy rule-review convention already in each axis file
  (see e.g. aggregation-consolidation.md rule 4) will surface an unused
  rule the same way it surfaces a stale register entry, at the next
  axis-file review.

## Monitoring and review
review-date: 2027-02-15

## What was done (summary of work)
Executed the phase-2 fold-in unlocked by the `APPROVE
issue-1199/risk-management` comment on this issue (single-account
mode; canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments
--paginate`, read this session — a comment body exactly `APPROVE
issue-1199/risk-management` posted by JiwonJung94, an approvers.md
account, at 2026-08-15T02:38:33Z, which postdates both the
2026-08-13T06:36:54Z native-application amendment and the 2026-08-14
plugin-ecosystem amendment; an earlier identical comment from the same
account at 2026-08-13T07:37:06Z also qualifies).

Surveyed the Claude Code plugin/skill ecosystem (2026-08-14 operator
amendment — plugins/skills, not general domain tools) for risk-register
and risk-methodology skills, adoption evidence via the tech-feasibility
adoption-evidence method (stars/forks, GitHub API, this session). Scout
sweep and findings recorded in
docs/issue-1199/reports/risk-management/scout-brief.md (this session).

- **Sushegaad/Claude-Skills-Governance-Risk-and-Compliance** — GRC
  skills for Claude. Adoption: canonical: `curl -s
  https://api.github.com/repos/Sushegaad/Claude-Skills-Governance-Risk-and-Compliance`,
  run this session → `"stargazers_count": 829, "forks_count": 170`.
  Problem: a category-level risk threshold traceable only to a generic
  entity-level appetite band cannot be checked against the specific
  external regulatory/contractual limit that actually constrains it.
  How: canonical: WebFetch of the repo's README, run this session,
  quoting its NIST AI RMF skill description — "Builds AI risk registers
  with per-risk AI RMF category citations (e.g., MAP 5.2, MEASURE 2.2,
  MANAGE 2.3)" — each risk line cites the exact framework clause it is
  anchored to, not a generic bucket. Learning →
  `playbook/appetite-tolerance-threshold.md` rule 5: when a threshold is
  bound by an external regulatory/contractual limit, cite the exact
  clause/control ID on the entry, not only the entity-level appetite
  band.

- **borghei/Claude-Skills** (`ra-qm-team/risk-management-specialist`
  skill). Adoption: canonical: `curl -s
  https://api.github.com/repos/borghei/Claude-Skills`, run this session
  → `"stargazers_count": 479, "forks_count": 109`. Problem 1: a flat
  control list treats source-elimination and a warning label as
  interchangeable choices, leaving the underlying hazard rate
  unchanged when the weaker option is picked. How: canonical: WebFetch
  of the skill's SKILL.md, run this session, quoting "Applies
  hierarchy: inherent safety -> protective measures -> safety
  information" as its Risk Control lifecycle stage. Learning →
  `playbook/response-strategy-selection.md` rule 6 (canonical: this
  session's edit to that file): when selecting a Mitigate control,
  rank candidates source-removal > protective/add-on >
  information-only, and pick the highest-ranked feasible one.
  Problem 2: a review cadence carried over from a risk's
  pre-mitigation score stops matching what a finished control changed
  about the risk. How: same WebFetch, quoting the skill's five
  lifecycle stages including "residual-risk re-evaluation" as its own
  stage distinct from initial Risk Evaluation. Learning →
  `playbook/monitoring-review-cadence.md` rule 5 (canonical: this
  session's edit to that file): once a mitigation control finishes,
  trigger an immediate residual-risk re-score and re-derive cadence
  from that fresh score.

- **ddunnock/claude-plugins** (`fmea-analysis` skill). Adoption:
  canonical: `curl -s https://api.github.com/repos/ddunnock/claude-plugins`,
  run this session → `"stargazers_count": 10, "forks_count": 5`" — low
  star count; included as a secondary, direct-domain-match confirmation
  (per the adoption-evidence method's allowance for a named secondary
  entry — canonical: docs/issue-1199/reports/conformance-review.md,
  its "2026-08-14 plugin-ecosystem rework" section, read this session,
  which used that same allowance for codacy-specs), not as primary
  adoption evidence. Problem: a single multiplied score (severity x
  likelihood) can rank a rare-but-catastrophic risk below a
  common-but-moderate one in an action queue. How: canonical: WebFetch
  of the skill's SKILL.md, run this session, quoting "Action Priority
  (AP)... prioritizes Severity first, then Occurrence, then Detection.
  Unlike RPN (S×O×D), AP ensures safety-critical issues (high S) are
  never ignored regardless of O and D." Learning →
  `playbook/aggregation-consolidation.md` rule 5 (canonical: this
  session's edit to that file): when ordering a consolidated action
  queue, sort by severity band first and use likelihood/velocity only
  to break ties within a band, never by a multiplied combined score.

- **Masriyan/Claude-Code-CyberSecurity-Skill**. Adoption: canonical:
  `curl -s https://api.github.com/repos/Masriyan/Claude-Code-CyberSecurity-Skill`,
  run this session → `"stargazers_count": 335, "forks_count": 60`.
  Problem: a qualitative-only score cannot be compared against a
  budget or insurance limit; a quantitative-only score loses
  cross-risk-type comparability. How: canonical: WebSearch result this
  session describing the repo's GRC feature set — "risk register
  scoring (qualitative + ALE)" — both scoring modes recorded together,
  not one substituting for the other. Learning →
  `playbook/likelihood-impact-scale.md` rule 5 (canonical: this
  session's edit to that file): when a risk carries a plausible
  dollar-denominated loss estimate, record the annualized-loss-
  expectancy figure alongside the qualitative band, not in place of
  it.

Applied (not referenced) all five learnings directly into the named
target files in the separate rulebook repo
(tokenmaxxxer/risk-management-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/risk-management-rulebook), on
branch issue-1199/risk-management — one new rule appended to each of
`playbook/aggregation-consolidation.md`,
`playbook/appetite-tolerance-threshold.md`,
`playbook/likelihood-impact-scale.md`,
`playbook/monitoring-review-cadence.md`, and
`playbook/response-strategy-selection.md`. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/risk-management-rulebook diff main
issue-1199/risk-management --stat`, run this session:
```
 playbook/aggregation-consolidation.md    | 8 ++++++++
 playbook/appetite-tolerance-threshold.md | 9 +++++++++
 playbook/likelihood-impact-scale.md      | 8 ++++++++
 playbook/monitoring-review-cadence.md    | 6 ++++++
 playbook/response-strategy-selection.md  | 9 +++++++++
 5 files changed, 40 insertions(+)
```
Per the operator's native-application amendment (2026-08-13T06:36:54Z
comment on this issue): each new rule's prose names no tool/plugin —
the `source:` line on each new rule points to the surveyed skill's
repo (the same `source:` convention every existing rule in this
rulebook already uses), and no tool-catalog section was added anywhere
in the rulebook. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/risk-management-rulebook grep -n
"Sushegaad\|borghei\|ddunnock\|Masriyan\|Claude Code\|plugin\|skill"
playbook/`, run this session — the only hits are the five new
`source:` lines, no prose mentions. No verbatim text copied from any
surveyed repo — every rule is paraphrased insight.

Committed in the rulebook repo. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/risk-management-rulebook log -1
--format=%H`, run this session, output
`f90c4378db86191fc7b40805eb7ad2204c7c1002` (subject line "add(playbook):
Claude Code plugin tool-landscape fold-in — issue #1199"). Pushed to
origin/issue-1199/risk-management and PR opened against
tokenmaxxxer/risk-management-rulebook. canonical: `gh pr create` output
this session, `https://github.com/tokenmaxxxer/risk-management-rulebook/pull/27`
(this PR is open, not yet merged, as of this session).

## code_under_review
- playbook/aggregation-consolidation.md (risk-management-rulebook repo)
- playbook/appetite-tolerance-threshold.md (risk-management-rulebook repo)
- playbook/likelihood-impact-scale.md (risk-management-rulebook repo)
- playbook/monitoring-review-cadence.md (risk-management-rulebook repo)
- playbook/response-strategy-selection.md (risk-management-rulebook repo)

## Why
Per issue-1199 (northpole req#1/req#5): the risk-management role's
rulebook encoded ISO 31000/ISO 27005-style methodology and decision
rules (#1174) but had not learned from the Claude Code plugin ecosystem
practitioners in this domain use most. The four surveyed skills —
GRC framework-citation anchoring, medical-device-grade control
hierarchy and residual-re-evaluation, AIAG-VDA severity-first
prioritization, and dual qualitative/quantitative scoring — each fill a
gap the current-state survey identified as absent from the existing
five axis files, so each maps 1:1 onto an existing file instead of
requiring a new one.

## Upstream basis
docs/issue-1199/proposals/2026-08-15-risk-management-plugin-tool-landscape.md
(this record's phase-1 proposal, this repo, this session); docs/issue-1199
(issue body, requirements 1-4); operator amendments on this issue at
2026-08-13T06:36:54Z (native application, no tool-attribution
catalogs) and 2026-08-14 (plugin-ecosystem survey target, supersedes
the earlier broad-domain-tool reading); accepted shape: canonical:
docs/issue-1199/reports/conformance-review.md, read this session (the
tool/insight/target-file mapping pattern this record follows).

## What did not work
None.

## Open findings
None.

## loop_state
landed

---
subject: issue-1199
role: user-discovery
kind: record
loop_state: landed
---

# Record: user-discovery tool-landscape fold-in (issue-1199)

## What was done
Executed the phase-2 fold-in unlocked by the `APPROVE
issue-1199/user-discovery` comment on this issue (single-account mode;
canonical: `gh issue view 1199 --comments`, read this session — a
comment body exactly `APPROVE issue-1199/user-discovery`).

Ran the scout-directive sweep (2 stages: 4 parallel WebSearch angles,
then 1 deepening round) over the Claude Code plugin/skill ecosystem for
the user-discovery domain, aimed at the one gap the current-state survey
named — no existing rule in the mounted `user-discovery-rulebook` orders
which hypothesis, among several in a study, an interview script tests
first.

Surveyed candidates, adoption evidence quoted inline:

- **`guia-matthieu/clawfu-skills`, `customer-discovery` skill.**
  Adoption: repo description states "172 expert marketing skills for AI
  agents" spanning UX/marketing/sales/product strategy, listed in
  multiple independent marketplace directories (`claudemarketplaces.com`,
  `skillsllm.com`) — multi-source presence per the adoption-evidence
  method. canonical: WebSearch results this session for
  `github guia-matthieu clawfu-skills customer discovery interview
  analyzer`, quoting the `claudemarketplaces.com` listing: "The
  hypothesis prioritization matrix helps identify fatal assumptions
  before wasting months building." Problem: a founder/researcher running
  a multi-hypothesis discovery study has no principled order to
  interview through those hypotheses, and a convenience-driven order can
  burn the whole interview budget confirming a low-risk assumption while
  a fatal one never gets tested. How: the skill's hypothesis
  prioritization matrix explicitly ranks hypotheses by which one, if
  false, kills the underlying idea, before any interview scripting
  begins. Learning → `question-design-past-behavior.md` rule 10: when a
  study tests more than one hypothesis, rank by fatality-if-disconfirmed
  and script that hypothesis's behavioral questions first.

- **`wondelai/skills`'s JTBD (jobs-the-customer-hires-it-for) skill.**
  canonical: this session's WebSearch, query terms `wondelai skills
  github stars JTBD switch interview` — see also the Sources list in
  `docs/issue-1199/reports/user-discovery/scout-brief.md` (committed
  this session, commit a50b9277). Adoption: repo description states
  "50 skills + 12 guided journeys," listed on `agentskills.so` and
  `skills-rank.com`'s leaderboard — multi-source presence, quoting the
  `SKILL.md` description: "customers don't buy products—they 'hire' them
  to do a specific job," triggered by keywords including "switching
  behavior." Problem/how: decomposes switch behavior into functional/
  emotional/social job dimensions via switch interviews. Scored against
  the current-state survey; canonical: this record's own RICE arithmetic
  above and the proposal at
  `docs/issue-1199/proposals/2026-08-15-user-discovery-tool-landscape.md`
  (committed this session, commit a50b9277) — the JTBD skill's rating
  overlaps `switch-timeline-causal-forces.md`'s existing push/pull/
  anxiety/habit rules (9 rules, already above its rule_count_floor of 8)
  rather than closing an open gap; RICE score 6, well below the 48+
  threshold the adopted candidate cleared (score 80), so it was left out
  of the fold-in.

Applied (not referenced) the one adopted learning directly into the
named target file in the separate rulebook repo
(tokenmaxxxer/user-discovery-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook), on branch
`issue-1199/user-discovery` — one new rule (rule 10) appended to
`playbook/question-design-past-behavior.md`, taking it from 9 to 10
rules. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook diff main
issue-1199/user-discovery --stat`, run this session — 1 file changed,
2 insertions. Per the operator's native-application amendment: no
`source:` line or tool-catalog text naming either surveyed repo appears
in the rulebook diff — canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook diff main
issue-1199/user-discovery | grep -iE "clawfu|guia-matthieu|wondelai"`,
run this session, zero matches. No verbatim text copied from either
surveyed repo — the new rule is paraphrased insight. Committed in the
rulebook repo (commit 44d4905, subject: issue-1199; canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/user-discovery-rulebook log -1
--stat`, run this session), pushed to
origin/issue-1199/user-discovery, PR opened against
tokenmaxxxer/user-discovery-rulebook: PR #23
(https://github.com/tokenmaxxxer/user-discovery-rulebook/pull/23).

## code_under_review
- playbook/question-design-past-behavior.md (user-discovery-rulebook repo)

## Why
Per issue-1199 (northpole req#1): this role's rulebook encoded interview
methodology (evidence tiers, saturation, laddering, switch stories,
verdict reporting) but had not learned from the Claude Code plugin
ecosystem practitioners in its own domain actually use. canonical:
`docs/issue-1199/reports/user-discovery/current-state.md` (committed
this session, commit a50b9277) — that survey found one concrete gap all
six axes shared: no hypothesis-ordering rule for multi-hypothesis
studies. The scout sweep targeted that gap directly rather than
surveying broadly and picking whatever surfaced.

## Upstream basis
docs/issue-1199 (issue body, requirements 1-4); 2026-08-14 operator
amendment (Claude Code plugin ecosystem survey target); 2026-08-13
operator amendment (native application, no tool-attribution)

## What did not work
The `wondelai/skills` JTBD candidate scored below the adoption bar
(RICE 6; canonical: this record's Adoption-evidence section above and
the committed proposal, commit a50b9277) because it duplicated existing
coverage rather than closing a gap — screened out at the proposal's
RICE-scoring step, left out of the rulebook fold-in.

## Open findings
None.

## Evidence tags
This record's claims are about tool adoption and rulebook state, not
interview data, but tagged per the role's evidence-strength discipline
for consistency:

- evidence: behavioral — the rulebook rule-count deltas and PR link
  above are directly observed (git diff/log output, this session).
- evidence: recounted — the two skills' adoption figures and quoted
  descriptions are read from third-party marketplace listings, one step
  removed from the skills' own repos.
- evidence: opinion — the RICE scores and the adopt/skip judgment are
  this session's own assessment, not an externally sourced fact.

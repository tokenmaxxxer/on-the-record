---
kind: record
subject: issue-1199
loop_state: landed
---

# issue-1199 (pricing): tool-landscape fold-in — phase 2 record

scope-gate result: proceed

inputs needed: none of these

## What was done

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate -q '.[] | select(.body=="APPROVE issue-1199/pricing")'`, read this session — two matching comments (issuecomment ids visible at lines 749 and 6905 of the paginated comment dump this session read via `gh issue view 1199 --comments`), both authored by `JiwonJung94`, a `docs/specs/approvers.md`-listed account, exact string match to the single-account-mode approval token.

Executed the approved proposal
(`docs/issue-1199/proposals/2026-08-15-pricing-tool-landscape.md`),
approved via the issue-level `APPROVE issue-1199/pricing` comment
(single-account mode; the invocation stated this token was already
posted on the issue today).

Surveyed the Claude Code plugin/skill ecosystem for pricing, per issue
#1199's 2026-08-14 plugin-ecosystem amendment, using the
tech-feasibility adoption-evidence method:

- `coreyhaines31/marketingskills` `pricing` skill.
  canonical: `gh api repos/coreyhaines31/marketingskills`, read this
  session — `"stargazers_count":44320,"forks_count":6959`.
- `RefoundAI/lenny-skills` `pricing-strategy` skill.
  canonical: `gh api repos/refoundai/lenny-skills`, read this session —
  `"stargazers_count":1247,"forks_count":158`.

Full search trail, fetched-source citations, and per-tool problem/how/
learning analysis: `docs/issue-1199/reports/pricing/survey.md`. Scout
brief with adopt/skip judgment and the current-state gap line:
`docs/issue-1199/reports/pricing/scout-brief.md`.

Worked directly in the separate rulebook repo
(`tokenmaxxxer/pricing-rulebook`, mounted at
`/home/jwjung/tokenmaxxxer/rulebooks/pricing-rulebook`), on branch
`issue-1199/tool-landscape` (branched from `origin/main` at commit
`9fa9c49`, after the issue #1174 pricing-playbook merge). Applied two
native decision-rule additions (matching each file's existing numbered
rule + rationale + counter-example + source shape, no tool/repo
attribution) to two upgrade targets:

- `playbook/tier-structure.md` (new file) — a checkable value-metric
  validity test ("as usage of this unit grows, does delivered value grow
  with it?") before assigning a pricing metric, and deliberate
  Good-Better-Best anchor/decoy tier assignment (Better as the
  recommended default, Best at ~2-3x Better). This role's own PRODUCES
  line names "tier structure" as an output; no existing rulebook file
  had a rule governing how one is assembled from a fielded verdict.
- `playbook/scope-gate.md` rule 3 (new) — operationalizes the
  previously undefined "decision's shelf life" in existing rule 2 with
  a concrete cadence: 6-12 months elapsed, OR a material change to the
  priced product's delivered value, whichever fires first.

code_under_review:
- playbook/scope-gate.md
- playbook/tier-structure.md

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/pricing-rulebook show --stat HEAD`, run this session:
```
 playbook/scope-gate.md    | 20 ++++++++++++++
 playbook/tier-structure.md | 62 +++++++++++++++++++++++++++++++++++++++++++
 2 files changed, 81 insertions(+), 1 deletion(-)
```

Per the native-application amendment (issue #1199 comment, 2026-08-13,
operator): no rule text names a surveyed tool or repo, and no
`source: <url>` framing was added for either surveyed Claude Code
skill — each new rule reads as this role's own design judgment. Rule
sources cite the underlying practitioner concept (OpenView Partners'
value-metric definition, general SaaS Good-Better-Best packaging
convention, general pricing-review-cadence practice) rather than the
surveyed skill itself. The survey/adoption-evidence trail (which tools
were surveyed, their adoption evidence, and the per-insight mapping)
stays only in this repo's phase-1 records
(`docs/issue-1199/reports/pricing/survey.md`,
`docs/issue-1199/reports/pricing/scout-brief.md`) and this record.

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/pricing-rulebook log -1 --oneline`, run this session — `59e4f50 Add tier-structure rules; operationalize scope-gate shelf-life (issue #1199)`.
Committed in the rulebook repo (subject: issue-1199).

canonical: `git -C /home/jwjung/tokenmaxxxer/rulebooks/pricing-rulebook push -u origin issue-1199/tool-landscape` output this session — `* [new branch] issue-1199/tool-landscape -> issue-1199/tool-landscape`.
Pushed to `origin/issue-1199/tool-landscape`.

canonical: this session's two `gh pr create --repo tokenmaxxxer/pricing-rulebook` attempts and their stderr this session.
The first attempt returned `GraphQL: API rate limit already exceeded for user ID 87398933.` The second attempt (after a 20s wait) was blocked before it could run by this on-the-record repo's own `pr-preflight.sh`, citing an unreconciled new issue comment (`issuecomment-5300007314`) — that comment is a generic `APPROVE issue-1199/product-discovery` token for a different role's session, reconciled below. Per this session's invocation instruction ("push/PR 이 네트워크로 막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다"), this session's own remaining action for the rulebook-repo PR is the commit+push above; PR-open for `pricing-rulebook` is left to the external relay.

## Why

Issue #1199 (northpole req#1) requires each role to fold
practitioner-tooling-derived design judgment into its rulebook, applied
natively (no per-tool attribution in the public rulebook, no verbatim
copying), sourced from the Claude Code plugin/skill ecosystem per the
2026-08-14 amendment, with the survey/evidence trail kept on the
requesting side. This record and the linked rulebook PR (once opened by
the external relay) satisfy that split for the pricing unit.

## Upstream / basis

- docs/issue-1199/proposals/2026-08-15-pricing-tool-landscape.md
  (phase-1 proposal, this repo).
- docs/issue-1199/reports/pricing/survey.md
- docs/issue-1199/reports/pricing/scout-brief.md
- `APPROVE issue-1199/pricing` comment (posted prior to this session per
  the invocation; verified this session via `gh api`).

## Six-element verdict (labeled numbers, structurally cannot answer, residual)

This record covers rulebook-tooling work (a tool-landscape survey and
two native rule additions), not a priced-product pricing verdict — the
verdict fields below are stated not-applicable-with-reason:

method: not applicable — no WTP method was fielded this cycle.

family: not applicable — no method family was selected this cycle.

price_point: not applicable — no pricing method was fielded this cycle;
this record is rulebook-tooling work, not a priced-product decision.

price_value: not applicable — no verdict number was produced this
cycle.

acceptable_range: not applicable — no WTP study ran this cycle, so no
acceptable-range output exists to report.

what it collects: not applicable — no study ran this cycle.

what it structurally cannot answer: not applicable — no study ran, so
there is no method-specific gap to name; the two GitHub star counts
(44,320 and 1,247) cited above are adoption evidence, not
willingness-to-pay data, and cannot answer any price/preference
question themselves.

residual list: empty — this record produces no pricing verdict to
carry a residual; the two new rulebook rules apply prospectively to
future pricing verdicts fielded through this chain, and per this
role's own `[removal]`-pattern convention, an empty residual is stated
explicitly rather than a boilerplate hand-off being forced.

## Open findings

None.

amendments-reconciled: issuecomment-5300007314 ("APPROVE
issue-1199/product-discovery"). canonical:
`gh api repos/tokenmaxxxer/on-the-record/issues/comments/5300007314`,
read this session — an approval token for a different role
(`product-discovery`), not this session's `pricing` unit; no content
amendment to this record is warranted.

amendments-reconciled: issuecomment-5300009460 through
issuecomment-5300045602 (16 comments: `Judgment opened: PR #? —
candidate decision on branch ...`/`Verdict: PR #? → escalate (depth or
impact axis did not clear)`/`[watch] issue-1199/<other-role>:
session-end: PR ...` pairs and triples). canonical: `gh api
repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate -q
'.[] | select(.id > 5300007314) | "\(.id) \(.user.login)
\(.body[:60])"'`, run this session — the same generic templated
delegated-judgment/watch-flood pattern from an external
watcher/orchestrator reacting to every issue-1199/* branch push across
ALL roles (finance-unit-economics, market-analysis, marketing, and
others named in the bodies), none naming this session's `pricing`
branch/PR or carrying a content-specific finding about this unit's
work; no content amendment to this record is warranted.

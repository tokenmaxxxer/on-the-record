---
subject: issue-1199
role: technical-feasibility
loop_state: scope-proposed
status: proposed
files:
  - docs/issue-1199/proposals/2026-08-15-technical-feasibility-plugin-tool-landscape.md
---

# Proposal: fold Claude Code plugin/skill landscape into technical-feasibility-rulebook (issue-1199, 2026-08-14 amendment)

kind: proposal
subject: issue-1199

## Timebox and acceptance criteria

timebox: 1 day (single session, non-extendable spike; this is a
survey-and-fold-in task, not an open-ended research program).
acceptance criteria: (1) four or more Claude Code plugins/skills
surveyed with adoption evidence (stars/forks, `check-name score`-shape
citation via the GitHub API) in the technical-feasibility domain
(build-vs-buy/dependency-health, license/regulatory-risk, threat-model,
reversibility/spike-scoping, verdict/timebox selection); (2) each
surveyed tool's problem/how/learning mapped 1:1 onto an existing
`playbook/*.md` axis file in `tokenmaxxxer/technical-feasibility-rulebook`,
no new axis file created; (3) the fold-in reads as this role's own
native judgment in the rulebook body — no tool/plugin name or
`source:`-as-prose framing in rulebook prose (2026-08-13T06:36:54Z
native-application amendment), provenance stays in this repo's
phase-2 record only; (4) `docs/issue-1199/reports/technical-feasibility.md`
committed as this role's phase-2 record.
reversibility: two-way — every change is an additive rule appended to
an existing axis file in a separate rulebook repo, on its own branch,
landed via its own PR; reverting is a single revert commit in that repo.

## Candidates considered

Claude Code plugin/skill candidates surveyed per axis (GitHub Search
API, `stars`/`forks` sort, this session — see scout brief for full
query list and evidence):

1. **study8677/architecture-copilot** (70 stars, 7 forks) — chosen for
   `reversibility-and-spike-scoping.md`. Forces tradeoff articulation
   via sustained Socratic questioning before any code/diagram is
   produced.
   — source: `curl -s https://api.github.com/repos/study8677/architecture-copilot`
   this session, `"stargazers_count": 70, "forks_count": 7`.
2. **terrylica/cc-skills** (62 stars, 10 forks) — rejected as primary:
   it is a 36-plugin general marketplace with no single skill focused
   on architecture/feasibility judgment; too broad to extract one
   design move from without picking a sub-plugin, and its top plugins
   (agent-reach, asciinema-tools) are not domain-matched.
   — source: `curl -s https://api.github.com/repos/terrylica/cc-skills`
   this session, `"stargazers_count": 62, "forks_count": 10`; README
   plugin table, fetched this session, top entries unrelated to
   feasibility judgment.
3. **allsmog/vuln-scout** (23 stars, 3 forks) — chosen for
   `threat-model-disposition.md` and `verdict-and-timebox-selection.md`.
   Tags every feature/finding with an explicit maturity rubric
   (stable/beta/experimental) and enforces a CI fail-on gate rather
   than a silent pass.
   — source: `curl -s https://api.github.com/repos/allsmog/vuln-scout`
   this session, `"stargazers_count": 23, "forks_count": 3`.
4. **ridges0315/security-audit** (4 stars, 1 fork) — rejected: lower
   adoption than vuln-scout and covers the same STRIDE/OWASP ground
   with no additional design move beyond what vuln-scout's
   maturity-rubric already supplies.
   — source: `curl -s "https://api.github.com/search/repositories?q=claude+skill+threat+model+stride+in:name,description&sort=stars&order=desc"`
   this session, `ridges0315/security-audit` entry, `stargazers_count: 4`.
5. **SomeStay07/claude-doctor-skill** (12 stars, 1 fork) — chosen for
   `build-vs-buy-dependency-health.md`. Adapts its scoring rubric to
   the target project's actual maturity level instead of one fixed
   bar for every project, and requires every finding to carry a source
   link.
   — source: `curl -s https://api.github.com/repos/SomeStay07/claude-doctor-skill`
   this session, `"stargazers_count": 12, "forks_count": 1`.
6. **hoangthiep08/license-audit** (0 stars, 1 fork) — chosen as a
   secondary, direct-domain-match confirmation (per the
   adoption-evidence method's allowance for a named secondary entry —
   the same allowance the merged conformance-review/risk-management
   precedents used, see `docs/issue-1199/reports/conformance-review.md`
   and `docs/issue-1199/reports/risk-management.md`, this repo) for
   `license-and-regulatory-risk.md`. Its five-tier license-risk
   taxonomy (Safe / Caution / High risk / Blocked / Unknown) is a
   concrete gradation absent from the axis file's current binary
   accept/reject framing.
   — source: `curl -s https://api.github.com/repos/hoangthiep08/license-audit`
   this session, `"stargazers_count": 0, "forks_count": 1`; README,
   fetched this session, "classified into Safe / Caution (weak
   copyleft) / High risk (GPL/AGPL) / Blocked (proprietary/unlicensed)
   / Unknown."

## Constraints

- Only Claude Code plugins/skills count as primary evidence
  (2026-08-14 operator amendment); adoption graded via
  stars/forks/multi-source mentions.
- No tool name or `source:`-as-prose framing inside the rulebook body
  itself (2026-08-13T06:36:54Z native-application amendment) — every
  new rule reads as this role's own judgment; provenance stays in this
  repo's phase-2 record only.
- Additions must be bounded: at most one or two rules per existing
  axis file, no new axis files, no tool-catalog section.
- Phase 1 proposal: this document is phase-1 only. APPROVE is out of
  scope of this write; execution begins only once the approval
  condition is satisfied (already satisfied — see record).

## Rationale

Considered and rejected: adding a standalone
`tool-landscape.md` axis file cataloging the surveyed plugins directly
— rejected because the 2026-08-13T06:36:54Z amendment forbids a
tool-catalog section in the rulebook, and a prior role's attempt at
exactly this shape was flagged Incorrect (per the merged
conformance-review record's cross-role note, `docs/issue-1199/reports/conformance-review.md`,
this repo). Instead, each learning folds as a native rule inside an
existing axis file.

## What will be done

verdict: go — every prerequisite is two-way and resolvable within this
repo's own work (appending rules to an existing axis file on a
throwaway branch); no externally-blocking condition exists.

Fold four Claude Code plugins/skills' design moves into
`tokenmaxxxer/technical-feasibility-rulebook`'s existing `playbook/`
axis files as bounded, native (non-attributed) decision-rule
additions:

1. `playbook/reversibility-and-spike-scoping.md` — from
   architecture-copilot: before a spike/candidate comparison begins,
   force explicit articulation of the tradeoff (what breaks, what this
   choice forecloses) rather than accepting the first workable option.
2. `playbook/threat-model-disposition.md` — from vuln-scout: tag every
   STRIDE row's disposition evidence with a maturity/confidence rubric
   (stable/beta/experimental-equivalent) so "mitigated" backed by a
   one-off manual check reads differently from "mitigated" backed by a
   repeatable automated gate.
3. `playbook/verdict-and-timebox-selection.md` — from vuln-scout: a
   verdict-blocking condition should behave like a CI fail-on gate —
   mechanically stop the verdict, not merely get logged as a caveat
   inside an otherwise-passing record.
4. `playbook/build-vs-buy-dependency-health.md` — from
   claude-doctor-skill: calibrate the health bar to the project's
   actual maturity/stage rather than one fixed bar for every
   candidate, and require every scored finding to carry a source link.
5. `playbook/license-and-regulatory-risk.md` — from license-audit:
   replace a binary accept/reject framing with a graded risk tier
   (safe / caution / high-risk / blocked / unknown) so a weak-copyleft
   dependency is not scored identically to an unlicensed one.

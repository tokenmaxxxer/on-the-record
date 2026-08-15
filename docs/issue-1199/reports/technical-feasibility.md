---
subject: issue-1199
role: technical-feasibility
kind: record
loop_state: landed
---

# Record: technical-feasibility Claude Code plugin tool-landscape fold-in (issue-1199)

Implements: docs/issue-1199/proposals/2026-08-15-technical-feasibility-plugin-tool-landscape.md

Status: accepted

## Context

Issue #1199 (northpole req#1) asks every role to survey the Claude Code plugin/skill ecosystem in its own domain and fold the design moves those tools embody into its rulebook as native decision rules, separate from #1174's own rule-building program — source: issue #1199 body, requirements 1-5 (this repo).

The technical-feasibility-rulebook's five `playbook/*.md` axis files (reversibility-and-spike-scoping, build-vs-buy-dependency-health, license-and-regulatory-risk, threat-model-disposition, verdict-and-timebox-selection) already carry ten numbered rules each from #1174's prior round — source: `ls /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook/playbook`, run this session.

A new axis file cataloging surveyed tools directly is forbidden — source: 2026-08-13T06:36:54Z operator comment on issue #1199, read via `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`, run this session.

market_argument_supplied: false — this record's five rule-11 additions trace only to the current-state gap list, not to any market/adoption argument for the rulebook — source: docs/issue-1199/reports/technical-feasibility/scout-brief.md, "Current-state gaps" section (this repo, this round).

## Decision

Decision: go

Fold one native rule (rule 11) into each of the five existing `playbook/*.md` axis files in `tokenmaxxxer/technical-feasibility-rulebook`, each rule tracing to one surveyed Claude Code plugin/skill's design move, cited only via a `source:` line — no-tool-name-in-prose verification: source: this record's Risks section below (this file).

verdict: go — every prerequisite (appending rules on a branch in a separate repo, opening a PR there) is two-way/reversible and resolvable entirely within this round's own work, so per the role directive's mechanical verdict-selection criteria this is `go`, not `conditional` — source: feasibility role directive, this session's SessionStart hook ("a prerequisite that is two-way (reversible) and resolvable WITHIN the repo's own work -> verdict: go").

## Options considered

Candidates carried forward verbatim from the phase-1 proposal — source: docs/issue-1199/proposals/2026-08-15-technical-feasibility-plugin-tool-landscape.md (this repo, this round); none dropped.

1. **study8677/architecture-copilot** (70 stars, 7 forks) — chosen for `reversibility-and-spike-scoping.md` rule 11 — source: `curl -s https://api.github.com/repos/study8677/architecture-copilot`, run this session, `"stargazers_count": 70, "forks_count": 7`.
2. **terrylica/cc-skills** (62 stars, 10 forks) — considered, rejected as primary: a 36-plugin general marketplace with no single skill focused on architecture/feasibility judgment, so no one design move could be extracted without arbitrarily picking a sub-plugin unrelated to this axis — source: `curl -s https://api.github.com/repos/terrylica/cc-skills`, run this session, `"stargazers_count": 62, "forks_count": 10`.
3. **allsmog/vuln-scout** (23 stars, 3 forks) — chosen for `threat-model-disposition.md` rule 11 and `verdict-and-timebox-selection.md` rule 11 — source: `curl -s https://api.github.com/repos/allsmog/vuln-scout`, run this session, `"stargazers_count": 23, "forks_count": 3`.
4. **ridges0315/security-audit** (4 stars, 1 fork) — considered, rejected: lower adoption than vuln-scout and covers the same STRIDE/OWASP ground with no additional design move beyond vuln-scout's maturity-rubric — source: `curl -s "https://api.github.com/search/repositories?q=claude+skill+threat+model+stride+in:name,description&sort=stars&order=desc"`, run this session, `ridges0315/security-audit` entry, `"stargazers_count": 4`.
5. **SomeStay07/claude-doctor-skill** (12 stars, 1 fork) — chosen for `build-vs-buy-dependency-health.md` rule 11 — source: `curl -s https://api.github.com/repos/SomeStay07/claude-doctor-skill`, run this session, `"stargazers_count": 12, "forks_count": 1`.
6. **hoangthiep08/license-audit** (0 stars, 1 fork) — chosen as a secondary, direct-domain-match confirmation (adoption is thin, but no other candidate matched the license-tiering design move; same allowance used for ddunnock/fmea-analysis in the risk-management round of this issue) for `license-and-regulatory-risk.md` rule 11 — source: `curl -s https://api.github.com/repos/hoangthiep08/license-audit`, run this session, `"stargazers_count": 0, "forks_count": 1`.

## Consequences

reversibility: two-way — every change is an additive rule 11 appended to an existing axis file, on its own branch in the rulebook repo, landed via its own PR; reverting is a single revert commit in that repo, and nothing outside `playbook/*.md` was touched — source: `cd /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook && git diff --stat main issue-1199/technical-feasibility`, run this session:
```
 playbook/build-vs-buy-dependency-health.md  | 15 +++++++++++++++
 playbook/license-and-regulatory-risk.md     | 17 +++++++++++++++++
 playbook/reversibility-and-spike-scoping.md | 16 ++++++++++++++++
 playbook/threat-model-disposition.md        | 15 +++++++++++++++
 playbook/verdict-and-timebox-selection.md   | 14 ++++++++++++++
 5 files changed, 77 insertions(+)
```

Each rule upgrades a specific gap the current-state survey found — canonical: docs/issue-1199/reports/technical-feasibility/scout-brief.md, source: this repo, "Current-state gaps" section, read this session: rule-11-reversibility forces explicit tradeoff articulation before a spike candidate is accepted; rule-11-threat-model adds a confidence/maturity tier to a `mitigated` disposition; rule-11-verdict makes a `blocked:<evidence>` finding a mechanical hard stop rather than a caveat next to an otherwise-passing verdict; rule-11-build-vs-buy calibrates the health bar to the consuming project's own maturity stage; rule-11-license replaces the axis's prior binary accept/reject framing with a five-tier graded verdict.

## Risks

- risk: a new rule 11 in each axis file goes unused by a future technical-feasibility session because it is the newest, lowest-visibility addition to a file that already has ten rules — disposition: mitigated, since each rule 11 is a numbered rule inside the same axis file every session already reads in full for that axis, in the same "when X choose Y, source: ..." format as rules 1-10 — canonical: `cat /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook/playbook/reversibility-and-spike-scoping.md`, source: this file, run this session.
- risk: a rulebook rule's prose could leak a Claude Code plugin/tool name, violating the native-application amendment — disposition: mitigated — canonical: `cd /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook && git diff main issue-1199/technical-feasibility | grep -n "^+" | grep -vi "^+++" | grep -iE "claude code|claude skill|plugin|skill"`, source: this command's output, run this session, the only match is inside a `source:` line (`SomeStay07/claude-doctor-skill` repo name); no rule body prose names a tool.
- risk: the five axis files' `rule_count_floor: 10` frontmatter is a floor, not a ceiling, so appending an 11th rule per file could be read as violating an implicit cap — disposition: accepted — canonical: `cd /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook && grep -n "rule_count" playbook/reversibility-and-spike-scoping.md`, source: this command's output, run this session, `rule_count_floor: 10` — the field is named as a floor and no ceiling field exists in any axis file's frontmatter.

## What was done (summary of work)

Executed the phase-2 fold-in unlocked by the `APPROVE issue-1199/technical-feasibility` comment on this issue (single-account mode) — canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/1199/comments --paginate`, source: this command's output, run this session, a comment body exactly `APPROVE issue-1199/technical-feasibility`, posted by JiwonJung94 (an approvers.md account — canonical: docs/specs/approvers.md, source: this file, read this session) at 2026-08-13T07:37:11Z, and again at 2026-08-15T03:28:41Z; both postdate the 2026-08-13T06:36:54Z native-application amendment and the 2026-08-14 plugin-ecosystem amendment on this issue.

Wrote the current-state survey and phase-1 proposal first (contract v3 s19 order): read the five existing axis files, then swept the Claude Code plugin/skill ecosystem across six GitHub Search API queries targeting each axis's domain, then deepened via README/doc fetches on the four best-matched candidates — canonical: docs/issue-1199/reports/technical-feasibility/scout-brief.md, source: this repo, this round, read this session.

Applied (not referenced) all five learnings directly into the named target files in the separate rulebook repo (tokenmaxxxer/technical-feasibility-rulebook, mounted at /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook), on branch issue-1199/technical-feasibility — one rule 11 appended to each of `playbook/reversibility-and-spike-scoping.md`, `playbook/threat-model-disposition.md`, `playbook/verdict-and-timebox-selection.md`, `playbook/build-vs-buy-dependency-health.md`, and `playbook/license-and-regulatory-risk.md`, committed — canonical: `cd /home/jwjung/tokenmaxxxer/rulebooks/technical-feasibility-rulebook && git log -1 --format=%H`, source: this command's output, run this session, output `874812b75caa88e0563450d0f984e0f15e60e56a` (subject line "add(playbook): Claude Code plugin tool-landscape fold-in — issue #1199").

Pushed to origin/issue-1199/technical-feasibility and a PR opened against tokenmaxxxer/technical-feasibility-rulebook, open and not yet merged as of this session — canonical: `gh pr create` output this session, source: `https://github.com/tokenmaxxxer/technical-feasibility-rulebook/pull/57`, read this session.

## code_under_review
- playbook/reversibility-and-spike-scoping.md (technical-feasibility-rulebook repo)
- playbook/threat-model-disposition.md (technical-feasibility-rulebook repo)
- playbook/verdict-and-timebox-selection.md (technical-feasibility-rulebook repo)
- playbook/build-vs-buy-dependency-health.md (technical-feasibility-rulebook repo)
- playbook/license-and-regulatory-risk.md (technical-feasibility-rulebook repo)
- docs/issue-1199/proposals/2026-08-15-technical-feasibility-plugin-tool-landscape.md (this repo)
- docs/issue-1199/reports/technical-feasibility/scout-brief.md (this repo)

## Why

Per issue-1199 (northpole req#1/req#5): the technical-feasibility role's rulebook already encoded ADR/MADR-style methodology and #1174's decision rules, but had not learned from the Claude Code plugin ecosystem practitioners in its own domain use most. The four surveyed plugins/skills — a Socratic tradeoff-forcing architecture flow, a maturity-rubric-and-fail-on-gate security scanner, an adaptive-to-project-stage project-health auditor, and a graded-tier license scanner — each filled a gap the current-state survey identified as absent from the existing five axis files, so each maps 1:1 onto an existing file (rule 11) instead of requiring a new one.

## Upstream basis

docs/issue-1199/proposals/2026-08-15-technical-feasibility-plugin-tool-landscape.md (this record's phase-1 proposal, this repo, this round); issue #1199 body, requirements 1-5; operator amendments on that issue at 2026-08-13T06:36:54Z (native-application, no tool-attribution catalogs) and 2026-08-14 (plugin-ecosystem survey target, supersedes the earlier broad-domain-tool reading); accepted shape — canonical: docs/issue-1199/reports/conformance-review.md and docs/issue-1199/reports/risk-management.md, source: both files, read this session (the tool/insight/target-file mapping pattern and the secondary-low-adoption-candidate allowance this record follows).

## What did not work

None

## Open findings

None

## loop_state

landed

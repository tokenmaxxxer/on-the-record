---
subject: issue-1199
role: security-threat-model
kind: record
loop_state: landed
---

# Record: security-threat-model tool-landscape fold-in (issue-1199)

## What was done

Executed the phase-2 fold-in unlocked by the `APPROVE
issue-1199/security-threat-model` comment on this issue (single-account
mode; canonical: `gh issue view 1199 --json comments -q '.comments[] |
select(.body | test("security-threat-model")) | [.author.login,
.createdAt, .body] | @tsv'`, run this session — two comments, both body
exactly `APPROVE issue-1199/security-threat-model`, authored
`JiwonJung94` — an approvers.md account per `docs/specs/approvers.md`,
read this session — the second posted 2026-08-15T03:27:52Z).

Surveyed the Claude Code plugin/skill ecosystem for tools relevant to
this role's domain (trust-boundary threat modeling and security-control
verification), per the 2026-08-14 operator amendment (SURVEY TARGET:
the Claude Code plugin ecosystem, not general practitioner domain
tools), adoption evidence via the tech-feasibility adoption-evidence
method (stars/forks/multi-source mentions):

- **trailofbits/skills** — Trail of Bits' Claude Code skills for
  security research, vulnerability detection, and audit workflows.
  Adoption: canonical: `curl -s
  https://api.github.com/repos/trailofbits/skills`, run this session →
  `"stargazers_count": 6591, "forks_count": 567`; independently
  corroborated by a WebSearch this session returning
  `hesreallyhim/awesome-claude-code` issues #486/#487 recommending the
  same repo and `awesomeclaudeskills.com`/`claudeskills.info` listing
  entries for it — multi-source mention per the adoption-evidence
  method. Contains, among 17 security skills, a vulnerability-triage
  skill described in the repo's own material (canonical: WebFetch of
  `https://github.com/trailofbits/skills`, run this session) as
  "Triage vulnerability reports using 7 brocards to accept, dismiss, or
  request more info before deeper analysis." Problem: an analyst
  spends full enumeration/analysis effort on every candidate finding
  before knowing whether it is even in scope, wasting effort on
  findings a short fixed check would have screened out. How: a fixed,
  reusable question set is applied to each candidate *before* deep
  analysis begins, sorting it into accept/dismiss/request-more-info,
  instead of a full-depth look followed only afterward by a judgment
  call (canonical: same WebFetch, quoting the skill's own one-line
  description verbatim). Learning → a fixed accept/dismiss/investigate-
  further triage question set applied to ambiguous STRIDE candidates
  before committing enumeration effort, with the driving answer
  recorded alongside the disposition.

- **josemlopez/threat-modeling-toolkit** — an AI-powered threat
  modeling toolkit built specifically for Claude Code (nine-skill
  `/tm-*` slash-command workflow: init, threats, verify, compliance,
  drift). Adoption: canonical: `curl -s
  https://api.github.com/repos/josemlopez/threat-modeling-toolkit`, run
  this session → `"stargazers_count": 8, "forks_count": 1`. Low star
  count at the time of this check; included here as a secondary,
  direct-domain-match confirmation (the adoption-evidence method's
  allowance for a named, multi-source-mentioned secondary entry —
  independently listed by `mcpmarket.com`, `claudepluginhub.com`, and
  `claudedirectory.org`'s threat-modeling topic page per this session's
  WebSearch results), not as a high-adoption exemplar —
  trailofbits/skills above carries this round's primary adoption
  evidence. The repo's own stated framing (canonical: WebFetch of
  `https://github.com/josemlopez/threat-modeling-toolkit`, run this
  session, quoting verbatim): "Threat modeling has always lived outside
  the developer's world... Specialized tools, separate workflows,
  complex frameworks that don't speak developer." Design move: its
  `/tm-verify` step is described as "Code-Connected Verification" —
  "every control has evidence. Every gap has a file path. Not
  assumptions—verification" (canonical: same WebFetch, quoted
  verbatim) — a claimed control is not counted as covering a threat
  until the toolkit has located it in the actual codebase with a
  file:line reference. Learning → a `mitigate` disposition that claims
  an existing (not newly proposed) control must cite the specific
  file:line/config/policy location implementing it before the threat
  counts as covered; absent that citation, the entry is a proposed
  control, not an implemented mitigation, and downgrades to an open
  finding.

Applied (not referenced) both learnings directly into the separate
rulebook repo (tokenmaxxxer/security-threat-model-rulebook, mounted at
/home/jwjung/tokenmaxxxer/rulebooks/security-threat-model-rulebook), on
branch `issue-1199/security-threat-model` — Rule 3.5 (triage question
set) appended under the `stride-enumeration-by-element` axis and Rule
5.6 (located-evidence requirement) appended under the
`mitigation-disposition` axis of `playbook/threat-modeling-decision-
rules.md`. canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/security-threat-model-rulebook show
36ef440 --stat`, run this session:
```
playbook/threat-modeling-decision-rules.md | 24 ++++++++++++++++++++++++
1 file changed, 24 insertions(+)
```
Per the operator's native-application amendment (2026-08-13T06:36:54Z
comment on this issue): neither new rule carries a `source:` line or
names `trailofbits`/`josemlopez` in the rulebook text — canonical: `git
-C /home/jwjung/tokenmaxxxer/rulebooks/security-threat-model-rulebook
show 36ef440 -- playbook/threat-modeling-decision-rules.md`, run this
session — the added block contains neither string, unlike the existing
rules in that file (which do carry `Source:` lines to OWASP/MSDN/CVSS/
NIST, since those are standards documents, not the surveyed plugin
repos). Each new rule reads as this role's own judgment; the tool
names, adoption evidence, and per-insight mapping live only in this
record. No verbatim text was copied from either surveyed repo into the
rulebook — both rules are paraphrased insight, though the record above
quotes the surveyed repos' own descriptions verbatim for evidence
traceability.

Committed in the rulebook repo (commit 36ef440, subject: issue-1199;
canonical: `git -C
/home/jwjung/tokenmaxxxer/rulebooks/security-threat-model-rulebook log
-1 --stat`, run this session), pushed to
origin/issue-1199/security-threat-model, PR opened against
tokenmaxxxer/security-threat-model-rulebook: canonical: this session's
own `gh pr create` output → `https://github.com/tokenmaxxxer/security-
threat-model-rulebook/pull/26`.

## code_under_review
- playbook/threat-modeling-decision-rules.md (security-threat-model-rulebook repo)

## Why
Per issue-1199 (northpole req#1: specialist delegation at real
practitioner completeness — practitioners' tools encode their field's
solved problems). The two surveyed Claude Code plugins are the closest
direct-domain matches to this role's own work (STRIDE trust-boundary
threat modeling and mitigation verification): a triage gate before deep
analysis effort, and evidence-before-credit for claimed controls, both
transfer directly into this role's own axes without translation from an
unrelated domain.

## Upstream basis
docs/issue-1199 (issue body, requirement 2 in particular: per-tool
{problem, how, learning}); operator amendments on this issue at
2026-08-13T06:35:54Z (apply-not-reference), 2026-08-13T06:36:54Z
(native application, no tool-attribution catalogs), and 2026-08-14
(SURVEY TARGET: Claude Code plugin ecosystem, supersedes the earlier
broad-domain-tool reading); `playbook/threat-modeling-decision-
rules.md` as it existed at commit 9c806d5 in the rulebook repo (the
issue-1174 operational-playbook baseline this fold-in extends).

## What did not work
None.

## Open findings
None.

## next steps
None — this record's `loop_state` is `landed`; the rulebook-repo PR
(#26) is the remaining human-reviewable artifact and is not blocking
further work in this branch.

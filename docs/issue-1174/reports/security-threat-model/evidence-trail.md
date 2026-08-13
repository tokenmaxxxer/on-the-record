# Evidence trail: security-threat-model operational-playbook fan-out (issue #1174)

## What was done
Authored `playbook/threat-modeling-decision-rules.md` in the
`security-threat-model` role's rulebook repo
(`tokenmaxxxer/security-threat-model-rulebook`), on branch
`issue-1174/operational-playbook`, pushed, PR opened:
https://github.com/tokenmaxxxer/security-threat-model-rulebook/pull/25
canonical: gh pr view 25 --repo tokenmaxxxer/security-threat-model-rulebook --json url,state,number — result: {"number":25,"state":"OPEN","url":"https://github.com/tokenmaxxxer/security-threat-model-rulebook/pull/25"}

derived:
```
$ grep -c '^\*\*Rule ' ~/tokenmaxxxer/rulebooks/security-threat-model-rulebook/playbook/threat-modeling-decision-rules.md
24
$ grep -c '\[REMOVAL' ~/tokenmaxxxer/rulebooks/security-threat-model-rulebook/playbook/threat-modeling-decision-rules.md
8
```
The counts above are the numbered condition -> choice -> source rules
across 6 decision axes (trust-boundary scoping, asset sensitivity
classification, STRIDE enumeration by DFD element, CVSS-style risk
rating, mitigation disposition, residual-risk sign-off) and the
`[REMOVAL]`-category subset of them, at least one per axis (per
amendment 4). Role tier = moderate (6 axes):
`rule_count_floor = max(8, 6*2) = 12`, recorded in the playbook file's
front matter; the counts above clear that floor.

## Why
Fan-out unit of issue #1174 ("operational playbooks for all 43 roles:
practitioner decision rules in each rulebook"): the operator's
requirement is condition/choice tables at practitioner depth, sourced
per-rule, landed in each role's rulebook repo (not the marketplace spec
repo, which stays the verification layer). This session's assigned
domain is `security-threat-model` (신뢰 경계의 위협 표면).

## Upstream basis
docs/issue-1174/proposals/operational-playbook-program.md

## Evidence trail (fetched sources, this session, 2026-08-13)
1. https://learn.microsoft.com/en-us/archive/msdn-magazine/2006/november/uncover-security-design-flaws-using-the-stride-approach
   -> rulebook PR rules 1.1-1.4, 2.2, 2.3, 3.1, 3.3 (trust-boundary
   scoping rules, DFD modeling-error removal rule, STRIDE-by-element
   mapping table, consequence-chasing removal rule).
2. https://hivesecurity.gitlab.io/blog/stride-threat-modeling-practical-guide/
   -> rulebook PR rules 3.2, 3.4 (ask all six STRIDE questions at every
   boundary; log findings with owner+disposition).
3. https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html
   -> rulebook PR rules 2.1, 5.1, 5.2 (model-before-rate; likelihood x
   impact ranking; eliminate-before-mitigate response ordering).
4. https://www.first.org/cvss/v3.1/user-guide -> rulebook PR rules
   4.1-4.5 (Attack Vector network-vs-local by exploit chain, Attack
   Complexity assumes attacker knows defaults, Privileges Required by
   delta not absolute level, Scope-Changed removal rule).
5. https://csrc.nist.gov/glossary/term/risk_response -> rulebook PR
   rules 5.4, 5.5, 6.1, 6.2, 6.3 (transfer needs a named instrument,
   accept needs a stated tolerance, residual rating must be
   post-mitigation, escalate-to-approver when residual exceeds
   tolerance, drop-from-active-list removal rule).
6. https://www.ivanti.com/blog/the-8-best-practices-for-reducing-your-organization-s-attack-surface
   -> rulebook PR rule 5.3, quoted directly in the playbook file cited
   above: disable unused services, ports, and accounts identified
   during modeling, instead of monitoring around them.
7. https://www.nature.com/articles/s41586-021-03380-y (Adams, Converse,
   Hales & Klotz, Nature 594, 2021, "People systematically overlook
   subtractive changes") -> academic-layer section of the rulebook PR,
   grounding why removal rules are forced per-axis rather than left
   implicit (amendment 4's named academic pointer).
canonical: playbook/threat-modeling-decision-rules.md in
tokenmaxxxer/security-threat-model-rulebook@issue-1174/operational-playbook
(this session's own fetch+write, see PR #25 diff) — every rule line in
that file carries its own `Source:` citation to one of the seven fetches
above.

No pretrained-recall content was used as a rule source; every rule
traces to one of the seven fetches above.

## Current kind and loop_state
kind: report
loop_state: pending-review
canonical: gh pr view 25 --repo tokenmaxxxer/security-threat-model-rulebook --json url,state,number — result: state OPEN, no review yet — this record only asserts the PR was opened, not that its content was accepted.

## Open findings
- PR 25's stored description text quotes an earlier, lower rule-count
  figure than the grep output in this file's own derived code fence
  above.
  canonical: this file's derived code fence (grep against
  playbook/threat-modeling-decision-rules.md, this session) compared
  against gh pr view 25 --repo tokenmaxxxer/security-threat-model-rulebook --json body.
  An attempted `gh pr edit` on PR 25 this session hit this parent
  repo's `pr-preflight.sh` amendments-reconciled check: a new issue
  comment (issuecomment-5277040258) landed mid-session, and the hook
  wants an `amendments-reconciled` line inside this role's exact
  phase-2 record path — a path this session cannot write pre-Approve
  (guarded separately by `approval-gate.sh`), matching the precedent
  already recorded on issue #1174 for the `issue-1174/localization`
  fan-out unit.
  next steps: once an APPROVE comment for this role lands (or a
  maintainer judges this evidence-trail record itself sufficient),
  retry `gh pr edit 25` on the rulebook-repo PR, pointing its body at
  the grep-derived counts above.
  resolution path: same rulebook-repo branch
  (`issue-1174/operational-playbook`), one follow-up `gh pr edit` call;
  no playbook content change is needed, only the PR description text.
- No depth-gate script exists yet in the rulebook repo (proposal (c)'s
  `gates/playbook_depth_gate.py` lands in the parent repo per that
  proposal, tracked separately, not owned by this fan-out unit) — the
  rule-count/removal-count figures above come from manual grep, not
  from an automated gate.
  next steps: none owned by this unit; the gate script is a separate
  parent-repo deliverable per proposal (c).
  resolution path: n/a to this unit.

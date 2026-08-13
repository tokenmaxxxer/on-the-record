# Evidence trail: accessibility operational-playbook fan-out (issue #1174)

## What was done
Authored `playbook/aria-and-contrast-rules.md` in the `accessibility`
role's rulebook repo (`tokenmaxxxer/accessibility-rulebook`), on branch
`issue-1174/operational-playbook`, pushed, PR opened:
https://github.com/tokenmaxxxer/accessibility-rulebook/pull/21
canonical: gh pr view 21 --repo tokenmaxxxer/accessibility-rulebook --json url,state,number — result: {"number":21,"state":"OPEN","url":"https://github.com/tokenmaxxxer/accessibility-rulebook/pull/21"}

derived:
```
$ grep -c '^\*\*Rule ' ~/tokenmaxxxer/rulebooks/accessibility-rulebook/playbook/aria-and-contrast-rules.md
9
$ grep -c '\[REMOVAL' ~/tokenmaxxxer/rulebooks/accessibility-rulebook/playbook/aria-and-contrast-rules.md
3
```
9 numbered condition -> choice -> source rules across four areas (ARIA
role selection, accessible naming, WCAG 1.4.3 contrast, focus
order/visibility), 3 of them REMOVAL-category, one counter-example, one
explicitly recorded open gap (roving-tabindex decision tree, not
generalized from a source that doesn't cover it).

## Why
Fan-out unit of issue #1174 ("operational playbooks for all 43 roles:
practitioner decision rules in each rulebook"): the operator's
requirement is condition/choice tables at practitioner depth, sourced
per-rule, landed in each role's rulebook repo (not the marketplace spec
repo, which stays the verification layer).

## Upstream basis
docs/issue-1174/proposals/operational-playbook-program.md

## Evidence trail (fetched sources, this session, 2026-08-13)
1. https://www.w3.org/WAI/ARIA/apg/practices/read-me-first/ -> rulebook
   PR rules 1.1, 1.2, 1.3 (role-is-a-promise; don't cloak native
   semantics; ARIA adds state, not replaces role/name).
2. https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/ ->
   rulebook PR rules 2.1, 2.2, 2.3 (remove aria-label overriding
   content-named roles; prefer visible text; remove
   title/placeholder-as-name).
3. https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html ->
   rulebook PR rules 3.1, 3.2, 3.3 (contrast thresholds by text size,
   unrounded comparison, explicit exemption conditions).
4. https://www.w3.org/WAI/WCAG22/quickref/?showtechniques=241%2C242#focus-order
   -> rulebook PR rules 4.1, 4.2, and the recorded open gap.
canonical: playbook/aria-and-contrast-rules.md in
tokenmaxxxer/accessibility-rulebook@issue-1174/operational-playbook (this
session's own fetch+write, see PR #21 diff) — every rule line in that
file carries its own `Source:` citation to one of the four URLs above.

No pretrained-recall content was used as a rule source; every rule
traces to one of the four fetches above.

## Current kind and loop_state
kind: report
loop_state: pending-review
canonical: gh pr view 21 --repo tokenmaxxxer/accessibility-rulebook --json url,state,number — result: state OPEN, no review yet — this record only asserts the PR was opened, not that its content was accepted.

## Open findings
- Roving-tabindex vs tabindex="0"/"-1" decision rule is not yet
  authored — the fetched WCAG quickref explicitly defers this to
  per-widget APG pattern pages (Listbox, Toolbar, etc.), which were not
  fetched in this round.
  next steps: fetch the relevant per-widget APG pattern page(s) and add
  the rule to the same rulebook branch/PR.
  resolution path: one APG pattern-page fetch per widget type, appended
  to playbook/aria-and-contrast-rules.md in a follow-up commit on
  issue-1174/operational-playbook, before broadening past these four
  areas.
- This fan-out unit covers 4 of the operator's named domains (ARIA,
  naming, contrast, focus) for the accessibility role only; the
  parent issue's full scope (all 43 roles) is handled as separate
  fan-out units per the issue's own sequencing, not by this record.
  next steps: none owned by this record — other roles' rulebooks are
  out of this session's write scope.
  resolution path: n/a to this unit; tracked at the parent issue level.

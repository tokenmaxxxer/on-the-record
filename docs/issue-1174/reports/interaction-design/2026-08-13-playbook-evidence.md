---
code_under_review:
  - interaction-design/playbook/01-form-control-and-layout.md (in tokenmaxxxer/interaction-design-rulebook)
type: feature
breaking: false
canonical: acceptance: python3 gates/playbook_depth_gate.py /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-interaction-design/interaction-design/playbook/01-form-control-and-layout.md --role interaction-design --floor 6 --axes addition,removal — result: PASS
verdict: pass
loop_state: escalate
---

## What was done

canonical: commit 96cd8ae on branch issue-1174/interaction-design in
tokenmaxxxer/interaction-design-rulebook (git log this turn, this
session's own push output).

Authored batch-1 operational playbook for the `interaction-design` role
per the approved phase-1 proposal
(docs/issue-1174/proposals/operational-playbook-program.md) and this
fan-out unit's brief: `interaction-design/playbook/01-form-control-and-layout.md`
in the role's rulebook checkout
(/home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-interaction-design/interaction-design).

7 condition->choice->source decision rules (R1-R7), one REMOVAL-category
rule (R7, modal misuse), a counter-example test per rule, a quick-
reference table, and a Provenance section stating research method and
open scope. canonical: this session's own WebSearch tool-call transcript
this turn (query log reproduced below) — every rule's source was
fetched live via WebSearch on 2026-08-13 against NN/G and W3C/WAI/WebAIM
primary sources; no pretrained-recall content was used to generate the
ratios/thresholds themselves.

Verified against this repo's own gate:
```
$ python3 gates/playbook_depth_gate.py /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer/runs/rulebooks/tokenmaxxxer-interaction-design/interaction-design/playbook/01-form-control-and-layout.md --role interaction-design --floor 6 --axes addition,removal
ACCEPT [addition] #0: 'R1 — control type by option count (small sets)' — ok
ACCEPT [addition] #1: 'R2 — control type by option count (large sets)' — ok
ACCEPT [addition] #2: 'R3 — field grouping by proximity, not by column' — ok
ACCEPT [addition] #3: 'R4 — navigation depth vs. breadth' — ok
ACCEPT [addition] #4: 'R5 — text contrast floor' — ok
ACCEPT [addition] #5: 'R6 — non-text (icon/control-boundary) contrast floor' — ok
ACCEPT [removal] #6: 'R7 — REMOVAL: modal used for non-blocking or mid-task content' — ok
REJECT #7: 'Rule table (condition -> choice, quick reference)' — no source citation
REJECT #8: 'Provenance' — no choice/action verb; no source citation

role=interaction-design accepted=7 floor=6 count_ok=True
PASS
```
floor=6 is a working value chosen for this batch by this session, not a
recorded program-wide N. canonical: `python3 -c "import
json;print(json.load(open('roles/specs/interaction-design.spec.json')))"`
run this turn — output has no `rule_count_floor`/`playbook_refs` keys,
confirming the phase-1-set N (issue #1174 requirement 4) is not yet
recorded anywhere in this role's spec.

## Evidence trail — sources fetched per rule (2026-08-13, WebSearch)

canonical: this session's own WebSearch tool-call outputs this turn
(five WebSearch calls, listed below with their queries and the source
URLs each returned and that the playbook cites).

- R1/R2 (control type by option count): query "Nielsen Norman Group form
  field input type selection dropdown vs radio buttons guidelines" —
  https://www.nngroup.com/articles/checkboxes-vs-radio-buttons/ ,
  https://www.nngroup.com/articles/listbox-dropdown/ ,
  https://www.nngroup.com/articles/web-form-design/
- R3 (proximity grouping): query "Nielsen Norman Group Gestalt proximity
  grouping form fields related inputs" —
  https://www.nngroup.com/articles/gestalt-proximity/ ,
  https://www.nngroup.com/articles/form-design-white-space/ ,
  https://www.nngroup.com/articles/common-region/
- R4 (nav depth vs breadth): query "Nielsen Norman Group menu navigation
  depth breadth mega menu guidelines" —
  https://www.nngroup.com/articles/mega-menus-work-well/
- R5/R6 (contrast floors): query "WCAG contrast ratio requirements text
  non-text 1.4.3 1.4.11" —
  https://www.w3.org/WAI/WCAG21/Understanding/non-text-contrast.html ,
  https://webaim.org/articles/contrast/
- R7 (modal removal): query "Nielsen Norman Group modal dialog overuse
  when not to use modals" —
  https://www.nngroup.com/articles/modal-nonmodal-dialog/ ,
  https://www.nngroup.com/articles/popups/

## Why

Requirement: northpole req#1/req#5 (specialist delegation is only real
with specialist knowledge at decision depth) as cited in issue #1174;
this is the `interaction-design` role's own fan-out unit of that
program's batch 1 (issue #1174 requirement 6: UX/design family first).

## Upstream basis

Based on: docs/issue-1174/proposals/operational-playbook-program.md,
and gates/playbook_depth_gate.py landed at commit 3321d3e on this branch
canonical: `git log --oneline -5` run this turn shows 3321d3e as
"issue-1174: playbook depth gate, spec pointer field, tracker
rendering" on this branch's history.

## Open findings

1. PR against tokenmaxxxer/interaction-design-rulebook could not be
   opened from this session. canonical: this session's own `gh pr
   create --repo tokenmaxxxer/interaction-design-rulebook ...` tool
   call this turn returned exit code with stderr "upstream-defect-scope-guard:
   `gh pr create` ... is denied — the upstream defect channel files
   issues only, never PRs (issue #1131 req#4)" — the guard's own denial
   fires because its target-repo check treats any `--repo` differing
   from this session's git origin (tokenmaxxxer/on-the-record) as
   in-scope for denial, not only the upstream-defect channel it names.
   The rulebook branch (issue-1174/interaction-design, commit 96cd8ae)
   IS pushed to origin on tokenmaxxxer/interaction-design-rulebook —
   canonical: this session's own `git push` output this turn showed
   `96cd8ae..96cd8ae issue-1174/interaction-design -> issue-1174/interaction-design`
   accepted by the remote; only the PR-open call is blocked.
   resolution path: on-the-record's external relay opens
   https://github.com/tokenmaxxxer/interaction-design-rulebook/compare/main...issue-1174/interaction-design
   , or a future revision of the guard adds an explicit allow-shape for
   a role's own rulebook-repo delivery PR (distinct from the
   upstream-defect-report channel it was built to block).
2. Batch coverage is partial: 7 rules against a working floor of 6, not
   yet the phase-1-set N from issue #1174 requirement 4 (see canonical
   spec-read above — that field is absent). Open axes named in the
   playbook's own Provenance section: color-combination visibility
   beyond contrast, usage-frequency-to-menu-depth beyond R4,
   background/editing-surface separation.
3. `roles/specs/interaction-design.spec.json` has no `playbook_refs`
   entry pointing at this playbook file yet (issue #1174 requirement 5
   wiring), per the same canonical spec-read above — out of this unit's
   frozen scope (playbook authorship only).

## Next steps

- Land the rulebook PR once open finding #1 resolves (relay or guard
  fix).
- A follow-up interaction-design batch to round the rule count up
  against a formally recorded N, and to cover the open axes named above.
- Wire `playbook_refs` in the role spec (separate unit — likely
  requirements-engineering or implementation role, not this one).

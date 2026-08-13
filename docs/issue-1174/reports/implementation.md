---
code_under_review:
  - gates/playbook_depth_gate.py
  - gates/test_playbook_depth_gate.py
  - gates/playbook_tracker.py
  - gates/test_playbook_tracker.py
  - gates/role_spec_shape.py
  - gates/test_role_spec_shape.py
  - docs/specs/role-spec-template.schema.json
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
# canonical: acceptance: python3 -m pytest gates/test_playbook_depth_gate.py gates/test_playbook_tracker.py gates/test_role_spec_shape.py -q — result: PASS
verdict: pass
loop_state: landed
---

## What was done

canonical: commit 3321d3e on this branch (git log this turn).
Built the verification infrastructure for the operational-playbook
program per the approved phase-1 proposal
(docs/issue-1174/proposals/operational-playbook-program.md, sections
(c)/(e)):

1. `gates/playbook_depth_gate.py` — `classify_block()` counts
   condition+choice+source rule blocks in a role's playbook text and
   rejects glossary-shaped (definition-only) blocks; `evaluate()`
   enforces the role's recorded `rule_count_floor` and amendment 4 (a
   playbook whose accepted rules are all `addition`-classified fails
   once at least one axis is declared, via `missing_removal_axes`).
   CLI: `python3 gates/playbook_depth_gate.py <file-or-dir> --role
   <name> --floor <N> [--axes a,b,c]`.
2. `roles/specs/*.spec.json` gained an optional `playbook_refs` pointer
   field: added to `docs/specs/role-spec-template.schema.json` and to
   `gates/role_spec_shape.py`'s `check()` via a new
   `check_playbook_refs()` — absent is legal, present entries require
   non-empty `axis`/`repo`/`path`/`section` strings.
3. `gates/playbook_tracker.py` renders a Markdown checklist from
   `roles/*.json` against `roles/specs/*.spec.json`'s `playbook_refs`
   (non-empty = landed) — unchecked roles stay visible in the output,
   never dropped.
4. `docs/specs/enforcement-boundary.md` gained rows registering both
   new gate modules (`gate-registration-guard.sh` requirement).

canonical: gate-registration-guard.sh's PreToolUse refusal this turn
(first commit attempt) forced adding the enforcement-boundary.md rows
before the commit succeeded — mechanical proof both new modules are now
registered.

No rulebook repo, no playbook content, and no per-role `playbook_refs`
edit landed in this PR — those stay out of scope per the proposal's own
"Out of scope" section; this PR is the mechanical validation layer the
per-role fan-out units land against.

## Why

Issue #1174 requires per-role playbooks to clear a depth gate before
landing and a spec-level pointer so quality-bar verdicts can cite a
specific rule; the approved proposal designed both but left the actual
scripts, schema edit, and tracker rendering to a later build step —
this PR is that step.

## Upstream / basis

docs/issue-1174/proposals/operational-playbook-program.md, sections
(c) (depth-gate spec) and (e) (spec→playbook pointer shape); approved
via issue-level comment `APPROVE issue-1174/implementation`.
canonical: `gh issue view 1174 --comments` output read this turn,
containing the exact-string comment `APPROVE issue-1174/implementation`.

## Verification

canonical: pytest run this turn against the three new/changed test
modules directly.
acceptance: python3 -m pytest gates/test_playbook_depth_gate.py gates/test_playbook_tracker.py gates/test_role_spec_shape.py -q — result: PASS
```
28 passed in 0.05s
```
canonical: pytest run this turn against the broader gates/ suite,
selecting the touched-area tests.
acceptance: python3 -m pytest gates/ -q -k "role_spec_shape or spec_schema or playbook" — result: PASS
```
92 passed, 420 deselected in 0.39s
```
canonical: `python3 gates/spec_index.py --update` executed twice this
turn (after the schema edit, and again after the enforcement-boundary.md
row addition) — both runs printed `docs/specs/reconciled-index.md
갱신됨` with no resulting working-tree diff against the committed index,
confirming the index stayed reconciled.

## What did not work

canonical: this session's own commit attempts this turn, described
below.
- First save attempt of this record was refused by two record-shape
  guards for missing evidence tags and for citing paths with no prior
  git history — rewrote with the citations above and committed the
  code files separately first so the paths would resolve.
- The code commit was refused once by a gate-registration guard: the
  two new gate modules had no row in `docs/specs/enforcement-
  boundary.md` — added the rows and re-ran `spec_index.py --update`.
- The code commit was then refused twice more by two guards that
  scanned the whole staged file rather than the diff and matched on
  `enforcement-boundary.md`'s own pre-existing self-documentation
  example strings (unrelated to this change) — used the documented
  commit-trailer escape hatches from each guard's own refusal message
  to proceed.

## Open findings

None open.

## Rationale for deviations

None — build matched the approved proposal's (c)/(e) design; no
scope-exceeded stop and no alternative swap occurred.

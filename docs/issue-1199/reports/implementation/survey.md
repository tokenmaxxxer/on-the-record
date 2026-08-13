# issue-1199 implementation survey (step 1: verification infra)

## Write surfaces
- `gates/playbook_depth_gate.py` (canonical: gates/playbook_depth_gate.py:1-244,
  read this session) — sibling model for #1199's fold-in shape gate:
  `evaluate()`/`classify_block()` split text into blocks, classify each
  with reason strings, return a report dict; `main()` prints a per-block
  table. Grep for an existing tool-learnings entry-shape check:

```
$ grep -rn "tool_learnings\|tool-learnings" gates/ docs/ roles/
```
  (no output — none exists; this is new infrastructure, not an extension.)
- `gates/playbook_tracker.py` (canonical: gates/playbook_tracker.py:1-64,
  read this session) — sibling model for #1199's 43-item tracker:
  `discover_roles()` reads `roles/*.json`, `is_landed()` reads a spec's
  array field, `render()` prints a Markdown checklist. #1199's tracker
  needs the same shape keyed on a different field
  (`tool_learnings_refs`, mirroring `playbook_refs`).
- `roles/specs/accessibility.spec.json` (canonical:
  roles/specs/accessibility.spec.json:1-97, read this session) — no
  `playbook_refs` field present in this sample spec, confirming the
  "field absent => not landed" branch `playbook_tracker.py:is_landed`
  already handles is the live case, not a hypothetical.
- Tests: `gates/test_playbook_depth_gate.py` and
  `gates/test_playbook_tracker.py` (canonical: both files, read this
  session) are the hermetic-test convention to mirror — in-memory
  literals / `tmp_path` fixtures only, no network, no writes outside
  pytest's own tmp dirs.

## Unknowns the survey resolved
- Per-role size cap: issue text says "a size cap per role" but does not
  name a number. Chosen approach: cap on entry COUNT per role's
  tool-learnings section, supplied via a `--cap` CLI arg — mirrors
  `playbook_depth_gate.py`'s existing `--floor` arg style (canonical:
  gates/playbook_depth_gate.py:203-217, read this session), an
  integer read from the command line at call time rather than a
  line/word-length heuristic, which would need a separate, unproven
  prose-length rubric this issue does not specify.
- Tracker denominator: `playbook_tracker.py:discover_roles` derives its
  role list from `roles/*.json` dynamically. Issue #1199's acceptance
  criterion asks for a 43-item tracker for THIS issue specifically.
  Decision: reuse `roles/*.json` as the shared role registry (same
  source both programs draw from) but key landed-state on a distinct
  spec field (`tool_learnings_refs`) so #1174's and #1199's landed-counts
  never share a field, and check the discovered count against 43 in the
  hermetic test fixture rather than baking the literal 43 into the
  renderer, keeping the renderer generic like its sibling per the
  issue's "reuse gates/playbook_tracker.py's convention" instruction.

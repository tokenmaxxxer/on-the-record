---
status: proposed
files:
  - gates/tool_learnings_gate.py
  - gates/test_tool_learnings_gate.py
  - gates/tool_learnings_tracker.py
  - gates/test_tool_learnings_tracker.py
---

## Request
Issue #1199 step 1: build verification infrastructure for the
tool-landscape learnings program — a fold-in shape gate (sibling of
`gates/playbook_depth_gate.py`) asserting each tool-learnings entry
carries `{tool, adoption evidence, problem, how, learning}` with a
fetched-source citation, plus a per-role entry-count cap; and a 43-item
tracker (reusing `gates/playbook_tracker.py`'s convention) for this
issue. This unblocks the later per-role fan-out (step 2+, not this
step).

## Constraints
- Hermetic tests only (issue's own acceptance text: "Hermetic tests").
- Sibling-of, not extension-of: `playbook_depth_gate.py` and
  `playbook_tracker.py` stay untouched — #1199 is a separate program
  from #1174 (issue text: "This is a SEPARATE program from #1174's
  rule-building — it runs independently").
- No per-role content in this step — step 1 is infra only; the 43
  per-role fan-out units are separate future work (issue's own
  execution plan: "step 1 implementation (fold-in shape gate + tracker
  wiring)" vs "step 2+ per-role fan-out units").

## Rationale
Considered extending `playbook_depth_gate.py` in place with a
`--mode tool-learnings` flag instead of a new sibling file. Rejected:
the depth gate's block classification is tuned to condition+choice+source
rule prose (`_COND_MARKERS`, `_CHOICE_VERBS`, glossary-shape rejection —
gates/playbook_depth_gate.py:24-65); a tool-learnings entry has a
different, fixed-field shape (`{tool, adoption evidence, problem, how,
learning}`) rather than free-form decision-rule prose, and the issue
itself asks for a gate that is "sibling" to the depth gate's *file*, not
a mode switch on it — conflating the two would make one file responsible
for two structurally different acceptance shapes and complicate both
gates' test suites for no coupling benefit (they check unrelated things
and are wired to unrelated programs per the "runs independently"
constraint above).

Considered hardcoding `43` as the tracker's role-count return value
instead of deriving it from `roles/*.json` at render time. Rejected: it
would silently drift from the actual role registry if a role is
added/removed, and `playbook_tracker.py`'s own convention (issue's
explicit ask: "reuse gates/playbook_tracker.py's convention") derives
the role list dynamically rather than hardcoding a count — the 43 is
checked as a test assertion against the live registry, not embedded in
the renderer.

## What will be done
- `gates/tool_learnings_gate.py`: parse a role's tool-learnings section
  (Markdown; entries as `##`/`###` headings or list items under a
  `## Tool learnings` heading, mirroring the depth gate's block-splitting
  approach) into candidate entries, classify each entry as accepted only
  if it carries all five required facets — tool name, adoption evidence
  (stars/downloads/mentions per the issue's tech-feasibility-adoption
  method), problem, how (the design move), and learning naming which
  deliverable/rule/judgment it upgrades — plus a fetched-source citation
  (URL or `source:` line). Enforce a `--cap` on accepted-entry count per
  role (fail if exceeded, per the issue's "bounded... not tool
  catalogs"). CLI: `python3 gates/tool_learnings_gate.py <file-or-dir>
  --role <name> --cap <N>`, exit 0 pass / 1 fail, per-entry reason table
  on stdout — same interface shape as `playbook_depth_gate.py`.
- `gates/test_tool_learnings_gate.py`: hermetic, in-memory literals only
  (mirrors `test_playbook_depth_gate.py`) — covers accept-all-facets,
  reject-missing-each-facet (five cases), reject-no-source-citation,
  reject-over-cap.
- `gates/tool_learnings_tracker.py`: mirrors `playbook_tracker.py` —
  `discover_roles()` reused as-is in spirit (reads `roles/*.json`),
  `is_landed()` checks a spec's `tool_learnings_refs` array field (not
  `playbook_refs`, to keep #1174/#1199 tracking independent per the
  Constraints), `render()` prints the same Markdown-checklist shape.
  CLI: `python3 gates/tool_learnings_tracker.py [--roles-dir] [--specs-dir]`.
- `gates/test_tool_learnings_tracker.py`: mirrors
  `test_playbook_tracker.py` — `tmp_path` fixtures only, never touches
  this repo's real `roles/`/`roles/specs/` trees.

## Out of scope
- The 43 per-role tool-landscape surveys and their fold-in content
  (step 2+ — separate fan-out units per the issue's own plan).
- Wiring `tool_learnings_refs` into any real `roles/specs/*.spec.json`
  file (that happens per-role, in step 2+, as each role's survey lands).
- Any change to `playbook_depth_gate.py` or `playbook_tracker.py`
  themselves.

## How you'll know it worked
- `pytest gates/test_tool_learnings_gate.py
  gates/test_tool_learnings_gate.py -q` passes hermetically (no network,
  no writes outside tmp_path).
- Running the gate against a hand-built sample entry missing one of the
  five required facets fails with that facet named in the reason table;
  a complete entry with citation and within cap passes.
- Running the tracker against a `tmp_path` fixture with N roles and M
  `tool_learnings_refs`-carrying specs renders `(M/N)` with the correct
  checked/unchecked marks.

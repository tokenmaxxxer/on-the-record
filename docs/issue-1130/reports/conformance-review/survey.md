---
name: conformance-review-survey
description: issue-1130 current-state survey — landed role-expertise-realization artifact vs. issue body/acceptance
---

# Current-state survey — issue #1130

kind: survey
subject: issue-1130

## Board condition

canonical: `docs/issue-1130/reports/implementation.md`, read directly this
session — `verdict: landed`, basis `103130b` (merge of PR #1148),
`dbe8d53` (merge of PR #1147).

canonical: `find docs -iname "*conformance*" -path "*1130*"`, run this
session, no output — no conformance-review record for this subject
exists yet, so the board condition this role fires on is met.

## Target artifact (what landed)

canonical: `git log --oneline --all -- docs/issue-1130`, run this
session:

```
197f5266 issue-1130: phase-2 implementation record (board record-only)
50b7ca71 issue-1130: fix substitution bypass in the 5 new deny gates (warrant hunt)
ba8ecd8a issue-1130: fix proposal write-set/body mismatch found by warrant hunt
d9f2393e issue-1130: phase-1 proposal — role expertise realization for cause-d/cause-b roles
```

canonical: `docs/issue-1130/proposals/role-expertise-realization.md`
frontmatter, read directly this session — write set: 14
`roles/specs/*.spec.json` five-activity extensions (content-design,
data-engineering, data-modeling, growth-analytics,
knowledge-management, localization, ml-engineering, observability,
pr-communications, refactoring-legacy, user-discovery, accessibility,
api-design, performance-engineering), 3 new gate-now hooks + tests
(accessibility-guard.sh, api-version-guard.sh, perf-measurement-guard.sh),
4 new cause-b routing-check hooks + shared test
(test-authoring-spawn-check.sh, issue-retrospective-spawn-check.sh,
interaction-design-spawn-check.sh, ux-engineering-spawn-check.sh),
`gates/spec_schema_five_activities_test.py`, and updates to
`on-the-record/hooks/hooks.json`, `docs/specs/role-invariant-coverage.md`,
`docs/specs/reconciled-index.md`.

## Spec basis

canonical: `gh issue view 1130`, read directly this session — the spec
is the issue body's requirements 1-4 and its Acceptance block's two
check clauses. No separate architecture.md exists for this issue; the
phase-1 proposal doubles as spec for this review since its "How you will
know it worked" section restates the acceptance checks verbatim.

## Spot-checks run this session (raw evidence for phase-2; not verdicts)

canonical: `python3 -m pytest gates/ -q -k spec`, run this session:

```
$ python3 -m pytest gates/ -q -k spec
........................................................................ [ 91%]
.......                                                                  [100%]
79 passed, 509 deselected in 0.53s
```

canonical: `roles/specs/*.spec.json` (all 14 in-scope files), read
directly this session via a python loop over each file's top-level
keys — every one of the 14 returned all 7 of `judgment_methodology`,
`planning_methodology`, `deliverable_form`, `feedback_methodology`,
`review_methodology`, `degree_level_knowledge`, `source_standard`.

canonical: `on-the-record/hooks/hooks.json`, read directly this session:

```
$ grep -E "accessibility-guard|api-version-guard|perf-measurement-guard|test-authoring-spawn-check|issue-retrospective-spawn-check|interaction-design-spawn-check|ux-engineering-spawn-check" on-the-record/hooks/hooks.json
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/perf-measurement-guard.sh" },
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/test-authoring-spawn-check.sh" },
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/issue-retrospective-spawn-check.sh" },
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/interaction-design-spawn-check.sh" },
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ux-engineering-spawn-check.sh" }
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/accessibility-guard.sh" },
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/api-version-guard.sh" },
```

canonical: `docs/specs/role-invariant-coverage.md`, read directly this
session:

```
$ grep -E "accessibility|api-design|performance-engineering" docs/specs/role-invariant-coverage.md
| 1 | accessibility | `accessibility-guard.sh` (issue #1130 phase 2) | **gate-now (landed)** | ...
| 2 | api-design | `api-version-guard.sh` (issue #1130 phase 2) | **gate-now (landed)** | ...
| 28 | performance-engineering | `perf-measurement-guard.sh` (issue #1130 phase 2) | **gate-now (landed)** | ...
```

canonical: `git status --short docs/specs/reconciled-index.md`, run this
session, no output — the index is not stale relative to the working
tree.

canonical:
`docs/issue-1130/reports/requirements-engineering/scout-brief.md`, read
directly this session — its `## Sources` section lists a per-role
citation list (named texts/URLs) for all 14 in-scope roles plus a
`Cause-b routing analysis` entry.

canonical: `on-the-record/hooks/accessibility-guard.sh` lines 1-13, read
directly this session — its header comment states file-pattern matching
runs against `tool_input.file_path` "always relative to the target
project root the hook fires in, never hardcoded to this repo's own
layout (issue #1130 req#4)". This is the hook's own stated design, not
yet checked this session against its actual matching code.

## Gaps / open questions for phase 2

canonical: `on-the-record/hooks/accessibility-guard.sh`,
`api-version-guard.sh`, `perf-measurement-guard.sh`, header comments
read this session (see above). Open item for phase 2: read each
script's path-matching code line-by-line before rendering a req#4
verdict — the comments alone are not that check.

canonical: `gh issue view 1130` body, read directly this session. The 6
cause-b routing fixes address the issue's board-condition-never-fires
gap, not one of the four numbered requirements verbatim.

canonical: `docs/issue-1130/reports/requirements-engineering/scout-brief.md`
"Adopt / skip" section, read directly this session.
Open item for phase 2: frame this cluster as its own requirement row
(tied to req#3's gate-now wiring scope), then read each routing-check
hook's own test file body directly for a refusal-case assertion.

canonical: `docs/issue-1130/proposals/role-expertise-realization.md`
§3, read directly this session — names `secure-coding`'s routing fix as
a reuse of `merge-allow-gate.sh` rather than a new file.

canonical: `on-the-record/hooks/merge-allow-gate.sh`, not yet read this
session. Open item for phase 2: read its content directly and diff
against pre-#1130 state for the `record_absent_for` consumer logic and a
matching refusal test.

## Scout

Skipped. Reason: this review's requirement list is extracted directly
from issue #1130's own numbered requirements/acceptance text and the
phase-1 proposal's "How you will know it worked" section, which restate
the acceptance checks verbatim — there is no open design decision for
this review to steer toward an external field; conformance review is a
fidelity check against an already-fixed spec, not a design/deliverable
choice with a market or methodology to survey.

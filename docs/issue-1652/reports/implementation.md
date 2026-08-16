---
code_under_review:
  - spawn.py
  - tests/test_goal_pin.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

## What was done

Implemented issue #1652 (northpole req#6, parent-goal propagation):
spawn.py's spawn-prompt builder (around what were lines 7395-7422) now
extracts the issue TITLE and the `## Acceptance` section's `- check:`
bullets, verbatim, and pins them into the spawned role's task prompt —
so the role sees its clean north star from turn 1, not only after it
chooses to run `gh issue view`.

canonical: `git show ebfa799b -- spawn.py tests/test_goal_pin.py` (this
turn's own commit, read this session).

- Switched the existing `gh_rest.fetch_issue_body` call to
  `gh_rest.fetch_issue`, which returns title+body in one REST round
  trip (already existed in gates/gh_rest.py:57-63, used elsewhere) —
  avoids a second network call for the title.
- Added `spawn._goal_pin_block(title, body)` — a pure function, no I/O
  — that reuses `gates/acceptance_gate.py`'s existing
  `_acceptance_section()` parser (rather than reinventing an `##
  Acceptance` heading-boundary scanner) to isolate the Acceptance
  section, then extracts `- check: <text>` bullet lines with a
  dedicated regex. Returns `""` (no injection at all) when there is no
  Acceptance section or no `check:` bullets in it — matching the
  acceptance criterion's "no empty header injected" / "today's prompt
  exactly" requirement for the no-Acceptance case.
- Wired the same try/except that already wraps the `req_line` gh-fetch
  (spawn.py, `_spawn_one`'s task-construction block) to also compute
  `goal_pin` and splice it into `task` right after `req_line`. Any
  exception (gh missing, network down, REST failure) leaves both
  `req_line = ""` and `goal_pin = ""`, identical to a `fetch_issue`
  call that returns `None` — so the fetch-failure prompt is
  byte-identical to both the pre-change prompt and the
  success-with-no-Acceptance prompt. No comment history is ever read
  or injected — only `title`/`body` from the single issue REST fetch,
  which is the issue's own current description, not a drifted thread.

## Why

northpole req#6 (requirement fidelity): web research cited in the
issue names re-injecting the CLEAN original objective into every
sub-task as the top low-cost anti-drift tactic, since context-fill
progressively marginalizes the original task spec otherwise. Reusing
`acceptance_gate._acceptance_section()` instead of a new heading parser
keeps exactly one definition of "what counts as the Acceptance
section" in the codebase (that gate already owns the canonical
boundary logic and is unit-tested against issue-310's edge cases).

upstream: #1652

## Tests

canonical: `python3 -m pytest -q tests/test_goal_pin.py` — result: 3
passed in 0.79s (this session's own run, reproduced below).

derived: `python3 -m pytest -q tests/test_goal_pin.py`
```
3 passed in 0.79s
```

- `test_title_and_criteria_present_verbatim` — RED before
  `_goal_pin_block` existed (AttributeError: module 'spawn' has no
  attribute '_goal_pin_block'), GREEN after.
- `test_fetch_failure_fallback_byte_identical_to_empty` — calls
  `spawn._goal_pin_block(None, None)` (the observable state
  spawn.py's except-block produces) and asserts `== ""`, matching the
  pre-change fallback exactly.
- `test_no_acceptance_section_leaves_prompt_unchanged` — an issue body
  with no `## Acceptance` heading yields `""` (no header, no crash).

## Acceptance disposition (per issue #1652)

- check: unit test (title+criteria verbatim, fetch-failure
  byte-identical fallback).
  canonical: `python3 -m pytest -q tests/test_goal_pin.py` — result: 3
  passed (see the Tests section above).
  provenance: executed-unit
- check: live — the issue's own acceptance bullet asks for a spawned
  role session's prompt to be inspected inline on a real spawn.
  unverifiable: this session has no live spawn harness / GitHub network
  path to run an actual `spawn.py` invocation against issue #1652 and
  inspect the resulting session log inside this turn — only the unit
  path was executed; this check stays open for a future live spawn.
  provenance: read
- empty state: an issue with no `## Acceptance` section — covered by
  `test_no_acceptance_section_leaves_prompt_unchanged` above, spawns
  with today's prompt exactly (no crash, no empty header injected).
  provenance: executed-unit

## Test-tier disposition (issue #1518 contract)

canonical: `.on-the-record/test-tiers.json` (read this session).

`spawn.py` and `tests/test_spawn.py` are both in `slow`'s
`trigger_change_classes`, so both tiers were run this session:

derived: `python3 -m pytest -q -m "not slow"`
```
1 failed, 2068 passed, 19 xfailed, 2 xpassed in 23.31s
```
The one failure — spec-index staleness for `roles/specs/brand-design`
— pre-dates this change: reproduced against branch tip `c36b039a`
(before any edit in this session) and is unrelated to spawn.py/prompt
construction. Left disposed as a pre-existing failure, out of this
issue's write set.

derived: `python3 -m pytest -q -m slow`
```
100 passed, 2 xfailed in 425.14s (0:07:05)
```

## What did not work

None.

## Open findings

None.

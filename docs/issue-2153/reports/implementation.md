---
issue: 2153
role: implementation
loop_state: landed
upstream:
  - path: docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md
    sha:
code_under_review:
  - on-the-record/hooks/skill-verdict-guard.sh
  - gates/record_lint.py
  - spawn.py
  - on-the-record/hooks/test_skill_verdict_guard.py
type: fix
breaking: false
verdict: pass
---

# issue-2153 — implementation record

## What was done

Narrowed the per-mounted-skill verdict obligation (issue #2039,
`skill-verdict-guard.sh`) to a per-*invoked*-skill obligation: a skill
mounted at spawn time that the session never actually called via the
Skill tool no longer requires a `skill-verdict:` line — not even a
`not-applicable:` row. Only a skill the session actually invoked still
requires one.

canonical: on-the-record/hooks/skill-verdict-guard.sh (working tree,
edited) — added `invoked_skill_names(path, mounted_set)`, scanning the
full transcript (not only the first user message) for assistant
`tool_use` blocks named `Skill`, taking the invoked skill name from
`input.skill`, intersected against the mounted-name set already
extracted from the first-user-message prefixes. A new
`if not invoked: finish(reminder)` short-circuit was added after the
existing `if not mounted: finish(reminder)` one.
`record_lint.skill_verdict_reason_check` is now called with `invoked`
in place of `mounted` as its required-name argument; the refusal
message text was reworded from "마운트된 스킬" to "실제로
호출한(invoked) 스킬".

canonical: gates/record_lint.py:389 (working tree, docstring edit
only) — `skill_verdict_reason_check`'s check logic is unchanged (it
was already generic over whatever name list it is given); the
docstring now describes the hook forwarding the invoked subset instead
of the full mounted list.

canonical: spawn.py:1823-1834 (`_SKILL_VERDICT_PROSE`) and
spawn.py:2343-2361 (inline `skill-obligations-index` directive line) —
both the materialized `.on-the-record/directive/skill-obligations.md`
section and the condensed always-on inline index text were reworded to
state the invoked-only scope and name an optional
`other mounted skills: not triggered` summary line. The substrings
`tests/test_spawn_directive_assembly.py`/`tests/test_directive_diet_2135.py`
assert on directly (`스킬-verdict 의무(이슈 #2039)`,
`정확히 하나씩 남겨야 한다`, `skill-verdict:`, `applied:`,
`not-applicable:`, `.on-the-record/directive/skill-obligations.md`)
were kept verbatim in the reworded prose.

canonical: docs/handbooks/skill-verdict-obligation.md (working tree,
edited) — rewritten to describe the invoked-only scope.

canonical: docs/specs/enforcement-boundary.md:166 (working tree,
edited) — the `skill-verdict-guard.sh` row updated to describe the
invoked-subset scan.
canonical: acceptance: `python3 gates/spec_index.py --update` — result:
ran clean, `docs/specs/reconciled-index.md` regenerated with no byte
diff, executed this turn.

canonical: on-the-record/hooks/test_skill_verdict_guard.py (working
tree, edited) — `_write_transcript` gained an `invoked=()` parameter
that appends simulated `Skill`-tool `tool_use` transcript entries. The
tests exercising the "this skill is required" path now supply
`invoked=[...]` explicitly for the skills they expect to be required.
Two new tests target this issue's two acceptance criteria directly:
`t_mounted_but_not_invoked_needs_no_verdict` (a mounted, never-invoked
skill needs no line) and
`t_invoked_skill_verdicts_only_for_invoked_subset_pass` /
`t_issue_2044_line_with_two_of_six_invoked_needs_only_those_two` (a
record carrying verdicts only for the invoked subset of mounted
skills), while `t_missing_skill_verdict_line_is_blocked` now invokes
its skill first so it still exercises "an invoked skill's own missing
verdict is refused."

## Why

canonical: derived: gh issue view 2153 --json body

```
Live measurement (fixture issue #43, docs-only, single-phase): the
session spent ~110s of a 377s run on record ceremony, including
writing a skill-verdict row for ALL 19 mounted skills when only 1-2
fired. A 'not used' row for 17 unfired skills answers no audit
question -- it is ceremony, not record.
```

The obligation's own point — close the gap where a session ignores a
skill with zero consequence — only bites on a skill the session
actually engaged with; a "not-applicable" row for a skill nobody
looked at answers no audit question. Scoping the requirement to
invoked skills (detected from real `tool_use` evidence in the
transcript, not a second self-report) keeps the real catch (issue
#2062's invoke-before-apply marker already proves invocation happened
before a skill's content is applied) while dropping the rows for
skills that were never engaged.

Considered and rejected: keeping the requirement scoped to all mounted
skills but making the "not-applicable" line optional/summarizable.
Rejected because that leaves the shape check itself demanding a line
(or an escape line) for every mounted name regardless of engagement —
the acceptance criteria ask for the requirement to narrow to invoked
names, not for a cheaper way to satisfy an unchanged per-mounted-name
requirement.

## Upstream basis

Builds on issue #2039's mechanism
(`docs/issue-2039/proposals/2026-08-22-per-skill-verdict-obligation.md`,
landed as `on-the-record/hooks/skill-verdict-guard.sh` +
`gates/record_lint.py`'s `skill_verdict_reason_check`) and issue
#2062's invoke-before-apply marker (`applied: invoked; ...`), both
already in the working tree at session start. Based on:
cad6d38ddcc13fb36ca149428eb81e710bd16f9a (main tip / HEAD at session
start).

## What did not work

None.

## Rationale for deviations

None. No divergence from an approved phase-1 proposal occurred — this
session ran under the `CORE_BUILD_NOW=1` build-now bypass (contract v3
s19a), which skips the phase-1 proposal round entirely, so there is no
approved proposal to diverge from. This heading is present only
because the record-shape gate's keyword check reads the hook-name
citations above (the existing sibling hook this fix's shape mirrors,
whose own name contains that keyword) as a deviation signal — not
because any scope-exceeded stop or plan swap happened in this session.

## Doc placement

- handbooks: `docs/handbooks/skill-verdict-obligation.md` (rewritten in place)
- specs: `docs/specs/enforcement-boundary.md` (row updated),
  `docs/specs/reconciled-index.md` (regenerated)
- reports (this issue): this record, filed under the standing
  per-issue reports bucket

## Acceptance verification

canonical: acceptance: `python3 -m pytest on-the-record/hooks/test_skill_verdict_guard.py -q` — result: pass, executed this turn, output below

```
...............                                                          [100%]
15 passed in 1.02s
```

canonical: acceptance: `python3 -m pytest gates/test_record_lint.py -q` — result: pass, executed this turn, output below

```
....................................................................     [100%]
68 passed in 1.01s
```

canonical: acceptance: `python3 -m pytest tests/test_spawn_directive_assembly.py tests/test_directive_diet_2135.py -q -m slow -k "not test_without_flag_is_byte_identical_to_today"` — result: pass, executed this turn, output below (the excluded test fails identically against unmodified HEAD — confirmed via `git stash` + rerun before any of this session's edits — due to this sandboxed session's own `CORE_BUILD_NOW` env var leaking into the test's env-isolation assertion; unrelated to this change)

```
..................                                                       [100%]
18 passed in 1.30s
```

canonical: acceptance: `python3 -m pytest gates/ on-the-record/hooks/ -q` — result: pass, executed this turn, output below

```
2754 passed, 10 xfailed in 17.49s
```

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

## skill-verdicts

canonical: this session's own transcript — no `Skill`-tool `tool_use`
entry was made this session, for any of the four mounted skills
(implementation-complexity-coupling-management,
implementation-design-pattern-selection,
implementation-performance-data-structure-choice,
implementation-blueprint — role→skill-repository mapping,
skill-repository 297e350). Under the invoked-only obligation this
record's own change implements, an un-invoked mounted skill owes no
`skill-verdict:` line — recorded here as the one summary line
`docs/handbooks/skill-verdict-obligation.md` names as optional:

other mounted skills: not triggered — the fix mirrors an
already-established existing sibling-hook pattern (the transcript-scan
shape of the hook mentioned above, and `record_lint.py`'s existing
one-function-per-rule convention) rather than opening a fresh
structure, GoF-pattern, coupling, or data-structure choice, so none of
the four coupling/pattern/data-structure/blueprint skills' triggers
matched closely enough to invoke.

---
issue: 2579
role: implementation-audit-4d2b6d61
author: implementation-audit-4d2b6d61
loop_state: complete
type: implementation
breaking: false
verdict: present
code_under_review:
  - directive_assembly.py
  - spawn.py
  - test/test_spawn_skills_mount.py
upstream:
  - path: directive_assembly.py
    sha: same-commit
---

# issue-2579 — implementation-audit-4d2b6d61 record

## What was done

Landed the residual piece the reopened issue #2579 named: the **record
provenance stamp**. `origin/main` already carried the `<source>:<name>`
qualifier and content-hash collision fix, and did not yet carry the
stamp — verified before starting:

```
derived: git show origin/main:skills.py | grep -c '_SKILL_SOURCE_LABELS\|_parse_skill_token'
result: 3
derived: git show origin/main:directive_assembly.py | grep -c skill_sources
result: 0
```

PR #2584 (closed; canonical: `gh pr view 2584` output, state CLOSED)
carried the stamp bundled with re-applications of the already-landed
qualifier/collision work, which is what made it unmergeable. This
change extracts only the stamp from that PR's diff (canonical: `gh pr
diff 2584`), rebased onto current `main`.

1. `directive_assembly.py::_stamp_additive_record_fields()` gains a
   `skill_sources: list | None = None` parameter. When truthy, it
   appends a second frontmatter line after `author:`:
   `skills: <name> (<source description>), ...` — one entry per
   mounted skill, using the existing `_sp._describe_skill_match()`
   one-liner (the same description already used in the task-injected
   "마운트된 스킬" text, #1742/#1774). Omitted entirely when
   `skill_sources` is empty/`None`.
2. `write_record_skeleton()` gains the same `skill_sources` parameter
   and threads it into `_stamp_additive_record_fields()`. PR #2584 had
   added this as the function's 4th positional parameter; current
   `main` had since grown its own 4th parameter (`task_text`, issue
   #2575's is-coding detector) that #2584's base predates, so here it
   is added as a 5th, keyword-passed parameter instead of colliding
   with `task_text`.
3. `spawn.py`'s only call site (inside the bootstrap sequence, next to
   the existing `write_record_skeleton(cwd, issue, role,
   _cross_family_task_text)` call) now passes
   `skill_sources=skill_sources` — the same `skill_sources` list
   `resolved_skill_sources()` already computes earlier in the same
   function for the roster/directive-mounting logic; no new
   resolution, just reusing what already exists in scope.
4. `test/test_spawn_skills_mount.py` gains a new test class, taken from
   PR #2584 unchanged: one test asserts the `skills:` line's exact
   text for a two-skill, two-source list; another asserts the line is
   entirely absent when no skills are mounted. derived: `git diff
   --stat test/test_spawn_skills_mount.py` —
   ```
   1 file changed, 32 insertions(+)
   ```
   Pass-count evidence (this change vs. the change stashed out) is
   under Acceptance evidence below.

## Why

The reopened issue's own diagnosis (canonical: `gh issue view 2579
--json comments -q '.comments[-1].body'`, quoted below under Upstream
basis) already located the gap precisely — no design decision was open
here, just correctly-scoped extraction. The one judgment call was
where to put the new parameter on `write_record_skeleton()`, resolved
by inspecting the current call site (derived: `grep -n
'write_record_skeleton(' spawn.py`) rather than blindly re-applying PR
#2584's diff, which would have reintroduced a positional collision
with `task_text`.

Non-goal (per spawning task): the stamp carries only skill name and
source, nothing more — no attempt to widen it to versions, hashes
beyond what `_describe_skill_match()` already renders, or timestamps.

## What did not work

None.

## Upstream basis

PR #2584 (closed, GitHub; canonical: `gh pr view 2584 --json
state,headRefName` output — state CLOSED, head
`issue-2579/diagnose-first-3b503f8e`) — the source of the extracted
stamp code and its two tests, verbatim except for the parameter-slot
adjustment described above. Its own record lived at an untracked (on
this branch) path on that closed PR's now-unmerged branch — not
reachable from this branch's history (derived: `git merge-base
--is-ancestor f4a1fba7 HEAD` — result: not an ancestor), so it is cited
here only via `gh pr diff 2584`'s output (canonical, quoted inline
above), never as a direct file path on this branch.

The reopening comment that scoped this session to the stamp alone:
canonical: `gh issue view 2579 --repo tokenmaxxxer/on-the-record --json
comments -q '.comments[-1].body'`.

## Acceptance evidence (executed live)

**The stamp materializes in an actual produced record** (not just "the
code path runs"):

acceptance: python3 script calling `spawn.resolved_skill_sources()` +
`spawn.write_record_skeleton(..., skill_sources=sources)` and printing
the produced file's frontmatter — result:
```
issue: 2579
role: demo-role
author: demo-role
skills: silent-failure-audit (skill-repository(297e350))
loop_state: in-progress
upstream:
  - path: <docs/issue-2579/... or code path this record builds on>
    sha:
```

**No regressions.**

acceptance: `python3 -m pytest test/test_spawn_skills_mount.py -q` —
result:
```
43 passed in 0.99s
```

acceptance: `python3 -m pytest test/ -q` on this branch with the change
in place — result:
```
15 failed, 286 passed in 2.33s
```

acceptance: same command with the change removed (`git stash`) —
result:
```
15 failed, 284 passed in 1.67s
```

derived: diffing the two runs' `short test summary info` blocks —
result: identical set of 15 failing test IDs in both runs, confirming
those failures pre-exist on `main` and this change adds exactly 2
passing tests with zero new failures.

## Open findings

None.

## Next steps

None; frontmatter `loop_state` above is the terminal value for this
record kind.

skill-verdict: implementation-audit — not-applicable: canonical: this
session's own transcript — no `Skill(implementation-audit)` tool call
was issued; the mounted `implementation-audit` skill is a two-session
builder/evaluator claim-extraction protocol for auditing a fresh
implementation against a specification, and this session instead lands
a small, already-scoped code extraction from a prior closed PR's diff
whose exact residual gap the issue's own reopening comment already
named — no specification claim-extraction step applies here.

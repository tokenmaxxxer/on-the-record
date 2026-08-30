---
issue: 2814
role: test-authoring-isolation-and-fixture-strategy-4d970533
author: test-authoring-isolation-and-fixture-strategy-4d970533
skills: test-authoring-isolation-and-fixture-strategy (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: gh issue view 2814
    sha: same-commit
---

# issue-2814 — test-authoring-isolation-and-fixture-strategy-4d970533 record

## What was done

Renamed the five filenames the issue named, `git mv` in every case so history
follows the file — renamed from `test/test_approval_role_field.py` to
`test/test_approval_skill_field.py`; renamed from
`test/test_branch_role_field.py` to `test/test_branch_skill_field.py`;
renamed from `test/test_flows_role_field.py` to
`test/test_flows_skill_field.py`; renamed from
`test/test_roster_role_field.py` to `test/test_roster_skill_field.py`;
renamed from `test/test_spawn_role_skill_resolution.py` to
`test/test_spawn_skill_resolution.py`.

acceptance: `ls test/ | grep -i role` — result (before this session's
changes, executed live at session start):
```
test_approval_role_field.py
test_branch_role_field.py
test_flows_role_field.py
test_roster_role_field.py
test_spawn_role_skill_resolution.py
```
acceptance: `ls test/ | grep -i role` — result (after the five `git mv`
calls above, executed live): empty output, zero matches.

No file body was rewritten beyond the rename itself, except three forward
references that the rename made incorrect and that this issue's third
acceptance criterion requires fixed: the renamed file's own `Run: python3
-m pytest ...` self-reference line, and two other test files' docstring
mentions of the pre-rename name of that same sibling file (population
below). Nothing else in any of the eight touched files changed — same
class names, same test names, same `role`-count inside each renamed
file's body, same prose otherwise.

Population searched for old-path references (checked live, both repos,
docs excluded), report includes the clean sweeps:
- `git grep -n --fixed-strings <old-name>` and a plain recursive `grep -rn
  --exclude-dir=.git --fixed-strings <old-name> .` over the on-the-record
  working tree, run once per old filename (5 filenames x 2 commands = 10
  sweeps) — derived: these 10 sweeps, executed live. Result: clean (zero
  non-docs hits) for renamed-from `test_approval_role_field.py`,
  renamed-from `test_flows_role_field.py`, renamed-from
  `test_roster_role_field.py`, and renamed-from
  `test_spawn_role_skill_resolution.py`. Non-docs hits found only for
  renamed-from `test_branch_role_field.py`, at
  `test/test_approval_gate_carriers.py:11`,
  `test/test_branch_naming_dual_scheme.py:12`,
  `test/test_local_dependency_env.py:9` and `:207`, and the renamed file's
  own line 27. All five lines were updated to cite
  `test/test_branch_skill_field.py` instead — re-swept after the edit:
  derived: `grep -rn --exclude-dir=.git --exclude-dir=docs --fixed-strings
  test_branch_role_field.py .` — result: empty (zero remaining hits).
- CI config sweep of this repo — derived: `find . -path ./.git -prune -o
  -type f \( -name '*.yml' -o -name '*.yaml' -o -iname Makefile -o -name
  tox.ini -o -name pytest.ini -o -name '*.cfg' -o -name '*.toml' \) -print
  | xargs grep -l 'role_field\|role_skill_resolution'` — result: empty,
  zero files.
- Second repo, `tokenmaxxxer-core` (checked out at
  `$ON_THE_RECORD/runs/rulebooks/tokenmaxxxer-core`) — derived: `grep -rn
  --exclude-dir=.git --fixed-strings <old-name> .` inside that repo's
  worktree, once per old filename (5 sweeps) — result: zero hits in all 5.
- `docs/` was excluded from this sweep per the acceptance criterion's own
  population scope. `docs/` paths that mention one of these filenames as
  prose/history exist and were left untouched, per the issue's explicit
  instruction not to touch anything under `docs/` — derived: `git ls-files
  docs/ | grep -i role | wc -l` — result: `58`.

Test-suite collection, before vs. after, compared as SETS OF TEST NAMES
(not just counts):
acceptance: `python3 -m pytest test/ --collect-only -q` (before) —
result:
```
443 tests collected in 0.24s
```
acceptance: `python3 -m pytest test/ --collect-only -q` (after, bytecode
cache cleared first) — result:
```
443 tests collected in 0.10s
```
derived: `diff <(sort before_ids_renamed.txt) <(sort after_ids.txt)`,
where `before_ids_renamed.txt` is the 443 before-run test IDs
(`file::class::test`) with only the filename segment of each ID mapped to
its post-rename name, and `after_ids.txt` is the 443 after-run test IDs,
both sorted — result: empty diff. The two sets of 443 fully-qualified test
IDs are identical once the filename segment is normalized for the rename
— no test appeared, vanished, or changed identity.

Full-suite run, before vs. after (checks the "no new bug" invariant):
derived: `python3 -m pytest test/ -q` run on the pre-rename tree (via
`git stash`) — result:
```
15 failed, 425 passed, 3 xfailed in 31.71s
```
derived: `python3 -m pytest test/ -q` run on the post-rename tree (via
`git stash pop`) — result:
```
15 failed, 425 passed, 3 xfailed in 32.00s
```
derived: `diff before_failures.txt after_failures.txt`, both files built
by `grep '^FAILED'` on the two runs' output and sorted — result: empty
diff, the same 15 `FAILED` test IDs in both runs. None of the 15 is in any
of the 5 renamed files or the 3 files whose forward-reference comments
were edited; they live in `test_convention_equivalence.py`,
`test_local_dependency_env.py`, `test_spawn_artifact_skill_pairing.py`,
`test_spawn_cross_family_skill_selection.py`, and
`test_spawn_skill_judge_haiku_timeout_overlap.py` — pre-existing failures
unrelated to file naming (this issue's declared scope) and to this
issue's stated non-goals.

Invariant: no return of the retired role axis in any reshaped form —
derived: `git show HEAD:test/<old-path> | grep -icE '\brole\b'` compared
against `grep -icE '\brole\b' test/<new-path>` for each of the 5 pairs,
executed live — result per pair (before -> after, renamed-from ->
renamed-to):
```
approval: 5 -> 5
branch:   22 -> 22
flows:    0 -> 0
roster:   2 -> 2
spawn:    3 -> 3
```
Every renamed file's body carries exactly the same count of the retired
noun after the rename as before it (the single 1-line self-reference fix
inside the branch file's own `Run:` line is the only body byte-diff,
already accounted for above) — the rename neither restores the axis nor
newly hides it.

Invariant: no overhead increase — derived: the two collect-only results
quoted above (`0.24s` before, `0.10s` after, both sub-second against the
same `443`-test suite, no growth, same collected count both runs).
derived: `git diff --stat HEAD` — shows only the 5 renames plus 3
one/two-line comment edits; no new fixture, import, or `conftest.py` hook
was added.

Invariant: monitor/watch machinery unbroken and not quieter — derived:
`python3 -m pytest test/test_watchdog_heartbeat_noise.py -q` — result:
```
6 passed in 0.84s
```
derived: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q`
— result:
```
30 passed in 2.36s
```
Neither file was renamed, edited, or referenced by this change; both are
fully green, and neither appears in the 15-item pre-existing `FAILED` set
quoted above (before or after) — same signal, not quieter.

Fourth acceptance criterion — paths carrying the retired noun as a kind,
enumerated across both repos, `docs/` excluded, current (post-rename)
state:

derived: `git ls-files | grep -v '^docs/' | grep -i role` in the
on-the-record repo, executed live post-rename — result:
```
harness/fixture-multirole/.claude-plugin/marketplace.json
harness/fixture-multirole/fixture_multirole/__init__.py
harness/fixture-multirole/fixture_multirole/cli.py
harness/fixture-multirole/fixture_multirole/storage_a.py
harness/fixture-multirole/fixture_multirole/storage_b.py
harness/fixture-multirole/pyproject.toml
harness/fixture-multirole/test_fixture_multirole.py
on-the-record/hooks/role-deviation-directive.sh
on-the-record/hooks/session-role-bind.sh
```
9 git-tracked paths (count is the 9 lines quoted directly above), none of
them one of the five files this issue named (all five now sit at their
renamed-to paths quoted in "What was done" above) and none touched by
this change.

derived: `git -C "$ON_THE_RECORD/runs/rulebooks/tokenmaxxxer-core" ls-files
| grep -v '^docs/' | grep -i role`, executed live against the canonical
checkout of the second repo — result:
```
core/contract/role-handoff-contract.md
core/hooks/lib/role-directive.sh
core/hooks/tests/run-role-directive-staging-tests.sh
core/hooks/tests/run-role-gates-tests.sh
```
4 git-tracked paths (count is the 4 lines quoted directly above). This
repo is also reachable via the on-the-record working tree's
`runs/rulebooks/tokenmaxxxer-core` mount, which is gitignored in this
repo — derived: `git check-ignore -v runs/rulebooks/tokenmaxxxer-core` —
result: matched by `.gitignore:1:runs/` — so it was not double-counted as
a third population.

on-the-record also has one untracked, real, non-`docs/` path carrying the
noun: `.on-the-record/role.json` — derived: `find . -path ./.git -prune -o
-path ./docs -prune -o -iname '*role*' -print`, executed live. This is
this session's own live workspace sidecar (see Open findings item 2),
not a test file and not one of the five this issue named.

None of these 9 + 4 + 1 = 14 non-docs paths is renamed by this change.
Reported per the acceptance criterion's "report the full list including
zero" instruction — for the five files this issue actually names, the
list is zero, shown at the top of this section.

## Why

The issue's own framing is the rationale: `#2600` partitioned the retired
noun's cleanup by occurrence *kind* — env vars, comments/docstrings, prompt
text, identifiers, persisted keys — and a filename is none of those, so no
slice claimed it. The fix is the mechanical one the issue asked for:
rename each file to the vocabulary its own body/tests already use
(`skill`, per `#2741`'s forward-only key rename), using `git mv` so
blame/history survive, then verify the rename changed nothing about what
runs or what other files expect to find at the old path.

The one-word substitution (`role` → `skill`) was chosen per file rather
than a more descriptive rewrite because every renamed file already uses
`skill` as its live vocabulary in the identifiers its tests exercise —
`ci._approved_skills_on_issue`, `flows._pr_approved(..., skill, ...)`, the
`{"skill": ...}` sidecar/record shape read in `test_branch_skill_field.py`
and `test_approval_gate_carriers.py`, and `gates/flows.py`'s
`_ROLE_TRAILER_RE` which matches the literal string `"skill: "` — derived:
`grep -n '_ROLE_TRAILER_RE' gates/flows.py` — result:
```
gates/flows.py:37:_ROLE_TRAILER_RE = re.compile(r"^skill:\s*([a-z0-9-]+)\s*$")
```
— the minimal edit that removes the retired noun and lands on vocabulary
the code already speaks, without touching what the files assert.

## What did not work

None.

## Upstream basis

- `gh issue view 2814` (issue body + acceptance criteria + non-goals),
  read live at the start of this session — same-commit (informs this
  record's own content, not a separate file/commit).
- Prior stranded-relay comments on issue #2814, read live via `gh issue
  view 2814 --comments` — canonical: that command's output, which showed
  a `test-authoring-isolation-and-fixture-strategy-49df91ca` session's
  branch failed PR creation with "No commits between main and
  issue-2814/test-authoring-isolation-and-fixture-strategy-49df91ca" —
  that prior branch carried no commits and nothing from it was reused.

## Open findings

1. Renamed-to `test/test_roster_skill_field.py`'s docstring (lines 1-2,
   unchanged by this rename) reads:
   ```
   """issue #1803: watch/roster explicit `role` field — dual-write,
   field-read, legacy-fallback, and string-key byte-identity coverage."""
   ```
   `#2741` renamed the persisted roster/workspace-index key from `role` to
   `skill`, forward-only — canonical: `grep -n 'entry.get' spawn.py`
   showing `_build_expected`/`_build_observed` reading `entry.get("skill")`,
   and the same file's own
   `WorkspaceIndexDualWriteTest.test_workspace_index_put_writes_role_field`
   asserting a `skill` key is written (test name still says `role_field`,
   also unchanged, also body content). The docstring's "explicit `role`
   field — dual-write" sentence describes a key name the code no longer
   writes. Per this issue's explicit instruction, this is reported and
   left as-is, not rewritten — rewriting it would remove the signal that
   it is stale. Resolution path: a future `#2600`/`#2811`-family slice
   scoped to docstring/comment prose — this issue's own non-goals assign
   file bodies to those, not to this rename.

2. `.on-the-record/role.json` is a real, currently-shipped production
   sidecar filename (written by `spawn.py`'s `issue_workspace()`, read by
   the `approval-gate.sh`, `pr-preflight.sh`, and `contract-guard.sh`
   hooks under `on-the-record/hooks/`, and by `pipeline.py`) whose
   *filename* still carries the retired noun even though its *contents*
   are keyed by `skill` — canonical: `grep -n 'role.json' on-the-record/hooks/pr-preflight.sh`,
   showing the shipped comment "issue #2741: this key was renamed role ->
   skill, forward-only; a sidecar written before that rename no longer
   resolves here" next to the literal path
   `.on-the-record/role.json`. This is a production artifact name, not a
   test filename, and out of this issue's five-file scope — surfaced only
   because the fourth acceptance criterion's path sweep found it.
   Resolution path: `#2626`'s completion judgement, which this issue's
   non-goals name as the consumer of this kind of finding.

3. `on-the-record/hooks/role-deviation-directive.sh`,
   `on-the-record/hooks/session-role-bind.sh`, and the 7
   `harness/fixture-multirole/` paths, plus `tokenmaxxxer-core`'s
   `core/contract/role-handoff-contract.md`, `core/hooks/lib/role-directive.sh`,
   and its two `run-role-*-tests.sh` scripts, also carry the retired noun
   in their paths and are out of this issue's scope (not test files, not
   the five named). Listed in full in "What was done" above per the
   acceptance criterion's "report the full list including zero"
   instruction; none renamed by this change.

## Next steps

None. loop_state is `landed` — derived: this record's own frontmatter, set
in this same commit, after the acceptance commands quoted throughout "What
was done" (`ls test/ | grep -i role`, the collect-only before/after run,
the full-suite before/after run, and the two watch/monitor suite runs)
were all executed live and returned the results quoted there. Findings 1-3
above hand off to the follow-up issues/judgements the original issue's
non-goals already named (`#2600`/`#2811`-family for docstring prose,
`#2626` for the broader completion judgement) — this issue's own scope
(five filenames) is fully addressed by the renames and sweeps above.

skill-verdict: work-in-english — applied: invoked; wrote this record, the
commit messages, and the PR title/body in English per the skill; only the
final user-facing summary is in Korean.
skill-verdict: model-routing — applied: invoked; confirmed the "if a step
takes fewer tool calls than briefing would, do it yourself" guard applies
here (5 mechanical `git mv` calls plus grep sweeps plus one ~32s test run)
and did the whole task in-session without delegating, consistent with
contract v3 s22 overriding the freelunch directive's default-delegate rule
for this headless, single-shot session.
skill-verdict: prose-modes — applied: invoked; wrote this record as a
decision-record/explanation for an expert reader (dense, no hand-holding
connectives per the reader axis), used comparison-style lists per the
mode table, and avoided restating the same acceptance line twice.
skill-verdict: test-authoring-isolation-and-fixture-strategy — not-applicable: invoked to check applicability; this issue is a mechanical filename rename plus reference/collection sweeps, so no fixture construction, scope, isolation/run-order, database cleanup, or test-double decision was made or reviewed.

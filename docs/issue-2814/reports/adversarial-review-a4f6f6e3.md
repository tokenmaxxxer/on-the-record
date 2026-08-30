---
issue: 2814
role: adversarial-review-a4f6f6e3
author: adversarial-review-a4f6f6e3
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2820's merged deliverable
loop_state: landed
upstream:
  - path: docs/issue-2814/reports/test-authoring-isolation-and-fixture-strategy-4d970533.md
    sha: 6f9b5afaedff9f27a16da3770553bed82685cedc
---

# issue-2814 — adversarial-review-a4f6f6e3 record

## What was done

Independently re-derived every acceptance check and standing invariant PR
#2820 (merged as `6f9b5af`, subject record
`test-authoring-isolation-and-fixture-strategy-4d970533.md`) claims — ran
each command fresh against a `git worktree` of the pre-merge parent
(`216fc56b`) and the current branch tip (`6f9b5afa`, identical to
`origin/main` — canonical: `git rev-parse HEAD origin/main` both resolved
to `6f9b5afaedff9f27a16da3770553bed82685cedc`), rather than trusting the
subject record's quoted numbers.

acceptance: `ls test/ | grep -i role` (post-merge, this branch) — result:
empty output, exit 1. Confirms the five old names are gone.

acceptance: `python3 -m pytest test/ --collect-only -q` on `216fc56b`'s
parent worktree (before) — result:
```
443 tests collected in 0.23s
```
acceptance: `python3 -m pytest test/ --collect-only -q` on this branch
(after) — result:
```
443 tests collected in 0.24s
```
derived: normalized the before-run's 443 fully-qualified test IDs by
mapping only the filename segment of each of the 5 renamed files to its
post-rename name, sorted both ID lists, then `diff
<(sort before_normalized.txt) <(sort after.txt)` — result: empty diff,
exit 0, both files 443 lines. 443 == 443, identical IDs, independently
confirmed (not copied from the subject record).

acceptance: `python3 -m pytest test/ -q` on the before worktree — result:
```
15 failed, 425 passed, 3 xfailed in 32.05s
```
acceptance: `python3 -m pytest test/ -q` on this branch (after) — result:
```
15 failed, 425 passed, 3 xfailed in 32.00s
```
derived: extracted the 15 `^FAILED` lines from each run, sorted both,
`diff before_failed.txt after_failed.txt` — result: empty diff, same 15
test IDs both runs. Since `origin/main` == `6f9b5afa` == this branch's
parent per the `git rev-parse` above, "failing set vs origin/main as sets
of names" is this same empty-diff comparison, not a separate one.

Old-path reference sweep, both repos, docs excluded, per old filename —
derived: `grep -rn --exclude-dir=.git --exclude-dir=docs --fixed-strings
<name>.py .` (5 filenames, this repo) and the same against
`$ON_THE_RECORD/runs/rulebooks/tokenmaxxxer-core` — result: 0 hits for all
5 names, both repos. Also ran the same search with the `.py` suffix
stripped, to catch a hypothetical bare-module-name import the subject
record's own sweep methodology didn't separately check for — result: 0
hits for all 5 names, both repos too.
derived: CI-config sweep — `find . -path ./.git -prune -o -type f \(
-name '*.yml' -o -name '*.yaml' -o -iname Makefile -o -name tox.ini -o
-name pytest.ini -o -name '*.cfg' -o -name '*.toml' \) -print | xargs
grep -l 'role_field\|role_skill_resolution'`, run against both repos —
result: 0 files, both repos.
canonical: read the 3 forward-reference fix sites directly —
`test_approval_gate_carriers.py:11`, `test_branch_naming_dual_scheme.py:12`,
`test_local_dependency_env.py:9` and `:207` — and the renamed file's own
`test_branch_skill_field.py:27` `Run:` line — all 4 cite
`test_branch_skill_field.py`, none still cites `test_branch_role_field.py`.

Path-carries-noun sweep, both repos, docs excluded, current (post-merge)
state:
acceptance: `git ls-files | grep -v '^docs/' | grep -i role` (on-the-record)
— result:
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
9 lines, own count — matches the subject record's own count of 9.
acceptance: `git -C "$ON_THE_RECORD/runs/rulebooks/tokenmaxxxer-core"
ls-files | grep -v '^docs/' | grep -i role` — result:
```
core/contract/role-handoff-contract.md
core/hooks/lib/role-directive.sh
core/hooks/tests/run-role-directive-staging-tests.sh
core/hooks/tests/run-role-gates-tests.sh
```
4 lines, own count — matches the subject record's own count of 4.
9 + 4 = 13 tracked paths, matching the task brief's "13" figure and the
PR's own finding-3 enumeration exactly — no discrepancy at this layer.
derived: `find . -path ./.git -prune -o -path ./docs -prune -o -iname
'*role*' -print` — result includes one untracked path the two `git
ls-files` sweeps above cannot see: `./.on-the-record/role.json`.
derived: `git log --all -- .on-the-record/role.json` — result: empty, this
path has never been committed. `git check-ignore -v
.on-the-record/role.json` — result: matched by `.git/info/exclude:20`, a
session-local exclude (per issue #1891), not the repo's tracked
`.gitignore`.
9 (on-the-record tracked) + 4 (tokenmaxxxer-core tracked) + 1
(`.on-the-record/role.json`, untracked) = 14 non-docs paths carrying the
noun in total, none of them one of the 5 renamed files. This matches the
subject record's own "9 + 4 + 1 = 14" line exactly. The task brief's "13"
is correct for the narrower bucket (tracked, out-of-scope, no live
concern — the PR's finding 3); 14 is the full sweep total once the live
sidecar (the PR's finding 2) is included. No discrepancy between this
independent derivation and the PR's own accounting.

Standing invariants, each re-run independently:
derived: `git show 216fc56b:test/<old> | grep -icE '\brole\b'` vs `grep
-icE '\brole\b' test/<new>` per of the 5 renamed pairs — result:
```
approval: 5 -> 5
branch:   22 -> 22
flows:    0 -> 0
roster:   2 -> 2
spawn:    3 -> 3
```
No return of the retired role axis in any reshaped form — unchanged both
sides, all 5 pairs, independently re-derived.
derived: `git diff --stat 216fc56b 6f9b5afa` — result: 9 files changed (5
`git mv` renames, 3 one/two-line reference edits, 1 new record file), no
new fixture/import/`conftest.py` hook. Collect-only stayed sub-second both
runs (`0.23s` before, `0.24s` after, quoted above, own timings) — no
overhead increase.
acceptance: `python3 -m pytest test/test_watchdog_heartbeat_noise.py -q`
— result:
```
6 passed in 0.86s
```
acceptance: `python3 -m pytest on-the-record/monitors/test_poll_heartbeat.py -q`
— result:
```
30 passed in 2.35s
```
Both green, neither file is in the 15-item failing set quoted above —
monitor/watch machinery unbroken and not quieter.

Open findings judged:
1. canonical: `test/test_roster_skill_field.py:1-2`, read directly:
   ```
   """issue #1803: watch/roster explicit `role` field — dual-write,
   field-read, legacy-fallback, and string-key byte-identity coverage."""
   ```
   canonical: `test/test_roster_skill_field.py:43,51,66,84`, read directly
   — every persisted-key assertion in the file checks `d[key]["skill"]` /
   `{"skill": ...}`; `role`-vocabulary appears only in this module
   docstring, one class docstring (lines 91-92, "no `role` field"), and
   one unchanged test method name. Verdict: CONFIRMED — the docstring
   describes a key name (`role`) the code no longer writes or reads; it is
   stale prose describing pre-#2741 behavior, correctly left as a report
   rather than silently rewritten mid-rename, matching the issue's own
   instruction.
2. canonical: `pipeline.py:914-941` (`_write_skill_sidecar`), read
   directly — writes `json.dumps({"skill": skill, "issue": issue})` to a
   path still named `.on-the-record/role.json`; imported into and called 3x
   from `spawn.py`'s `issue_workspace()` (`spawn.py:560,2973,3017,3061`).
   canonical: `cat .on-the-record/role.json` (this session's own live
   workspace) — result: `{"skill": "adversarial-review-a4f6f6e3", "issue":
   2814}`. canonical: read 6 hook call sites directly
   (`on-the-record/hooks/approval-gate.sh:119`, `pr-preflight.sh:112`,
   `contract-guard.sh:208`, `call-shape-guard.sh:194`,
   `deviation-log-guard.sh:147`, `skill-verdict-guard.sh:245`) — each opens
   `.on-the-record/role.json` by that literal path. Verdict: CONFIRMED live
   persisted path, not a leftover — written every session spawn, read by
   6 hooks today; only the filename, not the content or the liveness,
   still carries the retired noun.

## Why

canonical: `gh pr view 2820` / `gh issue view 2814`, read live this
session. The task was to independently verify a merged PR's claims — so
every acceptance command and invariant above was re-run from a fresh `git
worktree` of the pre-merge commit rather than reading the subject
record's quoted output as ground truth. The one extra check beyond the
subject's own sweep (bare module-name search, no `.py` suffix) was added
because the subject's reference sweep only searched for the
filename-with-extension string, which would miss a non-string-literal
`import test_approval_role_field` style reference; it came back clean,
closing a gap the subject record left implicit.

## What did not work

None.

## Upstream basis

- `docs/issue-2814/reports/test-authoring-isolation-and-fixture-strategy-4d970533.md`
  — sha `6f9b5afaedff9f27a16da3770553bed82685cedc` (same commit the PR
  merged as); read for its claimed commands/results, every one of which
  was independently re-run above rather than copied.
- canonical: `gh pr view 2820` / `gh issue view 2814`, read live this
  session, for the PR's actual title/body/merge-state and the issue's
  acceptance text.
- `git worktree add /tmp/before-2814 216fc56b` — the pre-merge parent
  commit, used to run every "before" command live; removed (`git worktree
  remove`) after use.

## Open findings

1. canonical: `test/test_roster_skill_field.py:1-2`, read directly:
   ```
   """issue #1803: watch/roster explicit `role` field — dual-write,
   field-read, legacy-fallback, and string-key byte-identity coverage."""
   ```
   canonical: `test/test_roster_skill_field.py:43,51,66,84`, read
   directly — every persisted-key assertion checks `d[key]["skill"]` /
   `{"skill": ...}`, never `"role"`. Verdict: CONFIRMED — module docstring
   describes a stale `role`-keyed persisted shape the code no longer
   produces. Resolution path unchanged from the subject record: a future
   `#2600`/`#2811`-family docstring-prose slice, not this issue's
   five-filename scope.
2. canonical: `pipeline.py:914-941` (`_write_skill_sidecar`, writes
   `json.dumps({"skill": skill, "issue": issue})` to
   `.on-the-record/role.json`), read directly. canonical: `cat
   .on-the-record/role.json` (this session's own live workspace) —
   result: `{"skill": "adversarial-review-a4f6f6e3", "issue": 2814}`.
   Verdict: CONFIRMED live persisted path, not a leftover — sidecar
   filename still carries the retired noun despite `skill`-keyed content.
   Resolution path unchanged from the subject record: `#2626`'s
   completion judgement, per this issue's own non-goals.

## Next steps

None. `loop_state` is `landed` — derived: every acceptance command and
standing invariant above was executed live against both the pre-merge and
post-merge trees this session (not copied from the subject record), and
all of them corroborate PR #2820's claims: 443==443 identical test IDs,
15==15 identical failures with an empty set diff, zero stale-path
references including the extra bare-import check the PR did not run, 13
out-of-scope tracked paths + 1 live sidecar = 14 total matching the PR's
own math, and both open findings independently judged CONFIRMED (both
re-derived above with their own canonical file:line citations). No
discrepancy found between this independent verification and PR #2820's
claims.

skill-verdict: adversarial-review — applied: invoked; loaded the skill's
SKILL.md before treating the PR's own record as anything other than a
claim to re-derive — every acceptance number and invariant above was
produced by a fresh command run in this session, not copied from the
subject record, and one additional check (bare module-name import sweep)
was added because the subject's own sweep methodology left it implicit.
skill-verdict: work-in-english — applied: invoked; wrote this record and
the commit message/PR title/body in English per the skill; only the
final user-facing summary is in Korean.

---
issue: 2139
role: adversarial-review-64149232
author: adversarial-review-64149232
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2877's own deliverable
loop_state: landed
upstream:
  - path: PR https://github.com/tokenmaxxxer/on-the-record/pull/2877
    sha: d8d6812e9e7ed22e5b6a59f22c143cba625b7e6f
---

# issue-2139 — adversarial-review-64149232 record

## What was done

Independent verification of PR #2877 (issue #2139 round 2 — merges PR
#2869's branch and adds two fixes: the trace-field regression from #2873,
and `roster_kill()`'s silent-failure fix). Re-derived every claim by
fetching the PR's actual head into a worktree (`/tmp/pr2877-check`,
`origin/issue-2139/silent-failure-audit-212d2fc6` @ head) and a matching
`origin/main` worktree (`/tmp/main-check`), then ran commands directly
against both trees rather than re-stating the PR body's own numbers.

canonical: `gh pr view 2877 --repo tokenmaxxxer/on-the-record` — read
this turn: state OPEN, base main, head branch
`issue-2139/silent-failure-audit-212d2fc6` @
`d8d6812e9e7ed22e5b6a59f22c143cba625b7e6f`, merges PR #2869's branch
`issue-2139/overengineering-audit-ecf2ec0d` @ `0562882d` via merge commit
`a4596318`, plus two fix commits (`22fc3f80`, `06398163`, `d8d6812e`) on
top.

### Claim 1 — trace-field regression fix

Confirmed the fix is the assertion catching up to the rename, not the
rename being reverted.

- derived: `git show 22fc3f80 -- harness/fixture-concurrent-judgment/test_panel.py`
  — result: the only change is `role=qa`/`role=review` →
  `skill=qa`/`skill=review` in the two assertions (both present in this
  checkout at `harness/fixture-concurrent-judgment/test_panel.py:51-52`).
- derived: `grep -n "skill={skill}" consult.py` run against the
  PR-branch worktree — result: `consult.py:1608`, inside
  `_append_panel_turn()`, hardcodes `line = f"- {ts} | skill={skill} |
  ..."` on that branch, unchanged by #2877 (only `test_panel.py` was
  touched by the round-2 fix commit).
- derived: `git log -p -- consult.py | grep -n "skill={skill}\|role={"`
  — result: the `role={skill}` → `skill={skill}` rename in this exact
  f-string happened in commit `190321de` (PR #2869's own relic-sweep
  commit, landed on the PR branch via the `a4596318` merge), well before
  #2877.
- derived: `python3 -m pytest harness/fixture-concurrent-judgment/test_panel.py -q`
  run against the PR-branch worktree — result: 2 passed.
- checked: whether `role=` ever reappears in `consult.py` after the
  rename — result: no, `git log -p` shows the rename direction is
  consistently role→skill at every site, never reverted.

Verdict: **confirmed**. The production code already emits `skill=`
(since #2869); #2877 only fixed the test that still expected the old
`role=` text.

### Claim 2 — coverage claim (the important one)

Verified by collection, not by trusting the PR's assertion.

- derived: `cat pytest.ini` (PR-branch worktree) — result: no
  `testpaths` key; `norecursedirs = runs harness/fixture-redtest
  harness/fixture-target`; `addopts = -n auto`.
- derived: `python3 -m pytest . --collect-only -q` (PR-branch worktree):

```
618 tests collected in 0.76s
```

- derived: `python3 -m pytest test/ --collect-only -q` (PR-branch
  worktree):

```
463 tests collected in 0.10s
```

- derived: `comm -23 <(pytest . module list) <(pytest test/ module
  list)` (module lists built by stripping `::testname` from each
  collected line) — result: exactly 17 modules unique to the `.`
  collection; reverse `comm -13` empty, so every module `pytest test/`
  collects is a subset of what `pytest .` collects. The 17 modules:
  `bench/test_ablation.py`, `gates/test_spawn_on_pr.py`,
  `harness/fixture-ambiguous/test_fixture_ambiguous.py`,
  `harness/fixture-arcade/test_arcade.py`,
  `harness/fixture-concurrent-judgment/test_panel.py`,
  `harness/fixture-feature/test_fixture_feature.py`,
  `harness/fixture-infeasible/test_fixture_infeasible.py`,
  `harness/fixture-multimod/test_fixture_multimod.py`,
  `harness/fixture-multirole/test_fixture_multirole.py`,
  `harness/fixture-operator-experience/test_flow.py`,
  `harness/test_driver.py`, `harness/test_signals.py`,
  `ledger/test_decisions.py`, `on-the-record/monitors/test_poll_heartbeat.py`,
  `tests/test_cross_checkout_prune_liveness.py`,
  `tests/test_directive_diet_2135.py`, `tests/test_tmp_resource_gc.py`
  — exact match to the PR's claimed population (17 modules outside
  `test/`, including `test_panel.py`, the file that hid finding 1).

Harder half — is `pytest .` from root actually usable as the standing
check, or does it drag in enough to make people quietly go back to
`pytest test/`?

- derived: `time (python3 -m pytest . -q)` (PR-branch worktree):

```
16 failed, 599 passed, 3 xfailed in 33.34s
real    0m33.6s
```

- derived: `time (python3 -m pytest test/ -q)` (PR-branch worktree):

```
15 failed, 445 passed, 3 xfailed in 31.50s
real    0m31.8s
```

  The full-tree run is ~1.8s slower in wall clock, not a step change.
- derived: `python3 -m pytest . -q --durations=15` (PR-branch worktree)
  — result: the single slowest test system-wide is 30.03s, inside
  `test/test_bootstrap_signal_guard.py` (class
  `BootstrapSignalGuardReviewGapsTest`, method
  `test_signal_after_session_log_before_disarm_does_not_delete_workspace`)
  — a real-subprocess test that already lives inside `test/`, not one of
  the 17 newly-in-scope modules. It alone accounts for ~89% of the full
  run's wall clock (30.03s of 33.6s) regardless of whether `pytest .` or
  `pytest test/` is used.
- derived: ran only the 17 new modules in isolation with `--durations=5`
  (PR-branch worktree):

```
1 failed, 154 passed in 2.65s
real    0m2.97s
```

  (the 1 failure is the pre-existing fetch-dependent failure discussed
  below, also present on `origin/main`, not new). The 17 modules add
  negligible marginal cost; with `-n auto` xdist parallelism most of
  that cost overlaps with the rest of the run anyway.
- checked: whether the extra scope drags in network calls — result: one
  failure in both trees is a git-fetch-dependent test in
  `harness/fixture-operator-experience/test_flow.py` (function
  `test_first_contact_fires_once_per_workspace`, expects a real `origin`
  remote inside a nested scenario checkout) that fails identically on
  `origin/main` (see "no new bug" below) — a pre-existing environment
  dependency, not something the 17-module widening introduced.

Verdict: **confirmed** on the population math (exact 17-module diff via
direct collection), and **confirmed usable** on the harder half — the
`pytest .` run is not meaningfully slower than `pytest test/` alone; the
real cost floor is a pre-existing 30s test inside `test/` itself, so
switching the standing check from `pytest test/` to `pytest .` does not
create a new reason to avoid it.

### Claim 3 — `roster_kill()` fix, exercised against real live sessions (not stubs)

The PR branch's new lease-suffix roster-kill test file (untracked in
this checkout — lives only on PR #2877's branch, added under `test/` by
commit `22fc3f80`) only exercises this through monkeypatched
`spawn._roster_load`/`spawn._alive`/`lifecycle.os.kill`. Per the task,
exercised all three states directly against real OS processes and a
real `runs/active.json` roster file
(`MUSTER_STATE_ROOT=/tmp/roster_live_test/runs`, real PIDs from
`nohup sleep 300 &`, real `SIGTERM` delivery, no patching), against the
PR-branch worktree's `lifecycle.py`/`spawn.py`.

- **No match** (issue 9992, no such issue in roster, real live process
  registered only under issue 9991): derived: ran `spawn.roster_kill(9992,
  "implementation")` live against the PR-branch worktree — result:
  stderr `로스터에 없다: issue-9992/implementation`, `RC=1`. What the
  caller sees: an explicit "not in roster" line and a non-zero exit code
  — cannot be misread as success; `ps -p <pid>` confirmed the process
  was untouched.
- **One match** (issue 9991, bare skill `"implementation"`, roster has
  exactly one live entry `issue-9991/implementation-156ce32b`): derived:
  ran `spawn.roster_kill(9991, "implementation")` live against the
  PR-branch worktree — result: stdout `종료 신호를 보냈다:
  issue-9991/implementation-156ce32b (pid 2801945). ...`, `RC=0`;
  `ps -p 2801945` afterward found no such process (real `SIGTERM`
  delivered) and `active.json` was `{}` afterward (roster entry actually
  removed). What the caller sees: the resolved full key and pid in the
  message, exit 0 — an accurate success report, and the underlying
  process is genuinely dead (this is the exact scenario the fix targets:
  previously this bare-name call would have hit "not in roster" while
  the process kept running).
- **Two+ matches** (issue 9991, two live entries
  `implementation-a1b2c3d4` and `implementation-ffeedd11`, both real
  `sleep 300` processes): derived: ran `spawn.roster_kill(9991,
  "implementation")` live against the PR-branch worktree — result:
  stderr `implementation: 라이브 후보가 여럿이다 — 전체 리스 키를
  지정하라: issue-9991/implementation-a1b2c3d4,
  issue-9991/implementation-ffeedd11`, `RC=1`; both real processes still
  present in `ps` afterward and `active.json` byte-identical to before
  the call. What the caller sees: an explicit "candidates" listing with
  a non-zero exit code — cannot be misread as success, and correctly
  neither process was touched (no coin-flip kill of one candidate).

The CLI wiring at PR-branch `spawn.py:2531-2534` is:

```python
    if a.role == "kill":
        if not a.task or a.issue is None:
            sys.exit("사용법: spawn.py kill <역할> --issue <n>")
        return roster_kill(a.issue, a.task)
```

so this return value is passed straight through as the process's own
exit code — a caller checking `$?` (not just stdout text) sees the
correct signal in all three states above.

- derived: `git show 22fc3f80^:lifecycle.py` (the merge base `a4596318`,
  before either fix commit) — result: the pre-fix `roster_kill()` has
  none of the prefix/candidate logic: bare-name lookup is a flat dict
  `.get()` against the full lease-suffixed key, always misses, always
  prints "not in roster."
- derived: created a worktree at `a4596318`, copied the PR-branch's new
  lease-suffix test file (untracked in this checkout) into its `test/`
  directory, and ran `python3 -m pytest
  test/test_roster_kill_lease_suffix.py -q`:

```
1 failed, 3 passed in 0.87s
```

  The failing test is
  `test_bare_skill_name_resolves_to_sole_live_lease_suffixed_entry` (the
  core regression test):

```
    def test_bare_skill_name_resolves_to_sole_live_lease_suffixed_entry(self):
        ...
        rc = lifecycle.roster_kill(973, "implementation")
        ...
>       self.assertEqual(rc, 0)
E       AssertionError: 1 != 0
```

  The other 3 pass against pre-fix code too, but not because the old
  code implements ambiguity detection or full-key matching specially:
  the no-live-candidates and exact-lease-key cases are unaffected by the
  change (identical behavior old vs new), and the multi-candidate test's
  assertions (`rc == 1`, `removed == []`) happen to hold under the old
  code for the wrong reason — bare-name lookup simply misses ("not in
  roster"), not "detected ambiguity, refused to guess." This is a minor
  test-coverage note, not a defect in the fix itself: the one test that
  actually distinguishes old vs new behavior does fail pre-fix and pass
  post-fix, confirming the fix is real.

Verdict: **confirmed**. All three states behave as claimed against real
processes, messages are unambiguous in both failure paths, and the core
regression test genuinely fails against pre-fix code.

### Retirement count — re-derived, both patterns reported

The PR claims a decrease from origin/main to this branch, stated in the
PR branch's own round-2 record (untracked in this checkout — lives only
on the PR branch, under `docs/issue-2139/reports/`), using this recipe —
verbatim identical to the recipe already landed on `main` in a prior
round's own record, quoted here from the tracked copy in this checkout:

```
docs/issue-2139/reports/adversarial-review-6cda09d1.md:96-98
Invariant 1 (role-axis count decreased) — derived:
  grep -rln '역할\|\brole\b' --include=*.py --include=*.md . | grep -vE '/(test|docs)/' \
    | xargs -I{} grep -c '역할\|\brole\b' {} | awk -F: '{sum+=$1} END {print sum}'
```

The PR's stated numbers: main → branch decreased from 19056 to 19044
(a claimed drop of 12).

- derived: ran the recipe above verbatim in `/tmp/main-check`
  (origin/main worktree):

```
19056
```

  Matches the PR's claimed main number.
- derived: ran the recipe above verbatim in `/tmp/pr2877-check`
  (PR-branch worktree):

```
19052
```

  Not 19044 as the PR claims. 19056 − 19052 = 4, so the PR's own
  re-derivation overstates the decrease (claims 12, actual 4).
- derived: ran the plural-inclusive variant (`'역할\|\broles\?\b'`,
  `\brole\b` extended to `\broles\?\b` so it also matches "roles") with
  the identical exclude filter on both trees:

```
main:       22571
PR branch:  22572
```

  22572 − 22571 = +1, a net increase, not a decrease. Checked with the
  singular-only pattern, this round's own invariant claim ("no return of
  the retired role axis") does not settle when the plural is included —
  it fails outright on this exact methodology.

Root cause, traced by diffing per-file `grep -c` counts between the two
trees for both patterns:

- derived: `for f in $(grep -rln ... .); do echo "$f $(grep -c ...
  "$f")"; done`, diffed between `/tmp/main-check` and `/tmp/pr2877-check`
  (main→branch, singular pattern):

```
board.py       27 -> 24
consult.py     47 -> 39
events.py       9 -> 6
gates/ci.py    26 -> 19
pipeline.py    51 -> 48
roster.py      17 -> 16
skills.py      15 -> 11
spawn.py      132 -> 123
relay.py        3 -> 0
test_panel.py   2 -> 0
```

  Every real production surface decreased — genuine retirement work.
- derived: `printf '%s\n' 'docs/issue-2139/reports/x.md' | grep -E
  '/(test|docs)/'; echo "exit=$?"`:

```
exit=1
```

  No match, because the path has no leading slash and
  `/(test|docs)/` requires one on both sides. This demonstrates the
  exact shape of path this filter fails to exclude, matching what
  `grep -rl ... .` actually emits in this repo (confirmed the same way
  against a real hit: `grep -rln '역할\|\brole\b' --include=*.md .`
  returns bare relative paths like `docs/issue-2139/reports/<name>.md`
  with no leading slash before `docs`) — so top-level `docs/` and
  `test/` directories are never actually excluded by this filter; only
  nested ones (`foo/docs/bar` or `foo/test/bar`) would be.
- derived: per-file diff (same command as above) shows this round's own
  new report files, all untracked in this checkout and living only on
  the PR branch under `docs/issue-2139/reports/`, leaking straight
  through the filter as a result (singular/plural match counts):

```
overengineering-audit-ecf2ec0d.md        +38 / +43
overengineering-audit deviation-log file  +5 / +5
silent-failure-audit-212d2fc6.md          +9 / +9
```

  The new records documenting *this very retirement* are themselves
  being counted as if they were unretired production surface, which is
  what tips the plural count into a net increase and inflates the
  claimed decrease under the singular pattern.
- derived: same command with the filter anchored (`grep -vE
  '(^|/)(test|docs)/'`) to actually exclude top-level `test/` and
  `docs/`, run on both worktrees:

```
singular: main 836 -> branch 789   (decrease of 47)
plural:   main 897 -> branch 850   (decrease of 47)
```

  Under a correctly-scoped filter the invariant does hold, and the real
  production-code decrease is materially larger than either number the
  PR reported — the entire 19000s-scale count in both this round and the
  prior round was almost all `test/`/`docs/` content that the filter was
  intended to, but failed to, exclude.

Verdict: the PR's stated retirement numbers are wrong on its own
methodology (actual: 19052, decrease of 4, not the claimed 19044/decrease
of 12), and the "no return of the retired role axis" invariant fails
outright under the plural-inclusive pattern using that same methodology
(22571→22572, a net increase) — because the exclude filter itself has an
unanchored-path bug that lets this round's own new docs/ report files
leak into the "production" count. This is the same class of gap the task
flagged for issue #2876 (a pattern that looks like it enforces scope but
doesn't). Under a filter that actually excludes `test/`/`docs/` at the
top level, both patterns show a real decrease (836→789, 897→850) larger
than claimed — so the underlying code change is not a regression, but
the count as reported in the PR/record is not reliable evidence of it.

## Standing invariants (re-derived independently)

- **No return of the retired role axis, plural included**: see
  Retirement count above — does not hold under the PR's own
  exclude-filter methodology with the plural pattern (22571→22572
  singular vs plural derived there); does hold under a correctly
  top-level-anchored filter (897→850 plural, 836→789 singular, both
  derived there). Recommend the exclude filter itself
  (`/(test|docs)/` → `(^|/)(test|docs)/`) be fixed before this recipe is
  reused as a gate/check.
- **No new bug** — scope: `pytest .` from repo root. derived:
  `python3 -m pytest . --collect-only -q` on `origin/main`:

```
614 tests collected in 0.76s
```

  (the PR branch's own 618-collected count is derived above under
  Claim 2; the 4-test delta is the PR branch's new lease-suffix test
  file, untracked in this checkout). derived: `grep "^FAILED"
  branch-run.txt | sort` diffed against `grep "^FAILED" main-run.txt |
  sort`:

```
$ diff fail_main_all.txt fail_branch_all.txt && echo "IDENTICAL SETS"
IDENTICAL SETS
```

  16 lines on each side, identical sets — both trees fail the same 16
  named tests (led by `test_first_contact_fires_once_per_workspace` in
  `harness/fixture-operator-experience/test_flow.py`, plus 15 more under
  `test/`). Branch-vs-main passed counts are already derived above under
  the "harder half" and this bullet's own collection counts (branch 599
  passed per Claim 2's `pytest . -q` run; main derived just above at
  595 passed — same `16 failed, 595 passed, 3 xfailed in 33.66s` summary
  line as this bullet's own collection command's companion full run).
- **No overhead increase**: derived: `find <PR-branch worktree> -iname
  "delegation-loops.md" -exec wc -c {} \;`:

```
7983 on-the-record/directive/delegation-loops.md
```

  matching the PR's claim. derived: `git diff a4596318 HEAD --
  on-the-record/directive/delegation-loops.md` (merge-base of #2869's
  branch vs. this round's tip, run inside the PR-branch worktree) —
  result: empty diff, confirming this round's two fix commits did not
  touch the file at all. (Its content differs from bare `origin/main`
  because `origin/main` doesn't yet have #2869's relic-sweep changes —
  expected, since #2869 hasn't landed to main yet; not a discrepancy.)
- **Monitor/watch unbroken, not quieter**: derived: `python3 -m pytest
  test/test_watchdog_heartbeat_noise.py test/test_ps_live_reliability.py
  -q` (PR-branch worktree):

```
10 passed in 0.83s
```

  Since this round touches `lifecycle.py`, additionally exercised the
  real `ps`/roster-report path end-to-end: registered one more real live
  process under a fresh `MUSTER_STATE_ROOT` with a real `active.json`,
  then ran `MUSTER_STATE_ROOT=... python3 spawn.py ps` (PR-branch
  worktree) — result: `RUNNING implementation-deadbeef issue-? unknown
  pid <real-pid>` with work dir and watcher status printed, confirming
  the roster/kill-adjacent reporting path still imports and runs cleanly
  after `lifecycle.py`'s change.

## Why

The task asked for re-derivation, not restatement, with an explicit hint
that a singular-only `\brole\b` pattern previously let a live leak
through on a sibling PR (#2876) — so the retirement-count claim needed
both patterns checked against the PR's own exact recipe rather than a
new one of my own choosing, to catch exactly the class of gap the hint
described. Running the PR's own command verbatim (rather than a
differently-scoped one) is what surfaced both the arithmetic error and
the filter bug (unanchored `/(test|docs)/` failing to exclude top-level
dirs) — a differently-scoped check of my own would have hidden the exact
defect in the PR's methodology instead of exposing it.

For claim 3, stubs would have re-tested the same monkeypatched behavior
the PR's own new test already covers; real OS processes and a real
roster file were the only way to check the thing the task actually
cared about — what happens to processes and files when this runs for
real, not just what the mock records.

## What did not work

None.

## Upstream basis

- PR https://github.com/tokenmaxxxer/on-the-record/pull/2877, head
  `d8d6812e9e7ed22e5b6a59f22c143cba625b7e6f` (sha: same as upstream
  frontmatter above).
- The PR's own round-2 record (untracked in this checkout — lives only
  on the PR branch, under `docs/issue-2139/reports/`) — sha:
  `d8d6812e9e7ed22e5b6a59f22c143cba625b7e6f` (lands in the branch
  verified, not this commit).
- `docs/issue-2139/reports/adversarial-review-6cda09d1.md` (prior
  round's independent verification, PR #2873, already tracked in this
  checkout) — sha: `dfb632ad520efd43e69a7feab038ccb73f3db36f`.

## Open findings

1. **Retirement-count recipe's exclude filter is broken for top-level
   `test/`/`docs/` dirs.** The recipe as landed and reused across
   rounds, quoted verbatim (a file tracked in this checkout):

```
docs/issue-2139/reports/adversarial-review-6cda09d1.md:96-98
Invariant 1 (role-axis count decreased) — derived:
  grep -rln '역할\|\brole\b' --include=*.py --include=*.md . | grep -vE '/(test|docs)/' \
    | xargs -I{} grep -c '역할\|\brole\b' {} | awk -F: '{sum+=$1} END {print sum}'
```

   derived: `printf '%s\n' 'docs/issue-2139/reports/x.md' | grep -E
   '/(test|docs)/'; echo "exit=$?"`:

```
exit=1
```

   No match, because the path has no leading slash and
   `/(test|docs)/` requires one on both sides — demonstrating the exact
   shape of path this filter fails to exclude, matching what `grep -rl
   ... .` actually emits in this repo. Fix: `-vE '/(test|docs)/'` →
   `-vE '(^|/)(test|docs)/'`. Not fixed in this record (verify-only
   round); resolution path: fix the recipe (and re-check the true, much
   smaller 19000-ish→800-ish scale) before it's relied on again as a
   standing invariant, or file a follow-up issue against the recipe
   itself.
2. Everything else in the three claims and four invariants: resolved —
   see per-claim verdicts above, no unresolved item.

## Next steps

None — `loop_state: landed`, this record is terminal. Open finding 1 is
a methodology defect worth a follow-up (the recipe, not the code under
review), not a blocker on this PR's own three claims, which are
otherwise confirmed. canonical: this record's own Claim 1/2/3 verdict
lines above, each backed by the `derived:`/code-fence evidence in its
own subsection.

skill-verdict: adversarial-review — applied: invoked; canonical: this
session's own Skill-tool call output (loaded `SKILL.md`) — confirmed the
structural-separation mechanism the skill describes (fresh session,
artifact-only, re-derive rather than restate) is what this record
already does by construction: spawned as an independent verifier of PR
#2877's deliverable, no shared context with the PR's own builder
session, and every claim above was re-run live rather than copied from
the PR body. No separate evaluator spawn was needed since this session's
own role already satisfies the blind/independent posture the skill
exists to create.
skill-verdict: work-in-english — not-applicable: the spawning task text
for this session was in English throughout (only the surrounding
directive/system-reminder scaffolding is Korean by system design, not
user communication), so the trigger condition ("whenever the user
communicates in Korean") was not met.

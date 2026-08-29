---
issue: 2803
role: adversarial-review-62cce5a5
author: adversarial-review-62cce5a5
skills: adversarial-review (skill-repository(c05de12))
verifies_subject: true  # independent verification of PR #2804, this issue's own deliverable
loop_state: landed
upstream:
  - path: 88d3018eaffd1fab27313c348c11bf6bc1899bac:test/test_spawn_attempt_staleness.py
    sha: 88d3018eaffd1fab27313c348c11bf6bc1899bac
---

# issue-2803 — adversarial-review-62cce5a5 record

## What was done

Independent re-verification of PR #2804 (branch
`issue-2803/test-authoring-isolation-and-fixture-strategy-381e4502`, head
`88d3018e`), which renames the four retired-noun (`role`) skill-slot
literals `test_spawn_attempt_staleness.py` pre-dated PR #2794 with, and
reports one open finding (six remaining prose occurrences of "role
family"). Does not restate PR #2804's own record
(`docs/issue-2803/reports/test-authoring-isolation-and-fixture-strategy-381e4502.md`
— untracked on this branch, `issue-2803/adversarial-review-62cce5a5`,
which has not merged PR #2804's branch) as evidence — every check below
was re-derived from scratch in throwaway git worktrees (`88d3018e` =
after, `88d3018e^` = `cb5d394c` = before, `origin/main` = regression
baseline), using my own search terms for the sweep rather than the PR's.

canonical: `gh pr view 2804` (title, Summary, Test plan, `Closes #2803`)
and `gh pr diff 2804` (full patch: 218 additions / 4 deletions — the two
fixture-literal hunks in `test/test_spawn_attempt_staleness.py` plus the
PR's own new record file).

### Acceptance check 1 — literal grep on the named file

```
$ grep -inE '\brole\b' test/test_spawn_attempt_staleness.py
214:    `secrets.token_hex(4)`) that `spawn.py:1990-1991` appends to every role
291:        """Over-broadening guard: same role family, different issue — must
303:        """Over-broadening guard: same issue, different role family — an
423:    (issue, role-family) must still resolve it."""
479:        # A later attempt for the same (issue, role-family) — different
507:        with no later successful attempt for that issue+role-family. Must
$ echo "exit: $?"
exit: 0
```
derived: confirmed the PR's own claim — 6 matches remain, exit 0 not 1.
The issue's literal acceptance check (`empty state: exit 1, zero matches`)
is not satisfied by this PR. See Open findings for my independent
judgment on whether that is correct scoping.

### Acceptance check 2 — rename is inert

Diff of the file at the PR's parent commit (`cb5d394c`) vs. the PR head
(`88d3018e`), executed-live:
```
$ git show cb5d394c^{}:test/test_spawn_attempt_staleness.py > /tmp/before_test_file.py
$ diff /tmp/before_test_file.py test/test_spawn_attempt_staleness.py
394,395c394,395
<         self._write_attempt("2999:role:1:1", 2999, "role", str(missing),
<                              reason, attempt_ts)
---
>         self._write_attempt("2999:stillblockedfault:1:1", 2999, "stillblockedfault",
>                              str(missing), reason, attempt_ts)
408,409c408,409
<         self._write_attempt("3000:role:1:1", 3000, "role", str(missing),
<                              reason, attempt_ts)
---
>         self._write_attempt("3000:tscarryfault:1:1", 3000, "tscarryfault",
>                              str(missing), reason, attempt_ts)
```
derived: exactly the four-line diff the PR claims, nothing else touched.

Test-name-SET comparison, before vs. after, in separate worktrees
(`git worktree add`, `-n0` to avoid xdist `[gwN]` noise in the name
extraction):
```
$ python3 -m pytest test/test_spawn_attempt_staleness.py -v -n0   # before (cb5d394c)
41 passed in 0.11s
$ python3 -m pytest test/test_spawn_attempt_staleness.py -v -n0   # after (88d3018e)
41 passed in <similar>
$ diff <(sort before_names) <(sort after_names)
(empty)
```
derived: `diff /tmp/before_names2.txt /tmp/after_names2.txt` — result:
empty, exit 0. Identical 41-name PASSED set both sides.

Each renamed fixture still drives the same code path — read, not just
diffed:
```
$ grep -n "def _write_attempt" -A5 test/test_spawn_attempt_staleness.py
def _write_attempt(self, attempt_id, issue, skill, cwd, reason, ts):
    ...
    fh.write(json.dumps({"event": "spawn_attempt", "attempt_id": attempt_id,
                          "issue": issue, "skill": skill, "pid": 4242, ...
```
`"stillblockedfault"`/`"tscarryfault"` land in the exact same third
positional slot (`skill`) the old `"role"` literal occupied, and the
colon segment of `attempt_id` mirrors it — this is the skill slot the
issue's Ask names, not a different field. The two tests' assertions
(`self.assertIn("spawn halted pre-workspace", printed)`,
`self.assertIn("attempted at", printed)`,
`self.assertIn(roster._iso(attempt_ts), printed)`) reference unrelated
substrings, not the identifier itself, so nothing else could have broken
silently. Rename confirmed inert both by name-set equality and by reading
what the two tests actually assert.

### Acceptance check 3 — sweep both repos for the shape (re-derived independently)

**on-the-record**, my own regex shapes (not the PR's):
```
$ git ls-files test/ | wc -l
40
$ grep -rn '"role"' test/ ; grep -rn "'role'" test/
$ grep -rnE '[0-9]+:role:[0-9]+:[0-9]+' test/
(all three: empty, exit 1)
```
derived: zero, matching the PR's claim, and matching the 40-file
population count it cites.

**tokenmaxxxer-core**, using the checkout already present at
`$MUSTER_WORKSPACE_ROOT/tokenmaxxxer-core-issue-233-adversarial-review-13d75b7e`
(verified this is the same commit the PR's record cites — `git rev-parse
HEAD` → `e7f1c4e6e183c40846351105d4c98c1ff355eada` — before trusting it as
a stand-in for a fresh clone):
```
$ git ls-files | grep -iE '(^|/)test' | wc -l
49
$ git ls-files core/hooks/tests/ core/hooks/test_board_gate.py | wc -l
34
```
derived: **the PR's record misstates its own search population.** It
claims to have swept "all 49 files matching test... specifically
`core/hooks/tests/*` (42 files, mostly `.sh`) and
`core/hooks/test_board_gate.py`" — but `core/hooks/tests/` alone has 33
files (not 42), and 33+1=34, not 49. The 15 files the shown sweep commands
never touch:
```
freelunch/hooks/tests/parse-check.sh
freelunch/hooks/tests/run-observe-tests.sh
scout/hooks/tests/parse-check.sh
terse/hooks/tests/parse-check.sh
test/hooks/test_handbook_trigger_gate.sh
test/hooks/test_trailer_gate.sh
test/test_directive_injection.py
tests/test_ordering_gate_livefire.py
tests/test_ordering_gates_237.py
tests/test_promoted_hooks.py
tests/test_side_effect_round.py
tests/test_silent_failure_repros.py
warrant/hooks/tests/run-directive-hunt-path-tests.sh
warrant/hooks/tests/run-hunt-guard-tests.sh
warrant/hooks/tests/run-hunt-tier-tests.sh
```
I swept these 15 myself:
```
$ grep -nE '[0-9]+:role:|"role"|'"'"'role'"'"'' <the 15 files above>
(empty, exit 1)
$ grep -lE 'attempt_id|spawn_attempt|_write_attempt' <the 15 files above>
(empty — none of them even carry the attempt_id/skill-slot concept)
```
derived: zero, so **the PR's final zero-occurrence conclusion for
tokenmaxxxer-core still holds** — but only because I extended the sweep
myself. The record's stated methodology ("all 49 files... specifically
[this list]") does not match what its own shown commands actually
covered, which is the same category of failure the issue exists to catch
(a completeness claim that outruns what was actually searched). This is
reported as a **process/rigor finding on the PR's evidence, not a
correctness defect** — the underlying claim (zero occurrences) survives
independent re-derivation over the true 49-file population.

## Open findings

1. **The six remaining "role family" prose occurrences are stale
   vocabulary for a live concept, not a separate legitimate use of the
   word — the PR's "unverifiable" framing undersells what's determinable
   from the file itself.** The PR's record tags this ambiguity as
   `unverifiable: whether the issue author intended... "zero after fixing
   only the four named places" or "zero over the whole file"`. I read the
   file directly rather than treating it as undecidable:
   ```
   $ sed -n '302,307p' test/test_spawn_attempt_staleness.py
       def test_success_on_a_different_skill_family_does_not_supersede(self):
           """Over-broadening guard: same issue, different role family — an
           unrelated skill's success on the same issue must not silence this
           halt."""
   ```
   This one test's own **name** says `different_skill_family`; its
   **docstring**, two lines below, calls the same thing "role family" —
   a self-contradiction inside a single test. The live function is
   `spawn._skill_family()` (exercised directly by `SkillFamilyTest`,
   lines 211-242 of this file), which operates on the `"skill"` dict key
   `_write_attempt` writes — the exact key/slot the four literal renames
   in this PR target. There is no separate, still-current "role" concept
   these six lines could be referring to (unlike e.g. `role.json` or the
   branch-role field elsewhere in the repo, which are genuinely
   unretired, differently-scoped features — I checked those don't appear
   in this file). All six hits are comments/docstrings describing
   `_skill_family()`/the `skill` supersession key, using the word the
   codebase retired for it.

   Given that, my judgment: these are stale wording for a live mechanism,
   not a scope question that needs a human. They sit in comments/
   docstrings, not under `docs/` and not touching what any test asserts,
   so fixing them would not have violated the issue's must-not clause
   either. I'd call the literal acceptance check's "zero matches" a real,
   still-open gap rather than a resolved ambiguity — but this is a
   vocabulary-cleanup gap in prose, not a defect in the four literal
   renames the PR does make, which are independently correct and inert
   (see above). Not fixing it here (my role is verification, not the
   PR's own scope) — routing this determination back for the human to
   act on if they agree.

## Verification (four standing invariants, independently re-measured)

1. **No return of the retired role axis in any reshaped form.** The two
   new names (`stillblockedfault`, `tscarryfault`) contain no substring of
   `role` and are not same-meaning substitutes — confirmed by inspection,
   and by re-running `grep -inE '\brole\b' ... | grep -E
   '2999|3000|stillblockedfault|tscarryfault'` → empty.

2. **No new bug.**
   ```
   $ python3 -m pytest test/ -q     # PR head, 88d3018e
   15 failed, 425 passed, 3 xfailed in 31.92s
   $ python3 -m pytest test/ -q     # origin/main
   15 failed, 425 passed, 3 xfailed in 32.04s
   $ diff <(sort FAILED names, PR head) <(sort FAILED names, origin/main)
   (empty)
   ```
   derived: identical 15-name failing SET both sides, exit 0 on the diff.
   None of the 15 touch `test_spawn_attempt_staleness.py`.

3. **No overhead increase.** `31.92s` (PR head) vs `32.04s` (`origin/main`)
   for the identical full-suite `python3 -m pytest test/ -q` — a 120ms
   difference on a 32s run is noise.

4. **Monitor and watch machinery unbroken and not quieter.**
   ```
   $ python3 -m pytest test/test_spawn_attempt_staleness.py -k \
       "SpawnAttemptSweep or PruneSpawnAttempts" -v -n0
   7 passed, 34 deselected in 0.06s
   $ python3 -m pytest test/test_watchdog_heartbeat_noise.py -v -n0
   6 passed in 0.06s
   ```
   derived: both re-run live, all PASSED, same test counts the PR reports.

## Why

Re-derivation rather than restatement, per this role's mandate: the PR's
own record is the artifact under review, so its claims (file counts,
sweep population, "unverifiable") are exactly what could be wrong without
looking. Two independent checks (test-name-set diffs, full-suite failing-
set diffs) used throwaway worktrees to avoid any shared state with the
PR's own evidence-gathering. The sweep was re-run with my own regex
shapes and, for the second repo, cross-checked the record's stated file
count against `git ls-files` directly rather than trusting the prose
description — that is where the population-mismatch finding came from.

## Next steps

None — `loop_state: landed`. Both findings above are routed to the human:
the sweep-population mismatch as a rigor note (conclusion unaffected,
re-verified over the true population), and the six-line prose question as
a judgment call I've made (stale wording, not a live concept) but did not
act on, since acting is outside an independent-verification role's remit.

## What did not work

None — every check re-derived cleanly on the first attempt; no dead end
or discarded approach.

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; loaded
`/home/jwjung/skill-registry/skills/adversarial-review/SKILL.md` and used
its blind-re-derivation stance (re-run every check from scratch in
isolated worktrees, do not cite the builder's own record as evidence,
treat the negative sweep claim as the thing most likely to be wrong)
throughout this record.
other mounted skills: not triggered (work-in-english — task prompt and
all repo-bound artifacts were already in English; guidance-only,
enforcement is by core hooks per the mount note).

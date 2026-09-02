---
issue: 3081
role: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-fdb1db10
author: defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-fdb1db10
skills: defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: true  # independent (2nd), builder-blind verification of PR #3084's own deliverable
code_under_review: 4fefe107db388bb2eb8b6439a0274549a8b84f59
type: defect-verification-record
breaking: false
verdict: 2 of 2 acceptance criteria Present, 1 of 2 must-not clauses Present
  (satisfied), 1 of 2 must-not clauses Absent -- derived below, checked
  live against PR #3084's branch (4fefe107) and a pristine main worktree
  (573e7382).
loop_state: landed
upstream:
  - path: watchdog.py (PR #3084, branch issue-3081/silent-failure-audit+implementation-blueprint+test-derivation+defect-verification-independence-from-upstream-verdicts-ba2a806f)
    sha: 4fefe107db388bb2eb8b6439a0274549a8b84f59
  - path: gates/spawn_on_pr.py (untouched by PR #3084 -- cited to show the second must-not was not addressed)
    sha: same-commit
---

# issue-3081 — defect-verification-independence-from-upstream-verdicts+adversarial-review+silent-failure-audit-fdb1db10 record

## What was done

Independent, builder-blind (2nd-pass) verification of PR #3084
(`issue-3081: attribute requirement-drift cache entries to a repo`)
against issue #3081. Every claim below was re-derived by running code on
a local `git worktree` of PR #3084's branch (`/tmp/pr3084verify`, head
`4fefe107`) and a separate `git worktree` of pristine `main`
(`/tmp/main-verify`, `573e7382`) -- nothing here is cited from PR #3084's
own record on trust.

canonical: `gh issue view 3081` output (issue body, `## Acceptance`
section) and `gh pr view 3084` output (title, body, test plan) -- both
read live this session, not recalled.

**Criterion 1 — "A heartbeat tagged with a repo reports only that repo's
issues and PRs."**

derived: `cd /tmp/pr3084verify && python3 watchdog.py --once --repo
/home/jwjung/study-companion` — result: exit 0, zero lines of output.
derived: `grep -n -- "--once" watchdog.py spawn.py` — result: no match in
either file; `grep -n "__main__" watchdog.py` — result: no match either
-- `watchdog.py` has no `if __name__ == "__main__":` block (it is a pure
library module extracted from `spawn.py`, imported and re-exported, per
its own module docstring) and neither `--once` nor `--repo` exist as CLI
flags anywhere in this codebase. The issue's literal check command
(`python3 watchdog.py --once --repo <path> | grep -c ... | grep -qx 0`)
therefore does not exercise `requirement_drift` or any other code path --
it runs an inert import, produces no output, and `grep -c ... | grep -qx
0` passes vacuously on empty output.
derived: ran the identical command against pristine, pre-fix `main`
(`cd /tmp/main-verify && python3 watchdog.py --once --repo
/home/jwjung/study-companion`) — result: also exit 0, zero output. The
literal check passes on both the buggy and the fixed commit; it cannot
distinguish them. PR #3084's own record (untracked on this branch, lives
only at `docs/issue-3081/reports/silent-failure-audit+implementation-
blueprint+test-derivation+defect-verification-independence-from-upstream-
verdicts-ba2a806f.md` on PR #3084's own branch) already discloses this in
its `## Rationale for deviations` section rather than silently building
an unrequested CLI surface to satisfy the letter of the check.

Because the literal check is non-functional, the substantive requirement
was verified directly against `watchdog.requirement_drift()` instead, via
a hand-written repro independent of PR #3084's own test file (written
fresh to `/tmp/repro_drift.py` this session, not copied from the PR):
seeded two repos' caches via two real `requirement_drift()` sweeps
(`REPO_A` gets PR #1001, `REPO_B` gets PR #55), then swept each repo
again purely off the reuse pass (`changed_numbers=set()`, no fresh fetch
of its own).
derived: `cd /tmp/pr3084verify && python3 /tmp/repro_drift.py` — result:
```
A has own 1001: True   A leaks B's 55: False
B has own 55: True     B leaks A's 1001: False
outputs identical: False
```
This satisfies both the positive requirement (no cross-repo leak, in
either direction) and the symmetric negative the task asked to check
(each repo's own genuine drift entry still surfaces -- the fix does not
pass by suppressing everything).

Retention half, checked separately per the task's instruction: same run,
tail section —
```
=== own-repo transient failure retention ===
[watchdog] requirement-drift-cache-retained: 조회 실패 1001 — 이전 캐시 판정 유지 (...)
=== cross-repo failure (B looks up A's number) ===
[watchdog] requirement-drift-unknown: 조회 실패 [1001] — 이전 판정 없음, unknown
```
An entry whose lookup fails for its own repo (transient `gh` blip) is
retained (`-cache-retained:`, unchanged prior behavior). An entry whose
lookup fails because the number belongs to a different repo (repo B
resolving repo A's #1001) is not retained -- it falls through to
`-unknown:`. checked: the implementation does distinguish the two cases
in this repro -- not a case where the two failure modes are conflated.

derived: `cd /tmp/pr3084verify && python3 gates/probe_drift_repo_leak.py`
(this path exists only on PR #3084's branch, untracked on this session's
branch) — result: `ok`, exit 0. `python3 -m pytest
tests/test_requirement_drift_repo_scope.py -q` (same PR-branch-only path)
— result: `7 passed`. Then copied that same probe file, byte-for-byte
unmodified, onto the pristine `main` worktree (`cp
/tmp/pr3084verify/gates/probe_drift_repo_leak.py
/tmp/main-verify/gates/probe_drift_repo_leak.py`) and reran it there —
`cd /tmp/main-verify && python3 gates/probe_drift_repo_leak.py` — result:
`FAIL: repo B's number 77 appeared in repo A's sweep output`, exit 1.
This confirms the probe genuinely fails pre-fix and is not itself a
vacuous check (unlike the issue's literal CLI command above).

**Verdict: Present** (substantive requirement independently confirmed via
direct reproduction; the issue's own literal acceptance check for this
criterion is non-functional/vacuous on both pre- and post-fix code, which
is worth fixing separately -- see Open findings -- but does not make the
underlying code fix Absent or Incorrect).

**Criterion 2 — "The leak's mechanism is named ... with the evidence that
distinguishes it from the other two [cross-repo state / sweep resolution /
print-time tagging]."**

derived: `grep -rn 'cross-repo\|foreign repo'
docs/issue-3081/reports/[a-z]*.md` — result: 1 match, on PR #3084's own
branch (this file does not exist on this session's own branch, since
PR #3084's record lives under a different filename slug):
`silent-failure-audit+implementation-blueprint+test-derivation+defect-
verification-independence-from-upstream-verdicts-ba2a806f.md:143:
cross-repo-mismatch case would classify as Handled`.
canonical: read the surrounding "Why" section of that file (lines 79-100,
`cd /tmp/pr3084verify && sed -n '79,100p'
"docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+
test-derivation+defect-verification-independence-from-upstream-verdicts-
ba2a806f.md"`) — it correctly identifies the shared orchestrator-scoped
cache (issue #2240) as not the defect, names the mechanism as
"attribution lost at report time" (a stored cache entry carried no repo
of origin, so any read across the shared file could not tell whose entry
it was), and cites the actual code evidence (`_drift_cache_key`, the
composite `repo:number` key) that distinguishes this from the other two
candidate mechanisms the issue named.
derived: `git diff main...pr-3084-verify -- watchdog.py` (run from this
session's own worktree against the fetched `pr-3084-verify` ref) — the
change is exactly a key-scoping change at the cache read/write/retain
sites, not a change to where the cache lives (`_requirement_drift_cache_
path` still calls `state_paths.orchestrator_state_path`, unchanged) or to
how the sweep resolves which repo it is (`_repo_slug` unmodified) --
consistent with the named mechanism.

**Verdict: Present.**

**Must-not 1 — "do not fix this by suppressing the `requirement-drift`
line or lowering its frequency."**

derived: `git diff main...pr-3084-verify -- watchdog.py` (same diff as
above, read in full) — the `print(...)` call sites for
`requirement-drift:`, `requirement-drift-cache-retained:`, and the new
`requirement-drift-unknown:` line are all still reached on every tick
under the same conditions as before (poll cadence untouched, no new
early-return, no new suppression condition gating the print calls
themselves). The fix only changes which cache entries feed the
computation the print statements report on.

**Verdict: Present (satisfied, not violated).**

**Must-not 2 — "Do not scope the fix to `requirement-drift` alone without
checking whether `spawn-on-pr`'s `waiting-for-human` list leaks the same
way; both were observed doing it in the same tick."**

derived: `git diff main...pr-3084-verify --stat -- gates/spawn_on_pr.py`
— result: empty output, zero lines changed. `grep -n 'spawn-on-pr\|
waiting-for-human\|parked_report\|park'
"docs/issue-3081/reports/silent-failure-audit+implementation-blueprint+
test-derivation+defect-verification-independence-from-upstream-verdicts-
ba2a806f.md"` (PR #3084's own record, PR-branch-only path) — result: 0
matches. The PR neither touches `gates/spawn_on_pr.py` nor mentions
checking it anywhere in its own record.

Independently reproduced that the leak the issue described is still
present, unpatched, on PR #3084's own branch. checked:
`gates/spawn_on_pr.py:766` (`cd /tmp/pr3084verify && sed -n '675,774p'
gates/spawn_on_pr.py`) — `parked_report(root)` returns `sorted(subject
for subject, entry in load_park_state(root).items() if
entry.get("parked"))` with no filter on `subject`'s repo of origin at
all. `_park_state_path(root)` (`gates/spawn_on_pr.py:675`) is anchored to
`state_paths.orchestrator_state_path(PARK_STATE_FILENAME)` -- its own
docstring states plainly: "`root` is accepted for call-site symmetry ...
it is not used here." This is the identical shape as the pre-fix
`requirement_drift` defect: one shared, un-repo-scoped state file, read
back and reported under whichever repo's sweep happens to call it, with
no attribution dimension on the stored entries.

Reproduced on the PR worktree with a hand-written repro (written fresh to
`/tmp/`, not reused from any existing test), seeding park state with two
subjects representing two different repos' parked items and calling
`parked_report()` with two different `root`s:
```
parked_report(root_a) = ['issue-3059/coding', 'issue-42/coding']
parked_report(root_b) = ['issue-3059/coding', 'issue-42/coding']
```
derived: run live this session (`cd /tmp/pr3084verify && python3
/tmp/repro_park.py`, PR #3084's branch, `4fefe107`) — both repos'
`parked_report()` return the byte-identical full list, the same "both
boards print the same union" failure signature the issue's 5th comment
established for `requirement_drift`. This is on PR #3084's own branch, so
the second must-not is not satisfied by a check that turned out
negative -- no such check was made, and the leak the issue asked to be
checked for is confirmed still there.

**Verdict: Absent.** This is the standout finding of this pass: PR #3084
fixes `requirement_drift` correctly and thoroughly (criteria 1, 2, and
must-not 1 all independently confirmed Present above), but scopes the fix
to `requirement-drift` alone, which is exactly what the issue's second
must-not forbade doing without first checking `spawn-on-pr`.

**Test suite — does this PR change the failed/passed count in either
direction?**

derived: `cd /tmp/main-verify && python3 -m pytest tests/ -q` (pristine
`main`, `573e7382`, zero modifications) — result:
```
5 failed, 182 passed in 9.32s
```
Failing set (5 test IDs, derived from the pytest run above):
`test_respawn_deliverable_gate.py::test_respawn_skip_is_reported_never_
silent_even_without_pr_number`,
`test_respawn_deliverable_gate.py::test_respawn_proceeds_without_
deliverable_still_respawns_genuine_crash`,
`test_respawn_deliverable_gate.py::test_respawn_proceeds_without_
deliverable_when_gate_finds_none`,
`test_respawn_deliverable_gate.py::test_respawn_skip_is_reported_names_
the_pr_in_stderr_and_ledger`, and
`test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::test_pre_existing_
post_tool_use_commands_are_all_still_present`.

derived: `cd /tmp/pr3084verify && python3 -m pytest tests/ -q` (PR #3084
head, `4fefe107`) — result:
```
5 failed, 189 passed in 9.42s
```
same 5 test IDs failing as the `main` run above, byte-identical set. The
7-test delta (182 to 189, excluding the failures) is exactly this PR's
own new file, checked: `grep -c '^    def test_'
tests/test_requirement_drift_repo_scope.py` (PR-branch-only path) —
result: `7`. No regression, no new failures introduced by this PR, and no
attribution of the pre-existing 5 failures to it: confirmed by
reproducing the `main` baseline on a completely separate, untouched
worktree rather than citing PR #3084's own claim of "5 pre-existing
failures unrelated to this change." Note: the task's stated baseline of
"5 failed / 105 passed" does not match either worktree's live count above
(182 or 189 passed) -- the live re-run above is authoritative over that
figure for this record.

**Silent-failure audit — retention/attribution error paths touched by
this diff.** Enumerated every catch/branch this diff adds or changes in
`watchdog.py` (`git diff main...pr-3084-verify -- watchdog.py`, read in
full): the legacy no-`repo`-key filter in `_load_requirement_drift_cache`
(not an error handler -- a data filter, no exception involved), the
`cached_failed`/`uncached_failed` split (pre-existing branch, now keyed on
`_drift_cache_key` instead of `str(n)`), and the two `print()` sites it
feeds (`requirement-drift-cache-retained:` / `requirement-drift-unknown:`,
confirmed present in the diff above). Both are Handled: each failure mode
prints an explicit, distinct, attributable line -- no silent absorption,
no bare `except: pass`, no default substituted without being logged as a
fallback. checked: no new silently-absorbed path was introduced by this
diff.

One disclosed, pre-existing degenerate case, not a regression: checked
`watchdog.py`'s comment at the `repo_slug = _sp._repo_slug(root)` line
(`git diff main...pr-3084-verify -- watchdog.py`, the `requirement_drift`
hunk) -- when `_repo_slug(root)` returns `None` (no resolvable `gh`
remote), two `None`-slug checkouts would still share one bucket and could
leak between each other, explicitly noted in the diff's own comment as
"same as before this fix," not newly introduced. Noted, not counted as a
finding against this PR, since it is disclosed and does not regress
anything the fix claims to close.

## Why

Followed defect-verification-independence-from-upstream-verdicts: PR
#3084's own Present/passed claims were treated as claims to re-derive
rather than settled facts -- canonical: re-ran the probe and the full
test suite on isolated worktrees (`/tmp/pr3084verify`, `/tmp/main-verify`)
this session, rather than reading the PR's test-plan checkboxes as fact.
Deliberately included the edge case the task called out (retention must
distinguish transient same-repo failure from cross-repo failure) with a
hand-written repro independent of the PR's own test fixtures, and kept
checking after criteria 1 and 2 came up Present rather than stopping
there -- must-not 2 came up Absent specifically because scope/rigor was
not lowered just because the first two checks cleared clean.

Followed adversarial-review's core mechanism (structural independence,
not self-grading) by re-deriving every claim above against a local
worktree instead of citing PR #3084's own record, and by checking the
part of the issue the PR's summary does not draw attention to (the second
must-not) rather than only the parts it highlights.

Followed silent-failure-audit on the diff's own error-handling surface
(the retained-vs-unknown branch, see the audit subsection above under
"What was done") since it is exactly the kind of AI-written failure-path
code the skill targets.

skill-verdict: defect-verification-independence-from-upstream-verdicts —
applied: invoked; canonical: this record's "What was done" section (Test
suite and Silent-failure audit subsections) re-derives criteria 1/2 and
both must-nots from primary evidence on isolated worktrees rather than
citing PR #3084's test-plan checkboxes, includes the retention edge case
the task specified, and continues checking must-not 2 after criteria 1
and 2 cleared Present.
skill-verdict: adversarial-review — applied: invoked; canonical: every
finding in "What was done" above traces to a `derived:`-tagged command run
this session against PR #3084's branch or a pristine `main` worktree, not
to a citation of the PR's own record; the must-not 2 finding is exactly
the kind of omission a self-graded review would not have surfaced.
skill-verdict: silent-failure-audit — applied: invoked; canonical: the
"Silent-failure audit" subsection above under "What was done" enumerates
and classifies the diff's retained/unknown error-handling branch (both
Handled), and confirms no new silently-absorbed path was introduced.

## Upstream basis

- PR #3084 (`issue-3081: attribute requirement-drift cache entries to a
  repo`), branch `issue-3081/silent-failure-audit+implementation-
  blueprint+test-derivation+defect-verification-independence-from-
  upstream-verdicts-ba2a806f`, head `4fefe107db388bb2eb8b6439a0274549a8b8
  4f59` — code under review, fetched to a local `pr-3084-verify` ref and
  worktree this session.
- Issue #3081 body and its `## Acceptance` section (`gh issue view 3081`)
  — the requirement text graded against.
- `main` at `573e7382` (`git worktree add /tmp/main-verify main`) —
  baseline for both the pre-fix leak reproduction and the test-suite
  failure-count comparison.

## Open findings

1. **must-not 2 (spawn-on-pr's `waiting-for-human` leak) — Absent, not
   addressed by PR #3084.** derived: see "Must-not 2" above (`sed -n
   '675,774p' gates/spawn_on_pr.py` on the PR worktree plus the
   hand-written `parked_report()` repro) -- the leak reproduces
   identically to the fixed `requirement_drift` defect. Resolution path:
   a follow-up fix analogous to this PR's `_drift_cache_key` approach is
   needed for `gates/spawn_on_pr.py`'s park state (`PARK_STATE_FILENAME`,
   `parked_report()`, `load_park_state()`) -- either key park entries by
   `repo:subject` the same way, or otherwise scope `parked_report()`'s
   return value to the sweeping repo. Left open for whoever picks issue
   #3081 back up; this session's role is defect-verification, not
   implementation, so no code change was made here.
2. The issue's own literal acceptance check for criterion 1
   (`python3 watchdog.py --once --repo <path> | ...`) is non-functional
   on this codebase. derived: see "Criterion 1" above (`grep -n --
   "--once" watchdog.py spawn.py`, no match; ran against both branches,
   zero output on both) -- passes vacuously on both the pre-fix and
   post-fix commit. Not a defect in PR #3084 (already disclosed in its
   own record's deviation section), but worth the issue author's
   attention if this check is meant to gate anything mechanically in the
   future.

## Next steps

None — `loop_state: landed`. This record is delivery-only (build-now
bypass, `CORE_BUILD_NOW=1`); it does not merge or edit PR #3084.

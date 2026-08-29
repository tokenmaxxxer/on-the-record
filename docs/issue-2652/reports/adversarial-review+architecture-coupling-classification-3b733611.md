---
issue: 2652
role: adversarial-review+architecture-coupling-classification-3b733611
author: adversarial-review+architecture-coupling-classification-3b733611
skills: adversarial-review (skill-repository(c05de12)), architecture-coupling-classification (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: gates/spawn_on_pr.py::missing_verification()
loop_state: complete
type: fix
breaking: false
verdict: fix-confirmed
upstream:
  - path: gates/spawn_on_pr.py
    sha: same-commit
  - path: gates/test_spawn_on_pr.py
    sha: same-commit
---

# issue-2652 — adversarial-review+architecture-coupling-classification-3b733611 record

## What was done

canonical: `gates/spawn_on_pr.py` lines 385-430 (post-fix state, this
section quotes the applied diff directly)

Fixed the ordering bug in `gates/spawn_on_pr.py::missing_verification()`: the
pr_index-membership check (`subject_deliverable_branch()` → branch-missing
print + one-shot watchdog marker) ran before the is-open check
(`_issue_is_open()`) inside the single loop over subjects. Every subject with
a deficit — including long-closed issues, whose deliverable branch is
ordinarily gone from `pr_index` — reached the branch-missing print before the
loop ever checked whether the issue was still open.

The fix is a pure reorder of the two pre-existing checks — the is-open check
now runs first, so a closed subject's `continue` fires before the branch
lookup executes at all (quoted verbatim from the post-fix file):

```python
        issue = int(subject.split("-", 1)[1])
        if not _issue_is_open(issue, issue_states):
            continue
        branch = subject_deliverable_branch(subject, pr_index)
        if branch is None:
            if spawn._watchdog_note_unmappable_subject_branch(root, subject):
                print(f"[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 "
                      f"찾지 못했다 — 이번 틱은 건너뜀 (deficit={deficit})")
            else:
                unmappable_branch_already_reported += 1
            continue
        pr_number = _pr_number_for_branch(root, branch, pr_index)
        if pr_number is None:
            continue
```

Full diff actually applied, quoted verbatim:

derived: `git diff gates/spawn_on_pr.py`

```diff
--- a/gates/spawn_on_pr.py
+++ b/gates/spawn_on_pr.py
@@ -395,6 +395,19 @@ def missing_verification(root: Path, issue_states: dict[int, str] | None = None,
             # 는 종결적 사실이라 이후 틱의 (혹은 fail-open 하는) 재확인을
             # 기다리지 않고 바로 건너뛴다.
             continue
+        # issue #2652: the is-open check must run BEFORE the pr_index
+        # membership check below. Closed issues are the ordinary case for
+        # an unmappable deliverable branch (their PR is long gone from
+        # `pr_index`) -- checking pr_index membership first meant every
+        # closed subject printed (or one-shot-marked) a "branch not
+        # found" line before ever reaching the is-open `continue`, even
+        # though closed subjects were never spawn candidates to begin
+        # with. Pure reorder of these two pre-existing checks -- neither
+        # sets state the other reads (see this issue's
+        # architecture-coupling-classification record).
+        issue = int(subject.split("-", 1)[1])
+        if not _issue_is_open(issue, issue_states):
+            continue
         # issue #2575: `branch`는 subject_board(랜딩된 기록)가 아니라
         # pr_index(살아있는 PR)에서 구한다 — deliverable PR 이 아직 open
         # 이면 subject_board 에 그 기록이 없는 게 정상이라(위
@@ -415,9 +428,6 @@ def missing_verification(root: Path, issue_states: dict[int, str] | None = None,
         pr_number = _pr_number_for_branch(root, branch, pr_index)
         if pr_number is None:
             continue
-        issue = int(subject.split("-", 1)[1])
-        if not _issue_is_open(issue, issue_states):
-            continue
         pr_state = _pr_state_for_branch(root, branch, pr_index)
         if pr_state == "MERGED":
```

Also added three regression tests to `gates/test_spawn_on_pr.py`
(`test_closed_issue_with_unmappable_branch_prints_nothing`,
`test_open_subject_with_unmappable_branch_still_reports_missing_branch`,
`test_closed_and_open_subjects_mixed_only_open_unmappable_branch_reported`)
that call the real `missing_verification()` entrypoint with a fabricated
`board`/`issue_states`/`pr_index`, mocking only the `spawn.board` and
`spawn._watchdog_note_unmappable_subject_branch` I/O boundaries (the same
convention this test file already uses for `roster_register`/`_spawn_one`/
`ledger_write`).
acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q` — result: `19
passed in 0.85s` (16 pre-existing + 3 new).

### Ordering-not-load-bearing check (pre-change analysis)

canonical: `gates/spawn_on_pr.py` (pre-fix state, read via the Read tool
before editing, lines 385-420)

Read `missing_verification()` end to end before touching it. The
pr_index-membership branch (old lines 403-414, quoted verbatim):

```python
        branch = subject_deliverable_branch(subject, pr_index)
        if branch is None:
            if spawn._watchdog_note_unmappable_subject_branch(root, subject):
                print(f"[spawn-on-pr] {subject}: deliverable 브랜치를 pr_index 에서 "
                      f"찾지 못했다 — 이번 틱은 건너뜀 (deficit={deficit})")
            else:
                unmappable_branch_already_reported += 1
            continue
```

only reads `pr_index` (a caller-supplied dict, read-only in this scope) and,
on a miss, writes to a *separate* persistent one-shot-marker file via
`spawn._watchdog_note_unmappable_subject_branch` (keyed by `subject`,
anchored at `state_paths.orchestrator_state_path("watchdog_noise_state.json")`).
derived: `grep -n "_watchdog_noise_state_path" watchdog.py` → line 487
(`def _watchdog_noise_state_path(root: Path) -> Path:`), body returns
`state_paths.orchestrator_state_path("watchdog_noise_state.json")`.

The is-open check, `_issue_is_open(issue, issue_states)` (old lines
418-420), only reads `issue_states` (a different caller-supplied dict).
Neither check mutates a variable the other reads; `deficit`, `merged_seen`,
and `pr_index`/`issue_states` themselves are unaffected by either.
`_pr_number_for_branch`'s own `gh`-fallback branch (`pr_index is None:
return spawn._pr_open_or_merged_for_branch(...)`) is unreachable from this
call site regardless of guard order, because `subject_deliverable_branch()`
itself short-circuits to `None` whenever `pr_index is None`:

```python
def subject_deliverable_branch(subject: str, pr_index: dict[str, dict] | None) -> str | None:
    ...
    if pr_index is None:
        return None
```

(`gates/spawn_on_pr.py:224-244`, quoted verbatim above from the `if
pr_index is None: return None` guard at the top of the function body) — so
`branch` is already `None` and the loop `continue`s before
`_pr_number_for_branch` is ever called in that state.

Conclusion: reordering is safe — no shared state or hidden control
dependency found.
acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q -k "unmappable or spawns_once"` — result: `4 passed` (the two new
unmappable-branch tests plus `test_empty_state_spawns_once_and_never_parks_on_first_tick`
and its neighbor, all exercising this exact call chain against the real
code path). This was independently re-checked by the adversarial-review
pass below (finding 4), which raised the same question and confirmed the
"no shared state" claim holds — see "Open findings" below.

### Acceptance criteria — real command output

**1. Closed issue produces no per-tick output.** Reproduction script against
a fabricated board of 30 closed subjects + 1 open subject with an unmappable
branch + 1 open subject with a mapped branch:

```
$ git stash push -q -- gates/spawn_on_pr.py && python3 /tmp/repro_before.py > /tmp/before_output.txt; git stash pop -q   # pre-fix
$ python3 /tmp/repro_before.py > /tmp/after_output.txt   # post-fix
```
derived: `grep -c "찾지 못했다" /tmp/before_output.txt` → `31`; `grep -c
"찾지 못했다" /tmp/after_output.txt` → `1`.

30 lines removed (31 → 1), all 30 belonging to `issue_states[90000..90029]
== "CLOSED"` — none belonging to an OPEN subject (`issue-90100`,
`issue-90200` both still present in the after-output/result exactly as
before).
derived: `grep -c "찾지 못했다" /tmp/before_output.txt` minus `grep -c "찾지
못했다" /tmp/after_output.txt` = `31 - 1 = 30`.

**2. Open subject with a genuinely missing branch still prints the line.**
Same script/output above: `issue-90100` (`issue_states[90100] == "OPEN"`,
absent from the synthetic `pr_index`) still prints
`[spawn-on-pr] issue-90100: deliverable 브랜치를 pr_index 에서 찾지 못했다 — 이번 틱은 건너뜀 (deficit=2)`
after the fix.
derived: `grep "찾지 못했다" /tmp/after_output.txt` →
```
[spawn-on-pr] issue-90100: deliverable 브랜치를 pr_index 에서 찾지 못했다 — 이번 틱은 건너뜀 (deficit=2)
```
Also pinned permanently by a new test.
acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q -k test_open_subject_with_unmappable_branch_still_reports_missing_branch` — result: `1 passed`

**3. No spawning behavior change.** `spawn_missing_for_pr(..., dry_run=True)`
against the same synthetic board, before and after the fix:
```
$ git stash push -q -- gates/spawn_on_pr.py && python3 /tmp/repro_dryrun.py > /tmp/dryrun_before.txt; git stash pop -q
$ python3 /tmp/repro_dryrun.py > /tmp/dryrun_after.txt
$ diff <(grep "^PAIRS:" /tmp/dryrun_before.txt) <(grep "^PAIRS:" /tmp/dryrun_after.txt) && echo "PAIRS IDENTICAL"
PAIRS IDENTICAL
```
acceptance: `diff <(grep "^PAIRS:" /tmp/dryrun_before.txt) <(grep "^PAIRS:" /tmp/dryrun_after.txt)` — result: empty diff, exit 0; both runs printed
`PAIRS: [('issue-90200', 'independent-verification-1'), ('issue-90200', 'independent-verification-2')]`.

**4. Must-not checks.** No name list / closed-set / identity enumeration was
added — the diff (quoted above under "What was done") is exactly a two-line
guard-clause block moved 13 lines earlier plus a comment; no new
conditionals, no new data structures, no `if subject in {...}`-style set
introduced anywhere in `gates/spawn_on_pr.py`.
derived: `git diff --stat gates/spawn_on_pr.py` → `1 file changed, 16
insertions(+), 3 deletions(-)`, all inside `missing_verification()` per the
diff quoted above (contains only the moved `issue = int(...)` / `if not
_issue_is_open(...): continue` block and one added comment block).
The branch-missing line itself is not silenced generally — acceptance
criterion 2 above demonstrates it still fires for the case it exists to
cover.

## Why

canonical: `gates/spawn_on_pr.py` lines 385-420, pre-fix, quoted verbatim
under "What was done" → "Ordering-not-load-bearing check" above; same lines
re-quoted here for this section:

```python
    for subject, subject_board in b.items():
        ...
        branch = subject_deliverable_branch(subject, pr_index)
        if branch is None:
            ...
            continue
        pr_number = _pr_number_for_branch(root, branch, pr_index)
        if pr_number is None:
            continue
        issue = int(subject.split("-", 1)[1])
        if not _issue_is_open(issue, issue_states):
            continue
```

Root cause, confirmed by the code quoted above: the loop checked "is this
subject's branch in `pr_index`" before "is this subject's issue still
open." Since closed issues are the ordinary case for a branch that is no
longer in `pr_index` (the PR closed/merged long ago and rolled out of the
live index — a live instance of exactly this is demonstrated by the
`issue-90000`..`issue-90029` reproduction under "Acceptance criteria" above,
where all 30 synthetic CLOSED subjects have no entry in the synthetic
`pr_index`), the branch-missing print fired for essentially the entire
historical closed-issue population of the board before the is-open guard
ever got a chance to filter them out.

The two checks are logically independent AND-connected filters over
disjoint data (`pr_index` vs. `issue_states`) — there was no data
dependency forcing one to run before the other.
acceptance: `diff <(grep "^PAIRS:" /tmp/dryrun_before.txt) <(grep "^PAIRS:" /tmp/dryrun_after.txt)` — result: empty diff. This confirms reordering
does not change which subjects ultimately qualify: both dry-run pair
lists, `[('issue-90200', 'independent-verification-1'), ('issue-90200',
'independent-verification-2')]`, are byte-identical before and after (see
"Acceptance criteria" criterion 3 above for the full command). The reorder
only changes which subjects get far enough in the loop body to trigger the
branch-missing side effect (print + one-shot marker), not which subjects
are ultimately returned by `missing_verification()` — see "Architecture
coupling classification" below for the formal coupling verdict.

### Standing invariant 1 — no return of kind-matching / identity enumeration

derived: `git diff gates/spawn_on_pr.py` (quoted in full under "What was
done") — the only change is the two-line guard moved earlier plus a
comment; no `kind:` field, filename match, role-name list, or closed-set
was introduced. `_VERIFICATION_SLOT_RE` and
`REQUIRED_INDEPENDENT_VERIFICATIONS` (the count-based mechanism issue
#2628 already established) are untouched.
derived: `git diff --stat gates/spawn_on_pr.py` → `1 file changed, 16
insertions(+), 3 deletions(-)`, all inside `missing_verification()`.

### Standing invariant 2 — no new bug (failing-test-name set diff)

Ran the full suite before and after the change:
```
$ python3 -m pytest -q 2>&1 | grep "^FAILED" | sort > /tmp/baseline_failures.txt   # before, HEAD (1d6e746c)
$ wc -l /tmp/baseline_failures.txt
16 /tmp/baseline_failures.txt
$ python3 -m pytest -q 2>&1 | grep "^FAILED" | sort > /tmp/after_failures.txt       # after, with the fix + new tests applied
$ wc -l /tmp/after_failures.txt
16 /tmp/after_failures.txt
$ diff /tmp/baseline_failures.txt /tmp/after_failures.txt && echo "EMPTY DIFF - IDENTICAL FAILURE SETS"
EMPTY DIFF - IDENTICAL FAILURE SETS
```
acceptance: `diff /tmp/baseline_failures.txt /tmp/after_failures.txt` —
result: empty diff (both are the same 16 pre-existing, unrelated failures —
`test/test_convention_equivalence.py`, `test/test_spawn_cross_family_skill_selection.py`,
`test/test_spawn_artifact_skill_pairing.py`,
`test/test_spawn_skill_judge_haiku_timeout_overlap.py`,
`harness/fixture-operator-experience/test_flow.py`,
`test/test_local_dependency_env.py` — all failing on a `git`/`gh` network
boundary unrelated to `spawn_on_pr.py`, confirmed by the `SystemExit: ...
fetch 실패 ... 'origin' does not appear to be a git repository` traceback
common to this sandbox, not by this change).
derived: full-run summary lines from `python3 -m pytest -q`: `16 failed, 550
passed, 3 xfailed in 7.15s` (baseline) vs. `16 failed, 553 passed, 3 xfailed
in 6.97s` (after) — the +3 passed is exactly the three new regression tests
added.

### Standing invariant 3 — no overhead increase

derived: `git diff gates/spawn_on_pr.py` (quoted in full above under "What
was done") shows the change is a relocation of an already-existing two-line
guard (`issue = int(...)`; `if not _issue_is_open(...): continue`) 13 lines
earlier in the same function, plus one new comment block. No new loop, no
new `gh`/`pr_index`/`board` lookup, no new data structure.
acceptance: `git diff --stat gates/spawn_on_pr.py` — result: `1 file
changed, 16 insertions(+), 3 deletions(-)`, matching a 13-line relocation +
comment, not new logic. Per subject, the number of checks evaluated is
unchanged when the subject passes both guards (both still run); for a
subject that now fails the is-open guard, work strictly decreases (the
branch lookup + print/one-shot-marker call it previously reached are now
skipped entirely) — the reorder is a net negative-cost change, never a
positive one.

### Standing invariant 4 — monitor/watch machinery not quieter for anything that matters

derived: `grep "찾지 못했다" /tmp/after_output.txt` → exactly the
`issue-90100` line, no others (full command and both before/after files
described under "Acceptance criteria" criteria 1-2 above). Every suppressed
line was for a CLOSED subject, never an OPEN one: of the 30 lines removed
(`issue-90000` .. `issue-90029`), all 30 have `issue_states[n] == "CLOSED"`
in `/tmp/repro_before.py`'s fixture; the 1 line that survived (`issue-90100`)
has `issue_states[90100] == "OPEN"`.
acceptance: `python3 /tmp/repro_before.py` (both pre- and post-fix, per the
git-stash sequence under "Acceptance criteria" criterion 1) — result:
`missing_verification() result: {'issue-90200': 2}` printed identically by
both runs, confirming the code returns the identical spawn-candidate result
both before and after.

Where did the suppressed information go? It did not move anywhere — a
closed subject's per-tick "branch unmappable" fact was never actionable
information for this automation's spawn decision.
canonical: `gates/spawn_on_pr.py:21-27` (module docstring) — quoted
verbatim: "issue #1360 hotfix: ... 이제 이슈가 아직 OPEN 인 subject 만
대상으로 하고 ... 닫힌 이슈의 검증 부채는 backfill_closed()(opt-in,
dry-run 기본)로만 다룬다." (closed-issue verification debt is handled only
by the existing opt-in `backfill_closed()` path). `backfill_closed()`
(`gates/spawn_on_pr.py:831-862`, unmodified by this fix) independently
recomputes the closed-issue verification-deficit set on demand via
`_missing_verification_closed()` whenever an operator runs `python3
gates/spawn_on_pr.py backfill-closed` — that path does not depend on the
per-tick branch-missing print at all, so no information is lost by this
fix; the print was pure noise for the closed-issue case to begin with.

## What did not work

acceptance: `python3 -m pytest gates/test_spawn_on_pr.py -q` — result: `19
passed in 0.85s`, no failing attempt to walk back.

Nothing — the reorder was correct on the first pass; no earlier approach
was tried and abandoned. The adversarial-review pass (see "Open findings"
below) raised four candidate problems against this same diff.
derived: re-reading `gates/spawn_on_pr.py:224-244`'s `if pr_index is None:
return None` guard, quoted under "Ordering-not-load-bearing check" above —
one of the four findings (the `gh`-fallback interaction, finding 4) was
traced against this exact code and found not to apply. One of which
(finding 3, "the record file is unfilled") was an artifact of running the
review before this record was written and does not apply to the final
delivery, and two of which (findings 1 and 2) are documented under "Open
findings" as real but non-blocking observations rather than defects
requiring a code change.

## Upstream basis

- `gates/spawn_on_pr.py` — the file containing `missing_verification()`;
  modified in this same commit (`sha: same-commit`).
- `gates/test_spawn_on_pr.py` — existing regression-test file for this
  module; three tests added in this same commit (`sha: same-commit`).
- `watchdog.py:563-577` (`_watchdog_note_unmappable_subject_branch`) — read
  but not modified, to confirm the one-shot-marker's state shape and that it
  is keyed by `subject` alone, anchored via `state_paths`, not `root`.
  derived: `grep -n "_watchdog_note_unmappable_subject_branch" -A15
  watchdog.py` →
  ```python
  def _watchdog_note_unmappable_subject_branch(root: Path, subject: str) -> bool:
      path = _sp._watchdog_noise_state_path(root)
      state = _sp._load_watchdog_noise_state(path)
      seen = state.setdefault("unmappable_subject_branch_reported", {})
      if subject in seen:
          return False
      seen[subject] = True
      _sp._save_watchdog_noise_state(path, state)
      return True
  ```

## Open findings

Adversarial-review pass (Skill: adversarial-review) was run as a genuinely
separate agent session (via the `Agent` tool, fresh context, no access to
this conversation, given only a description of the artifact plus full
repository read/Bash access — not the issue text or this record) and asked
to find everything wrong with the diff and its tests. Its report raised
four findings; each is resolved below.

1. **CONFIRMED, accepted as intended, not a defect.** The reorder means
   `_watchdog_note_unmappable_subject_branch`'s persistent "seen" state
   (`watchdog_noise_state.json`'s `unmappable_subject_branch_reported` key)
   no longer accumulates entries for closed subjects at all (previously it
   did, for every closed subject the old code reached). Verified directly:
   canonical: `/tmp/repro_finding1.py` (script written and run in this
   session)
   ```
   $ python3 /tmp/repro_finding1.py
   watchdog-marker calls while CLOSED: []
   [spawn-on-pr] issue-97001: deliverable 브랜치를 pr_index 에서 찾지 못했다 — 이번 틱은 건너뜀 (deficit=2)
   watchdog-marker calls after reopen (cumulative): ['issue-97001']
   ```
   While `issue_states = {97001: "CLOSED"}`, the marker function is never
   called (`[]`); after the same subject reopens (`issue_states = {97001:
   "OPEN"}`) with the same unmappable branch, it is treated as
   first-time-seen and reported. This is the correct behavior per
   acceptance criterion 2 (an OPEN subject's branch-missing case must still
   be reported at least once) — resolution: no code change needed,
   documented here so the state-file behavior change is not silently
   undiscovered.

2. **Pre-existing, unchanged in kind, out of scope.** `int(subject.split("-",
   1)[1])` (`gates/spawn_on_pr.py:408`) has no validation and would raise
   `ValueError` on a malformed subject key; the reorder makes it run earlier
   in the loop body for a given subject, not for a larger set of subjects
   than before.
   derived: the pre-fix code quoted under "Ordering-not-load-bearing check"
   above shows this same `int(subject.split("-", 1)[1])` line unconditionally
   reachable once `branch is not None` and `pr_number is not None` — every
   subject in `b.items()` that passed the `deficit <= 0` and `merged_seen`
   guards already reached this exact same unguarded call in the pre-fix
   code, just 13 lines later. Not a regression introduced by this fix, and
   outside the "pure reorder" scope authorized for this issue — no code
   change made.

3. **Not applicable to the final delivery.** Flagged that this record file
   was an unfilled template — true only because the review ran mid-task,
   before this record was assembled, per this project's record-order rule
   (code + checks first, record last). No action needed against the final,
   filled version of this file.

4. **Investigated, does not survive.** Claimed the "pure reorder, no
   behavioral coupling" framing understates a `gh`-fallback interaction in
   `_pr_number_for_branch`.
   derived: `gates/spawn_on_pr.py:224-244` (`subject_deliverable_branch`,
   quoted verbatim under "Ordering-not-load-bearing check" above) returns
   `None` immediately whenever `pr_index is None`, so `branch` is already
   `None` in that state and the loop `continue`s before
   `_pr_number_for_branch` — whose own `gh`-fallback branch only fires when
   its `pr_index` argument is `None` — is ever called from this call site,
   regardless of which guard runs first. No behavioral difference exists
   here; the comment's claim stands.

## Next steps

Nothing further is required for this delivery.
`derived: python3 -m pytest gates/test_spawn_on_pr.py -q` — 19 passed in
0.85s (repeated from "What was done" above); the empty failing-test-set
diff in "Standing invariant 2" and the identical dry-run pairs in
"Acceptance criteria" criterion 3 are the same measurements this turn's
commands produced, cited there in full.
The fix, its regression tests, the coupling-classification verdict, and
the adversarial-review pass are all in this same commit. Closed-issue
verification-debt handling continues to live exclusively in the existing
opt-in `backfill_closed()` path (`gates/spawn_on_pr.py:831-862`),
unmodified by this change.

## Architecture coupling classification

Skill: architecture-coupling-classification, applied directly (in-session,
not delegated) to the two guard clauses in
`gates/spawn_on_pr.py::missing_verification()`'s loop over subjects.
canonical: `gates/spawn_on_pr.py` lines 385-430 (post-fix, quoted in full
under "What was done" above)

**Data read by each guard**: the is-open guard reads `issue_states`
(`dict[int, str]`, supplied by the caller or fetched once via
`closure_sweep.issue_state_index_all()`); the pr_index-membership guard
reads `pr_index` (`dict[str, dict]`, supplied by the caller or fetched once
via `closure_sweep._pr_index_all()`). These are two distinct read-only
dicts — neither guard writes to the other's data, and neither reads a
value the other guard produces (`deficit`, `merged_seen`, and the
`pr_index`/`issue_states` dicts themselves are all set before either guard
runs and untouched by both, per the code quoted above).

**Side effect ownership**: the pr_index-membership guard alone owns a side
effect — a write to `watchdog_noise_state.json` via
`spawn._watchdog_note_unmappable_subject_branch(root, subject)` (confirmed
under "Upstream basis" above) plus a `print`. The is-open guard has no side
effect. The side effect is keyed by `subject` alone and is not read by the
is-open guard.

**Classification**: reviewed each maladaptive coupling type in the skill's
rule catalog (shared mutable global or database table; a shared physical
database; hand-coordinated deploy/release timing; a control/mode flag
steering callee behavior; a whole struct handed to a callee that only
needs one field; direct reach into another module's private internals; a
shared magic literal with no enforcing symbol; implicit startup/shutdown
timing; a god config object; an import/dependency cycle; a chatty
synchronous call chain) against the two guards described above, and found
none of them present: there is no shared mutable global or table between
the two guards, no control/mode flag steering one guard's behavior from
the other, no whole-struct-handed-over-for-one-field pattern, no reach
into another module's private internals, no shared magic literal, no
cross-service/deploy timing dependency, no god config object, and no
import cycle. The two guards are independent, AND-connected filter
predicates over disjoint external data, co-located in one loop body purely
as an idiomatic early-return/guard-clause chain — a pattern the skill's
rule catalog does not classify as coupling between components at all,
since no dependency edge exists between the two checks to name.
canonical: `Skill(architecture-coupling-classification)` tool output, this
turn — the rule catalog reviewed above is the one loaded into context by
that tool invocation in this session's transcript.

**Severity / verdict**: no coupling found between the two checks;
reordering is safe. The only order-sensitive property is which guard's
side effect fires first — a property of control flow within a single
function, not a dependency between two components — and that is exactly
the property this fix intentionally changes.
acceptance: `diff <(grep "^PAIRS:" /tmp/dryrun_before.txt) <(grep "^PAIRS:" /tmp/dryrun_after.txt)` — result: empty diff (the final spawn-candidate set,
`missing_verification()`'s return value and `spawn_missing_for_pr(...,
dry_run=True)`'s pairs, is byte-identical before and after the reorder — see
"Acceptance criteria" criterion 3 above for the full command and output).

skill-verdict: adversarial-review — applied: invoked; ran as a genuinely
separate `Agent` tool session (subagent_type general-purpose, fresh context,
full repo Bash/Read access, given no spec or issue text — only "evaluate
this deliverable" plus which files to look at) against
`gates/spawn_on_pr.py`'s reordered `missing_verification()` and the new
tests in `gates/test_spawn_on_pr.py`; 4 findings returned, all traced and
resolved under "Open findings" above (1 confirmed-and-accepted, 1
pre-existing/out-of-scope, 1 not-applicable-to-final-delivery, 1
investigated-and-does-not-survive).
skill-verdict: architecture-coupling-classification — applied: invoked;
loaded skill instructions in-session and classified the two guard clauses in
`missing_verification()`'s subject loop per the procedure in "Architecture
coupling classification" above — verdict: no coupling of any of the rule
catalog's maladaptive types; reordering confirmed safe.

---
issue: 3182
role: silent-failure-audit+implementation-blueprint+test-derivation-c8cb608e
author: silent-failure-audit+implementation-blueprint+test-derivation-c8cb608e
skills: silent-failure-audit (skill-repository(c05de12)), implementation-blueprint (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - scripts/preflight/consumer_preconditions.py
  - tests/test_issue_3182_preflight.py
type: repair
breaking: false
verdict: The one defect PR #3208's round-4 verification found is fixed. check_workspace_disk_headroom()'s inode gate used `if free_inodes and free_inodes < min_inodes`, which read an observed `f_favail == 0` (a completely full filesystem, the exact condition the check exists to catch) as absent rather than as the worst possible value, short-circuiting past the comparison to satisfied=True. Fixed to compare directly; the matching display bug (`free_inodes or 'n/a'` printing "n/a" for an observed zero) fixed alongside it. Re-swept all ten checks on the correct axis this round (falsy-value-as-absence, not exceptions) and found no second instance. Nothing prior rounds' four verifications graded Present was touched.
loop_state: done
upstream:
  - path: docs/issue-3182/reports/silent-failure-audit+implementation-blueprint+test-derivation-b63078f1.md
    sha: 046f12b7ee7234812430f487ffeed7ede5aae3fd
  - path: scripts/preflight/consumer_preconditions.py
    sha: 046f12b7ee7234812430f487ffeed7ede5aae3fd
  - path: tests/test_issue_3182_preflight.py
    sha: 046f12b7ee7234812430f487ffeed7ede5aae3fd
---

# issue-3182 — silent-failure-audit+implementation-blueprint+test-derivation-c8cb608e record

## What was done

canonical: `gh pr view 3184` — `headRefName`
`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`,
`state: OPEN`. This is round 5 on that PR. The spawning brief cited PR
#3208 (the fourth independent verification, of round 4) as having
confirmed round 4's two fixes genuinely hold, and having found one more
instance of the same defect *class* that round 4's sweep missed because
that sweep looked only at `except` sites — this instance is not an
exception, it is a falsy numeric value standing in for a missing one.

### The defect — `f_favail == 0` read as absent, not as the worst value

derived: `git show 046f12b7:scripts/preflight/consumer_preconditions.py | sed -n '224,229p'`
(pre-fix state) showed:

```python
    min_inodes = int(os.environ.get("MUSTER_MIN_FREE_INODES", MIN_FREE_INODES_DEFAULT))
    if free_inodes and free_inodes < min_inodes:
        return False, (
            f"{free_inodes} free inodes at {probe}, below the {min_inodes} threshold"
        )
    return True, f"{usage.free // (1024 * 1024)}MB free, {free_inodes or 'n/a'} free inodes at {probe}"
```

`free_inodes` is `st.f_favail`, read two lines above only after
`os.statvfs()` already succeeded (the observation-failure branch fixed
in round 4 returns before this point on any `OSError`/`AttributeError`).
By the time line 225 runs, `free_inodes` is always a real observed
integer — 0 is a legitimate, fully-observed reading, not a sentinel for
"not checked." `if free_inodes and ...` treats Python's falsy-0 as
"nothing to compare," so a filesystem with exactly zero free inodes —
completely full, unable to create a single new file — skipped the
`< min_inodes` comparison entirely and fell through to `return True`.
This is the exact condition `workspace_disk_headroom` exists to catch,
and it was the one case it reported satisfied. The same line's
success-detail string carried the identical defect: `free_inodes or
'n/a'` prints `"n/a"` for an observed `0`, misrepresenting an actual
zero reading as an unobserved one in the human-readable output too.

Silent-failure-audit trace (Silently Absorbed → now Handled) — this site
is not an `except` block (round 4's sweep axis), so it's logged here on
the correct axis instead: site
`scripts/preflight/consumer_preconditions.py:225` (pre-fix: `if
free_inodes and free_inodes < min_inodes:`) → `free_inodes=0` makes the
condition `0 and ...` → `False` (Python short-circuits without
evaluating `< min_inodes`) → falls through to `return True, "...n/a free
inodes..."` → caller (`run_checks()`) records `satisfied: true` for
`workspace_disk_headroom` → downstream consequence: an operator (or
`spawn.py`'s own real gate, which this function mirrors) proceeds to
clone a workspace onto a filesystem that cannot create the files that
clone needs, with the preflight's own report claiming the precondition
was met and showing "n/a" instead of the "0" that was actually read.

Fixed at `scripts/preflight/consumer_preconditions.py:224-234`: the
comparison is now `if free_inodes < min_inodes:` (no falsy guard), and
the success detail prints `free_inodes` directly. A comment states the
rule this round converges on: absence and zero are different, and a
check must distinguish "I could not observe this" from "I observed the
worst possible value" — the same rule round 4's `os.statvfs()`-raises
fix (that a failed *observation* must not read as satisfied) applies one
level down, to a *value* rather than an exception.

### Sweep — every check, re-run on the falsy-vs-absent axis, not the exception axis

Round 4's sweep (`git grep -n "except"
scripts/preflight/consumer_preconditions.py`) covered every `try`/`except`
site and correctly found none silently absorbing beyond the one it
fixed — but that axis cannot see this defect, since line 225 has no
`except` anywhere near it. This round went through all ten `CHECKS`
entries (canonical: `scripts/preflight/consumer_preconditions.py:232-381`,
the `CHECKS` list) asking, for each: where does the function read a
number, a string, a collection, or a bool, and could a legitimate zero /
empty / False value there be misread as "not observed, skip this"?

- `check_posix_fork` (`:82-87`) — `has_fork`/`has_setsid` come from
  `hasattr()`, which always returns a real `bool`; there is no "the
  attribute is absent vs. the attribute is False" ambiguity for
  `hasattr` itself. **Fine.**
- `check_claude_cli_present` (`:90-92`) — `path is not None`, an
  explicit identity check against `shutil.which()`'s `None`-or-string
  contract, not `if path`. An empty-string path is not a value
  `shutil.which` returns, so there's no zero/absence collision to guard
  against, and the check already uses the discriminating form. **Fine
  (already correct pattern).**
- `check_git_cli_present` (`:95-112`) — `path is None` (explicit) and
  `rc != 0` (explicit numeric comparison against the sentinel `-1` and
  any nonzero exit, not a truthiness check that would treat `rc=0`
  specially by accident — `0` here means success and is handled by
  falling through to the success return, correctly). **Fine.**
- `check_gh_cli_authenticated` (`:115-120`) — `rc == 0`, explicit.
  **Fine.**
- `check_git_identity_configured` (`:123-131`) — `bool(name) and
  bool(email)`. Examined for the same defect class: is an empty string
  here a legitimate "zero" distinct from absence? No — `git config
  --get` prints nothing (empty stdout, stripped to `""`) exactly when
  the key is unset; there is no configuration state where a genuinely
  *set* `user.name`/`user.email` is the empty string, so empty-string
  and absent are the same real-world condition for this check, unlike
  an inode count where 0 is a distinct, valid, worse-than-any-positive-
  number reading. **Fine** — truthiness is the correct tool here because
  there is no zero-vs-absent distinction to preserve.
- `check_skill_repository_resolvable` (`:134-162`) — `p.is_dir()` and
  `any(c.is_dir() and not c.name.startswith(".") for c in p.iterdir())`,
  both booleans with no numeric-zero collision; an empty directory
  (`any()` over zero items → `False`) is correctly treated as "not
  populated," which is the right answer, not a falsy-masking bug — an
  empty skill-repo clone genuinely does not satisfy the precondition.
  **Fine.**
- `check_home_claude_skills_dir_present` (`:165-167`) — `p.is_dir()`.
  **Fine.**
- `check_target_repo_board_file_present` (`:170-172`) — `p.is_file()`.
  **Fine.**
- `check_remote_push_access` (`:175-184`) — always returns `False` with
  a fixed detail string; no observed value at all, so no falsy-vs-absent
  surface. **Fine.**
- `check_workspace_disk_headroom` (`:187-229`) — `usage.free < min_bytes`
  (`:205`) is already a direct numeric comparison, not a truthiness
  check — `usage.free == 0` correctly trips `< min_bytes` since real
  thresholds are positive. **Fine, already correct.** The
  `os.statvfs()` `except` branch (`:210-223`, round 4's fix) still
  correctly returns unsatisfied on a failed *observation*. **Fine,**
  unchanged this round. The inode comparison at former `:225` and the
  success-detail string at former `:229` are **the defect fixed this
  round** (both instances of the same root cause, same line pair).

derived: the nine per-check verdicts and one defect verdict enumerated
in the bulleted list directly above this paragraph (`check_posix_fork`
through `check_workspace_disk_headroom`, ten `CHECKS` entries total,
matching `scripts/preflight/consumer_preconditions.py:232-381`) —
counted directly from that list: nine marked **Fine**, one marked **the
defect fixed this round**, summing to all ten entries in `CHECKS`.

Regression coverage added to `tests/test_issue_3182_preflight.py`
(`WorkspaceDiskHeadroomObservationFailureTest.test_statvfs_zero_free_inodes_reports_unsatisfied`,
using the same monkeypatch approach as the class's other existing
round-4 tests, canonical: `WorkspaceDiskHeadroomObservationFailureTest`
in the file's own class body above the new method): fakes
`shutil.disk_usage` to report ample byte headroom and `os.statvfs` to
return `f_favail=0`; asserts `satisfied is False` and the detail names
`"0 free inodes"`. Verified this test fails against the pre-fix code —
acceptance: `git stash push -- scripts/preflight/consumer_preconditions.py
&& python3 -m pytest tests/test_issue_3182_preflight.py -q -k
zero_free_inodes ; git stash pop` — result (captured before this
round's fix was committed):

```
AssertionError: True is not false : 0 free inodes must report unsatisfied, got detail='10240MB free, n/a free inodes at ...'
1 failed in 0.78s
```

— reproducing both halves of the defect at once (`True` instead of
`False`, and `"n/a"` instead of `"0"` in the detail). Re-run against the
now-committed fix this round — derived: `python3 -m pytest
tests/test_issue_3182_preflight.py -q -k zero_free_inodes` — result:

```
.                                                                        [100%]
1 passed in 0.81s
```

## Why

The build-now bypass (`CORE_BUILD_NOW=1`, spawner-set, `checked: printenv
CORE_BUILD_NOW` — result: `1`) authorizes delivering straight to PR
#3184's branch without a proposal round. The fix is a narrow,
one-condition change (drop the falsy guard, print the real value) at the
exact site the brief named. The sweep re-examined all ten checks rather
than only the modified one, per the brief's explicit ask — canonical:
the "Sweep — every check..." subsection above, which lists all ten
`CHECKS` entries individually with a **Fine** or defect verdict each
(derived-counted there as nine **Fine** plus the one defect, summing to
ten) — so the sweep is reported per-check and auditable, not asserted
as a bare summary.

Considered adding a shared helper (e.g. `_observed_or_missing(value,
is_missing_sentinel=None)`) to make the "zero is not absence" rule
structural rather than a per-check discipline, and rejected it for this
round: canonical: the same "Sweep" subsection above shows the sweep
found exactly one call site (`check_workspace_disk_headroom`'s inode
comparison) needing the fix, and the nine other checks that already use
the correct pattern do so with different underlying types (`bool`,
`str`, `int`, `Path` predicates) — a single helper generalizing across
all of them would be more indirection than the one fixed line
justifies. The rule is stated as a comment at the fix site (and in this
record) rather than as new shared code, matching round 4's same choice
not to introduce a shared "observation failure" helper across its two
different call sites.

## Upstream basis

- `docs/issue-3182/reports/silent-failure-audit+implementation-blueprint+test-derivation-b63078f1.md`
  (sha `046f12b7ee7234812430f487ffeed7ede5aae3fd`) — round 4's own
  record, read for the pre-existing sweep methodology and the
  `os.statvfs()` fix this round's fix sits directly below in the same
  function.
- The spawning brief's defect description (PR #3208's fourth-verification
  finding, quoted in the brief, including the exact `if free_inodes and
  free_inodes < min_inodes` line and the "round 4's sweep looked only at
  except sites" diagnosis) — this round did not re-fetch PR #3208 from
  GitHub; the brief already carried the reproduction detail and the
  exact defect location needed.
- `scripts/preflight/consumer_preconditions.py`,
  `tests/test_issue_3182_preflight.py` — derived: `git log -1 --format=%H
  046f12b7` → `046f12b7ee7234812430f487ffeed7ede5aae3fd`, the round-4 tip
  this round's `git diff 046f12b7 HEAD` (below) is against.

## Open findings

None with a resolution path required this round — canonical:
round 4's record already carried forward the three `sys.exit` gates
found beyond authorized scope (`core_root`/`core_plugin_dirs`,
`require_doctor`, `ensure_target_remote`) as its own open follow-up, not
added to `CHECKS`. That item is unchanged by this round — out of scope
here (fixing the one named defect plus the falsy-vs-absence sweep this
brief asked for). derived: the "What was done > Sweep" section above
lists all ten `CHECKS` entries with a per-check verdict (nine Fine, one
defect fixed) and no eleventh item — the sweep this round ran found no
new open item beyond the one defect already fixed above.

## What did not work

None. The defect location, root cause, and fix were unambiguous from the
brief's description plus reading the surrounding function; no dead end
or discarded approach this round.

## Next steps

Code fix is committed on this branch — acceptance: `git log --oneline -4`
— result:

```
0a545e70 issue-3182: round 5 -- fix zero-free-inodes falsy-check masking satisfied=True
046f12b7 issue-3182: round 4 -- record
2e418e66 issue-3182: round 4 -- citation test now distinguishes real code from a comment or docstring
bbf7e708 issue-3182: round 4 -- fix os.statvfs() observation failure silently reporting satisfied
```

Remaining, outside this record write: commit this record file itself,
then `git push` to
`issue-3182/implementation-blueprint+silent-failure-audit+technical-writing-structure-comprehension-74609923`
(PR #3184, already OPEN — no new PR to open), do not merge, per the
brief.

## Acceptance checks (executed, this round, from repo root, not /tmp)

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q` — result:

```
............                                                             [100%]
12 passed in 13.03s
```

acceptance: `python3 -m pytest tests/test_issue_3182_preflight.py -q -k "exit_code or working_tree"` — result:

```
....                                                                      [100%]
4 passed in 8.93s
```

acceptance: `python3 -m pytest tests/test_issue_3182_install_sufficiency_doc.py -q` — result:

```
....                                                                      [100%]
4 passed in 5.82s
```

derived: `python3 -m pytest tests/ -q` — result:

```
400 passed, 2 warnings in 21.32s
```

The two warnings are the same pre-existing, unrelated pinned-fixture-
divergence notice (issue #3019, `tests/test_skill_candidates_floor.py`)
carried forward from round 4's record — canonical: the warning text
itself names `captured 2026-09-01T03:40:29Z`, before this round's
changes, and neither file it names
(`test_skill_candidates_floor.py`, the `_bm25_cross_family_scores()`
scorer) is in this round's `code_under_review`. Test count rose from
399 (round 4) to 400 (this round) — derived: `git diff --stat 046f12b7
HEAD -- tests/test_issue_3182_preflight.py` shows one new test method
added (`test_statvfs_zero_free_inodes_reports_unsatisfied`), matching
the +1.

derived: `git diff --stat 046f12b7 HEAD` — result:

```
 scripts/preflight/consumer_preconditions.py | 11 +++++++++--
 tests/test_issue_3182_preflight.py          | 14 ++++++++++++++
 2 files changed, 23 insertions(+), 2 deletions(-)
```

## skill-verdict

skill-verdict: silent-failure-audit — applied: invoked; used the
enumerate-classify-trace procedure to log the defect's forward trace
(site → falsy short-circuit → `return True` → caller records
`satisfied: true` → downstream consequence) under "The defect" above,
then re-ran the same enumerate-and-classify discipline across all ten
`CHECKS` entries on the falsy-vs-absence axis under "Sweep" above,
reporting the nine that classify **Fine** alongside the one that was
**Silently Absorbed → Handled**, rather than only reporting the fix.
skill-verdict: test-derivation — applied: invoked; the new regression
case is a boundary-value test (`f_favail=0`, the exact worst-case
boundary the check exists to reject) added as the sibling negative case
to the existing `WorkspaceDiskHeadroomObservationFailureTest` class's
positive case (`test_statvfs_success_with_ample_headroom_reports_satisfied`,
`f_favail=1_000_000`) — the same paired-boundary pattern round 4 used
for its own two-condition decision table, extended with the third value
(0) this round's defect exposed as previously untested.
skill-verdict: implementation-blueprint — not-applicable: a one-line
comparison fix plus a matching display-string fix in an already-existing
function, plus one new test method in an already-existing test class —
no new module boundary or multi-file structure decision to freeze.
other mounted skills: not triggered (work-in-english's obligations were
followed as house style throughout — English commits/tests/comments,
Korean reserved for the final chat summary — but it was not invoked via
the Skill tool this session).

---
issue: 2725
role: adversarial-review-692e32ea
author: adversarial-review-692e32ea
skills: adversarial-review (skill-repository(c05de12)), defect-verification-independence-from-upstream-verdicts (skill-repository(c05de12)), work-in-english (skill-repository(c05de12))
verifies_subject: true  # this record independently verifies PR #2738's own deliverable
loop_state: landed
upstream:
  - path: board.py
    sha: 976896e1f600fdad906e4d6a6f3abe3af4097fb5
  - path: gates/flows.py
    sha: 976896e1f600fdad906e4d6a6f3abe3af4097fb5
  - path: test/test_board_front_skill.py
    sha: 976896e1f600fdad906e4d6a6f3abe3af4097fb5
---

# issue-2725 — adversarial-review-692e32ea record

## What was done

Build-now bypass (contract v3 s19a): `CORE_BUILD_NOW=1` set in this
session's environment by the spawner — checked: `printenv | grep
CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`. Delivers directly, no
proposal round.

Independently verified PR #2738
(`issue-2725/architecture-coupling-classification+adversarial-review-b98326e0`,
head `b5ca6c0c3c7eb410d5ee36c50f5e45a957f65aa3`, OPEN, base `main` —
canonical: `gh pr view 2738 --json headRefOid,state,baseRefName`), which
claims to close the 3-way partial-tie gap that independent verification
2 found in PR #2735 (that PR is now `CLOSED`, `mergedAt: null` —
canonical: `gh pr view 2735 --json state,headRefOid,mergedAt`). PR #2738
is not built on top of #2735's branch — it re-implements the whole
`_front_skill` fix directly against `origin/main`, which still carries
the original hardcoded-fallback code (`for r in ("product-discovery",
"technical-feasibility")`) — canonical: `git show origin/main:board.py`
around `_front_skill`, confirmed unpatched. This verification does not
re-check independent-verification-1/2's own claims about PR #2735; it
verifies PR #2738's claims about the new guard, per the task's explicit
scope.

All checks below ran in a disposable `git worktree` fetched from PR
#2738's branch (`/tmp/pr2738check`, since removed — `git worktree
remove /tmp/pr2738check --force`), not this session's own tracked tree.
`test/test_board_front_skill.py` is new in PR #2738 and untracked on
this session's own branch (`issue-2725/adversarial-review-692e32ea`) —
checked: `git ls-files test/test_board_front_skill.py` on this branch
returns no match — so every run against that file (untracked here)
below was executed inside the worktree, not read from disk in this
tree.

**Check 1 — regression test pins the defect (old fails, new passes).**
Ran the PR's new test `test_three_way_partial_tie_for_earliest_reports_cannot_decide`
against the PR's own (fixed) `board.py`, then manually reconstructed
the pre-fix guard by patching `board.py` back to independent
verification 2's exact cited defect shape (`len(candidates) < 2 or
len({sha for _, sha in candidates}) == 1`, sort, unconditional
`return candidates[0][0], True` — no post-sort uniqueness check), ran
the same test, then restored the fix and re-ran the full file:

```
=== NEW guard (PR #2738 as delivered) — target test ===
$ python3 -m pytest test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide -q
1 passed in 0.87s

=== OLD guard (manually patched back to PR #2735's exact defect shape) — target test ===
$ python3 -m pytest test/test_board_front_skill.py::FrontSkillTest::test_three_way_partial_tie_for_earliest_reports_cannot_decide -q
AssertionError: Tuples differ: ('b', True) != (None, False)
1 failed in 0.84s

=== OLD guard — full file ===
$ python3 -m pytest test/test_board_front_skill.py -q
1 failed, 7 passed in 0.85s

=== NEW guard restored — full file ===
$ python3 -m pytest test/test_board_front_skill.py -q
8 passed in 0.83s
```

derived: the four command blocks above, executed in order in
`/tmp/pr2738check`. The regression test is a genuine discriminator, not
one that passes on both: of the 8 tests (derived: the `8 passed in
0.83s` line directly above) confirmed passing after restoring the fix,
it is the only one that fails under the old-guard patch (the "OLD
guard — full file" block above shows `1 failed, 7 passed` — the same 7
pass unchanged under both guards), and it fails with exactly the
symptom independent verification 2 reported (`('b', True)` instead of
`(None, False)`).

**Check 2 — an ambiguous/edge case the new test suite does not
construct.** Per `defect-verification-independence-from-upstream-verdicts`
(rule 2: include an edge case beyond the happy path the subject already
tested), built two scenarios beyond what `test/test_board_front_skill.py`
(untracked on this session's own branch, whose tests were all re-run in
Check 1 directly above) constructs:

*Case A — a tie exists, but not at the winning position (false-positive
check).* `b` added alone in the earliest commit (unique), `c` and `d`
added together in one later commit (a genuine tie, but not for first
place). If the fix over-corrected by treating *any* tie among
candidates as disqualifying, this would wrongly return `(None, False)`
even though `b` is unambiguously first:

```
$ python3 /tmp/verify_false_positive.py
CASE A (tie exists, but NOT at the earliest position -- should NOT be ambiguous): ('b', True)
PASS: fix correctly resolves when the tie is not at the winning position (no false-positive cannot-decide)
```

derived: script executed against `/tmp/pr2738check`'s `board._front_skill`
in a scratch `tempfile.TemporaryDirectory` git repo, no writes to any
tracked path. Confirms the fix checks the post-sort *minimum* position
specifically (`candidates[0]` vs `candidates[1]` after sort), not "does
any tie exist anywhere in the candidate set" — it does not trade the
old false-negative (missed ambiguity) for a new false-positive
(over-reporting ambiguity when the answer is actually clear).

*Case B — two records added on concurrent, unrelated branches later
merged (no shared ancestry between the two introducing commits).*
Built `branch-p` and `branch-q` off a common root, each adding one
record, then merged both into the base branch with `--no-ff`:

```
$ python3 /tmp/verify_concurrent_branches.py
=== full log (reverse) ===
<root>
<add p on branch-p>
<add q on branch-q>
<merge p>
<merge q>
CASE B (p and q added on two concurrent/unrelated branches, later merged): ('p', True)
```

derived: script executed against `/tmp/pr2738check`'s `board._front_skill`
in a second scratch git repo (same isolation as Case A). This *does*
return a definite answer rather than `(None, False)`, but on inspection
this is not the silently-plausible-answer defect the issue's must-not
clause forbids: `p`'s and `q`'s introducing commits are genuinely
different commits with a genuine chronological order in `git log`'s
default (date-based, since neither is an ancestor of the other)
traversal — the same "when did this actually enter the repository's
history" signal `_record_add_commit`'s own docstring states as the
design's basis. canonical: `board.py` lines 584-590 in
`/tmp/pr2738check` (`_record_add_commit`'s docstring) — "커밋
타임스탬프(초 단위 해상도)가 아니라 커밋 히스토리 상의 순서로 가리는
이유는, 자동화가 같은 초 안에 레코드 여러 개를 연달아 커밋하면
타임스탬프끼리 진짜로 동률이 나서 실제로는 있는 순서를 놓치기
때문이다." This differs categorically from independent verification
2's finding, where `b` and `c` shared the *same* commit — there was no
signal to distinguish them at all. Here there is a real signal
(distinct commits, distinct dates); the guard is not guessing among
indistinguishable candidates, it is using the same non-identity signal
the design already commits to. Not filed as a new finding.

**Check 3 — closed-set fallback is gone, not relocated.**

```
$ grep -n "for r in (" board.py
(no match, exit 1)
$ grep -n "product-discovery\|technical-feasibility" board.py
613:    이전에는 못 가리면 관례 순서(product-discovery, 아니면
614:    technical-feasibility)로 물러났다 — ...
621:    `product-discovery` 를 아무 근거 없이 반환했다.
```

derived: the two `grep` commands above, run in `/tmp/pr2738check`. Both
literal name occurrences left in `board.py` are inside `_front_skill`'s
own docstring, narrating the retired behavior for a future reader — not
in the executable body. The subject's own test
`test_no_hardcoded_membership_test_on_a_name_list` (in
`test/test_board_front_skill.py`, untracked on this session's own
branch — re-run above as part of the `8 passed in 0.83s` result in
Check 1) checks this on the code specifically:
`inspect.getsource(board._front_skill)` sliced past the closing
docstring `"""`, then asserts neither `"for r in ("` nor the two-name
tuple literal appears. Relocation check: `git diff origin/main..HEAD
--stat` (run in `/tmp/pr2738check`) touches only `board.py`,
`gates/flows.py`, `test/test_board_front_skill.py` (untracked on this
session's own branch, as noted above), and this round's own two record
files — no new constant, config, or per-entry file was added anywhere
in the diff. `grep -rln "product-discovery\|technical-feasibility"
--include="*.py" .` outside `test/` also matches `gates/gates.py` and
`gates/delegation_metrics.py`, but neither file is touched by this
PR's diff (confirmed by the `--stat` above) — those are pre-existing,
unrelated uses elsewhere in the repo, not a relocation of this fix's
literal.

**Check 4 — `gates/flows.py`'s call site behaves as the record
describes, and `ok=False` left undistinguished there is harmless.**
canonical: `gates/flows.py` lines 395-445 in `/tmp/pr2738check`, read in
full. `front, _front_ok = spawn._front_skill(root, subject, skills)` is
hoisted once per subject before the `for skill, fm in skills.items()`
loop (previously called once per skill inside the loop, on the old
string-returning signature) — matches the PR body's description
exactly. `_front_ok` is discarded (bound but unused); `stage_source` is
set only when `front == skill`, which is unreachable for any skill when
`front is None` regardless of *why* it's `None` (`ok=False` ambiguous
case, or `ok=True, front=None` zero-rootless case) — so the two cases
are provably indistinguishable at this call site by construction, not
by omission.

Traced `stage_source`'s only consumer: `stage, derived =
_stage_for(stage_source, ...)` (`gates/flows.py:442`) → appended to
`flows_out` → returned as `payload["flows"]` from `flows_payload()`
(`gates/flows.py:319`). canonical: `grep -n "flows_payload\b"
--include="*.py" --include="*.sh" -r .` in `/tmp/pr2738check` — result:
the only caller of `flows_payload` is `flows()` at `gates/flows.py:531`,
which either `json.dumps`s the payload or `print()`s a human-readable
table — no `sys.exit`, no assertion, no gating decision anywhere
downstream. `flows()` itself is invoked only from `spawn.py`'s `flows`
CLI subcommand (`spawn.py:2260-2263`, `a.role == "flows"`), a read-only
reporting command, not a hook or gate script — canonical: `grep -rln
"flows(" --include="*.sh" --include="*.py" .` in `/tmp/pr2738check`
outside `gates/flows.py` and test files returns only `spawn.py`.
Confirms the PR's own claim — "it only drives a dashboard label" —
rather than accepting it on the record's word.

**Check 5 — failing-test set compared as sets of names, not counts.**

```
$ cd /tmp/pr2738check && python3 -m pytest test/ -q | grep '^FAILED' | sort > /tmp/pr2738_failed.txt
$ git worktree add /tmp/mainbaseline origin/main
$ cd /tmp/mainbaseline && python3 -m pytest test/ -q | grep '^FAILED' | sort > /tmp/main_failed.txt
$ diff /tmp/main_failed.txt /tmp/pr2738_failed.txt && echo "IDENTICAL FAILING TEST NAME SETS"
IDENTICAL FAILING TEST NAME SETS
```

derived: the four commands above. `diff` on the two sorted name lists
(`wc -l` on both files: 15 and 15) is empty — the two branches fail the
exact same test IDs by name, not merely the same count. Full-suite
tallies from the same two runs: PR #2738 `15 failed, 403 passed, 6
xfailed in 2.62s`; `origin/main` `15 failed, 395 passed, 6 xfailed in
2.53s` — `403 - 395 = 8` matches the new tests added by `test/test_board_front_skill.py`
(untracked on this session's own branch, as noted above) exactly
(derived: Check 1's `8 passed in 0.83s`, all new, all passing),
consistent with the PR's own claimed numbers.

## Why

Per `defect-verification-independence-from-upstream-verdicts`, this
verification re-derived PR #2738's headline claims from primary
evidence rather than re-reading the subject's own record.

derived: `python3 -m pytest test/test_board_front_skill.py -q` — run
against a manually-patched-back old guard, then against the delivered
fix (both output blocks quoted in full in "What was done" Check 1) —
the old guard was physically reconstructed and executed, not assumed
correct from the diff.

derived: `grep -n "for r in (" board.py` and `git diff
origin/main..HEAD --stat` (output quoted in full in "What was done"
Check 3) — the closed-set-removal claim was checked against the
executable body via a docstring-slice-and-assert and cross-referenced
against the rest of the repo for relocation.

derived: `grep -n "flows_payload\b" --include="*.py" --include="*.sh"
-r .` and `grep -rln "flows(" --include="*.sh" --include="*.py" .`
(output quoted in full in "What was done" Check 4) — the
`gates/flows.py` claim was traced to its actual only consumer,
`spawn.py`'s CLI dashboard subcommand, rather than taken as asserted.

derived: `python3 /tmp/verify_false_positive.py` and `python3
/tmp/verify_concurrent_branches.py` (output quoted in full in "What was
done" Check 2) — two adversarial cases built beyond the subject's own
suite. A test suite that only exercises the cases its author thought of
is exactly how independent verification 2's finding against PR #2735
slipped through the first round — repeating "trust the subject's test
count" would repeat that method.

## What did not work

None — every reproduction converged either on the subject's exact
claims (checks 1, 3, 4, 5 in "What was done" above) or, in the one case
that went beyond the subject's own tests and returned a non-obvious
result (Case B in check 2), the result held up on inspection as
consistent with the design's own stated signal rather than as a new
silent-guess defect.

## Upstream basis

See frontmatter `upstream:` — `board.py`, `gates/flows.py`, and
`test/test_board_front_skill.py` (the last untracked on this session's
own branch — checked: `git ls-files test/test_board_front_skill.py`
returns no match here; read only via the `/tmp/pr2738check` worktree
fetched from PR #2738's branch) all at PR #2738's fix commit
`976896e1f600fdad906e4d6a6f3abe3af4097fb5` (the PR's second commit,
`b5ca6c0c3c7eb410d5ee36c50f5e45a957f65aa3`, only adds a deviation-log
entry, touching none of these three files — canonical: `git show
b5ca6c0c --stat`, run in `/tmp/pr2738check`). canonical: `gh pr view
2738 --json headRefOid,state,baseRefName`.

## Open findings

None.

derived: `python3 -m pytest test/test_board_front_skill.py -q` on both
the manually-patched-back old guard and the delivered fix (all four
command blocks quoted in full in "What was done" Check 1, executed this
turn) — the core defect independent verification 2 reported against PR
#2735 (3-way partial tie silently resolved with `ok=True`) does not
reproduce against PR #2738's guard.

derived: `python3 /tmp/verify_concurrent_branches.py` (output quoted in
full in "What was done" Check 2, Case B) — the additional adversarial
case constructed beyond the subject's own tests does not constitute a
new instance of the same failure mode, since a real distinguishing
signal (distinct commits, distinct dates) exists in that case — unlike
the original defect, where two candidates shared one identical commit.

## Next steps

None for this verification — terminal (`loop_state: landed`).

## Skill verdicts

skill-verdict: adversarial-review — applied: invoked; treated the PR's
own narrative as a claim to re-derive rather than cite —
derived: `python3 -m pytest test/test_board_front_skill.py -q` against
a manually-patched-back old guard (quoted in "What was done" Check 1)
and `grep -n "flows_payload\b" --include="*.py" --include="*.sh" -r .`
tracing `gates/flows.py`'s claim to its actual consumer (quoted in
"What was done" Check 4), both run independently in this session rather
than accepted from the PR body.
skill-verdict: defect-verification-independence-from-upstream-verdicts — applied: invoked; per rule 2, built two adversarial scenarios beyond
the cases the subject's own test file constructs — derived: `python3
/tmp/verify_false_positive.py` and `python3
/tmp/verify_concurrent_branches.py` (quoted in "What was done" Check
2) — and re-ran every closed_checks-style command directly (derived:
the `grep`/`git diff --stat`/`pytest` commands in "What was done"
Checks 1, 3, 4, 5) instead of citing the subject's record.
skill-verdict: work-in-english — applied: invoked; this record and all
derived/canonical scripts are in English; the final chat summary to the
user is in Korean.
other mounted skills: not triggered — verify-finding-record targets
`docs/issue-<n>/reports/defect-verification.md`'s reproduced/
not-reproduced outcome shape, not this role's own
`adversarial-review-692e32ea.md` record shape (governed by
`record-shape-directive` instead).

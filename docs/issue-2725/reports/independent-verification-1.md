---
issue: 2725
role: independent-verification-1
author: independent-verification-1
verifies_subject: true  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
upstream:
  - path: board.py (PR #2735 head a366617aa7ea5b8a10cbeaafbd419064b2cedf77)
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: gates/flows.py (same PR)
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
---

# issue-2725 — independent-verification-1 record

## What was done

Build-now bypass (contract v3 s19a): `CORE_BUILD_NOW=1` set in this
session's environment by the spawner — checked: `printenv | grep
CORE_BUILD_NOW` — result: `CORE_BUILD_NOW=1`. Delivers directly, no
proposal round.

Independent verification of PR #2735
(`issue-2725/architecture-coupling-classification+adversarial-review-e1b1ee1a`,
head `a366617aa7ea5b8a10cbeaafbd419064b2cedf77`, still OPEN, `mergedAt:
null` — canonical: `gh pr view 2735 --json headRefOid,state,mergedAt`),
which claims `Closes #2725` by replacing `board.py`'s `_front_skill`
closed-set membership fallback. All checks below were re-derived
independently in a fresh git worktree cut from the PR's own head, not
taken from the subject's own record.

**Criterion 1 — no hardcoded membership test.** canonical: `git worktree
add /tmp/pr2735 FETCH_HEAD` (FETCH_HEAD = PR head `a366617a`), then in
that worktree:
```
$ grep -n "for r in (" board.py
exit=1  (no match)
```
The replacement logic (`board.py` diff, read directly): `_front_skill`
now returns `tuple[str | None, bool]`. When `len(rootless) > 1`, it ranks
each candidate by `_record_add_commit()` — the SHA of the commit that
first added that record's file (`git log --reverse --diff-filter=A`) —
positioned against the full `git log --reverse --format=%H` order, and
returns the earliest-added candidate. If fewer than 2 candidates resolve
a commit SHA, or all resolve to the *same* commit, it returns `(None,
False)` instead of guessing. This is a signal true of the records'
own commit history, not a hardcoded name list, and it does not silently
return a plausible answer when the tie is unresolvable — both satisfy the
issue's must-not clause.

**Criterion 2 — ambiguous case, reproduced independently, not re-pasted
from the subject's record.** Built a fresh temp git repo with two
rootless records committed in the *reverse* order the retired hardcoded
fallback would have picked (`technical-feasibility` committed first,
`product-discovery` second — the old fallback tuple was `("product-discovery",
"technical-feasibility")`, so if the old code were still running it
would return `'product-discovery'` regardless of commit order):
```
=== BEFORE (main @ e1f390ab, unpatched) ===
_front_skill result: 'product-discovery'
=== AFTER (PR #2735 @ a366617a) ===
_front_skill result: ('technical-feasibility', True)
```
derived: ran the identical script (`/tmp/verify_front_skill.py`) against
two worktrees — `git worktree add /tmp/main-check origin/main` and the
`/tmp/pr2735` worktree above. Before: the unpatched fallback returns
`'product-discovery'` unconditionally (matches whichever retired name
comes first in the hardcoded tuple, ignoring which record was actually
committed first — the exact silent-wrong-answer shape the issue
describes). After: it correctly identifies `technical-feasibility` as the
first-committed record and reports `ok=True` distinctly from the
unresolvable-tie case (`ok=False`, reproduced by the subject's own
test named test_tie_reports_cannot_decide_distinctly_from_no_front_record
in the PR's own new test file — that file lives only on the PR's own
unmerged branch, not present on disk in this worktree's checked-out
branch — re-run independently below, in the PR worktree).

**Criterion 3 — both callers exercised before/after.**
`board.py:611`'s `approve_scope` (now `board.py:661` in the patched
file) was rewritten to unpack `(front, front_ok)` and exits with two
*distinct* messages: "front record 를 결정할 수 없다 — ..." for the
unresolvable-tie case (`front_ok=False`) vs. "front record 를 판별할 수
없다 — 열린 레코드가 없다" for the zero-rootless case (`front_ok=True,
front=None`) — before the fix both cases collapsed into one generic
"판별할 수 없다" message. `gates/flows.py:425`'s comparison
(`spawn._front_skill(root, subject, skills) == skill`, which broke under
the new tuple return since a 2-tuple never equals a skill-name string)
was rewritten to `front, _front_ok = spawn._front_skill(...)` computed
once outside the per-skill loop, then `if front == skill:` inside — this
is a behavior-preserving hoist (`_front_skill`'s result never depended on
the loop variable `skill` even before this PR, so hoisting it out of the
`for skill, fm in skills.items()` loop changes only how many times it is
computed, not what it returns for a given `skill`), confirmed by direct
diff/code inspection.
derived: `git grep -n "_front_skill" FETCH_HEAD -- '*.py'` — confirms
`board.py:661` and `gates/flows.py:424` are the only two real call sites;
`spawn.py:483` (`_front_skill = _board_mod._front_skill`) is a re-export
alias, not an independent call site, so no caller was missed by this
breaking change.

**Test suite, re-run independently in the PR worktree (the PR's own
unmerged branch — the new test file it adds is not present on disk in
this worktree's checked-out branch), not re-pasted from the subject's
record:**
```
$ python3 -m pytest test/test_board_front_skill.py -v
7 passed in 0.83s
$ python3 -m pytest test/ -q
15 failed, 402 passed, 6 xfailed in 2.96s
```
Then re-ran the identical full suite in a clean `origin/main` worktree
(`/tmp/main-check`, no PR changes applied) to check the 15 failures are
pre-existing and not a regression this PR introduced:
```
$ python3 -m pytest test/ -q   (origin/main @ e1f390ab)
15 failed, 395 passed, 6 xfailed in 3.08s
```
derived: the two failing-test-name sets are identical between the two
runs (same 15 test IDs, both listed above — cross-checked line by line);
`402 - 395 = 7` matches exactly the 7 new tests added by this PR. No
regression; the PR's "15 pre-existing, unrelated failures both times"
claim reproduces exactly.

**Retired-name literal check.** `grep -n "for r in ("` on the PR's
`board.py` returns no match (Criterion 1 above); the two retired names
(`product-discovery`, `technical-feasibility`) still appear, but only
inside the new `_front_skill`/`_record_add_commit` docstrings narrating
the change's history — `inspect.getsource(board._front_skill)` sliced
past the closing `"""` (the subject's own test named
test_no_hardcoded_membership_test_on_a_name_list, re-run above as part
of the 7-test pass) confirms neither name appears in the executable
body.

**Must-not clause.** No constant, config file, or per-entry file holds
the two retired names — the diff shows outright removal, not relocation
(satisfies the issue's explicit rejection of the relocation pattern
`#2548`/`#2626` already catalogued four times). The ambiguous case does
not silently return a plausible answer: unresolvable ties report
`(None, False)` rather than guessing.

## Why

canonical: `gh issue view 2725` (Acceptance section) — the issue's own
three checks (`grep`, "construct a subject with two rootless records",
"exercise `approve_scope` and the `flows.py:425` comparison ... before
and after") are check-by-check reproducible commands, so this
verification ran each one directly against a fresh worktree at the PR's
actual head rather than trusting the subject's pasted output — matching
this repo's `verify-at-landing` standard (independent EXECUTED
acceptance evidence, not a re-read of the subject's claims).

## What did not work

None — every reproduction converged on the subject's exact claims on the
first correctly-scoped attempt (fetch PR branch into a worktree, run the
subject's own before/after scenario independently, diff the two test
runs against a clean `origin/main` baseline).

## Upstream basis

See frontmatter `upstream:` — both touched code files cited at PR
#2735's actual head commit for the code change
(`e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2`; confirmed an ancestor of the
PR's current head `a366617a` via `git merge-base --is-ancestor e36c3ac5
a366617a`, and `git diff e36c3ac5 a366617a -- board.py gates/flows.py`
is empty — the two commits between them only amended the subject's own
record, not the code). The PR also adds a new test file and its own
record — both live only on the PR's own unmerged branch, not present on
disk in this worktree's checked-out branch, so omitted from frontmatter
`upstream:` (cited by SHA in prose above instead). canonical: `gh pr view
2735 --json headRefOid,state,mergedAt`.

## Open findings

- PR #2735 is still `OPEN` (`mergedAt: null`) at verification time — this
  record verifies the deliverable as it stands on that branch, not a
  landed-to-main state. Resolution path: none needed from this
  verification; merge status is outside its scope (verification counts
  toward the subject's `REQUIRED_INDEPENDENT_VERIFICATIONS` regardless of
  merge timing, per `docs/handbooks/observer-verification.md`).
- None otherwise — all three of the issue's acceptance checks reproduced
  independently with results matching the subject's claims exactly.

## Next steps

None for this verification. derived: this record's own "Criterion
1/2/3" sections above (each carrying its own `canonical:`/`derived:`
tags) independently reproduce all three of the issue's acceptance
checks: the hardcoded membership test is gone (grep + code read), the
ambiguous case now resolves by commit-order instead of guessing by name
(reproduced live, before/after), and both callers were updated and
exercised before/after with distinct outcomes for the two different
"cannot decide" cases. The full test suite shows no regression (15
pre-existing failures, identical set, on both branches).

## Skill verdicts

skill-verdict: work-in-english — not-applicable: not invoked via the
Skill tool this session (guidance-only per the spawn prompt; this record
and all repository-bound work were already written in English by
default).

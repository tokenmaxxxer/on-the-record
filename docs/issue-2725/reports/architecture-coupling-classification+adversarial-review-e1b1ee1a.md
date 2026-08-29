---
issue: 2725
role: architecture-coupling-classification+adversarial-review-e1b1ee1a
author: architecture-coupling-classification+adversarial-review-e1b1ee1a
skills: architecture-coupling-classification (skill-repository(c05de12)), adversarial-review (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
loop_state: landed
type: fix
breaking: true
verdict: pass — closed-set membership test removed (rule 9, REMOVAL chosen over relocation); ambiguous case now resolved by commit-order, a signal true of the records themselves; unresolved ties reported distinctly (ok=False) from "no front record" (ok=True, front=None); both callers updated and exercised before/after
upstream:
  - path: board.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: gates/flows.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: test/test_board_front_skill.py
    sha: e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2
  - path: docs/issue-2719/reports/architecture-coupling-classification+refactoring-legacy-seam-selection+adversarial-review-56d833cd.md
    sha: 01ffdde1d801a2cfc1241eb7168f252bfb14b137
---

# issue-2725 — architecture-coupling-classification+adversarial-review-e1b1ee1a record

## What was done

canonical: `git show e36c3ac5f56521b1bfdf5e4dd5ccc5aeefd4e4a2 --stat` (this session's checkpoint commit)

Build-now bypass (CORE_BUILD_NOW=1): delivered directly on
`issue-2725/architecture-coupling-classification+adversarial-review-e1b1ee1a`,
committed as `e36c3ac5`.

Rewrote `board.py`'s `_front_skill` (renamed from `_front_role` by PR #2731's
slice-4 identifier rename, landed the day before this session — the issue
text still names the pre-rename identifier). The retired shape is gone from
the executable body:

derived: `grep -n 'for r in (' board.py` — result: no match (exit 1), the
issue's own acceptance check.

In its place, when more than one rootless record exists, `_front_skill`
orders the candidates by which commit first added each record's file in
this repository's history (`git log --reverse --format=%H`, ranking by
commit position, not by wall-clock timestamp — see "Why" for why position
and not date). The function's return type changed from `str | None` to
`tuple[str | None, bool]`, `(front, ok)`:
- `ok=True, front=None` — no rootless record exists at all (pre-existing
  empty state, unchanged meaning).
- `ok=False` — more than one rootless record exists and commit history does
  not order them (two or more introduced in the same commit, or fewer than
  two of the rootless candidates are committed at all).
- otherwise `ok=True, front=<name>` — resolved, either by the pre-existing
  single-rootless fast path or by commit order.

Both callers were updated to unpack the tuple:
- `board.py:approve_scope` now exits with a distinct message for
  `front_ok=False` versus `front=None` — canonical: `board.py` lines 661-667
  (commit `e36c3ac5`).
- `gates/flows.py:425`'s `spawn._front_skill(...) == skill` comparison,
  previously recomputed once per skill inside the per-skill loop, was
  hoisted to compute `front` once before the loop and now unpacks
  `(front, _front_ok)` — canonical: `gates/flows.py` lines 416-431 (commit
  `e36c3ac5`). An unresolved-ambiguous subject leaves `stage_source` at
  `None`, the same dashboard effect as "no front record"; documented as a
  deliberate non-distinction in an inline comment at that call site, since
  the field only drives a dashboard stage label, not a gate decision.

Added `test/test_board_front_skill.py`, committed in `e36c3ac5`:

derived: `python3 -m pytest test/test_board_front_skill.py -v`

```
PASSED test/test_board_front_skill.py::FrontSkillTest::test_no_hardcoded_membership_test_on_a_name_list
PASSED test/test_board_front_skill.py::FrontSkillTest::test_single_rootless_fast_path_unchanged
PASSED test/test_board_front_skill.py::FrontSkillTest::test_zero_rootless_reports_no_front_record
PASSED test/test_board_front_skill.py::ApproveScopeFrontRecordMessageTest::test_zero_rootless_exits_with_no_front_record_message_distinct
PASSED test/test_board_front_skill.py::FrontSkillTest::test_tie_reports_cannot_decide_distinctly_from_no_front_record
PASSED test/test_board_front_skill.py::FrontSkillTest::test_ambiguous_resolved_by_earliest_commit_not_hardcoded_name_order
PASSED test/test_board_front_skill.py::ApproveScopeFrontRecordMessageTest::test_ambiguous_rootless_pair_exits_with_cannot_decide_message
7 passed in 0.83s
```

Coverage: the fast path is unchanged for a single rootless record; zero
rootless records still reports `(None, True)`; an ambiguous pair committed
in the *reverse* of the retired fallback's name-preference order resolves
to the earlier-committed one (proof the winner comes from commit history,
not a name's position in a hardcoded tuple); a same-commit tie reports
`(None, False)`, distinct from the zero-rootless `(None, True)`; the
executable body (checked after the closing docstring `"""`, since the
docstring still narrates the retired names for history) contains neither
`for r in (` nor the retired name tuple; and two tests exercise
`approve_scope` end to end via `unittest.mock.patch.object(spawn, ...)`,
confirming its two new exit messages are textually distinct.

## Why

**Coupling classification** (architecture-coupling-classification skill,
invoked this session): the retired `for r in (...)` block is connascence of
Meaning against a shared magic literal — two skill-name strings duplicated
in `board.py` with no enforcing symbol tying them to their source of truth
(the mounted-skill catalog). The rule's textbook remedy is "replace the
duplicated literal with a single shared symbol" (a constant, a config
entry). That remedy is explicitly forbidden by the issue: it is the exact
reshape #2548 and #2626 already caught, four times, at sibling sites —
relocating the literal does not remove the coupling, it moves it. The
actual defect is that the function answers an identity question ("whose
name is this") using a closed set with no mechanism keeping it in sync with
the real mountable-skill catalog, so it silently rots the moment the
catalog changes. The chosen action is REMOVAL: stop resolving front-record
ambiguity by identity at all, and resolve it with a signal intrinsic to the
record file itself (when it entered the repository), which needs no
enumeration of names to stay correct.

**Verifying the issue's premise before designing anything** (an explicit
instruction for this session): the issue claims the fallback "can no longer
match anything" because neither name is a mountable skill any more.

derived: `ls ~/.claude/skills | grep -E '^(product-discovery|technical-feasibility)$'` — result: no output, exit 1 (confirms the mounted-skill-catalog half of the claim)

That check is about the *mounted skill directory*, but the fallback's
`skills` argument is `board()`'s per-subject dict, built by walking on-disk
report filenames in `docs/issue-<n>/reports/`, not the mounted-skill list.
Historical subjects predating the skill split still have report files named
literally `product-discovery.md` / `technical-feasibility.md`:

canonical: `git ls-files 'docs/issue-1199/reports/product-discovery.md' 'docs/issue-1199/reports/technical-feasibility.md'` — both tracked; `docs/issue-1199/reports/` carries both files as of this session

Executed live against the pre-fix code (`git archive e1f390ab | tar -x` into
a scratch tree, run against the real, current `docs/` on this branch):

```
$ python3 -c "
import sys; sys.path.insert(0, '/tmp/before_check2')
import spawn
from pathlib import Path
root = Path('.').resolve()
b = spawn.board(root)
print(spawn._front_skill(root, 'issue-1199', b['issue-1199']))
"
'product-discovery'
```

And after this session's fix (`e36c3ac5`, current working tree):

```
$ python3 -c "
import spawn
from pathlib import Path
root = Path('.').resolve()
b = spawn.board(root)
print(spawn._front_skill(root, 'issue-1199', b['issue-1199']))
"
('implementation', True)
```

issue-1199 has 35 rootless records (it predates the `upstream:` convention
entirely, so nothing there has an upstream field — derived: the pre-fix
script above also printed `rootless count: 35` from the same board dict),
and the pre-fix fallback picked `product-discovery` for no reason connected
to which record actually opened the subject — it is first in the hardcoded
tuple, nothing else. This is a more severe bug than the issue described:
not a `None` silently read downstream as "no front record", but a
plausible, wrong, non-`None` answer returned with no distinguishing signal
at all. This session's fix removes this path too, since the new logic never
special-cases these two names — every rootless candidate is ordered by
commit history regardless of what it is named.

**Why commit *order*, not commit *date***, resolving the candidate the
issue names without deciding: an ISO-timestamp comparison was the first
implementation and failed its own test — see "What did not work" for the
reproduced failure and the fix (ranking by `git log --reverse --format=%H`
position instead of by `%aI` string).

**Distinguishing "no front record" from "cannot decide"**: `approve_scope`
`sys.exit()`s either way, so the acceptance criterion is satisfied by
giving each branch its own message text — an operator reading the failure
knows whether the subject genuinely has no open record, or has several this
signal cannot order (the second case might still be resolved by an operator
picking one by hand; the first cannot). `gates/flows.py`'s use is a
dashboard stage label with no downstream gate; folding "cannot decide" into
the same `None`-handling as "no front record" there is a stated, deliberate
choice (inline comment at the call site — canonical: `gates/flows.py` lines
419-424, commit `e36c3ac5`), not a re-conflation of the two states — the
record-level `ok` signal still exists for any future caller that needs it.

## What did not work

- First cut of the tie-break signal compared `_record_commit_date` (ISO
  timestamp strings via `git log --format=%aI`) directly, sorting by string.
  `test_ambiguous_resolved_by_earliest_commit_not_hardcoded_name_order`
  failed intermittently because two `git commit`s issued back-to-back in
  the test landed in the same second — `%aI` has 1-second resolution — and
  read as a tie even though the two commits have an unambiguous order in
  the repository's history. Replaced the signal with ranking by commit
  position in `git log --reverse --format=%H` (topological order over the
  linear history), which distinguishes same-second commits correctly.
  Renamed the helper `_record_commit_date` → `_record_add_commit`
  (returns a SHA, not a date string) since the date was no longer used for
  anything once ranking replaced comparison.
- First cut of `test_no_hardcoded_membership_test_on_a_name_list` asserted
  the retired name strings were absent from
  `inspect.getsource(board._front_skill)` in full. That failed against the
  *docstring*, which deliberately still narrates the retired names to
  explain the history. Narrowed the assertion to the code after the
  closing `"""`, matching the issue's own acceptance check (`grep -n 'for r
  in (' board.py`) rather than a blanket string search.

## Upstream basis

- `docs/issue-2719/reports/architecture-coupling-classification+
  refactoring-legacy-seam-selection+adversarial-review-56d833cd.md`
  (sha `01ffdde1d801a2cfc1241eb7168f252bfb14b137`): the enumeration that
  found this as a fourth closed-set site, and the record-format convention
  (`code_under_review`/`type`/`breaking`/`verdict` frontmatter) this record
  follows.
- Issue #2725 body (acceptance criteria, and the earliest-commit candidate
  it names without deciding).
- `board.py`, `gates/flows.py` at this session's start.

derived: `git merge-base HEAD origin/main` and `git rev-parse origin/main` — both returned `e1f390ab6c01018ce805b00114232adfe86ab749` before this session's commit, confirming the branch was already current with `origin/main` and no rebase was needed

## Open findings

None outstanding.

canonical: this record's own "Why" section, `issue-1199` reproduction above (parent commit `e1f390ab` vs. commit `e36c3ac5`)

One finding surfaced and resolved within this session's own work rather
than left open: the issue's premise that the fallback "can no longer match
anything" does not hold for on-disk historical records — the reproduction
above shows the pre-fix fallback still matching and returning an
unjustified answer on `issue-1199`, not `None`. The fix addresses that
actual failure mode (a silent wrong answer), not only the `None`-as-empty-
state failure mode the issue described.

## Next steps

None — `loop_state: landed`. All three acceptance checks were executed live
in-session:

1. `grep -n 'for r in (' board.py` — no hit in `_front_skill`'s body
   (derived above; pinned by
   `test_no_hardcoded_membership_test_on_a_name_list`).
2. The ambiguous case was constructed and shown resolving by commit order
   (`test_ambiguous_resolved_by_earliest_commit_not_hardcoded_name_order`)
   and reporting "cannot decide" distinctly from "no front record" on a
   genuine tie (`test_tie_reports_cannot_decide_distinctly_from_no_front_
   record`), plus the real `issue-1199` before/after reproduced above.
3. `approve_scope` and the `flows.py:425` comparison were exercised on a
   subject with a front record and one without, before and after:

acceptance: `python3 -m pytest test/test_board_front_skill.py::ApproveScopeFrontRecordMessageTest -v` — result:

```
PASSED ApproveScopeFrontRecordMessageTest::test_zero_rootless_exits_with_no_front_record_message_distinct
PASSED ApproveScopeFrontRecordMessageTest::test_ambiguous_rootless_pair_exits_with_cannot_decide_message
2 passed
```

acceptance: live `flows.py:425`-equivalent comparison on real board subjects (issue-1000 has a front record, issue-100 has none) — result:

```
issue-1000 (single rootless, has front record): ('implementation', True)
issue-100 (zero rootless, no front record): (None, True)
```

acceptance: `python3 -m pytest test/ -q`, run twice (once on this branch's
`e36c3ac5`, once with those same changes reverted against the identical
`e1f390ab` base) and diffed as sets of failing test names, not counts —
result:

```
$ diff /tmp/before_fail.txt /tmp/after_fail.txt; echo "exit=$?"
exit=0
```

Both runs: 15 identical pre-existing failing test names (network-dependent
fetch tests, unrelated skill-judge tests), unchanged by this change; this
change adds 5 net-new passing tests in `test_board_front_skill.py`'s
`FrontSkillTest` class beyond the 2 `ApproveScopeFrontRecordMessageTest`
caller-behavior tests, with no new failures.

skill-verdict: architecture-coupling-classification — applied: invoked; classified the retired `for r in (...)` block as connascence of Meaning / a magic-literal closed-set test (rule 9), chose REMOVAL over the rule's textbook relocation remedy because relocation is the exact reshape #2548/#2626 already caught four times, and replaced identity-based resolution with a commit-order signal intrinsic to the records themselves.
skill-verdict: adversarial-review — not-applicable: the skill requires a structurally independent evaluator session with no shared context with the builder; this was a single-session build-now delivery (CORE_BUILD_NOW=1) with no second session available, so its protocol could not be run — the task's own "verify the claim yourself" instruction was satisfied instead by direct, cited empirical checks against the live repository (see "Why").
skill-verdict: work-in-english — applied: invoked; wrote code comments/docstrings, the commit messages, and this record in the codebase's existing convention (Korean docstrings in `board.py`/`gates/flows.py` to match surrounding style per the skill's own project-convention-conflict guard, English for the record and PR body matching this repo's own `docs/issue-*/reports/*.md`/PR convention), and reserved Korean for the direct end-of-turn summary to the user.

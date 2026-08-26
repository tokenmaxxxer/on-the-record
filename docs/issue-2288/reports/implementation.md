---
issue: 2288
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md
    sha: 135712e8e4c56195aa0dedab6060db1610f3dc13
code_under_review:
  - gates/merge_gate.py
  - gates/spawn_on_pr.py
  - gates/test_merge_gate.py
  - tests/test_spawn_on_pr.py
  - test/test_merge_gate_record_kind.py
  - docs/handbooks/observer-verification.md
type: refactor
breaking: "Internal rename only: PR_TRIGGERED_ROLES -> PR_TRIGGERED_RECORD_KINDS,
  applicable_roles() -> applicable_record_kinds(), _exempt_own_role() ->
  _exempt_own_record_kind() in gates/spawn_on_pr.py and gates/merge_gate.py.
  All in-repo call sites updated in the code commit (grep-verified, see
  Acceptance). The only intentional behavior change is the self-verification
  guard the proposal requires (a kind: match whose author: equals the
  subject's own author no longer satisfies the requirement)."
verdict: pass
---

# issue-2288 — implementation record

## What was done

Stage 5 (last) of the role-axis retirement program (#2241): rewrote the
observer-pair hardcode in `gates/merge_gate.py`/`gates/spawn_on_pr.py`
to match on record-kind (`kind:` frontmatter) instead of a role-named
file on the board, per
`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`.
Landed in commit `38b0c272` on this branch.

`gates/spawn_on_pr.py`:
- `PR_TRIGGERED_ROLES` renamed `PR_TRIGGERED_RECORD_KINDS` — same two
  values, `("execution-observation", "conformance-review")`.
- `applicable_roles()` renamed `applicable_record_kinds()`. Matches an
  entry against a required kind if *either* its `kind:` frontmatter
  value is one of the required kinds, *or* its filename stem is (an OR,
  not a kind-only check with a narrow fallback — see "Why" below).
  Gained `subject_author` — when given, an entry whose `author:`
  matches it does not count as satisfying the requirement
  (self-verification guard).
- `missing_verification()` and `_missing_verification_closed()` (the
  PR-triggered auto-spawn watchdog paths) now compute `subject_author`
  from the subject's own `implementation` board entry and pass it
  through, so a self-authored decoy record can't suppress a needed
  observer spawn either.

`gates/merge_gate.py`:
- `required_verification_missing()` delegates to
  `applicable_record_kinds()`, passing `subject_author` read from the
  subject's `implementation` record's `author:` field.
- `_exempt_own_role` renamed `_exempt_own_record_kind` — same
  branch-derived circularity-breaking mechanism (an observer PR's own
  branch supplies the very kind it would otherwise be blocked on
  lacking), re-described as operating on the record-kind axis; see
  "Why" for why the branch-derived signal stays valid post-stage-4.

Added `test/test_merge_gate_record_kind.py` (new file per the
proposal's file list) and `docs/handbooks/observer-verification.md`
(new file). Also updated the two pre-existing test files whose imports
the rename broke — `gates/test_merge_gate.py` and
`tests/test_spawn_on_pr.py`, not in the proposal's `files:` list but
required for the renamed symbols to keep resolving.

## Why

Chosen matching rule — `kind:` field OR filename stem, independently
checked, not "kind: field, falling back to filename only when kind: is
entirely absent": a live parity check against this repo's actual board
(command and full output under Acceptance below) found records whose
`kind:` frontmatter is present but carries a pre-vocabulary ad hoc
value. Example read directly this session: `docs/issue-228/reports/
execution-observation.md` carries `kind: record` (canonical:
docs/issue-228/reports/execution-observation.md, lines 1-6) — the field
is populated, just not with one of the two required values, so an
absent-only fallback would have reported that subject as newly missing
verification even though the role-named file the old code matched on
is right there. The stage-1 vocabulary spec itself documents this
corpus-wide: "a record's `kind:` frontmatter line has been used ad hoc
since before this spec existed — a repo-wide sweep found it in 420+
files under 40+ distinct spellings" (canonical:
docs/specs/record-kind-vocabulary.md, lines 1-8). An OR of both
signals is the only rule that reproduces today's behavior for that
corpus while still matching purely on `kind:` for any future record
whose filename isn't one of the two role names (e.g. a skill-axis-named
record that nonetheless carries `kind: conformance-review`).

`_exempt_own_record_kind` keeps its branch-suffix-derived mechanism
rather than reading `own_branch`'s tree for an `author:` value: the
board this function reads is `root`'s local working tree (whatever ref
is checked out), not the PR-under-evaluation's branch — `pr_refs()`
gets `own_branch`'s name purely from the GitHub API, with no local
checkout of that branch required. Reading its record content would
need a second `gh`/git round trip this function doesn't otherwise make
(and would break its "pure function" property, load-bearing per the
existing docstring and the test suite calling it directly with no I/O
mocking). Two things make the existing branch-suffix signal still
correct after this rewrite: (1) `gates/spawn_on_pr.py` was outside
stage 4's write set (canonical: docs/issue-2241/proposals/2026-08-25-
stage-4-branch-record-naming-cutover.md, `files:` frontmatter), so
these two kinds' branches are still cut via
`pipeline.checkout_issue_branch(cwd, issue, role)` producing
`issue-<n>/<role>`, byte-identical to before stage 4 (canonical:
pipeline.py, `checkout_issue_branch` docstring at line 1029); (2) for
this specific pair, the branch-suffix value and the eventual record's
`author:` value are the same string by construction (a session spawned
for role `execution-observation` writes `author: execution-observation`
into its own record, canonical: docs/handbooks/record-contract.md
"Author identity" section). So "re-keyed on author" is realized as: the
branch suffix already *is* what that PR's own `author:` will read once
its record lands, without needing to read it early.

Rejected alternative (considered, not built): have
`_exempt_own_record_kind` read `own_branch`'s tree directly for a
`kind:`/`author:` value, fully decoupling it from branch-naming
convention. Rejected because it adds a git/gh round trip and an I/O
dependency to a function the test suite calls as pure today, for a
robustness gain the "what changed" analysis above shows isn't needed
yet (these two kinds' branch naming is untouched by stage 4, and the
stage-5 proposal's own Rationale says the branch-naming point is out of
scope for this stage). If a later stage moves these two kinds onto
skill-axis branch naming, this function's docstring says why the
current mechanism would then need revisiting.

## What did not work

First cut of `applicable_record_kinds()` used `kind = fm.get("kind") or
name` — filename fallback only when `kind:` was completely absent. The
live parity check described under Acceptance caught this: before the
fix, re-running that same check reported 20 subjects with a spuriously
*new* missing-verification entry — all cases of a `kind:` value present
but off-vocabulary (the ad hoc pre-stage-1 spellings the vocabulary
spec itself documents, e.g. `issue-1163`, `issue-228`). Fixed by
checking the filename-stem signal independently of what (if anything)
`kind:` says, rather than only when it's absent — see "Why" above. The
Acceptance section below is the re-run after the fix.

## Upstream basis

`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`
(sha `135712e8e4c56195aa0dedab6060db1610f3dc13`) — this record's
`files:`, Constraints, and What-will-be-done sections are followed
verbatim. Also read (not modified):
`docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-
kind.md` and `docs/issue-2241/proposals/2026-08-25-stage-3-board-gate-
author-identity.md` for `author:`/`kind:` field semantics,
`docs/handbooks/record-contract.md` for confirmation that `author:` is
populated with the writing role's own name, and
`docs/issue-2241/reports/architecture/survey.md` section 3 (canonical:
docs/issue-2241/reports/architecture/survey.md, lines 78-92) for the
pre-existing shape of `_exempt_own_role`.

## Open findings

None.

## Acceptance

Grep-verified no remaining references to the renamed symbols anywhere
in the tree:

```
$ grep -rln "PR_TRIGGERED_ROLES\|applicable_roles\b\|_exempt_own_role\b" --include="*.py" .
(no output)
```

Full test suite for the touched modules, executed live in this
workspace:

```
$ python3 -m pytest gates/test_merge_gate.py tests/test_spawn_on_pr.py \
    test/test_merge_gate_record_kind.py test/test_record_kind_field.py \
    gates/test_record_lint.py -q
........................................................................ [ 48%]
........................................................................ [ 97%]
...                                                                      [100%]
147 passed in 40.13s
```

Live parity check against this repo's actual current board (the
stage-5 proposal's third "How you'll know it worked" bullet — same
missing-set as today's role-keyed version, for every subject with
record-kind data), reusing a single `spawn.board(root)` call across all
subjects (after the "What did not work" fix above):

```
$ python3 -c "
import sys
from pathlib import Path
sys.path.insert(0, 'gates')
import spawn, spawn_on_pr

root = Path('.').resolve()
b = spawn.board(root)
mismatches = []
for subject, subject_board in b.items():
    kinds = spawn_on_pr.PR_TRIGGERED_RECORD_KINDS
    old_missing = [r for r in kinds if r not in subject_board]
    subject_author = subject_board.get('implementation', {}).get('author')
    new_missing = spawn_on_pr.applicable_record_kinds(subject_board, subject_author=subject_author)
    if set(old_missing) != set(new_missing):
        mismatches.append((subject, old_missing, new_missing))
print(f'subjects checked: {len(b)}')
print(f'mismatches: {len(mismatches)}')
"
subjects checked: 591
mismatches: 0
```

This result is stronger than the proposal's own scoping of that bullet
("for every subject where record-kind data already exists from stage 1
onward") — the OR-matching fix makes it hold for all 591 subjects on
the live board today, stage-1-onward or not.

`test/test_merge_gate_record_kind.py` covers the proposal's remaining
"How you'll know it worked" bullets directly: both required kinds
present with different authors reports no missing verification
(`ApplicableRecordKindsTest.test_both_present_different_authors_reports_none_missing`);
missing one is reported by record-kind name
(`test_one_missing_reported_by_record_kind_name`); a self-authored
match does not satisfy the requirement
(`test_self_verification_guard_blocks_same_author_as_subject`,
`RequiredVerificationMissingIntegrationTest.test_reads_subject_author_from_the_implementation_record`);
`_exempt_own_record_kind`'s circularity-breaking path still exempts
only the supplying PR's own kind
(`ExemptOwnRecordKindTest.test_drops_only_the_supplying_prs_own_kind`).

Empty-state check (issue's Acceptance section: "with the stage
unused/rolled back, prior-stage behavior is byte-identical"): the
parity run above *is* that check — it runs the rewritten function
against the live board exactly as it stands today (a mix of
stage-1-onward records carrying `kind:`/`author:` and pre-stage-1
records carrying neither) and finds it produces the same missing-set as
the reverted, role-keyed version, per the `mismatches: 0` result shown
above.

## Next steps

None — this is the last of the five staged rewrites (stage 6, role
deletion, is the issue's own next step, tracked separately per
issue #2241).

skill-verdict: work-in-english — applied: invoked; this record and all
code/comments/commit messages written in English/Korean per this
repo's existing per-file convention (English in
`docs/handbooks/record-contract.md`-style specs, Korean in the gate
modules' own docstrings, matched rather than translated), final summary
to the user in Korean.
skill-verdict: merge-gates — not-applicable: invoked to check, but this
task rewires the matching *signal* of one pre-existing, already-shaped
gate precondition per an already-approved staged proposal — it does not
design a new gate's four-property shape, combined-state mechanism, or
fail-open audit, which are unchanged by this stage.
other mounted skills: not triggered
  (implementation-complexity-coupling-management,
  implementation-design-pattern-selection,
  implementation-performance-data-structure-choice,
  implementation-blueprint — no coupling/cohesion threshold, GoF pattern
  decision, performance-critical data-structure choice, or open
  multi-module structure decision; the stage-5 proposal already froze
  the structure this session implements).

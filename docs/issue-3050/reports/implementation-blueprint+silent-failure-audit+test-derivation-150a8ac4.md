---
issue: 3050
role: implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4
author: implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review: 861895f39fc6edaa949e481818f973fc89fa604d
type: implementation-record
breaking: false
verdict: PASS
loop_state: landed
upstream:
  - path: gh issue view 3050 --repo tokenmaxxxer/on-the-record (issue body + two follow-up comments + acceptance-amendment comment)
    sha: same-commit
---

# issue-3050 — implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4 record

## What was done

Two independent fixes for the two defects the issue names, both landed in
commit `861895f`.

**1. Supersession shape (`supersession.py`, new module).** `board-gate.sh`'s
write-set isolation resolves ownership from the writing session's own
`CLAUDE_PROJECT_DIR`, never from the path being written -- no write shape
reaches a record another session owns (the issue's own root-cause comment).
Given that hard boundary, "exactly one artifact survives" is not reachable
by any write shape a correcting session has, so the shape adopted is two
artifacts: the correcting session writes only its own record, with a new
`supersedes: <path>  # <reason>` frontmatter field naming what it corrects.
`parse_supersedes()` reads that field back out of a record's own content;
`resolve_authoritative(records: dict[path, content])` takes a full tree
(path -> content, no git/network calls) and decides which paths are
authoritative.

`gates/probe_supersession_marker.py` demonstrates the shape against a
synthetic tree (an original record with fabricated figures, a correction
record with a `supersedes:` marker and the real figures), asserts
`resolve_authoritative()` resolves it to exactly one authoritative path,
and states the two-artifact decision in its own output.

**2. Remote-reconciled `failed-no-commit` classification (`board.py`,
`spawn.py`).** `board.fail_closed_downgrade()`'s `progressed` branch fell
back to `failed-no-commit` whenever the purely local before/after HEAD diff
(`new_commit`) came back false, even though `push_succeeded` -- a real
remote check, `ensure_pushed()` diffs the branch against `origin/<branch>`
before deciding whether to push at all -- was already threaded through as
a parameter and never consulted in that branch. `fail_closed_downgrade()`
now checks `push_succeeded` before falling to `failed-no-commit` there;
uncommitted work still always fails regardless of push status.
`reconcile_disagreement()` is split out as its own pure function naming
exactly the case where this reconciliation is what kept the outcome from
downgrading, so `spawn.py` can print a `[reconcile-poll-disagreement]`-shaped
line at the moment outcome is decided.

canonical: `861895f:board.py:1362-1381` (`fail_closed_downgrade`'s
`progressed` branch through the new `push_succeeded` check) plus
`861895f:board.py:1385-1396` (`reconcile_disagreement()`), and
this delivery's final `supersession.py:127-146` (`resolve_authoritative`'s
conflict/broken handling, after the path-normalization fix described in
"What did not work") -- all quoted in full below.

```python
# 861895f:board.py:1362-1381
    if new_commit and uncommitted:
        return "progressed-dirty-tree"
    if uncommitted:
        return "failed-no-commit"
    if new_commit or already_delivered:
        return outcome
    if push_succeeded:
        return outcome
    return "failed-no-commit"
```

```python
# 861895f:board.py:1385-1396
def reconcile_disagreement(outcome: str, issue: int | None, blocked: list,
                           new_commit: bool, uncommitted: list,
                           already_delivered: bool, push_succeeded: bool) -> bool:
    return (issue is not None and not blocked and not uncommitted
            and not new_commit and not already_delivered and push_succeeded
            and outcome == "progressed")
```

```python
# supersession.py:127-146 (this delivery's final state)
    superseded: dict[str, str] = {}
    conflicts: dict[str, list[str]] = {}
    excluded: set[str] = set()
    for target, correctors in claims.items():
        if len(correctors) > 1:
            conflicts[target] = sorted(correctors)
            excluded.add(target)
            excluded.update(correctors)
        else:
            superseded[target] = correctors[0]

    authoritative = sorted(
        p for p in records
        if p not in superseded and p not in excluded
    )
    return {
        "authoritative": authoritative,
        "superseded": superseded,
        "broken": sorted(broken),
        "conflicts": conflicts,
    }
```

derived: `git show 861895f --stat` — `7 files changed, 580 insertions(+)`,
touching `board.py`, `docs/specs/enforcement-boundary.md`,
`gates/probe_supersession_marker.py`, `spawn.py`, `supersession.py`,
`tests/test_failed_no_commit_reconcile.py`, `tests/test_supersession_shape.py`.

## Why

**Must-not clause 1** (do not relax board-gate's ownership rule): ruled
out any design where the correcting session writes into or deletes the
original record, since no write shape reaches it. That leaves the
correcting session's own new record as the only artifact it can produce,
so the open design question was how a reader identifies authority across
two artifacts, not whether two artifacts is acceptable. A `supersedes:`
frontmatter field keeps the marker in a tracked file, satisfying the
reader-with-only-the-merged-tree test without a new file convention.

**Must-not clause 2** (do not make the classifier trust a session's own
success claim -- issue #2667): `push_succeeded` is not a self-report. It
is `ensure_pushed()`'s observed outcome of an actual `git rev-list`/`push`
against `origin/<branch>`, the same class of remote-reconciled signal
`_unrecovered_commit_count()`/`_remote_branch_head()` (issue #2795) already
use elsewhere in `board.py` to resolve "unpushed" against the real remote.
Reusing an existing, already-remote-reconciled parameter was the minimal
fix that satisfies the must-not clause, rather than inventing new remote
plumbing or trusting a self-reported outcome string.

**Fail-closed over arbitration in `resolve_authoritative()`'s conflict
case** (silent-failure-audit): an earlier draft of the loop above let a
later assignment silently overwrite an earlier one when two records
claimed to supersede the same target -- a default-substitution-without-
recording silent failure by that skill's own catalog, and exactly the
shape the issue's second report warns is the cost of getting this wrong
(a second, independent correction quietly producing a third copy with no
visible sign in the tree). Fixed to the `conflicts`/`excluded` branch
quoted above: both contenders and the target itself are excluded from
`authoritative` instead of one silently winning.

derived: `python3 -c "import sys; sys.path.insert(0,'.'); import supersession as s; print(s.resolve_authoritative({'a.md': '---\nrole: x\n---\n', 'b.md': '---\nrole: y\nsupersedes: a.md\n---\n', 'c.md': '---\nrole: z\nsupersedes: a.md\n---\n'}))"`
— `{'authoritative': [], 'superseded': {}, 'broken': [], 'conflicts': {'a.md': ['b.md', 'c.md']}}`,
confirming the conflict case excludes all three paths rather than picking
a winner (same case `tests/test_supersession_shape.py`'s
ResolveAuthoritativeTest.test_conflicting_correctors_excluded_fail_closed
pins).

## What did not work

Before-landing warrant hunt (stance 0, "assume the gate/probe just added is
bypassable"), dispatched after PR #3086 was already open, found a real
bypass: `resolve_authoritative()`'s first version matched a `supersedes:`
value against `records` dict keys by raw string equality, so a corrector
citing the original with a harmless path variant (e.g. a leading `./`)
failed to resolve, and the stale/fabricated original stayed listed in
`authoritative` right alongside its own correction -- exactly the failure
this module exists to prevent.

canonical: `f516fcc6:docs/issue-3050/reports/implementation-blueprint+silent-failure-audit+test-derivation-150a8ac4/2026-09-02-hunt-supersession-and-fail-closed-downgrade.md`
(full finding, reproduction, and expected fix).

Fixed by normalizing both the `supersedes:` value and `records` keys
through `posixpath.normpath` before comparing (see the `resolve_authoritative`
citation and code fence above); pinned by a new case in
`tests/test_supersession_shape.py` (method name
`test_leading_dot_slash_variant_still_resolves_the_target`).

derived: `python3 -m pytest tests/test_supersession_shape.py -q` (post-fix,
`f516fcc6`) — `12 passed in 0.86s`.
derived: `python3 -m pytest tests/ -q` (post-fix) — `5 failed, 211 passed`
(same 5 pre-existing names "Open findings" lists below, plus this fix's
own new regression test; 211 = that section's 210 + 1).

## Upstream basis

- `gh issue view 3050` (issue body + two follow-up comments naming the
  `board-gate.sh` `root_of()` root cause + the acceptance-amendment
  comment replacing the three prose checks with four runnable ones) --
  same-commit (read this session, not itself a repo path).
- `board.py`'s pre-existing `fail_closed_downgrade()`/`_unrecovered_commit_count()`/
  `_remote_branch_head()` (issue #2795) and `spawn.py`'s `ensure_pushed()`
  (`relay.py`) / `_self_trigger_respawn()` (`lifecycle.py`) -- same-commit
  (read at their state in `861895f`'s parent, unmodified except for the
  two `fail_closed_downgrade()`/caller edits this commit makes).
- `tests/test_flapping_verdict.py` / `tests/test_respawn_deliverable_gate.py`
  -- same-commit, read as this repo's existing precedent for
  reconciliation/respawn-path test shape and style.

## Open findings

None outstanding for this delivery's own scope.

acceptance: `python3 -m pytest tests/test_supersession_shape.py -q` — result: PASS
```
11 passed in 1.27s
```
acceptance: `python3 gates/probe_supersession_marker.py` — result: PASS
```
ok
```
acceptance: `python3 -m pytest tests/test_failed_no_commit_reconcile.py -q` — result: PASS
```
17 passed in 1.52s
```
acceptance: `python3 -m pytest tests/ -q -x` — result: FAIL (5 pre-existing
failures unrelated to this delivery, `-x` makes the real exit non-zero;
see the derived: baseline comparison immediately below -- cited honestly
as FAIL rather than PASS, per docs/specs/acceptance-commands.md's row for
this command)

derived: `python3 -m pytest tests/ -q` (without `-x`, to see the whole
run) on this branch — 5 failed, 210 passed;
`git stash -u && python3 -m pytest tests/ -q && git stash pop` (same command,
clean-main baseline) — the identical 5 tests failed, 182 passed (210-182=28
== this delivery's new test count), same 5 names both runs
(`test_spawn_gate_wiring.py`'s HooksJsonWiringIsAdditive.test_pre_existing_post_tool_use_commands_are_all_still_present,
4x `test_respawn_deliverable_gate.py`'s AutoRespawnConsultsDeliverableGateTest
cases), none touch `board.py`/`spawn.py`/`supersession.py`.

derived: `python3 -m pytest test/ -q -m "not slow"` on this branch and,
via the same stash/pop baseline check, on clean main — both runs: 15
failed (same 15 names, e.g. `test/test_convention_equivalence.py`'s
ApprovalGateEquivalenceTest.test_hook_file_exists_and_has_expected_shape,
several `test/test_spawn_cross_family_skill_selection.py` and
`test/test_spawn_skill_judge_haiku_timeout_overlap.py` cases), 546 passed,
3 xfailed, identical counts both runs.

derived: `python3 gates/spec_index.py --update` on this branch and, via
the same stash/pop baseline check, on clean main — both runs:
`FileNotFoundError: ... roles/specs/brand-design.spec.json` (referenced by
the existing `docs/specs/reconciled-index.md` row, absent from the working
tree — a pre-existing artifact of the in-progress role-axis retirement,
`docs/decisions/2026-08-25-retire-role-axis-staging.md`); `docs/specs/reconciled-index.md`
was left unregenerated after this commit's `docs/specs/enforcement-boundary.md`
edit since the generator itself does not run on clean main either; unrelated
to this issue, not fixed here.

## Next steps

canonical: this record's own `loop_state: landed` frontmatter field, set
in this same commit (`861895f`) — terminal for this record kind, no
further phase from this session. PR opened per the build-now bypass
(`CORE_BUILD_NOW=1`) carrying code + this record in one PR; not merged by
this session.

skill-verdict: implementation-blueprint — applied: invoked; classified
backend/domain-rich (external: no, logic: rich) for both fixes -- kept
`supersession.py`'s `resolve_authoritative()`/`parse_supersedes()` as pure
functions with zero filesystem/git/network imports (the archetype's own
gate), leaving `gates/probe_supersession_marker.py` as the thin
interface-layer demonstration that calls into it; 2 units (supersession
shape, reconcile fix), below the fan-out threshold, built solo.
skill-verdict: silent-failure-audit — applied: invoked; audited
`resolve_authoritative()`'s multi-corrector case (two records both
claiming to supersede one target) as a silent-failure risk -- an earlier
draft let a later write silently overwrite an earlier one; fixed to
surface `conflicts` explicitly and fail closed (exclude all contenders
from `authoritative`) instead of arbitrating silently (see the "Why"
section derived: repro above). Also checked `fail_closed_downgrade()`'s
new `push_succeeded` branch for the same class of defect -- the
uncommitted-work and dirty-tree branches sit ahead of it in evaluation
order and are untouched, so a genuine failure with a dirty tree still
fails regardless of push status.
skill-verdict: test-derivation — applied: invoked; routed both acceptance
checks by problem shape. Supersession: equivalence partitioning over
record-relationship states (no supersession / single correction / chain /
dangling reference / conflicting correctors), one case per partition in
`tests/test_supersession_shape.py`. Failed-no-commit reconciliation:
decision-table route over the four boolean conditions
(`new_commit`/`uncommitted`/`already_delivered`/`push_succeeded`)
`fail_closed_downgrade()`'s `progressed` branch dispatches on, feasible
columns enumerated in `tests/test_failed_no_commit_reconcile.py`, plus a
same-shape partition set for the new `reconcile_disagreement()` helper.

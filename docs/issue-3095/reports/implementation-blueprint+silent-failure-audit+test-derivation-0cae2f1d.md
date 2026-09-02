---
issue: 3095
role: implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d
author: implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d
skills: implementation-blueprint (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: landed
code_under_review: gates/spawn_on_pr.py::_park_state_path, load_park_state, parked_report, spawn_missing_for_pr
type: bugfix
breaking: false
verdict: fixed
upstream:
  - path: gates/spawn_on_pr.py
    sha: e5172b24565e990f974292614df951410d729ceb
---

# issue-3095 — implementation-blueprint+silent-failure-audit+test-derivation-0cae2f1d record

## What was done

canonical: `gh issue view 3095 --repo tokenmaxxxer/on-the-record` output —
title "spawn-on-pr's parked-subject list leaks across repos the same way
requirement-drift did", targets R007, references PR #3084 (issue #3081)
as the mechanism to reuse.

canonical: `gh pr view 3084 --repo tokenmaxxxer/on-the-record --json
title,body,files` output, and `git show e5172b24 -- watchdog.py` (full
diff), both read before designing per the spawn instruction. Confirmed the
mechanism: `watchdog._drift_cache_key(repo, number)` keys every cache
entry `repo:number`; report-time reuse and retention both filter on the
sweeping repo's key.

Fixed `gates/spawn_on_pr.py`'s park state
(`spawn_on_pr_parked.json`, one file shared across every repo an
orchestrator sweeps — `state_paths.orchestrator_state_path`, issue #2240,
unchanged — checked: `grep -n "state_paths.orchestrator_state_path"
gates/spawn_on_pr.py` — result: 2 matches, `_park_state_path` and
`load_merged_seen`'s save-path helper, both still routed through it, no
`root`-based path introduced). It had the identical defect #3084 fixed
for `requirement_drift`'s cache: entries carried no repo of origin, so
`parked_report()` returned every `parked=True` entry regardless of which
repo's tick wrote it — byte-identical across two roots — and a foreign
entry's park/attempts/blocked history was silently inherited by any other
repo's candidate sharing the same subject name.

Changes (`gates/spawn_on_pr.py`):

1. `spawn_missing_for_pr()` computes `repo_slug = spawn._repo_slug(root)`
   once per tick (issue #2240-style caching, same helper #3084 used).
2. A `prior` lookup (`park_state.get(subject)`) whose `repo` doesn't match
   this tick's own `repo_slug` is treated as absent — evicted, not
   inherited into this subject's park/attempts/ceiling decision. This is
   the retention-split counterpart to `is_approval_blocked()`'s existing
   fail-closed retention (a real gh-lookup failure for an own-repo subject
   still parks/retains, unchanged).
3. All four park-state write sites (recheck-skip, should_park, ceiling-hit,
   spawned) now tag the entry with `"repo": repo_slug`.
4. `parked_report()` filters to entries whose `repo` matches the reading
   root's own `repo_slug`, instead of returning every `parked=True` entry
   in the shared file.

Added `gates/probe_parked_report_repo_leak.py` (standalone acceptance
probe, registered in `docs/specs/enforcement-boundary.md`) and
`tests/test_spawn_on_pr_repo_scope.py`. derived: `python3 -m pytest
tests/test_spawn_on_pr_repo_scope.py --collect-only -q`:
```
6 tests collected in 0.03s
```
(test-derivation skill: decision table over entry-repo-matches-sweep-repo
× read/retention context — see the file's own docstring table). Both
drive the real entrypoints
(`spawn_on_pr.spawn_missing_for_pr`/`parked_report`) with gh/git/spawn
boundaries mocked, same idiom `gates/test_spawn_on_pr.py` already used.

Sensitivity control (issue #3081's must-not #2 — a check must not pass
vacuously on a CLI flag that doesn't exist; a probe must demonstrably
leak on unfixed code):
derived: `git worktree add --detach /tmp/otr-main-check origin/main` (main
at `ed45102b13a755bc27dc342dd471f578a8e8e083`), copied this session's
unmodified `gates/probe_parked_report_repo_leak.py` into that worktree,
ran `python3 gates/probe_parked_report_repo_leak.py` there — result:
`FAIL: parked_report(root_a) and parked_report(root_b) are identical
(['issue-3059']) -- no per-repo filter is running at all (issue #3095).`,
exit 1. Re-ran the same unchanged probe file in this branch's checkout —
result: `ok`, exit 0. Worktree removed after (`git worktree remove
/tmp/otr-main-check --force`).

## Why

Reused #3084's mechanism (tag at write, filter at read, evict a
foreign-repo prior) rather than writing a parallel implementation, per the
issue's explicit ask; canonical: `gh pr view 3084` body (cited in "What
was done" above) is this section's basis.

One deliberate divergence from #3084's exact shape, stated here per the
issue's own instruction ("if #3084's mechanism cannot be shared... say so
in the record with the reason"): drift's fix re-keys every cache entry as
`repo:number` (`_drift_cache_key`) — both the read path AND the write path
go through that compound key, so a same-numbered PR from two different
repos can never collide on write either. This fix keeps park-state entries
keyed by the bare `subject` string (unchanged from before) and adds a
`"repo"` field to the value instead of compounding it into the key.

Reason: `gates/test_spawn_on_pr.py` (pre-existing, not touched by this
change) hardcodes the bare-subject key assumption throughout — checked:
`grep -c "KEY = SUBJECT" gates/test_spawn_on_pr.py` — result: 1 (the line
`KEY = SUBJECT # issue #2628: park state is keyed by subject alone, not
"subject/role"`) — and seeds/reads fixtures as `{KEY: {...}}` with no
`repo` field at all. Re-keying to `f"{repo}:{subject}"` (matching
`_drift_cache_key`) would have required rewriting most of that file's
fixtures. checked: `python3 -m pytest gates/test_spawn_on_pr.py -q`
against this session's actual committed change — result: 27 passed
(unaffected, confirms the compatibility choice held).

Known boundary this leaves open, not covered by the issue's three
acceptance checks: because the key itself still isn't repo-scoped, a
*literal* subject-name collision (same `issue-<n>` string genuinely open
in two different swept repos, e.g. both have their own "issue-100") can
still have one repo's tick overwrite the other's on-disk entry for that
key on write (not just misread it) if both repos happen to touch that
same-named subject. checked: `python3 -m pytest
tests/test_spawn_on_pr_repo_scope.py -q` — result: 6 passed, none of which
exercises this write-collision path (the file's own tests only assert the
read-time filter and the retention/eviction split, both of which this fix
does close). This narrower write-collision edge case, which requires the
rarer same-numbered-issue coincidence PR #3084's own `_drift_cache_key`
comment also names as the collision driver, is left open. A future fix
could close it by re-keying the same way `_drift_cache_key` did, at the
cost of also updating `gates/test_spawn_on_pr.py`'s fixtures.

## What did not work

None.

## Upstream basis

gates/spawn_on_pr.py (sha: e5172b24565e990f974292614df951410d729ceb, the
branch point) — `_park_state_path`, `load_park_state`, `parked_report`,
`spawn_missing_for_pr` (this record's `code_under_review:`).

PR #3084 / issue #3081 (merged into main as commit
e5172b24565e990f974292614df951410d729ceb) — `watchdog._drift_cache_key`/
`_load_requirement_drift_cache` is the mechanism reused here. canonical:
`gh pr view 3084 --repo tokenmaxxxer/on-the-record --json title,body,files`
output and `git show e5172b24 -- watchdog.py` (full diff), both read
before designing this fix (same sources cited in "What was done" above).

## Open findings

None.

## Next steps

None — `loop_state: landed`. Acceptance, all re-run fresh this session
immediately before writing this record:

derived: `python3 -m pytest tests/test_spawn_on_pr_repo_scope.py -q`
```
......                                                                   [100%]
6 passed in 1.41s
```

derived: `python3 gates/probe_parked_report_repo_leak.py`
```
[spawn-on-pr] park=1건 waiting-for-human (승인-대기 상태 변화 없음): ['issue-3059']
ok
```
(per the sensitivity control in "What was done" above, this same
unmodified probe file `FAIL`s with exit 1 against unmodified `origin/main`.)

derived: `python3 -m pytest tests/ -q` (5 pre-existing
failures unrelated to this change, see below)
```
5 failed, 195 passed, 2 warnings in 9.31s
```
The 5 failures (`tests/test_respawn_deliverable_gate.py` x4,
`tests/test_spawn_gate_wiring.py::HooksJsonWiringIsAdditive::
test_pre_existing_post_tool_use_commands_are_all_still_present`) are
pre-existing and unrelated to this change. derived: `git stash -u &&
python3 -m pytest tests/ -q; git stash pop`, run on this same working tree
before this session's edits were staged — result:
```
5 failed, 189 passed, 2 warnings in 9.28s
```
same 5 test names failed pre-change. derived: `189 + 6 = 195` (189
pre-change passed, plus this session's `tests/test_spawn_on_pr_repo_scope.py`,
collected as 6 tests per the collect-only run in "What was done" above) —
matches the 195 passed shown in the post-change run directly above.

Not one of the three required checks; reported separately per the spawn
instruction, not attributed to this change: `python3 -m pytest test/ -q`
(singular) — derived, run this session — result:
```
15 failed, 548 passed, 3 xfailed in 32.03s
```
15 matches the count the spawn instruction attributes to issue #3091.

skill-verdict: test-derivation — applied: invoked; retroactive check on
the already-derived `tests/test_spawn_on_pr_repo_scope.py` decision table
(own-repo retention, cross-repo eviction, parked_report inclusion/
exclusion, non-identical reports) — the skill flagged one missing column
(a legacy entry with no `repo` key at all, matching #3081's own test
suite's coverage), added as `TestLegacyEntries::
test_legacy_entry_without_repo_key_excluded_from_resolvable_repo` in a
follow-up commit. derived: `git log --oneline -- tests/test_spawn_on_pr_repo_scope.py`:
```
bb0c3f6f issue-3095: add legacy-entry-without-repo-key decision-table column
ab0d81e4 issue-3095: attribute spawn-on-pr's park state to a repo
```
(second commit is the follow-up that added this case, raising the file
from 5 to 6 tests per the collect-only count above).
skill-verdict: silent-failure-audit — not-applicable: this change adds no
new error-handling path (no new try/except); it adds attribution tagging
and a read-time filter over existing, already-audited failure paths
(`is_approval_blocked`'s fail-closed gh-lookup-failure handling is
unchanged).
skill-verdict: implementation-blueprint — not-applicable: single-function-
area bugfix inside one existing module, reusing an established mechanism
from PR #3084 rather than deciding new structure; not multi-module
architecture work and no parallel fan-out.

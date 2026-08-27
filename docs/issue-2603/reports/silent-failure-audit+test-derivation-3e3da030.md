---
code_under_review:
  - lifecycle.py
  - roster.py
  - tests/test_cross_checkout_prune_liveness.py
type: fix
breaking: false
verdict: pass
loop_state: landed
issue: 2603
role: silent-failure-audit+test-derivation-3e3da030
author: silent-failure-audit+test-derivation-3e3da030
upstream:
  - path: lifecycle.py
    sha: same-commit
  - path: roster.py
    sha: same-commit
---

# issue-2603 — silent-failure-audit+test-derivation-3e3da030 record

## What was done

Made `lifecycle.py::_sibling_live_sessions()` distinguish "sibling roster
file absent" (legitimate empty state) from "sibling roster file exists but
unreadable/unparseable" (unknown), and made the unknown case read as
possibly-live rather than absent on both prune paths.

canonical: `git diff --stat -- lifecycle.py roster.py tests/test_cross_checkout_prune_liveness.py` — result: `lifecycle.py | 102 +++++++++++++++------`, `roster.py | 17 ++--`, `tests/test_cross_checkout_prune_liveness.py | 134 ++++++++++++++++++++++++++--`, `3 files changed, 215 insertions(+), 38 deletions(-)`.

`roster.py::_roster_load_checked()` (issue #2203) already drew exactly the
absent-vs-unreadable line for its own `_sp.ROSTER`, returning `(d, None)`
on success (including a legitimately-empty/absent roster) and `({}, reason)`
when the file exists but can't be read or parsed. It took no path argument.
Generalized it to `_roster_load_checked(path: Path | None = None)`, `p =
_sp.ROSTER if path is None else path`, so it can classify any roster file —
its one existing caller (`board.py`'s `roster_ps()`) is unaffected since it
already calls it with no arguments.

`_sibling_live_sessions(sibling_root)` now calls
`_sp._roster_load_checked(path=roster_path)` instead of its own inline
`json.loads`/`try`/`except (OSError, ValueError)` classifier, and its
return type changed from `dict[Path, dict]` to `tuple[dict[Path, dict], str
| None]` — `(live, None)` on success (file absent or parses to a normal
roster), `({}, load_error)` when the file exists but is unreadable/corrupt.

`_live_workspaces_union()`'s return type changed the same way, to
`tuple[dict[Path, dict], list[str]]` — the second element is a list of
`"<sibling-path>: <reason>"` strings, one per sibling whose roster could
not be read this run (normally empty). A sibling with `load_error is not
None` is skipped for the union (contributes nothing, same as before) but
its identity+reason is now recorded instead of silently discarded.

`_workspace_clean_state(w, live, unreadable=None)` gained a third,
optional parameter. If `w` isn't a recognized-live entry and `unreadable`
is non-empty, it now returns `("unknown", <detail naming the unreadable
sibling(s)>)` instead of falling through to the git-dirty check that would
otherwise conclude "safe to delete." All three prune call sites
(`roster_clean()`, `auto_sweep()`, `_prune_orphaned_sidecars()`) were
updated to unpack `live, unreadable = _sp._live_workspaces_union()`, pass
`unreadable` into `_workspace_clean_state()`, and print one line per
unreadable sibling before iterating candidates — `_prune_orphaned_sidecars()`'s
own directory-exists / roster-match short-circuits are untouched, so an
orphaned sidecar set whose paired workspace directory is already gone
keeps being pruned by age regardless of any unrelated sibling being broken.

canonical: `python3 -m pytest tests/test_cross_checkout_prune_liveness.py -v` — result: 14 passed in 0.96s.

Test file changes: updated the two existing `mock.patch.object(spawn,
"_live_workspaces_union", spawn._live_workspaces)` pre-fix-repro patches
to `lambda: (spawn._live_workspaces(), [])` (the mock target's return
shape had to follow the new tuple contract); flipped
`SiblingDiscoveryBoundaryTest`'s
`test_malformed_sibling_roster_does_not_crash_and_degrades_to_zero` (which
directly encoded this issue's defect — asserted the workspace got swept
when B's roster was corrupt) to
`test_malformed_sibling_roster_does_not_crash_and_keeps_workspace`,
asserting survival instead; added a new
`UnreadableSiblingRosterPruneTest` class with three methods covering the
three acceptance checks (workspace survives both prune paths; the same
run completes, prunes a genuinely-dead-elsewhere orphaned sidecar set, and
names the unreadable sibling in its stderr; a sibling with no roster file
at all stays fully prunable with no warning printed).
derived: `grep -c "    def test_" tests/test_cross_checkout_prune_liveness.py` — result: 14 (11 pre-existing + 3 new).

Full regression check, derived: `python3 -m pytest test/ tests/ -q` —
result: 15 failed, 318 passed. All 15 failures are in
`test_convention_equivalence.py`, `test_local_dependency_env.py`,
`test_spawn_cross_family_skill_selection.py`,
`test_spawn_artifact_skill_pairing.py`, and
`test_spawn_skill_judge_haiku_timeout_overlap.py` — none of which import
or exercise `lifecycle.py`'s prune/liveness functions or `roster.py`'s
`_roster_load_checked()`.

Pre-existing-failure check, derived: `git stash && python3 -m pytest
test/test_convention_equivalence.py test/test_local_dependency_env.py
test/test_spawn_cross_family_skill_selection.py
test/test_spawn_artifact_skill_pairing.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py -q && git stash pop`
— derived from that same command: 15 failed, 75 passed on the unmodified
pre-fix tree, and derived from comparing that run's printed `FAILED` test
IDs one-by-one against the post-fix run's `FAILED` test IDs quoted two
paragraphs above: the two lists are identical, so none of these 15
failures were introduced by this session's edits.

## Why

Root cause. canonical: `git show HEAD:lifecycle.py` (pre-fix
`_sibling_live_sessions()`, before this session's edit):

```python
    roster_path = sibling_root / "runs" / "active.json"
    try:
        roster = json.loads(roster_path.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(roster, dict):
        return {}
```

`{}` is the exact same return value whether the roster file never existed
(a checkout that never spawned — legitimately empty) or whether it exists
but is unreadable/half-written/permission-denied (unknown). `{}` means
"this sibling has no live sessions," so on the destructive prune path a
sibling that is merely broken becomes indistinguishable from a sibling
that is genuinely empty — its actually-live workspaces read as dead and
become eligible for deletion. This is a Silently-Absorbed-shaped defect in
silent-failure-audit terms: the read failure is caught and converted into
a value ("no live sessions") that is not distinguishable from a true
negative, and none of the three prune call sites carried any signal that
the sibling's answer was unknown rather than confirmed.

Design choice — reuse over re-classification. canonical:
`git show HEAD:roster.py` lines 68-70 (`_roster_load_checked()`'s own
pre-fix docstring, issue #2203):

```
    호출부(워치독, 리스 정리, `_live_workspaces()` 등, 이슈 #2492 가 같이
    건드리는 prune 경로 포함)는 지금처럼 실패를 빈 로스터로 흡수해도 되는
    자리라, 그 동작을 이 이슈에서 바꾸지 않는다 — `ps` 만 이 구분이 필요.
```

This is the primitive the issue points at: it already distinguishes
absent from unreadable for `_sp.ROSTER`, and its own docstring names the
prune path as deliberately left on absorb-as-empty for a later issue to
revisit — this issue is that revisit. Writing a second, ad hoc classifier
inside `_sibling_live_sessions()` was rejected: two functions
independently deciding what "unknown" means for the same shape of failure
(a JSON roster file that may be absent, unreadable, or malformed) is
exactly how this kind of defect reappears — one gets fixed, the other
doesn't, and nothing keeps them in sync. Generalizing
`_roster_load_checked()` to take an optional `path` (defaulting to the
existing `_sp.ROSTER` behavior) let `_sibling_live_sessions()` call the
same classifier against a sibling's roster path with no duplicated logic
and no behavior change for the one existing caller (`board.py`'s
`roster_ps()`).

Design choice — conservative-but-bounded "unknown" on the prune path, not
abort. Issue #2597's reasoning (a broken neighbour must not kill or block
this checkout's own prune) is explicitly preserved: an unreadable sibling
never raises, and every prune run still completes and still prunes
whatever is genuinely, unambiguously dead — canonical:
`python3 -m pytest tests/test_cross_checkout_prune_liveness.py::UnreadableSiblingRosterPruneTest::test_prune_completes_prunes_dead_elsewhere_and_names_unreadable_sibling -v` — result: 1 passed, confirming in the same run that a corrupt sibling both leaves the ambiguous workspace alone and still removes a genuinely-dead-elsewhere orphaned sidecar set. What changed is only the
disposition of a *candidate workspace that isn't otherwise known to be
live* while at least one sibling roster is unreadable this run — it is
now left alone (`"unknown"`) rather than falling through to the
git-dirty check that would otherwise pronounce it safe to delete. This
is deliberately not fine-grained per-workspace attribution (a corrupt
roster file carries zero recoverable information about which specific
workspace paths it referenced), so it is a blanket, conservative stance,
scoped only to workspace-directory candidates that would otherwise be
concluded dead purely from roster-based liveness. It does not touch
`_prune_orphaned_sidecars()`'s directory-exists short-circuit, so an
orphaned sidecar set whose paired directory is already gone — deadness
established independently of any roster — keeps being pruned by age in
the same run.

Rejected alternative: reconstructing which specific workspace paths an
unreadable sibling roster "would have" referenced (e.g. from stale
snapshots or naming conventions) so only that workspace is protected and
everything else keeps being judged on today's rules. Rejected because a
JSON file that fails to parse or can't be read carries no recoverable
per-entry information — there is no snapshot to fall back to and no
naming convention that ties a workspace directory to the checkout that
spawned it (workspace names are `<project>-issue-<n>-<role>`, independent
of which checkout's roster tracks them). Any such reconstruction would be
guesswork presented as certainty, which is the opposite of what "unknown
must not mean empty" asks for.

Empty-state regression preserved. canonical:
`python3 -m pytest tests/test_cross_checkout_prune_liveness.py::UnreadableSiblingRosterPruneTest::test_missing_sibling_roster_file_stays_prunable -v` — result: 1 passed; the test deletes checkout B's `runs/active.json`
entirely (rather than corrupting it) and asserts the workspace is still
swept with `removed == 1` and no "확인 불가" (cannot-determine) text in
stdout — the `FileNotFoundError` branch of `_roster_load_checked()`
returns `(., None)`, so `load_error is None` and nothing is added to
`unreadable`.

## What did not work

None — the design in the spawning brief (reuse `_roster_load_checked()`,
preserve the non-abort/non-block guarantee, keep absent distinct from
unreadable) mapped directly onto the existing code shape; no dead end or
reverted approach occurred this session.

## Skill verdicts

skill-verdict: silent-failure-audit — applied: invoked; classified the
pre-fix `_sibling_live_sessions()` as Silently Absorbed — canonical: the
`except (OSError, ValueError): return {}` / `if not isinstance(...):
return {}` pair quoted verbatim under "Why" above (`git show
HEAD:lifecycle.py`), which folds a caught read/parse failure into the
same value as a true empty result with no signal at any of the three call
sites that the answer was unknown rather than confirmed. Used that
framing to keep the fix's own new failure path (an unreadable sibling)
surfaced instead of re-absorbed — the new `unreadable` list and the
per-run printed line are exactly the "make the caught failure visible"
response the audit calls for, rather than converting the enumeration into
a second silent absorb.

skill-verdict: test-derivation — applied: invoked; routed the issue's
three acceptance checks through Given-When-Then + regression scenario
derivation: check 1 (workspace survives both prune paths) and check 2
(prune completes, prunes dead-elsewhere, names the sibling) became
`UnreadableSiblingRosterPruneTest`'s two GWT-shaped scenario methods over
the same two-checkout fixture the file already established —
derived: `python3 -m pytest tests/test_cross_checkout_prune_liveness.py::UnreadableSiblingRosterPruneTest -v` — result: 3 passed. The must-not-regress empty-state guarantee ("a sibling with no roster file
stays prunable") became its own boundary-value test
(`test_missing_sibling_roster_file_stays_prunable`, absent vs. present-
but-corrupt being the exact boundary this issue turns on); check 3
("regression case from `tests/test_cross_checkout_prune_liveness.py`")
was satisfied by re-running the file's own pre-existing 11 methods
unmodified in behavior (only two mock-patch call shapes updated to match
the new tuple return contract) plus flipping the one existing test that
had encoded this issue's defect as its expected outcome.

## Upstream basis

- `lifecycle.py`, sha: same-commit — `_sibling_live_sessions()`,
  `_live_workspaces_union()`, `_workspace_clean_state()`, and the three
  call-site wirings (`roster_clean()`, `auto_sweep()`,
  `_prune_orphaned_sidecars()`).
- `roster.py`, sha: same-commit — `_roster_load_checked()` generalized to
  take an optional `path`.
- `tests/test_cross_checkout_prune_liveness.py`, sha: same-commit — two
  mock-patch call-shape fixes, one flipped test, and the new
  `UnreadableSiblingRosterPruneTest` class.
- GitHub issue #2603, canonical: `gh issue view 2603` output run this
  session (verbatim Ask/Acceptance/Non-goals) — the three acceptance
  checks this record's tests map to.
- GitHub issue #2492/PR #2597 and issue #2203/PR #2598, canonical: the
  spawning prompt's summary of both, cross-checked against
  `docs/issue-2492/reports/silent-failure-audit+test-derivation-5e871946.md`
  and `git show HEAD:roster.py` (`_roster_load_checked()`'s own
  docstring, quoted under "Why" above) — the two prior-landed pieces this
  issue's fix reuses and does not reopen.

## Open findings

None.

## Next steps

None — loop_state: landed. Code and this record commit together; a PR
carrying both follows.

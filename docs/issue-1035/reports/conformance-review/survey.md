# Conformance-review survey for issue #1035 (decision_queue session scope)

kind: report

## Scout skip record

canonical: `gh issue view 1035`, read this session (Acceptance block,
quoted below) — scouting skipped: this is a verification task against
an already-closed issue's fixed spec (R001's 3 acceptance cases named
verbatim in the issue), no design decision is open for this review to
steer.

## Board condition

canonical: `gh issue view 1035` (`state: CLOSED`) and `gh pr view 1053
--json mergeCommit,files,body,title` (`mergeCommit.oid:
846e3a8d503d3e13c114f6632c55c6420e4f524a`), both read this session —
`issue-1035/implementation` landed via merged PR #1053, on
`origin/main`. No conformance-review record for this commit sha exists
in the repository yet (see next listing) — the board condition this
role spawns on is met.

derived: `find docs/issue-1035 -type f`, run this session:
```
docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md
docs/issue-1035/reports/implementation.md
docs/issue-1035/reports/implementation/2026-08-12-hunt-decision-queue-session-scope.md
docs/issue-1035/reports/implementation/survey.md
```
canonical: same listing, run this session — no conformance-review
subtree present under `docs/issue-1035/reports/` yet.

## What the issue requires (R001)

canonical: `gh issue view 1035`, read this session — Acceptance block:
> Cases in `tests/test_flows.py`: foreign-session aged item excluded
> under default scope; own aged item still included; global view still
> lists both.
> check: `python3 -m pytest tests/test_flows.py -k decision`

## What PR #1053 delivered

canonical: `gh pr view 1053 --json mergeCommit,files,body,title`, run
this session — merged, changed `gates/flows.py`, `spawn.py`,
`tests/test_flows.py`, `docs/specs/flows-schema.md`,
`docs/issue-1035/reports/implementation.md`,
`docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md`.

canonical: `git show 846e3a8d -- gates/flows.py spawn.py`, read this
session — `flows_payload(root, all_scope=False)` now loads the roster
via `spawn._roster_load()`, builds `roster_own_keys` from
`spawn._roster_own(roster_all, all_scope=all_scope)` (the #1013
ownership predicate), and gates each `decision_queue` append through a
local `_own_item(subject, role)`: items with no roster entry at all
stay visible (observation-loss invariant), items with a roster entry
are included only when that entry's `session_id` matches. `all_scope=True`
bypasses the filter entirely. `spawn.py`'s `flows` CLI dispatch now
forwards the pre-existing `--all` flag through as `all_scope=a.all`.

canonical: `git show 846e3a8d -- tests/test_flows.py`, read this
session — `DecisionQueueSessionScope` test class adds exactly the 3
cases the issue's Acceptance block names: foreign-session item (issue
66, `session_id: session-B`) excluded from the caller's (`session-A`)
default-scope `decision_queue`; own item (issue 70, `session_id:
session-A`) still included, and is the only entry (`len(...) == 1`);
`all_scope=True` lists both (`{66, 70}`).

## Re-run

canonical: `python3 -m pytest tests/test_flows.py -k decision -v`, run
this session:
```
tests/test_flows.py::DecisionQueueSessionScope::test_all_scope_lists_both_own_and_foreign PASSED
tests/test_flows.py::DecisionQueueSessionScope::test_foreign_session_aged_item_excluded_by_default PASSED
tests/test_flows.py::DecisionQueueSessionScope::test_own_session_aged_item_still_included_by_default PASSED
3 passed
```
canonical: same command output, run this session — all 3 named
acceptance cases reproduce green against the current working tree, not
just as claimed in `docs/issue-1035/reports/implementation.md`.

## Preliminary verdict

canonical: the "Re-run" and "What PR #1053 delivered" sections above,
this session — R001 (decision_queue session-ownership scoping):
**Present**. The merged diff implements exactly the
default-scope-excludes-foreign, own-item-still-included,
`--all`-still-lists-both shape the issue's Acceptance block specifies,
and the 3 named test cases reproduce live in this session, not merely
as narrated in the implementation record.

## What did not work

None.

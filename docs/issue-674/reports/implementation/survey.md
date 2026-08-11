# Survey — `flows --json` calling closure_sweep breaks §4's call-count contract (issue #674)

The issue body already fixes the design: keep the `hygiene.closure_sweep`
field, stop the flows path from running the sweep, report every board
subject as `not-run-in-flows` in `closure_sweep_skips`, keep
`schema_version` at 1. This survey maps the current code and doc surfaces
that design touches.

## The call site

derived: `grep -n "closure_sweep\|def flows_payload" gates/flows.py`
```
290:def flows_payload(root: Path) -> dict:
433:    import closure_sweep
434:    violations, closure_sweep_skips = closure_sweep.find_violations(
435:        root, subjects=b, issue_states=issue_state_by_n)
448:        "hygiene": {
449:            "closure_sweep": violations,
450:            "closure_sweep_skips": closure_sweep_skips,
451:            "unapproved_open_prs": unapproved_open_prs,
```

The flows_payload function in gates/flows.py builds the board dict as `b
= spawn.board(root)` near its top (line 293), then near the bottom calls
`closure_sweep.find_violations(root, subjects=b,
issue_states=issue_state_by_n)` and writes the two return values straight
into `hygiene.closure_sweep` / `hygiene.closure_sweep_skips`. `b`'s keys
are the board's subjects (`issue-<n>` strings) — `spawn.board()`
(spawn.py, function board, line 1274) only ever produces keys matching
`^issue-[0-9]+$`, filtering and warning on anything else, so no
subject-name validation is needed on the flows side when this call is
replaced.

## Why `find_violations` itself is still slow here, despite two prior
## optimizations landed against it

The find_violations function in gates/closure_sweep.py already carries
two landed perf fixes that predate this issue:

- issue #189: callers may pass a prefetched `issue_states` map, skipping
  find_violations's own `gh issue view` per subject. `flows_payload`
  already does this (`issue_states=issue_state_by_n`, itself built from
  the single repo-wide `gh issue list` call `_issue_list_all` makes).
- issue #682: find_violations now calls a `_pr_index_all` helper once
  per invocation (one `gh pr list --state all` call) instead of looping
  `spawn._pr_for_branch` + a per-branch `gh pr view` for every
  subject-role pair. The commit message for that fix
  (`7a39b01`) records 367s -> 8.9s on this repo.

Despite both fixes being live in the code, issue #674's own measurement
(148 subjects, 174 subject-role pairs, 2026-08-10) shows
find_violations still costing ~91s, attributed to 10 sampled
`_pr_for_branch` calls extrapolated to the full pair count — i.e. the
`_pr_index_all` fast path is not the one running; find_violations is
falling back to its pre-#682 per-branch path. `_pr_index_all` takes that
fallback when the single `gh pr list` call itself fails, or when its
result hits the hard-coded `_PR_INDEX_LIMIT` of 1000 rows (closure_sweep.py,
around the `_pr_index_all` function) — in either case it returns
`(None, True)` and the caller loop drops back to `spawn._pr_for_branch`
+ `_pr_view_state_body` per pair. Root-causing *why* the fallback
triggers on this repo is exactly the "make find_violations itself cheap"
work the issue text places out of scope, deferred to a future issue that
also reopens §2.5's wording. This survey does not chase that further —
the chosen design (below) removes flows_payload's call to
find_violations entirely, so the fallback trigger stops mattering to
flows regardless of its root cause.

## Other find_violations callers — unaffected, out of scope

Two other call sites exist and are explicitly out of scope per the issue
body:

- gates/closure_sweep.py's own `main` function (the standalone
  `python3 gates/closure_sweep.py [--repo] [--post]` verb) — no call-count
  contract, not on a CI timeout budget.
- spawn.py's `_board_wide_sweep` function (around line 1980, per the
  issue body; used by `roster_watchdog`, issue #464) — calls
  `find_violations(root)` with no `subjects=`/`issue_states=` prefetch,
  paying the full uncached cost on every watchdog tick. Real, named in
  the issue's own "Out of scope" section as a separate problem.

Neither caller is touched by this proposal.

## Test surfaces that assert today's pass-through behavior

Two test files currently assert that `flows_payload`'s
`hygiene.closure_sweep` / `hygiene.closure_sweep_skips` are a verbatim
pass-through of whatever `closure_sweep.find_violations` returns — that
assumption breaks under the new design (the fields become locally
computed, independent of find_violations, once flows_payload stops
calling it) and both need updating:

- test_flows.py — the FlowsStageMapping test class imports closure_sweep
  and its setUp method monkeypatches `closure_sweep.find_violations` to
  return `([], [])` by default (so the class's other tests aren't
  network-dependent). One test, named test_closure_sweep_skips_surface_in_hygiene,
  overrides that mock to return a `gh-issue-view-failed` skip record and
  asserts it appears verbatim in `payload["hygiene"]["closure_sweep_skips"]`.
  That assertion is exactly what the new design breaks by construction:
  skips will no longer come from find_violations's return value.
- test_spawn.py — the FlowsPayload test class (this file's docstring
  calls it "the existing test home" that predates the #222 split
  producing test_flows.py) carries the same setUp monkeypatch of
  closure_sweep.find_violations, plus one test, named
  test_hygiene_includes_closure_sweep_and_unapproved_prs, that patches
  find_violations to return a violation record and asserts
  `payload["hygiene"]["closure_sweep"]` equals that mocked record
  verbatim. That assertion also breaks by construction under the new
  design (closure_sweep is always `[]` from the flows path now,
  regardless of what find_violations would have returned).

Neither file's other tests reference closure_sweep and are unaffected.
test_spawn.py separately carries a ClosureSweep-focused test class
(around line 7732, issue #682's own gh-call-count regression tests) and
a `_board_wide_sweep` test group (around line 3331) — both exercise
find_violations or its spawn.py caller directly, not through
flows_payload, so neither is touched by this change.

## Doc surface — docs/specs/flows-schema.md

Three sections describe the behavior this issue changes:

- §2.5 (`hygiene`, around line 198-216): documents `closure_sweep` /
  `closure_sweep_skips` as "verbatim ... passed through unchanged" from
  find_violations's return value. That description stops being accurate
  once flows_payload no longer calls find_violations.
- §4 (GitHub API call-count contract, around line 260-277): the "up to
  `S` calls — `gh issue view`" bullet exists specifically to describe
  find_violations's (now-moot, from the flows side) fallback path, and
  the accompanying prose says the issue-state map is "reused by
  `hygiene.closure_sweep`" — both need to change once that reuse no
  longer happens because the call itself is gone from this path.
- §7 (worked example, around line 306-376): shows a populated
  `hygiene.closure_sweep` entry with one violation. Under the new design
  this field is always `[]` from the flows path, so the worked example
  needs to show a `closure_sweep_skips` entry instead.

§2.5's existing wording that "a consumer must not read an empty
`closure_sweep` together with a non-empty `closure_sweep_skips` as
clean" already covers the shape this design produces going forward —
the issue body cites this directly ("§2.5 already forbids reading an
empty closure_sweep as clean ... that distinction already exists to
carry this"), so that specific sentence needs no change, only the
surrounding description of where the two arrays' contents come from.

## `schema_version` — no bump needed

`gates/flows.py` sets `FLOWS_SCHEMA_VERSION = 1` (line 19), used
verbatim as the payload's `schema_version`. §3 of flows-schema.md ("Bump
`schema_version` only on a breaking change: a field is removed, a field
is renamed, or a field's type changes ... additive changes ... never
bump") already covers this case without new wording: both
`hygiene.closure_sweep` and `hygiene.closure_sweep_skips` keep their
existing names, and both stay arrays — only their *contents'* provenance
changes (locally computed vs. passed through from find_violations). That
is not a type change or a rename, so schema_version stays 1, matching
the issue's explicit requirement (repo-status-board's
`SUPPORTED_SCHEMA_VERSION = 1` would otherwise reject the payload
outright).

## Skip condition check (scout directive)

The spec leaves no design decision open: the issue body states the field
to keep, the exact per-subject skip shape
(`{"subject", "reason": "not-run-in-flows"}`), and the schema_version
constraint, and explicitly places the one open design question (making
find_violations itself cheap) out of scope for this issue. Scouting was
skipped on that basis — this is a pure "implement the already-decided
design" change with no product-facing or architectural choice left to
research.

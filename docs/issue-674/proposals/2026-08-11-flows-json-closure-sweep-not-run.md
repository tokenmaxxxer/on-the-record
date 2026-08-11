---
status: proposed
files:
  - gates/flows.py
  - test_flows.py
  - test_spawn.py
  - docs/specs/flows-schema.md
  - docs/issue-674/reports/implementation.md
---

## Request

`flows --json` calls `closure_sweep.find_violations()` from inside
`flows_payload`, which breaks the linear-in-subjects/flat-in-roles
call-count contract docs/specs/flows-schema.md §4 states, and has been
timing out the deployed repo-status-board (60s per-repo subprocess
budget) on every run since 2026-08-08. The issue body has already
decided the fix: keep the `hygiene.closure_sweep` field (removing it
would be a breaking §3 change forcing `schema_version: 2`, which
repo-status-board's `SUPPORTED_SCHEMA_VERSION = 1` would reject
outright), stop running the sweep inside the flows path, and report
every board subject as `not-run-in-flows` in `closure_sweep_skips`
instead. `schema_version` stays 1.

## Constraints

- `hygiene.closure_sweep` and `hygiene.closure_sweep_skips` keep their
  existing names and array types — only the values change, so
  `schema_version` must stay 1 (docs/specs/flows-schema.md §3: only a
  removed/renamed field or a type change forces a bump; this is neither).
- `flows_payload` must not call `closure_sweep.find_violations()` at
  all, directly or indirectly — this is what makes the fix independent
  of find_violations's own performance instead of contingent on
  root-causing why it currently falls back to its slow per-branch path
  on this repo (survey, "Why find_violations itself is still slow
  here").
- The other two find_violations callers (closure_sweep.py's own `main`
  standalone verb, and spawn.py's `_board_wide_sweep` used by
  `roster_watchdog`) are untouched — neither is under a call-count
  contract or a CI timeout budget, and both are explicitly out of scope
  in the issue body.
- `closure_sweep_skips` gets exactly one record per board subject
  (`{"subject": <name>, "reason": "not-run-in-flows"}`), not one per
  subject-role pair — matching the issue's acceptance wording ("one
  `{"subject", "reason": "not-run-in-flows"}` record per subject").
- A zero-subject board still emits `hygiene.closure_sweep: []` with an
  empty `closure_sweep_skips` (issue's stated empty state) — not an
  error, not a single sentinel record.

## Rationale

**Alternative considered: make `find_violations()` itself cheap** (reuse
the repo-wide PR/issue lists §4 already fetches, so the sweep keeps
running inside `flows_payload` but stops paying per-subject `gh` calls).
Rejected for this issue: the survey found two perf fixes (issue #189's
prefetched `issue_states`, issue #682's `_pr_index_all`) already landed
inside find_violations, yet the issue's own 2026-08-10 measurement still
shows ~91s, attributed to a fallback path that bypasses the #682 fast
path under conditions not yet root-caused. Chasing that fallback is
uncertain-sized investigative work the issue body explicitly places out
of scope ("§2.5 will be worded to allow it" — as future work, not this
one), and doing it here would block a fix for a live, dated outage
(repo-status-board failing since 2026-08-08) behind a perf
investigation with no fixed bound.

**Alternative considered: drop the `hygiene.closure_sweep` field
entirely** now that flows won't populate it with real data. Rejected:
removing a field is a breaking change under §3, forcing
`schema_version: 2`; repo-status-board's `SUPPORTED_SCHEMA_VERSION = 1`
would then reject the whole payload outright, turning a slow board into
a blank one — strictly worse than today's timeout for every consumer
until repo-status-board's own schema constant is separately updated (a
different repo, no coordinated deploy available from here).

**Chosen approach**: keep the field, stop populating it from
find_violations, report every subject as unchecked via
`closure_sweep_skips`. This needs no consumer-side change (verified by
acceptance item 3: `rsb --json` against all three configured repos
exits 0 with `errors: []`), stays inside `schema_version: 1`, and
removes the entire find_violations call — and therefore its performance
characteristics — from the `flows --json` path rather than depending on
them.

## What will be done

- In gates/flows.py's `flows_payload` function: delete the
  `import closure_sweep` / `closure_sweep.find_violations(...)` call and
  its two return values. Replace `hygiene.closure_sweep` with a literal
  `[]` and build `hygiene.closure_sweep_skips` as one
  `{"subject": subject, "reason": "not-run-in-flows"}` record per key of
  `b` (the `spawn.board(root)` dict already computed earlier in the
  function), sorted for deterministic output.
- test_flows.py: rewrite `test_closure_sweep_skips_surface_in_hygiene`
  (FlowsStageMapping class) as the acceptance-named red/green pair —
  patch `closure_sweep.find_violations` to raise/fail the test if
  called, write board records for a couple of subjects, and assert
  `hygiene.closure_sweep == []` and `hygiene.closure_sweep_skips`
  contains exactly one `not-run-in-flows` record per subject. Drop the
  now-unused `closure_sweep.find_violations` default-mock from setUp if
  nothing else in the file still needs it (checked at build time — the
  file's only other tests don't touch `closure_sweep`).
- test_spawn.py: update the `FlowsPayload` class's setUp (no longer
  needs to default-mock `closure_sweep.find_violations` if nothing calls
  it) and rewrite `test_hygiene_includes_closure_sweep_and_unapproved_prs`
  to assert the new not-run-in-flows shape instead of a find_violations
  pass-through, so this file's copy of the same coverage stays accurate
  rather than silently asserting a passthrough that no longer happens.
- docs/specs/flows-schema.md: update §2.5's `closure_sweep` /
  `closure_sweep_skips` field notes to describe the new source (locally
  computed in flows_payload, not find_violations's return value) and the
  new skip reason; update §4 to drop the "up to `S` calls — `gh issue
  view`" bullet describing find_violations's now-removed reuse of the
  prefetched issue-state map, and note that `hygiene.closure_sweep` is
  no longer sourced from a `gh`-hitting call at all; update §7's worked
  example to show `closure_sweep: []` with a `closure_sweep_skips` entry
  in place of the current violation example.
- Record the work in docs/issue-674/reports/implementation.md per
  contract v3 s19/s20, including the acceptance evidence (timed live
  run, unit test output, `rsb --json` run) named below.

## Accumulation

This change removes one call site (`closure_sweep.find_violations()`)
from gates/flows.py's `flows_payload` function; it does not add a new
inline `subprocess`/`gh` call there or anywhere else — the replacement
is a local loop over the already-in-memory `b` dict, no network call.
gates/flows.py already contains several other inline `gh`-hitting
helpers (`_pr_list_all`, `_issue_list_all`, `spawn._issue_comments` via
`comments_for`) that this change does not touch and does not add to; the
shape-1 inline-subprocess-call count this repo's accumulation gate
tracks (gates/closure_sweep.py's own `_current_accumulation_counts`
function) goes down by one call site, not up. No new roles/*.json-style
repeated file is introduced either, so no shape-5 change. There is
nothing here for a future N-more-times question to answer.

## Out of scope

- Making `find_violations()` itself cheap, or root-causing why its
  `_pr_index_all` fast path is not the one running on this repo today —
  named explicitly out of scope in the issue body, deferred to a future
  issue that also reopens §2.5's wording to allow the sweep back into
  the payload.
- `_board_wide_sweep()` (spawn.py, `roster_watchdog`, issue #464) and
  closure_sweep.py's own standalone `--post` verb — neither is under a
  call-count contract, both out of scope per the issue body.
- repo-status-board's unset `RSB_ALERT_WEBHOOK` secret and its swallowed
  stderr on failure — a different repo, out of scope per the issue body.
- Any change to `schema_version` or to repo-status-board's
  `SUPPORTED_SCHEMA_VERSION` constant.

## How you'll know it worked

- `spawn.py flows --json -C .` on this repo completes well inside
  repo-status-board's 60s per-repo timeout and exits 0 — verified with a
  timed live run; a zero-subject board still emits
  `hygiene.closure_sweep: []` with an empty `closure_sweep_skips`.
- `flows_payload()` never calls `closure_sweep.find_violations()` — a
  red/green unit pair patches `find_violations` to fail the test if
  called, then asserts `hygiene.closure_sweep == []` and one
  `{"subject", "reason": "not-run-in-flows"}` record per subject in
  `closure_sweep_skips`.
- `schema_version` stays 1 and repo-status-board consumes the payload
  unchanged — verified by running `rsb --json` against all three
  configured repos and asserting exit 0 with `errors: []`.

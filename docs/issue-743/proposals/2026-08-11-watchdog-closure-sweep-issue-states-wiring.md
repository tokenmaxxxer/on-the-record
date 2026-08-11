---
status: proposed
files:
  - gates/closure_sweep.py
  - spawn.py
  - gates/test_closure_sweep.py
  - tests/test_spawn.py
  - docs/issue-743/reports/implementation.md
---

## Request

`closure_sweep.find_violations()` already accepts an `issue_states`
map and already skips its own per-subject `gh issue view` call when a
subject's issue is present in that map (issue #189), but none of the
three deployed callers (`spawn.py`'s watchdog-tick
`_board_wide_sweep()`, `spawn.py`'s own `closure-sweep` CLI subcommand,
and `gates/closure_sweep.py`'s standalone `main()`) builds that map and
passes it in — each pays a full per-subject `gh issue view` cost on
every run. On this repo that measures ~101s/tick for the watchdog path
(166 subjects × ~0.61s/issue-view). #674 explicitly named this same gap
in `_board_wide_sweep` as a separate, deferred problem when it removed
`gates/flows.py`'s unrelated call into `find_violations`. This issue
fixes the caller side only, mirroring the bulk-fetch pattern
`find_violations` already uses for PR lookups (`_pr_index_all`).

## Constraints

- `find_violations()`'s own algorithm is untouched — issue body's "범위
  밖" explicitly excludes changing it; this issue only fills an
  already-existing parameter at call sites.
- The `gates/flows.py` path stays untouched — #674 already fixed it by
  removing the call entirely; out of scope here per the issue body.
- The new bulk-fetch helper must follow `_pr_index_all`'s established
  `(index, ok)` / truncation-safe shape (survey, "The prefetch shape
  already established"): `ok=False` means the `gh` call itself failed
  (never read as "no issues"); hitting the row-count limit returns
  `(None, True)` so callers fall back to `find_violations`'s existing
  per-subject path rather than silently truncating (issue #224's
  lesson).
- A zero-subject board must still produce an empty result with no error
  (issue's stated empty state for Acceptance item 1) — the bulk-fetch
  helper returning an empty dict, or `find_violations` receiving no
  subjects at all, must not raise.
- Existing tests asserting `find_violations`'s own `issue_states`
  handling (`tests/test_gates.py`'s
  `t_find_violations_uses_prefetched_issue_state_skips_issue_view` /
  `t_find_violations_without_issue_states_still_calls_issue_view`) are
  not touched — they test the callee, which this issue does not change.

## Rationale

**Alternative considered: have `find_violations()` build its own bulk
prefetch internally when `issue_states` is not supplied**, instead of
requiring callers to build and pass it. Rejected: the issue body is
explicit that "고칠 것은 호출부다" (the fix belongs at the call sites) —
`find_violations` already has an injectable-parameter design specifically
so callers can supply a repo-wide prefetch they may already be
computing for other reasons (`gates/flows.py`'s caller, before #674
removed it, reused its own `_issue_list_all()` this way). Moving the
fetch inside `find_violations` would silently reintroduce a `gh` call
inside the "범위 밖" algorithm the issue explicitly protects, and would
make every caller pay for a fresh bulk fetch even when the caller has
no better source, instead of leaving that choice at the call site.

**Alternative considered: reuse `gates/flows.py`'s `_issue_list_all()`
by importing it from `closure_sweep.py`.** Rejected (survey, "Why not
just import `gates/flows.py`'s helper"): it fetches a `body` field
`closure_sweep` never uses, and it would create a new
`closure_sweep.py` → `flows.py` import that doesn't exist today, crossing
the exact independence boundary #674 established between the two paths
(so a change to one can't accidentally couple to the other's
performance or availability). A small sibling helper next to the
already-proven `_pr_index_all`, with the same shape, keeps the module
self-contained and consistent with its own existing pattern.

**Alternative considered: merge the new bulk-issue-fetch with
`spawn_coverage._list_open_issues()`'s existing `gh issue list` call**
inside `_board_wide_sweep` (both run back-to-back in that function).
Rejected: `_list_open_issues` fetches `--state open` only and
`number,createdAt`; `find_violations` needs closed issues too (to
classify `OPEN_PR_ON_CLOSED_ISSUE`) and needs `state`, not `createdAt`.
Merging would mean changing a second, independently-tested module
(`gates/spawn_coverage.py`) and its own test suite for a marginal extra
`gh`-call saving beyond what this issue's acceptance criteria ask for —
a plausible future optimization, not this one.

**Chosen approach**: add one small bulk-fetch helper,
`issue_state_index_all(root)`, to `gates/closure_sweep.py` — one `gh
issue list --state all --json number,state --limit 1000` call, `(dict[int,
str] | None, bool)` return shape mirroring `_pr_index_all`. Each of the
three callers calls it once and passes the result as `find_violations`'s
existing `issue_states=` argument.

## What will be done

- `gates/closure_sweep.py`: add `issue_state_index_all(root) -> tuple[dict[int, str] | None, bool]`
  next to `_pr_index_all`, using the same `_PR_INDEX_LIMIT`-style
  truncation guard (a new `_ISSUE_INDEX_LIMIT = 1000` constant). Update
  `main()` to call it once and pass `issue_states=` into
  `find_violations(root, issue_states=issue_states)`.
- `spawn.py`: in `_board_wide_sweep()` (watchdog-tick path, around line
  1946), call `closure_sweep.issue_state_index_all(root)` once and pass
  the result into `closure_sweep.find_violations(root,
  issue_states=issue_states)`. In the `closure-sweep` CLI subcommand
  (around line 3719), the same wiring.
- `gates/test_closure_sweep.py`: update `MainExitCode`'s
  `test_exit_code_is_2_and_prints_could_not_check` to stub
  `closure_sweep.issue_state_index_all` alongside the existing
  `find_violations` stub, so `main()` stays network-independent.
- `tests/test_spawn.py`: update the four existing `Watchdog`-class
  `_board_wide_sweep` tests to configure
  `fake_cs.issue_state_index_all.return_value` on their `MagicMock`
  stand-in for `closure_sweep` (survey: unpacking an unconfigured
  `MagicMock()` return value raises `ValueError`). Add:
  - a call-count test driving the real `gates/closure_sweep` module
    through the real `spawn._board_wide_sweep()` at two different
    subject counts, with `_issue_view` stubbed to record calls and
    `issue_state_index_all`'s underlying `gh` call stubbed to return
    full coverage — asserting the `_issue_view` call count is identical
    (not scaling) across subject counts (Acceptance item 1).
  - a before/after comparison test calling `closure_sweep.find_violations`
    once without `issue_states` (per-subject `_issue_view` stubbed) and
    once with a prebuilt `issue_states` matching those same stubbed
    values, against one fixture PR index, asserting identical
    `violations`/`skips` (Acceptance item 2).
  - a light test for the CLI `closure-sweep` subcommand wiring (spawn.py
    line 3719), since no existing test covers that path at all (survey).
- Record the work in `docs/issue-743/reports/implementation.md` per
  contract v3 s19/s20, including the acceptance evidence named below.

## Accumulation

This change adds one new function (`issue_state_index_all`) to
`gates/closure_sweep.py` and three call sites that invoke it — it does
not add a new *inline* `subprocess`/`gh` call pattern beyond what
`_pr_index_all` already established in the same file; it is a sibling of
an existing shape, not a new one. It replaces N per-subject `gh issue
view` calls (the shape this issue is fixing) with 1 bulk call per
`find_violations` invocation across all three callers — the accumulation
direction is a reduction in per-tick/per-run `gh` call count, not an
addition. No new `roles/*.json`-style repeated file is introduced. If
this pattern (a bulk-fetch-and-pass-down-to-an-injectable-parameter)
comes up again for a different `gh` query, the existing
`_pr_index_all`/`issue_state_index_all` pair in `gates/closure_sweep.py`
is the model to follow — no new module or abstraction is being proposed
here.

## Out of scope

- Changing `find_violations()`'s internal algorithm — explicitly out of
  scope per the issue body.
- The `gates/flows.py` path — already fixed by #674, untouched here.
- Merging the new bulk-issue fetch with
  `spawn_coverage._list_open_issues()`'s call inside
  `_board_wide_sweep` (Rationale, alternative rejected).
- Any change to `docs/specs/flows-schema.md` — this issue does not touch
  the `flows --json` payload contract.

## How you'll know it worked

- Acceptance item 1: a unit test stubs the `gh`-hitting calls inside
  `spawn._board_wide_sweep()`'s real call into `gates/closure_sweep`,
  counts `_issue_view` invocations at two different subject counts, and
  asserts the count is constant (not proportional to subject count); a
  zero-subject board produces an empty result with no error.
- Acceptance item 2: a unit test compares `find_violations()`'s return
  value (`violations`, `skips`) on the same fixture board and PR index,
  called once the old way (no `issue_states`) and once the new way
  (prebuilt `issue_states` matching the same underlying issue states),
  asserting they are identical; a zero-violation board yields empty
  lists both ways.
- The full test suite (`python3 -m pytest`) run at phase-2 completion
  shows no new failures beyond the three already-red tests on `main`
  (`gates/test_boundary.py::t_all_gates_modules_recorded`,
  `gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint`,
  `tests/test_gates.py::t_find_violations_uses_record_evidence_for_keywordless_merge`)
  — pasted output recorded in `docs/issue-743/reports/implementation.md`.

---
code_under_review:
  - gates/closure_sweep.py
  - gates/test_closure_sweep.py
type: bugfix
breaking: false
verdict: pass
loop_state: landed
---

## What was done

`find_violations()` in `gates/closure_sweep.py` previously `continue`d
silently past any subject whose issue number was absent from a
successfully-fetched issue-state index (e.g. cross-repo subjects) —
pinned by `OutOfIndexSubjectIsNotAGhFailureSkip` from PR #1641. Per
issue #1643, such a subject is now classified ONCE as out-of-scope with
a distinct reason (`closure_sweep.OUT_OF_INDEX_SUBJECT =
"out-of-index-subject"`), added to `violations` (not `skips` — it is
not a `gh` failure). A local, uncommitted state file
(`runs/closure_sweep_out_of_index_seen.json`, gitignored, same pattern
as the existing `BACKOFF_STATE_REL`/`board_sweep_queue.json` state
files) tracks which subjects already received the one-time
classification, so a subsequent tick does not repeat it.
`format_report()` and `_violations_digest()` were updated to handle
violation entries that carry no `pr`/`role` key (out-of-scope entries
report only `issue`/`subject`).

`gates/test_closure_sweep.py`'s `OutOfIndexSubjectIsNotAGhFailureSkip`
class was updated: its two existing tests (previously asserting total
silence) now assert the one-time out-of-scope classification and empty
`skips`; two new tests pin "second tick does not repeat" and the
empty-state acceptance ("boards with all subjects in-index keep today's
behavior byte-identical" — no violation, no state file written). Each
test now uses its own `tempfile.TemporaryDirectory()` as `root` since
the classification is tracked in local state under `root/runs/`.

## Why

Watch-coverage principle (issue #1613 residual, referenced in #1643):
silently skipping out-of-index subjects forever leaves them permanently
unobserved. A one-time, distinctly-reasoned classification surfaces
them without re-noising every tick.

## Upstream

Based on: gates/closure_sweep.py at HEAD (commit 48856ea6), and
`OutOfIndexSubjectIsNotAGhFailureSkip` as landed by PR #1641
(issue-1613/implementation).

## Acceptance verification

checked: `find_violations()` on a fresh out-of-index subject — result:
one `OUT_OF_INDEX_SUBJECT` violation, `skips == []`.
canonical: gates/test_closure_sweep.py::OutOfIndexSubjectIsNotAGhFailureSkip::test_subject_missing_from_successful_index_is_not_a_gh_failure_skip

checked: a second `find_violations()` tick on the same subject/root —
result: no repeat classification (`second == []`).
canonical: gates/test_closure_sweep.py::OutOfIndexSubjectIsNotAGhFailureSkip::test_subsequent_tick_does_not_repeat_the_classification

checked: board with all subjects in-index — result: no out-of-scope
entries, no state file written (empty-state acceptance).
canonical: gates/test_closure_sweep.py::OutOfIndexSubjectIsNotAGhFailureSkip::test_all_in_index_board_is_byte_identical_to_no_out_of_scope_entries

derived:
```
$ python3 -m pytest gates/test_closure_sweep.py -q
21 passed in 1.29s
```

## What did not work

None.

## Open findings

None.

## Doc placement

No env var, config key, new dependency, migration, or public
signature/wire-format change — no handbook or decision-record entry
required.

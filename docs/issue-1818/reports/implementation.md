---
code_under_review:
  - gates/ci.py
  - spawn.py
  - test/test_convention_equivalence.py
  - test/test_approval_role_field.py
  - conftest.py
loop_state: landed
type: feature
breaking: false
verdict: pass
---

## What was done

Delivered the approved proposal (docs/issue-1818/proposals/approval-record-carrier.md):
`gates/ci.py:189` `_approved_roles_on_issue` now reads a workspace-local
structured approval record (`.git/gh-read-cache/issue-<n>-approvals.json`,
sibling to the existing `spawn._etag_cache_path` comments-cache
convention) before its comment scan (canonical: gates/ci.py:189-224,
this branch), unions any roles it holds into the result, then — after
the always-run, unmodified comment scan — writes back any newly-scanned
`{role: {actor, timestamp}}` entry not already covered by the record
(write-through cache). `spawn.py` gained the one new helper
`_approval_record_path` (`spawn.py:1334`, next to `_etag_cache_path`)
for the record file path; no read-path signature changed. New
`test/test_approval_role_field.py` covers dual-write shape,
field-read-preferred, fallback for a role the record does not yet
cover, the legacy token-only case, `_ok=False` fail-closed, and a
corrupt record file falling back to the scan. `test/test_convention_equivalence.py`
gained two additions-only cases under `ApproveGrammarEquivalenceTest`
proving the record-present and record-absent paths produce identical
role output.

## Why

Requirements engineering + risk consults on this issue (frozen migration
order entry 4, docs/issue-1792/reports/implementation.md §Migration
order) require: dual-write a structured approval record alongside the
unchanged APPROVE-token comment, with the python needle consumer
(`_approved_roles_on_issue`) reading the record when present and
falling back to the exact-needle scan otherwise, identical outcomes on
both paths, harness green with additions only.

## Upstream / basis

- docs/issue-1818/proposals/approval-record-carrier.md (approved via
  issue comment `APPROVE issue-1818/implementation`)
- docs/issue-1818/reports/implementation/survey.md
- 2b3cccd5 (phase-1 commit, this branch)

## Acceptance evidence

### `python3 -m pytest test/test_convention_equivalence.py -q` (executed live)

```
bringing up nodes...
bringing up nodes...

...............................                                          [100%]
31 passed in 0.85s
```

`git diff HEAD~1 -- test/test_convention_equivalence.py` — additions only
(0 removed/altered lines against the phase-1 baseline commit; `+39` new
lines, no existing golden-case line touched):

```
 test/test_convention_equivalence.py | 39 +++++++++++++++++++++++++++++++++++++
 1 file changed, 39 insertions(+)
```

### `python3 -m pytest test/test_approval_role_field.py -q` (executed live)

```
bringing up nodes...
bringing up nodes...

......                                                                   [100%]
6 passed in 0.81s
```

Covers dual-write shape, field-read, fallback (record-absent role),
and the legacy token-only case (`test_legacy_token_only_issue_resolves_identically_to_today`),
plus `_ok=False` fail-closed and corrupt-record fallback.

### `python3 -m pytest gates/test_closes_gate_ci.py -q` (executed live, PR #1820 orchestrator-blocker fix)

Re-run three times in a row to rule out xdist-order flakiness:

```
bringing up nodes...
bringing up nodes...

......................................................                   [100%]
54 passed in 1.29s
```
```
bringing up nodes...
bringing up nodes...

......................................................                   [100%]
54 passed in 1.33s
```
```
bringing up nodes...
bringing up nodes...

......................................................                   [100%]
54 passed in 1.41s
```

## What did not work

A snapshot/delete/restore fixture design for isolating
`.git/gh-read-cache/*-approvals.json` across test workers — see
`## Rationale for deviations` for why it was rejected in favor of the
per-test `tmp_path` monkeypatch that shipped instead.

## Rationale for deviations

The approved proposal's build-steps section did not anticipate that
delivering the write-through cache would break other, pre-existing
tests outside this issue's original frozen write set. Once the cache
landed, `gates/test_closes_gate_ci.py` (not in the original `files:`)
started failing, first reported as a filed deviation with a resolution
path (docs/issue-1818/reports/implementation/deviation-log.md). The
PR #1820 orchestrator then amended the issue scope to include
`gates/test_closes_gate_ci.py` and `conftest.py` (canonical: PR #1820
orchestrator comment — "The issue scope has been amended to include
gates/test_closes_gate_ci.py and conftest.py: add the cache-isolation
fix ... re-run the full gates/test_closes_gate_ci.py suite live (must
be green), and update the record"), so this revision delivers that fix
inside the now-widened scope: `conftest.py` gained an autouse
`_isolated_gh_read_cache_approvals` fixture that monkeypatches
`spawn._approval_record_path` to a per-test `tmp_path`, so no test —
under any pytest-xdist worker — ever reads or writes the real repo's
`.git/gh-read-cache/*-approvals.json`.

A snapshot/delete/restore approach was tried first and rejected:
sibling xdist worker processes share this same working tree and raced
on the same real cache files. That race actually deleted this repo's
pre-existing `issue-245-approvals.json` and `issue-304-approvals.json`
cache files (canonical: `ls .git/gh-read-cache/` immediately after
running `gates/test_closes_gate_ci.py` with the snapshot/delete/restore
fixture, this session — the two files were present beforehand per an
earlier `md5sum` check in this same session and absent afterward).
Losing them is not data loss in the durable sense: the cache is
documented best-effort (canonical: gates/ci.py:204-209
`_write_approval_record`, inline comment "write-through cache is
best-effort; the comment scan stays authoritative") and self-heals from
the next real comment scan. It does confirm per-test tmp-path
isolation, not real-file snapshotting, is the correct fix shape, which
is what this revision ships.

## Open findings

canonical: `python3 -m pytest gates/test_closes_gate_ci.py -q` executed
live on this branch's working tree after the `conftest.py` isolation
fix, three consecutive times (pasted above under `## Acceptance
evidence`) — 54 passed on each of the three runs, no flakiness across
xdist worker orderings. The prior finding (write-through cache leaking
real `.git/gh-read-cache` approval state into tests that assumed
`_approved_roles_on_issue` was memoryless when called with the real
repo checkout `Path(".")`) is resolved by scoping the cache path to a
per-test `tmp_path`, not by disabling or weakening any assertion in
`gates/test_closes_gate_ci.py` itself.

canonical: `python3 -m pytest tests/test_gh_quota_guard.py::test_sweep_call_budget
tests/test_spawn.py -k test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts -q`
executed live on this branch, then repeated after `git stash` (pre-issue-1818
main state) with the same result — both failures reproduce identically
without this issue's changes, so they are pre-existing and unrelated to
this delivery. Not in this issue's (amended) scope.

resolution path: none outstanding for the amended scope — the
cache-isolation fix is delivered and its target suite is green per the
canonical citation above. The two pre-existing, unrelated
`tests/test_gh_quota_guard.py`/`tests/test_spawn.py` failures remain
open on `main` independent of this issue; no action taken on them here
as they are out of scope.

## Next steps

None — `loop_state: landed`, delivered scope (including the
PR #1820-amended `gates/test_closes_gate_ci.py`/`conftest.py`
cache-isolation fix) is green per the canonical evidence above.

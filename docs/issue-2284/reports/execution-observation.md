---
issue: 2284
role: execution-observation
author: execution-observation
kind: execution-observation
loop_state: handed-off
upstream:
  - path: docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md
    sha: ccee895997e7629495aee4ff7c0588e3082c75bc
  - path: 3808d7fbcca4066b461231b51ba37e7fbf4ececa:docs/issue-2284/reports/implementation.md
    sha: 3808d7fbcca4066b461231b51ba37e7fbf4ececa
subject: PR #2317 (issue-2284/implementation @ 3808d7fbcca4066b461231b51ba37e7fbf4ececa)
test: independent re-execution of lease_key byte-identity, author: append-only stamping, record-kind advisory-only wiring
result: passed
assertedBy: execution-observation
---

# issue-2284 — execution-observation record

## What was done

Independently re-executed PR #2317's three stage-1 claims against a
detached `git worktree add --detach` checkout of its head commit
(`3808d7fbcca4066b461231b51ba37e7fbf4ececa`, at `/tmp/pr2317-worktree`,
outside this session's own `issue-2284/execution-observation` branch),
using hand-written probes distinct from the PR's own test files. All
three hold.

**1. `lease_key` byte-identity for existing role callers.**
canonical: `3808d7fbcca4066b461231b51ba37e7fbf4ececa:roster.py:131-141`
(`def lease_key(issue: int, disambiguator: str) -> str: return
f"issue-{issue}/{disambiguator}"`) and
`3808d7fbcca4066b461231b51ba37e7fbf4ececa:spawn.py:2887` (`roster_key =
lease_key(issue, role) if issue is not None else ...`).
derived: a standalone probe run in the worktree comparing
`roster.lease_key(issue, role)` against the pre-stage inline shape
`f"issue-{issue}/{role}"` for three `(issue, role)` pairs (`(2284,
"implementation")`, `(1, "x")`, `(99999, "execution-observation")`) —
```
CLAIM1 lease_key byte-identical for role callers: OK
CLAIM1b spawn.py's one construction site delegates to roster.lease_key: OK
```
Also grepped for other inline `f"issue-{issue}/{role}"` producers beyond
the two the PR's own record names
(`3808d7fbcca4066b461231b51ba37e7fbf4ececa:board.py:1084`,
`3808d7fbcca4066b461231b51ba37e7fbf4ececa:spawn.py:978`, both
`key.split("/", 1)[1]` — unaffected, they only need the opaque second
half) and found one more: derived: `grep -n
'f"issue-{issue}/{role}"' pipeline.py` in the worktree →
`3808d7fbcca4066b461231b51ba37e7fbf4ececa:pipeline.py:917`, inside
`checkout_issue_branch()` — a git branch-name string
(`issue-<n>/<role>`, board-gate's write-branch convention per that
function's own docstring), never passed to
`roster_register`/`lease_renew`/`lease_key`. Same string shape,
unrelated domain — not a gap in the byte-identity claim, noted only so
a future stage doesn't mistake it for an unconverted lease call site.

**2. `author:` stamping is append-only.**
canonical: `3808d7fbcca4066b461231b51ba37e7fbf4ececa:spawn.py:2135-2150`
(`_stamp_additive_record_fields`) and
`3808d7fbcca4066b461231b51ba37e7fbf4ececa:spawn.py:533-2192`
(`write_record_skeleton` refuses to touch an existing record file).
derived: a standalone probe in the worktree calling
`spawn.write_record_skeleton()` twice against the same fresh temp
workspace and a synthetic `(issue=424242, role="execution-observation")`
pair, mutating the file between calls to simulate a session filling it
in —
```
CLAIM2a author: stamped on first skeleton write: OK
CLAIM2b respawn into same workspace does not touch existing record (append-only by construction): OK
```
the second call left the mutated file byte-identical to what the probe
wrote before calling it again — the guard is the pre-existing
"never overwrite an existing record" behavior, not new enforcement code.

**3. record-kind check is advisory-only, never in blocking aggregation.**
canonical: `3808d7fbcca4066b461231b51ba37e7fbf4ececa:gates/record_lint.py:435-459`
(`record_kind_vocabulary_check`, whose own docstring states it is
"deliberately not called from `lint_record()`'s aggregation").
derived: `inspect.getsource(record_lint.lint_record)` in the worktree
contains no reference to `record_kind_vocabulary_check` (source
inspection, not a grep on the PR's test file).
derived: end-to-end check — wrote a record file with
`kind: totally-bogus-kind-xyz` under a synthetic temp
`<tmpdir>/docs/issue-424242/reports/` tree (not a repo path — a
throwaway probe fixture) and called `record_lint.lint_record()` on it
directly:
```
lint_record() violations on bad-kind record: ['레코드 경로 형태가 아니다: tmpz2kmf97g/docs/issue-424242/reports/execution-observation.md — docs/issue-<n>/reports/<role>.md 형태여야 한다.']
CLAIM3b end-to-end: lint_record() surfaces no kind-vocabulary violation for an out-of-vocabulary kind: OK
```
the only violation returned was an unrelated path-shape complaint (from
the temp dir's non-canonical path prefix, not from the `kind:` value);
no kind-vocabulary violation appeared. Confirmed
`record_kind_vocabulary_check()` does fire in isolation against the
same text (`direct advisory check result: [...'totally-bogus-kind-xyz'...]`
— one advisory line), so the absence inside `lint_record()` is because
the check is wired out, not because it's a no-op.

Also re-ran the PR's own pasted acceptance commands against the same
worktree checkout rather than trusting the pasted numbers:
acceptance: `python3 -m pytest 3808d7fbcca4066b461231b51ba37e7fbf4ececa:test/test_issue_scoped_lease.py 3808d7fbcca4066b461231b51ba37e7fbf4ececa:test/test_record_kind_field.py -v` — result:
```
10 passed in 9.07s
```
acceptance: `python3 gates/spec_index.py .` — result:
```
통과: 모든 spec 문서가 기록된 해시와 일치한다
```
acceptance: `python3 -m pytest test/ gates/ -q` (full regression,
backgrounded — 7m46s) — result:
```
1200 passed, 8 xfailed in 466.00s (0:07:46)
```
All three reproduce the counts PR #2317's own record claims
(`3808d7fbcca4066b461231b51ba37e7fbf4ececa:docs/issue-2284/reports/implementation.md:222-232`).

## Why

canonical: the three re-execution results in "What was done" above
(`CLAIM1`/`CLAIM1b`, `CLAIM2a`/`CLAIM2b`, `CLAIM3a`/`CLAIM3b`, and the
three reproduced acceptance commands).
Chose to re-execute against a `git worktree --detach` checkout of the
PR's actual head commit, with hand-written probes distinct from the
PR's own test files
(`3808d7fbcca4066b461231b51ba37e7fbf4ececa:test/test_issue_scoped_lease.py`,
`3808d7fbcca4066b461231b51ba37e7fbf4ececa:test/test_record_kind_field.py`),
rather than reasoning from the diff alone or only re-running those two
files in place. This role's job is independent verification via probes
distinct from the artifact under review, not re-invocation of the PR
author's own test files — a test suite authored by the same session
that wrote the implementation can share a blind spot (testing the
shape it built rather than the shape the proposal required). Writing
separate probes for the three specific behaviors this issue's task
named (byte-identity, append-only, advisory-only) closes that gap;
rejected relying solely on the PR's pasted evidence as the alternative,
since re-execution rather than claim-reading is this record kind's
whole purpose.

## Upstream basis

- `docs/issue-2241/proposals/2026-08-25-stage-1-lease-identity-record-kind.md`
  (sha `ccee895997e7629495aee4ff7c0588e3082c75bc` on `main`).
  derived: `git log -1 --format=%H origin/main -- <path>` — result:
  `ccee895997e7629495aee4ff7c0588e3082c75bc` — the authoritative
  stage-1 spec PR #2317 claims to implement verbatim.
  derived: `gh pr view 2317 --json files` file list contains no
  `board-gate.sh` or `merge_gate.py` entry, matching the proposal's
  Constraints (no touch to those two files).
- `3808d7fbcca4066b461231b51ba37e7fbf4ececa:docs/issue-2284/reports/implementation.md`
  — PR #2317's own delivery record (commit-pinned; this file does not
  exist on this session's own branch, only on `issue-2284/implementation`
  at that sha) — read for its claims, then independently re-derived
  above rather than trusted.
- `gh pr diff 2317` — the full 8-file changeset, each commit-pinned to
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa` since none exist on this
  session's own branch:
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:docs/handbooks/record-contract.md`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:docs/issue-2284/reports/implementation.md`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:docs/specs/record-kind-vocabulary.md`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:gates/record_lint.py`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:roster.py`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:spawn.py`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:test/test_issue_scoped_lease.py`,
  `3808d7fbcca4066b461231b51ba37e7fbf4ececa:test/test_record_kind_field.py`.

## Open findings

None. All three re-executed claims hold (see canonical/derived
citations under "What was done"); the one extra inline
`f"issue-{issue}/{role}"` site found
(`3808d7fbcca4066b461231b51ba37e7fbf4ececa:pipeline.py:917`) is a git
branch name, not a lease-key consumer, so it is a note rather than an
open finding — no resolution path needed.

## Next steps

None — `loop_state: handed-off` is execution-observation's terminal
state (`roles/specs/execution-observation.spec.json`'s
`loop_state.terminal`). derived: the acceptance runs pasted under
"What was done" (`10 passed in 9.07s`; `spec_index.py` clean; `1200
passed, 8 xfailed in 466.00s`) are this record's own terminal evidence
— no further action items remain for this record.

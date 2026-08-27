---
status: proposed
files:
  - docs/issue-2574/reports/conformance-review.md
---

Scout-skip condition: no design decision. This is a verification/audit
task against a fixed record skeleton already provided
(`docs/issue-2574/reports/conformance-review.md`) and a fixed
five-verdict finding shape mandated by this repository's mounted
conformance-review skills — there is no build alternative to weigh, so
no separate survey document is warranted.

## Request

Independently re-verify PR #2578 (issue-2574/implementation, already
merged to `main`) against issue #2574's four acceptance checks and its
empty-state clause, and record the verdicts.

## Constraints

- Write only `docs/issue-2574/reports/conformance-review.md` (this
  role's own record). Do not touch the implementation record or any
  code under review.
- Every verdict needs a commit-pinned, re-runnable citation (traceability
  skill), not a paraphrase of what the implementation record already
  claims.
- The record-shape and finding-record skills govern the write's
  internal shape once phase 2 opens; this proposal only reserves the
  write set.

## Rationale

The analysis itself is already complete (this session independently
traced the `CORE_BUILD_NOW` propagation chain from all four call sites
through `spawn.py` into `on-the-record/hooks/approval-gate.sh`, and
re-ran the check-4 grep twice against both the pre-merge and merged
commit). What is gated is only the mechanical write of the record file
— `docs/issue-2574/reports/conformance-review.md` sits on this role's
own phase-2 execution surface per `approval-gate.sh`, and this session's
environment carries `CLAUDE_ROLE=conformance-review` /
`TOKENMAXXXER_SPAWNED=1` with no `CORE_BUILD_NOW=1`.

Rejected alternative: writing the finished findings directly since the
work is "just documentation, not code." Rejected because
`approval-gate.sh` treats `reports/<role>.md` as execution output
exactly like code (by explicit design, per that file's own header
comment), and this session observed that treatment firsthand — a Write
to the record file was refused by the live hook mid-session. Routing
around that refusal (e.g. by editing outside the declared write set, or
by asking the session's own tools to set `CORE_BUILD_NOW`) is exactly
what issue #2574 itself names as out of scope ("do not fix this by
having sessions set `CORE_BUILD_NOW` themselves") and what the warrant
protocol forbids (no execution-surface write before an Approve). This
session's own gate refusal is, incidentally, live corroborating
evidence that issue #2574's underlying symptom is real and still
reproducible under the currently-installed plugin build — noted for
the record, not routed around.

## What will be done

On Approve: write the finished conformance-review record — four
requirement blocks (checks 1-4, each Present with commit-pinned
evidence) plus one additional finding (the implementation record's own
check-4 `derived:` grep transcript does not reproduce against the
shipped commit: wrong line numbers for two `lifecycle.py` hits, and a
third `lifecycle.py` hit — the one at the literal call site the issue
names — missing from the record's quote entirely, verdict Incorrect on
that specific citation, not on the underlying code) — to
`docs/issue-2574/reports/conformance-review.md`, matching the skeleton
already on disk.

## Out of scope

- Editing `docs/issue-2574/reports/implementation.md` to fix its stale
  check-4 citation — that file belongs to the implementation role.
- Re-running the regression test suite independently; the implementation
  record's own before/after `git stash` comparison was read and found
  methodologically sound on inspection, not independently re-executed.
- Any change to `on-the-record/hooks/approval-gate.sh` or `spawn.py`.

## How you'll know it worked

`docs/issue-2574/reports/conformance-review.md` carries `loop_state:
complete`, four Present verdicts (one per acceptance check) each with a
file:line + commit-sha citation, and one Incorrect verdict naming the
implementation record's stale check-4 evidence — all reproducible by
re-running the cited `git show`/`git grep` commands against the cited
shas.

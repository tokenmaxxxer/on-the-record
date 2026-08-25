---
issue: 2226
role: execution-observation
loop_state: handed-off
upstream:
  - path: PR #2243 (branch issue-2226/implementation)
    sha: 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a
subject: gates/record_lint.py, gates/claims.py, gates/risk_report.py, gates/ci.py @ 26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a
test: "python3 -m gates.<X> vs python3 <X>.py for X in {record_lint, claims, risk_report, ci}; empty-state acceptance gate from issue #2226; python3 -m pytest gates/test_record_lint.py -q"
result: passed
assertedBy: issue-2226/execution-observation session, 2026-08-25, independent re-execution in a detached worktree (/tmp/pr2243-verify) checked out at PR #2243's head commit
---

# issue-2226 — execution-observation record

## What was done

Independently re-executed PR #2243 (`issue-2226/implementation`, head
`26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a`) against issue #2226's stated
bug and acceptance gate, in a fresh `git worktree` checked out at the
PR's head commit — running each command myself this turn rather than
citing the PR's own claimed test-plan output.

canonical: this session's own execution transcript, this turn — every
fenced block below is this turn's actual command + output, produced in
the worktree at `/tmp/pr2243-verify` (or the isolated dirs noted inline).

1. **Baseline reproduction on `main` (pre-fix)**: copied `main`'s
   `gates/record_lint.py` + `gates/gates.py` into an isolated dir and ran
   `python3 -m gates.record_lint`:
   ```
   File ".../gates/record_lint.py", line 31, in <module>
       RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md
   AttributeError: module 'gates' has no attribute 'RECORD_PATH'
   exit: 1
   ```
   This is the same `AttributeError` the issue reports.

2. **`python3 -m gates.record_lint` on the PR branch, run against this
   repo's real `docs/` tree**: no `AttributeError` — the run went past
   the former crash line and produced lint output, exit code 1 (nonzero
   because it has findings to report, not a crash). `diff` against
   `python3 gates/record_lint.py`'s output showed the first 1804 lines
   byte-identical before both runs hit this environment's output/time
   limits scanning the full real repo (~2000+ docs records) — a
   scale/timeout characteristic of the tool against this large tree,
   symmetric across both invocation forms, not something the fix
   introduced.

3. **Issue's own defined acceptance gate — empty-state**: fresh temp
   repo, `git init`, no `docs/issue-*/reports/*.md` records at all. Both
   forms ran to the same terminal state and reported nothing:
   ```
   === python3 -m gates.record_lint (empty state) ===
   record_lint: no records found under /tmp/empty_repo_test — 검사할 레코드가 없다.
   exit: 0

   === python3 gates/record_lint.py (empty state) ===
   record_lint: no records found under /tmp/empty_repo_test — 검사할 레코드가 없다.
   exit: 0
   ```

4. **The three other sibling entry points named in the issue's audit
   ask** (`claims.py`, `risk_report.py`, `ci.py`), each re-run both ways
   against the real repo:
   - `claims.py`: `python3 -m gates.claims` and `python3 gates/claims.py`
     — both exit code 1 (has findings), no traceback, no
     `AttributeError`.
   - `risk_report.py`: `python3 -m gates.risk_report` and
     `python3 gates/risk_report.py`, capped at 120s each:
     ```
     exit: 0
     502 /tmp/riskm.out
     exit: 0
     502 /tmp/riskd.out
     IDENTICAL
     ```
   - `ci.py --help` (`ci.py` has no `--help` flag — an arg-parsing
     failure unrelated to the sibling-import fix): both forms failed the
     same way, `fatal: cannot change to '.../--help'` — symmetric, not a
     crash-vs-no-crash difference between invocation forms.

5. **Test suite claimed in the PR**: ran
   `python3 -m pytest gates/test_record_lint.py -q` myself this turn:
   ```
   ....................................................................     [100%]
   68 passed in 17.06s
   ```
   That count matches what the PR's own test-plan states.

## Why

Issue #2226 required independent execution-observation, not a citation of
the PR author's own transcript: re-derive the before/after contrast
(reproduce the original `AttributeError` on `main`, then re-run the fix
branch to check its absence) and re-run the issue's own stated
acceptance gate (empty-state) plus the three named sibling entry points,
rather than trusting PR #2243's self-reported test-plan checklist.

## Upstream basis

- PR #2243, branch `issue-2226/implementation`, head commit
  `26c128ce7e0ed3c29232fdb95dc39e4a3d405c7a` (two commits: `71bfa6d` fix,
  `26c128c` deviation-log entry).
- Issue #2226 body: the `AttributeError` repro and the acceptance section
  (`gates/test_record_lint.py` gate, empty-state test, executed-live
  provenance requirement).

## Open findings

None — resolution path: not applicable, no open finding to resolve. The
fix resolves the exact `AttributeError` this record reproduced under
`python3 -m gates.record_lint`, both invocation forms behave
symmetrically (including on the three other named sibling entry points),
and the issue's defined empty-state acceptance gate reaches exit code 0
on both forms.

## Next steps

None — loop_state is terminal (`handed-off`); no next steps or
resolution path are outstanding.

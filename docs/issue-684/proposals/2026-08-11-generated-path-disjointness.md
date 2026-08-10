---
status: proposed
files:
  - docs/issue-684/reports/implementation/survey.md
  - docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md
  - docs/specs/generated-paths.md
  - on-the-record/hooks/product-capture-stopgate.sh
  - on-the-record/hooks/test_product_capture_stopgate.py
  - gates/test_generated_paths.py
---

# issue-684 phase 1 — generated write-path disjointness audit + enforcement

## Request

For every file `on-the-record/hooks/*.sh` (and the vendored `gates/*.py`)
writes into a target repo's worktree, enumerate the path, classify it as
out-of-tree, issue-scoped, or collision-risk, fix or justify each risk,
and add a filesystem-derived enforcement test — same shape as
`gates/test_boundary.py` — so a future hook that adds a non-disjoint
write path fails CI.

## Constraints

- Inventory doc must be committed with file:line per generator (#684
  acceptance).
- The enforcement test must derive its inventory from hook sources, not
  a hand-maintained list (#684 acceptance, mirrors `gates/test_boundary.py`).
- Empty-state generators (hooks that write nothing) must appear as `n/a`
  and be covered by the same completeness check.
- Two simulated concurrent issues must be shown to yield disjoint write
  sets.
- Out of scope per the issue text: the warrant counter / hunt-report
  naming (core#200) and human-authored file collisions (write-scope
  territory).

## Rationale

**Alternative considered: a runtime PreToolUse hook that intercepts every
write and checks it live, instead of a static-source enforcement test.**
Rejected — the issue explicitly asks for the `test_boundary.py`
completeness-from-filesystem pattern (derive the inventory mechanically,
assert against it), not a new runtime gate. A live interception hook
would also need registration in `hooks.json`'s lifecycle-event map the
same way `record-scaffold.sh`'s own header note says a PreToolUse form
was rejected for it (no natural trigger event to hang a "generator is
about to write" check off); a static test that reads the hook source and
checks the constructed-path shape has no such registration problem and
runs in CI on every change, catching the defect before a session ever
executes the hook.

**Alternative considered: leave `product-capture-stopgate.sh`'s
`docs/product/<cat>.md` path as-is and only document it as a known risk.**
Rejected — the survey (docs/issue-684/reports/implementation/survey.md)
found this is the one generator in the current inventory that is neither
out-of-tree nor issue-scoped: it is keyed only by a fixed category name,
exactly the anti-pattern issue #684 names ("never keyed only by
date/topic/global name"). Documenting it without fixing it would leave a
known, reproducible cross-issue merge-conflict source in place, contrary
to the issue's "fix or justify" requirement — a risk this well-defined has
no honest justification to record instead of a fix.

## What will be done

1. Fix `product-capture-stopgate.sh`: change the write target from
   `docs/product/<cat>.md` to an issue-scoped path,
   `docs/issue-<n>/product/<cat>.md`, deriving `<n>` from the same
   transcript/session context the hook already reads to build `flagged`
   (the hook runs inside a Claude Code hook payload that carries the
   session's issue context the same way other hooks in this inventory
   derive `<n>`). Update its existing test
   (`on-the-record/hooks/test_product_capture_stopgate.py`) to assert the
   new path shape.
2. Write `docs/specs/generated-paths.md`: a markdown table (mechanism |
   classification | verdict), one row per generator in the survey,
   `gates/test_generated_paths.py`'s golden reference.
3. Write `gates/test_generated_paths.py`, mirroring
   `gates/test_boundary.py`'s shape:
   - derive the actual generator inventory by parsing
     `on-the-record/hooks/*.sh` for write-producing calls
     (`write_text`, `open(..., "w")`, `mkdir`) and extracting the
     path-construction expression per hit;
   - assert every derived path either resolves outside the target-repo
     root (out-of-tree) or its constructed path string contains an
     issue-number placeholder (`issue-<n>`, `issue-{issue}`, or
     equivalent f-string/shell interpolation of an issue variable);
   - assert completeness against `docs/specs/generated-paths.md` the same
     way `test_boundary.py` checks against
     `docs/specs/enforcement-boundary.md` — every hook with a write
     call must have a recorded verdict, hooks with none are asserted
     `n/a`;
   - a two-issue simulation: instantiate the path-construction logic for
     `record-scaffold.sh`, `delegated-judgment-gate.sh`, and the fixed
     `product-capture-stopgate.sh` with issue numbers 100 and 200 and
     assert the resulting path sets are disjoint.

## Accumulation

`docs/specs/generated-paths.md` gains one row per future generator that
writes into a target repo, the same way `docs/specs/enforcement-boundary.md`
grows one row per new gate/hook. `gates/test_generated_paths.py` derives
its inventory from `on-the-record/hooks/*.sh` at test time, so a future
hook is picked up by the test automatically; the suite only fails when
that hook's write path is missing a spec row or fails the
out-of-tree/issue-scoped check. The spec table is the only file a human
edits by hand as generators accumulate, and it grows by exactly one row
per new generator — never a repeated inline check added elsewhere.

## Out of scope

- The warrant counter and hunt-report naming (core#200).
- Human-authored file collisions (write-scope territory).
- The `<seq>` auto-decision/remediation counter collision under
  same-issue concurrent sessions (within-issue, not cross-issue —
  outside this issue's disjointness framing).
- The shared-checkout marker/clone races in `self-update.sh`,
  `directive.sh`, `impact-guard.sh`, `decision-queue-stopgate.sh` — these
  are out-of-tree relative to every target repo, so they cannot produce
  the git merge conflict this issue is about; any liveness race between
  concurrent sessions on the same marker is a different problem class.

## How you'll know it worked

- `python3 gates/test_generated_paths.py` passes, deriving its inventory
  from `on-the-record/hooks/*.sh` (not a hand list) and failing loudly if
  a hook is added with a write call absent from
  `docs/specs/generated-paths.md`.
- `python3 on-the-record/hooks/test_product_capture_stopgate.py` passes
  against the new `docs/issue-<n>/product/<cat>.md` path.
- The two-issue simulation inside `gates/test_generated_paths.py` asserts
  disjoint write sets for issue 100 vs. issue 200.

---
status: proposed
files:
  - docs/specs/generated-paths.md
  - on-the-record/hooks/gate-registration-guard.sh
  - on-the-record/hooks/test_gate_registration_guard.py
  - docs/issue-839/reports/implementation.md
---

# Proposal — issue #839 step 1, implementation

## Request

`gates/test_generated_paths.py::t_all_generators_recorded_and_disjoint`
fails on main: `stop-poll-rearm.sh` has no write call in its own file text,
but `docs/specs/generated-paths.md` records it `out-of-tree` instead of
`n/a`. The row landed wrong in `d4a8228` alongside `poll-rearm.sh`'s row,
and `gate-registration-guard.sh` (issue #759) only checks that a row
*exists* for a newly-staged hook, never that its classification matches
what the same commit's own source derives — so the wrong row landed
without the PreToolUse gate catching it. The issue hands over two
decisions: fix the doc cell or change the spec's unit, and whether the
guard should be strengthened to check classification match too.

## Constraints

- Do not touch `gates/test_generated_paths.py` — the doc-vs-test mismatch
  is a documentation error, not a defect in the test's derivation logic
  (survey Decision 1).
- Do not touch `on-the-record/hooks/spawn-allow-gate.sh` or its test file
  — a concurrent issue-834 session is editing them on a different branch.
- Do not touch `on-the-record/hooks/poll-rearm.sh`, `stop-poll-rearm.sh`,
  or `impact-guard.sh`'s cited-string false positive — out of scope per
  the issue text; #801/#829 already landed the rearm behavior itself.
- The `gate-registration-guard.sh` extension must only ever evaluate
  newly-staged (`A`/`R`/`C`) hook scripts — the guard's existing narrow
  trigger for already-registered ("M") hooks must not change.
- Every existing case in `on-the-record/hooks/test_gate_registration_guard.py`
  must keep passing unmodified in behavior.

## Rationale

**Alternative considered (Decision 1): change `gates/test_generated_paths.py`'s
unit from file-level grep to source-chain-tracing, so a hook that sources
a write-capable library inherits that library's classification.** Rejected
— the survey
(`docs/issue-839/reports/implementation/survey.md`, Decision 1) found the
spec's own text (`docs/specs/generated-paths.md` lines 3-5) and the
mechanism's origin proposal
(`docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md`
lines 79-81, Rationale lines 39-50) both specify a file-level static grep
deliberately, rejecting a more powerful runtime/call-graph mechanism for
the same reason this alternative would reintroduce: added complexity
(relative-path resolution, "is the sourced write function actually
reachable on this call path" reasoning, risk of over-flagging a hook that
sources a library but never invokes its writing function) for a problem
the survey showed, by grepping every hook for `source`/`.` statements, has
exactly one affected row in the current tree (`stop-poll-rearm.sh`;
`directive.sh` already matches independently and would be unaffected by
either unit). A one-row problem does not justify a unit change whose own
origin proposal already considered and rejected the more general
mechanism.

**Alternative considered (Decision 2): leave `gate-registration-guard.sh`
at presence-only and record that reuse is impractical.** Rejected — the
survey verified live that reuse is bounded and cheap, not impractical: the
guard already extracts the classification value from every
`generated-paths.md` row it reads (its `_ROW_RE`'s non-greedy second
capture group, proven by direct regex replay in the survey), its trigger
is already scoped to only the commit's newly-staged hook files (never the
whole directory), and the two regexes needed
(`_WRITE_CALL_RE`/`_ISSUE_PLACEHOLDER_RE`) already exist in
`gates/test_generated_paths.py` in a form directly portable into the
guard's Python heredoc — the same inline-porting pattern the guard's own
header comment already commits to for the presence check. Leaving it at
presence-only would leave the exact failure mode #839 reports (row exists,
classification wrong) uncaught at commit time indefinitely, for a fix the
survey showed costs a bounded, same-shape addition.

**Known limitation, surfaced by this proposal's own after-proposal hunt**
(`docs/issue-839/reports/implementation/2026-08-11-hunt-generated-paths-row-fix-and-guard-extension.md`,
stance 0, verdict FINDING): the ported `check()` logic verifies
classification value shape (is it `n/a`/`out-of-tree`/`issue-scoped`, is
an `issue-scoped` placeholder present) but never verifies that an
`out-of-tree` claim is actually truthful against the hook's constructed
write path. A hook that genuinely writes in-tree with no issue placeholder
(a real `collision-risk` generator per issue #684's own definition) but is
mislabeled `out-of-tree` still passes both `check()` today and the
extended guard, reproduced live in the hunt record with a scratch hook and
`check()` imported unmodified. This gap is inherited from
`gates/test_generated_paths.py::check()` as it already ships on main — the
extension does not introduce it and does not widen it, and it does not
affect this issue's own incident: `stop-poll-rearm.sh` has no write call
at all, so it falls through `check()`'s `n_a_hooks` branch (any non-`n/a`
classification recorded for a non-writer is already flagged), which is
the exact comparison both the existing test and the extension perform
correctly. The extension's honest scope is restated in "How you'll know
it worked" below and as an explicit Out-of-scope item — a path-expression
truthfulness verifier for `out-of-tree` claims is a materially larger
feature (parsing and evaluating each hook's constructed path expression)
than reusing an existing value-shape comparison, and is not what issue
#839's own text asks for (verdict-cell match against what the existing
derivation already computes, not a new deeper semantic check).

## What will be done

1. `docs/specs/generated-paths.md`: replace the `stop-poll-rearm.sh` row's
   classification from `out-of-tree` to `n/a`, with verdict text that
   states the reason honestly (no write call in this file's own text
   under the file's stated grep unit) while pointing at where the actual
   write is recorded (`poll-rearm.sh`'s row, unchanged, still
   `out-of-tree`) — the exact row text verified live in the survey's
   Decision 1 section.
2. `on-the-record/hooks/gate-registration-guard.sh`: for each path in the
   already-computed `hook_scripts` list, read its staged content via
   `git show :path` (falling back to disk, mirroring `read_spec()`'s
   existing staged-content preference), and:
   - duplicate `_WRITE_CALL_RE` and `_ISSUE_PLACEHOLDER_RE` from
     `gates/test_generated_paths.py` inline in the guard's Python heredoc
     (same porting convention `recorded_names()`/`_ROW_RE` already use for
     the row-parsing side);
   - parse the file's own recorded classification from
     `docs/specs/generated-paths.md` (reusing the existing 3-column
     `_ROW_RE` match, whose second capture group is already the
     classification column);
   - deny the commit if: the file has no write-call match and is recorded
     anything other than `n/a`; or has a write-call match and is recorded
     `collision-risk` or a value outside `{out-of-tree, issue-scoped}`; or
     is recorded `issue-scoped` with no issue-placeholder match in its own
     staged text;
   - leave the existing presence check (row must exist at all) unchanged
     and leave `enforcement-boundary.md`'s check untouched — the
     extension applies only to the `generated-paths.md` side, and only to
     hook scripts already in `hook_scripts`.
3. `on-the-record/hooks/test_gate_registration_guard.py`: add a regression
   case staging a newly-added hook script with no write call in its own
   text but a `generated-paths.md` row recorded `out-of-tree` (mirroring
   this exact incident's shape), asserting the commit is denied with a
   message naming the mismatch; keep all 12 existing cases passing
   unmodified.
4. Run `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` on the
   branch and compare its failure set against the same command run at
   `origin/main`, per the issue's Acceptance section; paste both results
   into the phase-2 record.
5. Write `docs/issue-839/reports/implementation.md`, this role's phase-2
   record, citing this proposal and the survey as upstream basis.

## Accumulation

`docs/specs/generated-paths.md` already accumulates one row per generator
by design (`docs/issue-684/proposals/2026-08-11-generated-path-disjointness.md`'s
own Accumulation section) — this proposal changes one existing row's
classification, it does not change that growth pattern or add a second
place a classification is recorded. The `gate-registration-guard.sh`
extension does not add a per-generator maintenance step either: it derives
write-call presence and issue-placeholder shape from each newly-staged
hook's own source at commit time, the same way
`gates/test_generated_paths.py` already does for the whole directory at
test time — a future hook still needs exactly one new row in
`docs/specs/generated-paths.md` and nothing else, whether or not this
proposal lands. If a future commit repeats this exact incident shape (a
new hook lands with a spec row present but classified wrong), the extended
guard denies it at commit time instead of leaving it for someone to
notice the suite is red; no accumulating list of special-cased hook names
is introduced — the check re-derives from source on every commit, not
from a hand-maintained registry that would grow one entry per hook.

## Out of scope

- Changing `gates/test_generated_paths.py`'s derivation unit (Decision 1,
  rejected above).
- `on-the-record/hooks/spawn-allow-gate.sh` (issue-834, concurrent
  session, different branch).
- `poll-rearm.sh`/`stop-poll-rearm.sh`'s re-arm behavior itself (#801,
  #829, already landed).
- `impact-guard.sh`'s quoted-string false positive (separate issue, named
  out of scope in #839's own text).
- A shared-helper refactor that has `gate-registration-guard.sh` import
  `gates/test_generated_paths.py` directly instead of duplicating its two
  regexes — the guard's own header comment already commits to inline
  porting specifically because a repo-checkout-relative import cannot be
  guaranteed at hook-invocation time; revisiting that design choice is a
  separate proposal, not this one's shape.
- Verifying that an `out-of-tree`/`issue-scoped` claim is actually
  truthful against a writer hook's constructed path (as opposed to
  checking the recorded value's shape). This session's after-proposal hunt
  (Rationale, Decision 2's "Known limitation" paragraph) reproduced a
  genuinely in-tree, non-issue-scoped hook mislabeled `out-of-tree` still
  passing both today's `check()` and this proposal's extension — a
  pre-existing gap in `gates/test_generated_paths.py::check()` itself, not
  introduced or widened here, and not what issue #839's own text asks the
  guard to check. A path-expression truthfulness verifier is a
  materially larger feature and a separate, larger issue if wanted.

## How you'll know it worked

`python3 -m pytest gates/test_generated_paths.py -q` passes (4/4), with
`t_all_generators_recorded_and_disjoint` in particular no longer failing
on the `stop-poll-rearm.sh` row. `python3 -m pytest
on-the-record/hooks/test_gate_registration_guard.py -q` passes, including
the new regression case proving a newly-staged hook with a
classification-mismatched `generated-paths.md` row gets denied at commit
time, while every existing case (presence-only denials, the already-green
`n/a`-with-no-write-call case, the untouched-`M`-edit case, the
`ORCHESTRATE_OFF` bypass case) keeps its current outcome. `python3 -m
pytest gates/ tests/ on-the-record/hooks/ -q` run on the branch reports a
failure set with `t_all_generators_recorded_and_disjoint` removed and no
new failure beyond that, compared side-by-side against the same command
run at `origin/main` (survey's Baseline section: 1 failed, 1209 passed, 2
skipped, 1 xfailed) — the delta is exactly minus one failure, plus the new
regression test.

---
code_under_review:
  - gates/test_record_lint.py
type: test
breaking: false
verdict: pass
loop_state: landed
---

Subject: issue-744, phase 2 (delivery). Upstream: the approved phase-1
proposal `docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md`
(approved via the issue-level comment `APPROVE issue-744/implementation`),
itself based on `docs/issue-744/reports/implementation/survey.md`.

## What was done

Implemented exactly the phase-1 proposal's "What will be done" section —
two new test functions in `gates/test_record_lint.py`, plus this record:

- `t_orphaned_path_reference_check_denies_genuinely_missing_path` — a
  regression pin confirming `orphaned_path_reference_check` still denies a
  backtick-quoted path ('gates/this-file-was-never-written.py') that is
  genuinely nonexistent, not a ':identifier()' locator, and not a path
  this write set will create later — the legitimate-refusal case #744's
  own body requires to keep failing.
- `t_orphaned_path_reference_check_false_positives_documented_gap` — an
  `xfail`-marked test (`strict=True`, reason string citing #744 and the
  deferred-scope decision), documenting the two known false-positive
  shapes from the survey: a 'path:identifier()' locator suffix on a real
  file ('gates/real_module.py:helper()') and a reference to a path this
  same write set will create later (this very record's own path). Asserts
  the ideal future behavior (`bad == []`); currently `xfailed` since the
  check still denies both. `strict=True` means a future logic fix that
  resolves either shape turns this into a visible `XPASS` failure, not a
  silent gap closing unnoticed.
- Dispatched the warrant-hunter at both cadence points: after-proposal
  (phase 1, already resolved — see survey.md's own "Evidentiary note"
  section) and before-landing (this phase), both appended to the existing
  `docs/issue-744/reports/implementation/hunt-2026-08-11-gate-noise-item-dispositions.md`.
  The before-landing dispatch (stance 1: "assume this change and another
  plugin's rule cancel each other") surfaced a real composition bug in my
  first draft of the xfail test — see `## What did not work` and
  `closed_checks:` below.

Per-item disposition, restating the survey's verdicts (no gate logic
touched, per #744's own scope note deferring item 2 until #730's
guidance-only countermeasure has been observed in effect):

- **Item 1** (`docs/specs/reconciled-index.md` companion-update
  requirement): resolved upstream, tokenmaxxxer-core#204. Regression
  coverage already exists — `gates/test_hooks_parity.py`'s
  `t_live_fire_deny_before_commit_lands` — and authoring-time guidance is
  present live in this very session's own context. Nothing added here.
- **Item 2** (backtick-quoted paths to not-yet-created files /
  `path:function` notation): guidance-only fix (#730) already landed and
  live; the underlying regex gap is real and reproducible but explicitly
  out of #744's own current scope. This phase-2 delivery adds the
  regression pin plus the documenting `xfail` described above — no logic
  change.
- **Item 3** (`reports/hunt-*.md` ownership vs board-gate role-scope):
  duplicate of #705, whose open phase-1 proposal
  (`docs/issue-705/proposals/2026-08-11-align-post-pr-record-guidance-with-gates.md`)
  already targets this exact mechanism. The hunt-record-path portion is
  already resolved upstream, tokenmaxxxer-core#202; #705's broader scope
  (record-claim-guard/record-fields-gate template alignment) remains open
  and untouched by this issue. No duplicate prescription added here.
- **Item 4** (trailer-gate and heredoc commit messages): the originating
  claim ("trailer-gate cannot parse heredoc commit messages") is false as
  stated — already fixed upstream 2026-08-07, tokenmaxxxer-core#151, four
  days before #744 was filed. The issue-759 stranding this item cited as
  evidence is better explained by (a) a warrant-hunter's adversarial
  probing of an unrelated gate (expected to hit denials) and (b) the
  separately-already-fixed untracked-file-staging gap,
  tokenmaxxxer-core#203. No trailer-gate code or message change is
  warranted; no on-the-record-side change added here.
- **Direction-conflict check** (`on-the-record/hooks/gate-registration-guard.sh`,
  issue-759, vs #744): resolved as "keep both, not in conflict" — that
  hook's own header comment already names #744 explicitly and its trigger
  is narrow by construction (only a newly-staged mechanism file with no
  spec row). Not weakened, narrowed, or removed.

## Why

Reason: #744's Acceptance requires, per item, either a unit test
reconstructing the previously-denied input to check whether it now passes
or is correctly still denied, or — if a candidate turns out to be a
legitimate refusal rather than noise — a recorded judgment with no
prescription. The phase-1 survey already reached and documented that
judgment for items 1, 3, and 4 (each already resolved upstream or
duplicated elsewhere); item 2 is the one candidate the issue's own text
keeps a change deferred on, so phase 2's job is narrowed to exactly what
the proposal scoped: pin the legitimate-refusal case as a regression
test, and document the deferred false-positive gap as a strict `xfail` so
a future logic change surfaces instead of landing unnoticed.

## What did not work

- First draft of `t_orphaned_path_reference_check_false_positives_documented_gap`
  wrote to a 'gates/real_module.py' path inside the fixture's temp repo
  without first creating the `gates/` subdirectory (the `_repo_with_record`
  helper only creates the directory tree for the record's own path, e.g.
  `docs/issue-517/reports/`). Expected: the write succeeds and
  `record_lint.lint_record()` runs against both backtick references,
  reporting them as violations (which the `xfail` then documents).
  Actual: `write_text()` raised an uncaught `FileNotFoundError` before
  `lint_record()` ever ran — the test never exercised the check it
  claimed to. Caught by the before-landing warrant hunt (stance 1), which
  also noted this masked a secondary, narrower gap: pytest's `xfail`
  machinery catches any exception type as "expected" (so `pytest -q`
  still reported `xfailed`, hiding the defect), but this file's own bare
  `_run_all()` runner (`python3 gates/test_record_lint.py`, the module
  docstring's other documented invocation form) only catches
  `AssertionError` and so crashed with an unhandled traceback instead of
  a normal `FAIL` line. Fixed by adding
  `(d / "gates").mkdir(parents=True, exist_ok=True)` before the write.
  Re-checked after the fix: `pytest -q` still reports `8 passed, 1
  xfailed` (now for the intended reason — `bad` actually contains the two
  path-reference violations, not a crash), and
  `python3 gates/test_record_lint.py` now prints a normal `FAIL ...` line
  with an `AssertionError` message and exits 1 (matching every other test
  in the file that fails via a plain `assert`), instead of an uncaught
  traceback.
  derived: `python3 -m pytest gates/test_record_lint.py -q -rx`
  ```
  ........x                                                                [100%]
  =========================== short test summary info ============================
  XFAIL gates/test_record_lint.py::t_orphaned_path_reference_check_false_positives_documented_gap - #744 item 2, deferred by #744's own scope note until #730's guidance-only countermeasure has been observed in effect: orphaned_path_reference_check cannot distinguish a `path:identifier()` locator suffix, or a reference to a path this same write set will create later, from a genuinely hallucinated path — all three currently deny identically. A fix that resolves either shape should turn this xfail into an unexpected pass (caught by strict=True), not a silent gap.
  8 passed, 1 xfailed in 3.28s
  ```

closed_checks:
- check: after-proposal warrant hunt, stance 0 (assume the gate just
  touched is bypassable)
  code_sha: docs/issue-744/reports/implementation/survey.md,
  docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md
  result: finding resolved within phase 1 — see survey.md's own
  "Evidentiary note" section; no further action needed in phase 2.
- check: before-landing warrant hunt, stance 1 (assume this change and
  another plugin's rule cancel each other)
  code_sha: gates/test_record_lint.py
  result: finding fixed in this delivery (missing `gates/` mkdir before
  write) and re-checked — see `## What did not work` above. The residual,
  narrower structural gap the hunt also noted (the file's bare
  `_run_all()` runner has no concept of `pytest.mark.xfail` at all, so it
  will always report any xfail-marked test's exception as a plain `FAIL`
  rather than an expected pass) is a pre-existing property of this file's
  dual-invocation pattern, not introduced or fixed by this delivery, and
  out of this proposal's frozen write set to change; no live CI path
  invokes the bare form (`.github/workflows/` retired per #460), so
  nothing automated depends on it.

## Open findings

None outstanding — the one before-landing finding above was fixed in
this delivery and re-checked.

## Next steps

None — landed.

## Resolution path

N/A — no open findings.

## Doc placement

- No new env var, config key, dependency, or migration introduced —
  nothing for docs/handbooks/.
- No public signature or wire format changed
  (`orphaned_path_reference_check` and `lint_record` keep their existing
  signatures and behavior — this delivery is test-only, per the
  proposal's own out-of-scope note) — nothing for this issue's decisions
  bucket.
- The full-suite pass-count benchmark this change is measured against is
  recorded below under Test evidence, not narrated only in prose.

## Test evidence

checked: `python3 -m pytest gates/test_record_lint.py -q` shows the new
regression pin passing and the new xfail test reported as `xfailed`
— result: verified
  derived: `python3 -m pytest gates/test_record_lint.py -q`
  ```
  ........x                                                                [100%]
  8 passed, 1 xfailed in 2.96s
  ```

checked: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` grows
only by the 2 new tests over the phase-1 survey's baseline, with zero new
failures caused by this diff
— result: verified with two caveats, both independently checked as
unrelated to this diff's content (canonical: the two stash-isolated runs
below, taken on the unmodified current `main` tip, commit `c1cf884`,
before any of this session's edits were reapplied)

The full-suite run below was taken with this diff present but not yet
committed (working tree "dirty" relative to `HEAD`):
  derived: `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q`
  ```
  FAILED gates/test_capability_gates.py::t_actual_tree_schema_field_orphans_catches_alive
  FAILED tests/test_gates.py::t_rulebook_version_is_recorded - AssertionError: ...
  2 failed, 1150 passed, 2 skipped, 1 xfailed in 153.96s (0:02:33)
  ```
That collected total is exactly the phase-1 survey's baseline plus this
diff's 2 new tests (see `docs/issue-744/reports/implementation/survey.md`'s
"Baseline: main is green" section for the pre-diff figure), but with 2
failures where the survey recorded zero. Both were isolated by
`git stash`ing this diff and rerunning against the clean, currently-
committed `main` tip (`c1cf884`) before restoring the diff with
`git stash pop`:

  derived: `git stash && python3 -m pytest gates/test_capability_gates.py::t_actual_tree_schema_field_orphans_catches_alive tests/test_gates.py::t_rulebook_version_is_recorded -q`
  ```
  F.                                                                       [100%]
  1 failed, 1 passed in 0.50s
  ```

`t_actual_tree_schema_field_orphans_catches_alive` fails identically on
the clean, unmodified `main` tip — it is pre-existing drift in
`docs/specs/flows-schema.md` field usage unrelated to `gates/record_lint.py`
or this issue, introduced by commits that landed on `main` after the
phase-1 survey's baseline was captured (the survey's baseline predates
#799's merge). Fixing it is outside this proposal's frozen write set
(`gates/test_record_lint.py` only) and outside #744's scope (record-lint
gate noise, not `flows-schema.md` drift) — reported here as a discovered
pre-existing anomaly, not fixed.

`t_rulebook_version_is_recorded` passes on the clean tree and only fails
while this repo's own working tree (the self-hosted rulebook checkout
`spawn.rulebook_version()` reads) has uncommitted changes — a property of
running the suite before landing, not a regression this diff's content
causes. It is expected to pass again once this commit lands and the tree
is clean.

Net: after this commit lands, the expected full-suite state is 1 failure
(the pre-existing, unrelated `t_actual_tree_schema_field_orphans_catches_alive`,
already present on `main` before this delivery), the new xfail reported
as `xfailed`, and every other count unchanged from the phase-1 survey's
baseline plus this delivery's 2 new tests.

## Acceptance verification

- new regression pin denies a genuinely missing backtick path, the case #744 requires to keep failing — checked: gates/test_record_lint.py::t_orphaned_path_reference_check_denies_genuinely_missing_path — result: pass
- new xfail test documents item 2's two false-positive shapes and reports xfailed as designed — checked: gates/test_record_lint.py::t_orphaned_path_reference_check_false_positives_documented_gap — result: pass
- this file's own suite runs clean, 8 passed 1 xfailed, zero unexpected failures — checked: gates/test_record_lint.py — result: pass
- repo-wide full suite grows only by these 2 new tests over the phase-1 survey's baseline, zero new failures caused by this diff, per the stash-isolated proof above — checked: full-suite — result: pass
- pre-existing schema-field-orphans failure on main, unrelated to this diff and outside this proposal's frozen write set — checked: gates/test_capability_gates.py::t_actual_tree_schema_field_orphans_catches_alive — result: fail: pre-existing drift in docs/specs/flows-schema.md, reproduces identically on clean main before this change, out of #744's scope, reported not fixed

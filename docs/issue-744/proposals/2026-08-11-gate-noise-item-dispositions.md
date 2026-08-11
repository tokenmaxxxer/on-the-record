---
status: proposed
files:
  - docs/issue-744/reports/implementation/survey.md
  - docs/issue-744/proposals/2026-08-11-gate-noise-item-dispositions.md
  - gates/test_record_lint.py
  - docs/issue-744/reports/implementation.md
  - docs/issue-744/reports/implementation/hunt-*.md
---

## Request

#744 asks for a per-item disposition (automate the fix, add authoring-time
guidance, relax the rule, or add a corrective command to the refusal
message) across four gate-friction candidates: the docs/specs/reconciled-index.md
companion-update requirement, backtick-quoted paths that resolve to
nothing on disk, reports/hunt-*.md ownership under board-gate, and
trailer-gate's handling of heredoc-bodied commit messages. It explicitly
rejects "fix everything with guidance text" as an acceptable single
answer and asks each item to be judged noise-vs-legitimate on its own
evidence, plus a judgment on whether issue-759's new
gate-registration-guard.sh should be treated as a conflicting direction.

## Constraints

- This repo's write set cannot reach tokenmaxxxer-core (board-gate.sh,
  trailer-gate.sh, warrant/coding/record-shape plugin directives all live
  there, per repo-boundary finding in the survey) — no fix authored here
  can touch that code.
- Item 2's check logic (`gates/record_lint.py`'s
  `orphaned_path_reference_check`) must not change: #744's own body
  places this out of scope until #730's guidance-only countermeasure has
  been observed in effect.
- `on-the-record/hooks/gate-registration-guard.sh` (issue-759) must not be
  weakened, narrowed further, or removed: the survey's direction-conflict
  check found it already narrowly scoped and explicitly aware of #744, not
  a source of noise.
- No new gate/hook module is added by this proposal, so
  gate-registration-guard.sh's same-commit spec-row requirement does not
  apply to this work.

## Rationale

For items 1, 3, and 4, the alternative considered was building on-the-record-side
duplicate fixes (e.g., vendoring a corrected copy of trailer-gate.sh's
heredoc-parsing logic, or board-gate.sh's role-scope check, into this
repo so #744 could claim full code-level coverage). Rejected: the survey
found all three already fixed upstream in tokenmaxxxer-core within hours
of #744 being filed, spun out of the same #726 audit #744 itself draws on.
Vendoring a second copy here would recreate exactly the byte-diverged,
drifting duplication tokenmaxxxer-core's own issue-66 already eliminated
once by promoting shared hooks to core canon — the opposite of a
noise-reduction outcome.

For item 2, the alternative considered was fixing
`orphaned_path_reference_check`'s regex now — special-casing a trailing
`:identifier()` locator suffix and adding a will-create allowlist for
paths the same PR's own write set names — instead of only adding
regression coverage for the current behavior. Rejected: #744's own text
places this change out of scope until the effect of #730's guidance is
observed, and jumping ahead here would conflate "the guidance didn't
work" with "the guidance was never given a chance," which is exactly the
premature-conclusion risk the issue is trying to avoid by asking for
per-item evidence rather than a blanket fix.

## What will be done

- Add two test functions to `gates/test_record_lint.py`:
  - A regression pin confirming `orphaned_path_reference_check` still
    denies a genuinely nonexistent, non-locator, non-future-file backtick
    path reference (the legitimate case #744 says must keep failing).
  - An `xfail`-marked test (strict, with a reason string citing #744 and
    the deferred-scope decision) documenting the two known false-positive
    shapes from the survey — a `path:identifier()` locator suffix and a
    reference to a path the same write set will create later — so a
    future change to the check's logic that resolves either shape turns
    this test into a visible, unexpected pass instead of a silent gap.
- Write `docs/issue-744/reports/implementation.md` (the phase-2 record)
  stating, per item, the verdict already reached in the survey: item 1
  resolved upstream (tokenmaxxxer-core#204, verified live and via the
  existing `gates/test_hooks_parity.py` live-fire test); item 2
  guidance-landed with a deferred, now-regression-pinned logic gap; item 3
  a duplicate of #705, already resolved upstream for the hunt-record-path
  portion (tokenmaxxxer-core#202) with #705's broader scope left
  untouched and open; item 4's originating claim falsified, with the
  actual issue-759 stranding attributed to a warrant-hunter's expected
  adversarial denials plus the separately-already-fixed untracked-file-staging
  gap (tokenmaxxxer-core#203); and the gate-registration-guard.sh
  direction-conflict check resolved as "keep both, not in conflict."
- Dispatch the warrant-hunter at both the after-proposal and
  before-landing transitions per the warrant plugin's own cadence, and
  fold its findings into the phase-2 record's `closed_checks:` entries.

## Out of scope

- Any change to `gates/record_lint.py`'s check logic (item 2's deferred
  fix) — tracked as a known limitation by the new xfail test, not fixed
  here.
- Any change to tokenmaxxxer-core's board-gate.sh, trailer-gate.sh, or
  the warrant/coding/record-shape plugin directives — outside this
  session's write set; already resolved upstream per the survey.
- Filing a tokenmaxxxer-core issue for the two narrower residual gaps the
  survey found (trailer-gate's CLAUDE_PROJECT_DIR-vs-cwd root resolution
  during sandboxed experiments; the still-refused unquoted
  `-m $(cat <<EOF ...)` form) — issues are user-authored only, per
  contract; this proposal's record states the findings so the user can
  file them if wanted.
- #705's own broader scope (record-claim-guard/record-fields-gate
  template alignment for the post-PR record write) — owned by #705, not
  duplicated here.
- Weakening, narrowing, or removing `on-the-record/hooks/gate-registration-guard.sh`.

## How you'll know it worked

- `python3 -m pytest gates/test_record_lint.py -q` shows the new
  regression pin passing and the new xfail test reported as `xfailed`
  (not `failed`, not silently absent).
- `python3 -m pytest gates/ tests/ on-the-record/hooks/ -q` still reports
  zero failures, growing only by the new test count over this survey's
  1127-passed/2-skipped baseline.
- `docs/issue-744/reports/implementation.md` exists with `loop_state:
  landed`, cites #705 for item 3 and #726/tokenmaxxxer-core#151/#202/#203/#204
  for the upstream-resolved items, and carries `closed_checks:` entries
  for both warrant-hunter dispatches.
- `git diff --stat` against `main` shows no file outside this proposal's
  frozen write set touched.

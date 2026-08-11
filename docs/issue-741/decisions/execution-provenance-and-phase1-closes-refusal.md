# Decision: execution-provenance logging + phase-1 closes-refusal

Subject: issue-741

## (a) Chosen: self-logging provenance, not a forced cache reinstall

`contract-guard.sh` now appends one JSON line — its own absolute path,
sha256 of its own file content, and the phase2/is_src_test/is_record/
closes_present_before verdict it computed — to
`$CONTRACT_GUARD_PROVENANCE_LOG` (default
`~/.claude/on-the-record/hook-provenance.log`) on every `gh pr merge` it
reaches a verdict on, wrapped in `try/except Exception: pass` so a log
failure can never become a new deny path.

**Rejected — extend `self-update.sh` to force-reinstall the plugin
install cache.** `self-update.sh`'s own comment already documents that
`claude plugin update` reads only a version string and reports
"already latest" forever — recalling that command gives no guarantee the
cache actually refreshes, a trap already hit once. Overwriting
`~/.claude/plugins/cache/...` from inside a hook script would also mean a
repo-owned script mutating Claude Code's own installer state, a much
larger blast radius than this request's actual priority: make the
mismatch observable, not fix the installer.

## (b) Chosen: pr-preflight.sh denies an author-written phase-1 Closes

`pr-preflight.sh` now runs one more check, only when `phase == "phase1"`
and `check_body` found no other violation: scan the body via
`_CLOSES_REF.finditer()` (not `.search()` — see below) for a
closing-keyword match against the PR's own issue, and `deny()` if found.

**Rejected — allow it.** Contract v3 s19 states plainly: "Merging a
phase-1 PR must not auto-close the issue." Allowing is a contract
violation, not a design option.

**Rejected — silently strip the keyword from the body.** This would
invert the two hooks' established division of labor:
`contract-guard.sh`'s broker-attach *corrects* a phase-2 PR's missing
trailer (issue #653) — but `pr-preflight.sh` has never rewritten a body,
only refused before the act executes (its own header: "Denied before the
merge/create/edit executes"). Silently erasing an author's own words also
teaches nothing; denying at `gh pr create`/`gh pr edit` time is the
cheapest possible correction point — the PR doesn't exist yet, or the
edit hasn't landed.

**Rejected — gate this inside `check_body` itself.**
`tests/test_gates.py::t_pr_reference_phase1_does_not_gate_closing_
keywords_itself` pins the opposite (`check_body(126, "Closes #126",
"phase1") == []`) and states outright that this responsibility belongs to
`gates/ci.py::_phase1_mismatch`. Changing `check_body` breaks that pin and
crosses issue #228's owned boundary for no reason — `_phase1_mismatch`
already exists, correctly, with its own tests; the actual gap is that
nothing calls it anymore (its one caller, `gates/ci.py`'s `main()`, was
the GitHub Actions runner retired by issue #460). Porting its logic
inline into `pr-preflight.sh` — the same pattern issue #512 already used
for `accumulation-claim-guard.sh`/`call-shape-guard.sh` — restores a live
caller without touching `check_body`'s contract.

**`.finditer()`, not `.search()`.** The after-proposal warrant hunt
(stance 0, `docs/issue-741/reports/implementation/
hunt-2026-08-11-execution-provenance-and-phase1-closes-refusal.md`) found
the proposal's own draft wording pointed at this file's existing
`.search()` idiom, which stops at the first closing-keyword match even
when it names a *different* issue — `gates/ci.py::_closes_ref_for_issue`'s
own docstring documents hunting and fixing exactly this bypass once
already. The shipped check iterates every match via `.finditer()` and
only stops on one naming the PR's own issue, matching
`_closes_ref_for_issue`'s semantics without importing it (zero-install: no
`gates/` checkout assumed in the consumer repo).

## Known, accepted residual risk — the two hooks' phase signals can disagree

The before-landing warrant hunt (stance 1, same hunt-record file) found
that `contract-guard.sh`'s phase-2 test (`APPROVE issue-<n>/` prefix, any
role accepted — issue #312's deliberate choice: phase is a property of
the issue, not the role) and `pr-preflight.sh`'s phase-2 test (exact
`APPROVE issue-<n>/<branch-role>` match) can read the same issue's
approval comments and disagree, when a *different* role's approval
comment exists for the same issue. This divergence pre-dates this
delivery (documented as an open, deliberately-deferred gap in
`docs/issue-653/reports/architecture/survey.md` gap #1, and again in this
issue's own `docs/issue-741/decisions/phase2-signal-choice.md` "Scope
boundary" section) — issue #653's ADR reasoned it was safe to defer
because `pr-preflight.sh` never executes a merge or writes `Closes`
itself.

This delivery changes that reasoning's premise: `pr-preflight.sh` now
*does* have a deny path tied to its own phase computation. The hunt's
concrete scenario — a cross-role approval comment makes
`contract-guard.sh` compute phase2 while `pr-preflight.sh` computes
phase1 for the same issue, so `pr-preflight.sh`'s new check would refuse
a `gh pr edit` manually re-attaching `Closes #<issue>` after a
`contract-guard.sh` broker-attach failure — is real and reproduced, but
requires three preconditions together (a different role's approval
comment already exists on the issue; `contract-guard.sh`'s own `gh pr
edit` broker-attach has already failed once; a session then hand-retries
the identical edit), and its fix is exactly the phase-signal unification
`docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`
and `docs/issue-741/decisions/phase2-signal-choice.md` already scoped
out, twice, on separate investigations. This proposal's own re-
investigation found no new grounds to reopen that boundary either.
Accepted as a residual risk, not fixed here — recorded for whichever
future issue does take up the signal-unification gap.

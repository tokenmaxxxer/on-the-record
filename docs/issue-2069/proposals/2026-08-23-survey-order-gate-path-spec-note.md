---
status: proposed
files:
  - docs/specs/survey-conventions.md
  - docs/issue-2069/reports/implementation.md
---

## Request

`survey-order-gate` hardcodes the phase-1 survey path as
`docs/issue-<n>/reports/implementation/survey.md`, refusing every
non-`implementation` role's proposal write even though `board-gate.sh`
(contract v3 s11) forbids that same role from writing into another
role's `reports/implementation/` tree. Issue #2069 asks for the survey
path to be resolved per spawning role (`reports/<role>/survey.md`) or to
accept any `docs/issue-<n>/reports/*/survey.md`, with the tradeoff
stated, plus regression tests covering a non-implementation role's
phase-1 proposal write, run through the fast test tier.

## Constraints

- `docs/issue-2069/reports/implementation/survey.md` (this issue's own
  survey, written before this proposal) establishes that
  `survey-order-gate.sh` — like its sibling `proposal-shape-gate.sh`,
  already resolved identically by issue #638 — does not exist anywhere
  in this repository's history, is not registered in
  `on-the-record/hooks/hooks.json`, and is not reachable from
  `on-the-record/hooks/directive.sh` (which exits immediately for any
  role session, the only kind of session that files a phase-1
  proposal). It is external-harness tooling this repo does not package.
- No fabricated hook, stub script, or boundary-spec row for a mechanism
  this repo does not own — `gates/test_boundary.py` must not gain a row
  asserting a file that isn't real (same constraint #638 already applied
  to the sibling name).
- Regression tests must exercise real code in this repo. A test that
  imports or hand-rolls a copy of a gate that lives outside this repo
  would not regress against the actual gate's behavior — it would just
  encode this repo's guess and silently drift out of sync the moment the
  external harness changes.

## Rationale

Considered writing `on-the-record/hooks/survey-order-gate.sh` from
scratch inside this repo — implementing the per-role or any-role-glob
resolution issue #2069 asks for as new packaged gate code — and wiring
it into `hooks.json` plus a matching `PreToolUse` registration, with
regression tests against that new file. Rejected this: it would silently
convert a bug report about an *external* mechanism into a *different*
mechanism this repo invents and ships under the same name, which the
external harness (the thing actually producing the refusals in #2069's
tm-dicequest reproductions) would never load or run — the fix would look
complete in this repo's test suite while doing nothing to the surface
the issue is actually about, worse than leaving the report accurate.
This is the same choice #638 already made for the sibling gate name
`proposal-shape-gate.sh`, for the identical reason (empty git history,
absent from `hooks.json`, `directive.sh` structurally can't fire in a
role session) — landed in `docs/issue-638/reports/implementation.md`
(commit `43bd01a5`).

Also considered doing nothing beyond a record entry (pure "not our
code" note, no spec change). Rejected as incomplete: #2069 explicitly
asks for the path resolution to be *chosen*, with its tradeoff stated,
even though this repo can't enforce that choice mechanically. This repo
does own `docs/specs/` — the convention text a harness implementing this
gate should read. Recording the chosen resolution there gives the
external harness (or the next session reading this repo's specs) an
actual, tradeoff-justified answer to build against, instead of leaving
#2069's suggested direction as an unresolved list of two options in an
issue comment.

## What will be done

1. Add a "Phase-1 survey path" section to `docs/specs/survey-conventions.md`
   stating the chosen resolution: the survey path is role-scoped —
   `docs/issue-<n>/reports/<spawning-role>/survey.md` — never hardcoded
   to `reports/implementation/`, with the accept-any-role-glob
   alternative named and rejected (glob acceptance would let a session
   satisfy the gate by pointing at a *different* role's stale survey
   file, defeating the ordering norm's actual purpose: proving *this*
   session did its own research before drafting).
2. `docs/issue-2069/reports/implementation.md` (phase-2 record, written
   only after approval per contract v3 s19) will state that this repo
   contains no `survey-order-gate.sh` to patch and no reachable code
   surface to regression-test against, cite the survey's evidence, and
   record the spec-note addition as the actionable output — mirroring
   #638's resolution shape for the sibling gate name.
3. Run the fast tier from `.on-the-record/test-tiers.json` (if present)
   or record the tiering gap per the test-tier directive if absent, and
   fence the output in the phase-2 record.

## Out of scope

- Writing `on-the-record/hooks/survey-order-gate.sh` or any new gate
  code — there is nothing in this repo's history to restore, and
  fabricating it asserts a mechanism this repo does not own.
- Regression tests against the external gate's actual refusal behavior —
  not reachable from this repo; the phase-2 record will state this
  plainly rather than fabricate a test with nothing real behind it.
- Correcting any other repo's `on-the-record/` checkout or the external
  orchestrator's own source — out of this repo's write reach.
- Re-litigating issue #638's conclusion about `proposal-shape-gate.sh` —
  reused as precedent, not reopened.

## How you'll know it worked

- `docs/specs/survey-conventions.md` states the role-scoped survey path
  convention with the rejected alternative and its reason, in the same
  spec file the on-the-record convention already lives in.
- `docs/issue-2069/reports/implementation.md` names the evidence trail
  (empty git history, absent from `hooks.json`, `directive.sh`'s
  structural inability to fire in a role session) and states plainly
  that no code change or regression test in this repo can reach the
  actual gate.
- The fast test tier (or the tiering-gap note, if `.on-the-record/test-tiers.json`
  is absent) is fenced in the phase-2 record with an unchanged failure
  count relative to `main`, matching #638's precedent of showing zero
  new failures introduced.

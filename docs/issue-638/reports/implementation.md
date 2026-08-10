---
code_under_review:
  - docs/issue-638/reports/implementation.md
type: docs
breaking: false
verdict: resolved
loop_state: landed
---

## What was done

Audited `proposal-shape-gate.sh` and `survey-order-gate.sh`, the two hook
names #623's drive flagged as referenced-but-missing from the packaged
`on-the-record/hooks/` tree (finding 2, per issue #638).

Resolved answer: **both names are external-harness tooling, not a
packaging gap.** Evidence:

- `git log --all -- '**/proposal-shape-gate.sh' '**/survey-order-gate.sh'`
  returns empty — neither file has ever existed anywhere in this repo's
  history.
- `on-the-record/hooks/hooks.json` never lists either name.
- `on-the-record/hooks/directive.sh`, the plugin's only
  `UserPromptSubmit` injector, contains no reference to either name and
  provably cannot fire into a role session at all — it exits immediately
  when `CLAUDE_ROLE` is set (confirmed by reading the script directly).
- The two gate behaviors #600's session actually experienced are real,
  but they come from an external layer (the harness that spawns role
  sessions and injects directives) — the same layer observed firing in
  this very session under the same two names (`proposal-shape-gate.sh`,
  `survey-order-gate.sh`) via the `<proposal-shape-directive>` and
  `<survey-order-directive>` system reminders.

There is nothing in this repo to rename, restore, or stub. Fabricating a
hook and a boundary-spec row for it would assert a mechanism this repo
does not own and cannot enforce — worse than the stale reference it
would replace. This record is the corrected reference: it states plainly
that the two names name external-harness tooling, not `on-the-record`
package artifacts.

**Stale-claim sites named, not corrected from this branch:**

- `docs/issue-600/reports/implementation.md` lines 73, 83
- `docs/issue-623/reports/execution-observation.md` lines 39, 61, 130, 156

`board-gate.sh` (external harness hook, contract v3 s10) refuses any
write under `docs/issue-600/` or `docs/issue-623/` from branch
`issue-638/implementation` (confirmed by a direct Edit attempt on
`docs/issue-600/reports/implementation.md`, refused: "writing
docs/issue-600/ requires branch issue-600/implementation"). Correcting
those two files requires a session on each issue's own branch
(`issue-600/implementation`, `issue-623/implementation`) — out of #638's
reach from here, handed off explicitly rather than left silently
uncorrected.

Other occurrences of the two names elsewhere in `docs/` (#319, #245,
#547, #517, #363, #373, #419) were checked and are the standing
directive boilerplate text quoted verbatim in unrelated surveys/proposals
— not claims about file location, out of scope per the proposal.

## Why

Basis: `docs/issue-638/proposals/2026-08-10-resolve-gate-naming-reference.md`.
The proposal's Rationale already ruled out fabricating a hook/stub as
worse than the stale reference; this record executes exactly the
"correct the prose" path it chose.

## Boundary test (unchanged failure count)

```
$ python3 -m pytest gates/test_boundary.py
============================= test session starts ==============================
collected 10 items

gates/test_boundary.py F.........                                        [100%]

=================================== FAILURES ===================================
_________________________ t_all_gates_modules_recorded _________________________

    def t_all_gates_modules_recorded():
        bad = check()
>       assert not bad, "\n".join(bad)
E       AssertionError: remediation_spawn.py 가 docs/specs/enforcement-boundary.md 에 판정(verdict)이 기록된 행으로 없다 — 기록되지 않은 게이트가 조용히 존재한다(#441).

========================= 1 failed, 9 passed in 0.05s ==========================
```

Pre-existing, unrelated failure (`remediation_spawn.py` missing a
boundary-spec row, tracked at #441) — same failure, same count, before
and after this issue's change. This issue's change adds zero new
boundary-test failures.

## What did not work

None.

## Open findings

None.

## Hunt record

docs-only, no before-landing dispatch — every touched path in this
transition is under `docs/` (fast path per warrant directive).

## Doc-placement ladder

- [x] No env var / config key / new dep / migration / setup step
  introduced — nothing added to a handbook.
- [x] No library-or-format choice or changed public signature/wire
  format — no decisions entry needed.
- [x] No benchmark or investigation numbers produced — nothing beyond
  this record itself.

---
kind: implementation
code_under_review: 1245e87dc0000000000000000000000000000000
loop_state: coding
type: hardening
breaking: false
verdict: pending
---

# Implementation record — issue #2093 hook-crash class fix

Status: **phase 1 only**. This record exists at this point solely to carry the
skill-verdict lines that issue #2039 requires of every session (skill-verdict-guard
checks this path specifically). The delivered work is the phase-1 survey and proposal;
no code has been written, and this record will be rewritten as the real phase-2 record
once an approval per contract v3 s19 opens phase 2.

kind: implementation
loop_state: coding

## What was done

- Surveyed the current state of hook input parsing:
  `docs/issue-2093/reports/implementation/survey.md`.
- Scouted the field (platform hook semantics, total-parsing prior art, registry-driven
  conformance testing, shell-string parsing robustness):
  `docs/issue-2093/reports/implementation/scout-brief.md`.
- Wrote the proposal: `docs/issue-2093/proposals/hook-crash-class-fix.md`.
- Opened the phase-1 PR, https://github.com/tokenmaxxxer/on-the-record/pull/2095.

Doc-placement ladder outcomes:

- [x] survey → `docs/issue-2093/reports/implementation/survey.md` (phase-1 report home)
- [x] scout brief → `docs/issue-2093/reports/implementation/scout-brief.md`
- [x] proposal → `docs/issue-2093/proposals/hook-crash-class-fix.md`
- [x] record → `docs/issue-2093/reports/implementation.md` (this file, phase-1 stub)
- [ ] handbook update → `docs/handbooks/hooks.md` (phase 2)

## Why

The issue asks for a class fix, not an instance fix. Establishing what the class actually
is required reading the corpus first: the issue's stated premise (ad-hoc `json.loads` on
stdin per hook) turned out not to describe the code, and the real crash surface is
downstream of the decode. Proposing against the stated premise would have produced a
library nothing needed.

## Upstream

docs/issue-2093/reports/implementation/survey.md

## Open findings

- The ledger home is contested: the issue text names `runs/`, the only hook-authored
  precedent is `~/.claude/on-the-record/`. The proposal picks the latter and states why;
  an approver may overrule.
- `#2092` has not landed. If it lands before phase 2, this branch rebases onto it;
  otherwise proposal step 6 subsumes it. Either way it is a live coordination risk.
- The `runs/` directory line format was not read during the survey.

## Next steps

Wait for an approval per contract v3 s19. On approval, execute the proposal's steps 1-9
in order, holding step 7 (the `hooks.json` rewire) until step 5's conformance test is
green.

## Resolution path

Each open finding resolves inside phase 2: the ledger-home question resolves by the
approver either accepting the proposal's choice or naming `runs/` in review feedback; the
#2092 coordination resolves at rebase time against main; the `runs/` line format resolves
by reading it if and only if the ledger home is overruled to `runs/`.

## What did not work

None — no execution work has been attempted yet.

## Skill verdicts (issue #2039)

skill-verdict: implementation-blueprint — applied: invoked; classify routed
backend/no-external-callers/transform/sync to the pipeline archetype, which shaped
`hook_input.py` in the proposal as staged total transforms (raw -> payload -> command ->
cd-target), each independently testable with an explicit input/output shape and an
explicit error channel, and whose speculative-generality anti-pattern drove the
rule-of-three check (five real cd-extraction call sites migrate, not one).

skill-verdict: implementation-complexity-coupling-management — applied: invoked; rule 7
(encode a forbidden import direction as a checked rule at the point of introduction, not
after a cycle accumulates) became proposal step 8 — `hook_input.py` imports the standard
library only, never `gates/` and never another hook. Rule 6 (do not grow a low-cohesion
shared module) split the fail-open ledger out of the parser into a separate
`hook_ledger.py` rather than bolting it onto the parsing module.

skill-verdict: implementation-performance-data-structure-choice — applied: invoked; rule 4
(a fixed per-message cost linear-scales into the dominant cost at volume) applied to the
~522 real subprocess spawns implied by 58 `hooks.json` registrations x a 9-case corpus,
producing the `slow`-marker placement plus a fast-tier smoke subset over the five migrated
hooks, rather than one undifferentiated matrix in the default suite.

skill-verdict: implementation-design-pattern-selection — not-applicable: no GoF-style
pattern was under consideration; returning a typed failure from a total parse boundary is
a function-contract decision, not Strategy/Factory/Visitor/Observer/Decorator indirection.

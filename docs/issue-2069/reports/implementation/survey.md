# Survey: issue #2069 — survey-order-gate's hardcoded survey path

## Write surface checked

Searched for the gate `survey-order-gate.sh` (and its sibling
`proposal-shape-gate.sh`, referenced together in the same directive
family) anywhere in this repository.

canonical: `git log --all -- '**/survey-order-gate.sh' '**/proposal-shape-gate.sh'` (this session, repo root)

```
$ git log --all -- '**/survey-order-gate.sh' '**/proposal-shape-gate.sh'
(empty)
$ find . -iname "*survey-order-gate*" -not -path "*/.git/*"
(empty)
$ grep -n "survey-order-gate\|proposal-shape-gate" on-the-record/hooks/hooks.json
(no match)
```

canonical: `on-the-record/hooks/directive.sh:23` (read directly, this session)

`on-the-record/hooks/hooks.json` registers `on-the-record/hooks/directive.sh`
as the plugin's only `UserPromptSubmit` hook. It contains no reference to
either gate name, and cannot fire into a role session at all:

```
on-the-record/hooks/directive.sh:23:
[ -z "${CLAUDE_ROLE:-}" ] || { trap - EXIT; exit 0; }
```

A role session (the kind that files phase-1 proposals under
`docs/issue-<n>/proposals/`, the exact write path this issue is about)
runs with `CLAUDE_ROLE` set, so this hook exits before doing anything.

## Prior resolution of the identical question (issue #638)

canonical: `docs/issue-638/reports/implementation.md` (read directly, this session)

Issue #638 already audited this exact pair of names
(proposal at `docs/issue-638/proposals/2026-08-10-resolve-gate-naming-reference.md`,
landed as `docs/issue-638/reports/implementation.md`, commit `43bd01a5`).
Its finding, stated in that record: both names are external-harness
tooling, never packaged under `on-the-record/hooks/` — supported there
by empty `git log --all` history, absence from `hooks.json`, and
`directive.sh`'s structural inability to fire in a role session. That
same record notes its own session observed the identical
`<proposal-shape-directive>` / `<survey-order-directive>` system
reminders this session also received — evidence the directives are real
and firing, but from a layer this repo does not own or control: an
external orchestrator that spawns role sessions and injects
`UserPromptSubmit` directive text, separate from the packaged
`on-the-record/hooks/directive.sh`.

#2069's own reproductions (issue body, `gh issue view 2069`, this
session) are from a consumer repo (`tm-dicequest`), observed through
`spawn.py watch --follow` gate-refusal events from an orchestration
session — the same external harness layer #638 identified, not
`on-the-record`'s packaged gate code.

canonical: `grep -n "survey" spawn.py` (this session)

`spawn.py` in this repo references `survey.md` only in Korean-language
code comments citing past survey findings (`spawn.py:393,2469,3511,4209,
7867,8145,8772`) — none of these are gate logic.

canonical: `grep -rn "survey.md" gates/*.py roles/*.py` (this session)

Grepping `gates/*.py` and `roles/*.py` for survey-path logic that
hardcodes `reports/implementation/survey.md` and checks it against role
name returns nothing beyond one doc-comment citation
(`gates/accumulation.py:9`, not gate code).

## What this repo does and does not own

- **Does not own**: the mechanical gate that refuses a phase-1 proposal
  write when `docs/issue-<n>/reports/implementation/survey.md` is
  absent. No such file, hook registration, or check exists anywhere in
  this repository's history (evidence above).
- **Does own**: the directive *text* describing the survey-order norm,
  injected into this session as `<survey-order-directive>` (this
  session's own system reminders) but, per the `directive.sh` read
  above, not sourced from this repo's packaged hook.
- Consequence for #2069: there is no file in this repo whose code change
  would alter `survey-order-gate.sh`'s hardcoded path, and no regression
  test in this repo's suite can exercise that external gate's behavior
  — a test written against a mechanism this repo does not contain would
  either import nothing real or hand-roll a duplicate implementation
  divorced from whatever the external harness actually runs, which would
  drift out of sync silently.

## Skill verdicts (issue #2039 obligation)

canonical: `ls docs/issue-2069/reports/` (this session, repo root)

`ls docs/issue-2069/reports/` shows only the `implementation` directory
(this survey's own home) — the phase-2 record path referenced by
`skill-verdict-guard.sh` does not exist on disk yet, because this
session is phase-1 only: role-handoff contract v3 s19 withholds that
record until the human Approve, same as code. The per-skill verdict
obligation is recorded here instead, in this issue's phase-1 survey, and
will be restated in the phase-2 record once phase-2 opens:

- skill-verdict: implementation-complexity-coupling-management — not-applicable: no coupling/cohesion metric, accessor chain, cross-module import direction, or check-ordering decision arises in this docs-only proposal round.
- skill-verdict: implementation-design-pattern-selection — not-applicable: no code and no GoF-pattern decision; this issue produces a survey and a proposal document only.
- skill-verdict: implementation-performance-data-structure-choice — not-applicable: no data structure, algorithm, or communication-scheme choice arises in this round.
- skill-verdict: implementation-blueprint — not-applicable: no multi-module/file code is being structured; the deliverable is a spec-note addition to one existing markdown file.
- skill-verdict: observability-phase-trace — not-applicable: no phase-2 implementation record exists yet for this issue to check against its phase-1 methodology; this session is the phase-1 session itself.
- skill-verdict: model-routing — not-applicable: single-session investigation and two document writes with no delegation or model-tier decision to make.

## Skip-condition note (scout directive)

This issue's own suggested direction ("resolve the survey path
per-role... or accept any `docs/issue-<n>/reports/*/survey.md`") is a
design choice for the gate itself — but the gate is not code this repo
holds, so there is no design surface here to scout against exemplar
systems; scouting best-in-class gate design would inform a system this
repo cannot ship. Scouting is skipped under the scout-directive's second
skip condition ("the spec leaves no design decision open" — inverted
here: the decision exists but not in this repo's reach). The
choice-with-tradeoff the issue asks for is made in the proposal below at
the one place this repo can act: the spec text documenting the intended
convention for any harness implementing this gate.

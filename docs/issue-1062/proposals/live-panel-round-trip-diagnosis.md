---
status: proposed
files:
  - docs/issue-1062/reports/implementation/survey.md
  - docs/issue-1062/proposals/live-panel-round-trip-diagnosis.md
---

## Request

#1062: post-#1060 live re-run of the panel path reportedly still degraded with "no
SendMessage round-trip observed", and both degrade-path `consult_cmd()` calls reportedly
returned no judgment JSON. Diagnose with a bounded live reproduction (not unit stubs): why no
round-trip despite the retry-discovery prompt fix, and why both consult verdicts failed to
parse in that context. Fix what's fixable in `spawn.py`; if a platform constraint blocks
headless inbox messaging, ground it with transcript evidence and record the supported
alternative. Requirement linkage: R001 (req#5).

## Constraints

- No unit-stub reproduction — the diagnosis must come from actually running
  `spawn.py consult`/`spawn.py panel` as live `claude -p` subprocesses, per the issue's own
  "not unit stubs" instruction.
- Acceptance is satisfied by either a real `SendMessage` round-trip in the run record, or a
  grounded degraded run where both consult verdicts are real (non-error) — the record itself
  is checked by `gates/record_lint.py`.

## Rationale

Considered proposing a speculative code change to `_run_panel_session()`'s retry prompt or to
`consult_cmd()`'s timeout, on the theory that the originally-reported failure was a timing or
truncation defect. Rejected: this session's own bounded live reproduction (see survey) ran
both `consult_cmd()` and `panel_cmd()` against the current `main`-derived code twice and got a
real `SendMessage` round-trip and real, parseable verdicts both times — there is no
reproduced defect to target a code change at, and changing retry/timeout constants without a
reproduced failure mode risks masking a future real regression under an untested "fix." A
diagnosis session's job when the reported failure does not reproduce is to ground that finding
with live evidence, not to guess at a patch.

## What will be done

- Land this session's already-executed live evidence in the survey
  (`docs/issue-1062/reports/implementation/survey.md`), which cites the real panel round-trip
  record produced by `_append_panel_turn()` at `docs/issue-1062/reports/panel/rest-v1-v2.md`
  and the consult trace at `docs/issue-1062/reports/consult-log.md`. Those two files are
  `panel`/`consult` role output (contract v3 s11: `implementation` writes only
  `implementation.md`, `implementation/**`), so this role's commit does not stage them; they
  remain on disk as the artifacts this survey's citations point to.
- On phase-2 approval: write the phase implementation record
  (`docs/issue-1062/reports/implementation.md`) stating the diagnosis outcome — both reported
  failure modes did not reproduce live on current `main`; no `spawn.py` code defect was found
  to fix from this evidence; the issue's acceptance criterion (a live panel run whose record
  shows >=1 `SendMessage` round-trip) is satisfied by the `rest-v1-v2.md` record already
  produced this session.
- No change to `spawn.py` itself is anticipated — the write set is docs-only, consistent with
  there being no reproduced defect to fix.

## Out of scope

- Retroactively investigating the specific prior run referenced by the issue
  (`docs/issue-973/reports/panel/...`) — that record was never committed anywhere in this
  repo's history and cannot be recovered.
- Speculative hardening of `consult_cmd()`/`panel_cmd()` timeouts or retry counts absent a
  reproduced failure.
- Any change to the panel/consult CLI surface (already delivered under #1044/#1045).

## How you'll know it worked

```
python3 gates/record_lint.py docs/issue-1062/reports/panel/rest-v1-v2.md
```
passes, and the record shows `degraded: False` with `turns` present for both roles
(`position`, `rebuttal`, `verdict` lines for `role=architecture` and `role=api-design` in
`docs/issue-1062/reports/panel/rest-v1-v2.md`), satisfying the issue's stated acceptance: "A
live panel run whose record shows >=1 SendMessage round-trip."

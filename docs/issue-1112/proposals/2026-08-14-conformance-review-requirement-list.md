---
status: proposed
files:
  - docs/issue-1112/reports/conformance-review.md
---

## Intent

Extract the discrete, checkable requirement list for issue #1112 from
its own stated Problem/Acceptance text and northpole req#3 citation, so
phase 2 can render a per-requirement Present/Surface/Absent/Incorrect/
Unverifiable verdict against the landed fix (commit
be8cf825cc3b3cd2a5beee9e26d0eea51cc66b61, merged via PR #1119).

## Constraints

- Verdicts are phase-2 work, gated on human approval (contract v3 s19);
  this proposal states the requirement list only, no verdicts.
- Per docs/issue-1112/reports/conformance-review/survey.md, the target
  files are spawn.py and gates/test_consult_json_parse.py.

## Requirement list

R1 — Root cause identified. The regression's actual cause (not just a
symptom match to #1097) is named and traced to a specific code path.
Source: issue body, "Root-cause and fix so the failure cannot recur
silently."

R2 — Fix applied at the identified root cause. The code change actually
addresses R1's named cause, not a workaround elsewhere.
Source: issue body Problem section.

R3 — Regression guard exists and passes. `gates/test_consult_json_parse.py`
reproduces the cited 17:29 failure mode and, run against the fix,
does not report a failure.
Source: issue Acceptance, first `check:` bullet.

R4 — Regression guard is not merely a live smoke. The issue explicitly
distinguishes "a regression test" from "just a live smoke" — R3 must be
an executable, repo-committed unit test, not only a manual/live run.
Source: issue Problem section, "the fix must include a regression
guard, not just a live smoke."

R5 — Live smoke performed. `spawn.py consult requirements-engineering
"<tradeoff question>" -C <board repo>` is run and returns an `ok:`/`no:`
verdict line recorded in a consult trace.
Source: issue Acceptance, second `check:` bullet.

R6 — Failure cannot recur silently (northpole req#3 alignment).
Per northpole req#3 ("real-wired verification"): the fix must not
degrade the actual, real-wired consult path used for issue-drafting
validity checks — i.e. the guard/smoke must exercise the real
`consult_cmd()`/`role_settings()` wiring, not a mock standing in for it.
Source: issue body's "northpole req#3" line + Acceptance's empty-state/
provenance notes (`provenance: executed-unit`, `provenance:
executed-live`).

## Out of scope

Judging code quality, style, or scope beyond these six requirements;
re-running the regression suite or the live smoke (phase-2 work);
deciding whether the fix's chosen mechanism (`inject_self_hosted_hooks`
flag) was the best possible design — conformance review checks
presence/correctness against the stated requirement, not superiority of
approach.

## How you will know it worked

Phase 2 produces docs/issue-1112/reports/conformance-review.md with one
verdict row per R1–R6 above, each verdict traceable to an evidence
citation from the landed code or its records.

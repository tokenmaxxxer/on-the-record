---
status: proposed
subject: issue-2241
stage: 2
files:
  - consult.py
  - docs/specs/consult-guidance-source.md
  - test/test_consult_no_rulebook_identity_regression.py
---

# Stage 2 — confirm consult.py's guidance source, role identity stays exposed

## Request

Formally document and regression-guard that `consult.py`'s guidance
*content* resolution is unconditionally skill-repository sourced (per
issue #1955), and make explicit that `role` identity remains exposed as
a lookup *key* in this stage — that exposure is not this stage's defect
to fix; it's stages 4 and 6's work.

## Constraints

- Frozen decision `single-skill-axis`: this stage must not introduce
  any new role-shaped lookup structure while narrowing the existing one.
- Must not touch `_ROLE_SKILLS` (`skills.py:286-330`) or the
  `roles/<role>.json` existence-check call sites in `consult.py` — the
  issue's own staging places renaming/removing that key at stages 4
  and 6, not here (see Rationale).

## Rationale

Chosen: this stage's scope is confirmation plus regression coverage,
not new removal work — this survey (`docs/issue-2241/reports/architecture/survey.md`,
section 5) found that #1955 already executed the "resolves its
judgment source from skill-repository" half of this stage's stated
goal; `consult.py:470-471,484` and `skills.py:333-355`
`resolve_role_source()` carry no allowlist branch today. Rejected
alternative: also migrate `_ROLE_SKILLS`'s key from role to skill name
in this same stage, since the work is adjacent and "already being
touched." Rejected because that key-migration is exactly stage 4's
branch/record-naming concern and stage 6's deletion concern; jumping
the staging order here risks the same premature-cutover failure mode
issue #2241's own text attributes to incidents #2233/#2238 — doing
naming work before the concepts stage 1 lands are proven wired through
the rest of the system.

## What will be done

- `docs/specs/consult-guidance-source.md`: a short spec stating, with
  citation to `consult.py:470-471,484` and `skills.py:333-355`, that
  guidance content resolution is unconditional skill-repo for every
  role, and that this is the state stage 2 confirms rather than
  changes.
- `test/test_consult_no_rulebook_identity_regression.py`: asserts no
  code path in `consult.py` reads a rulebook/plugin-repo identity for
  guidance content (a regression guard against re-introducing the
  allowlist branch #1955 removed).
- No change to `_ROLE_SKILLS` or the `roles/<role>.json`
  existence-check validation — both stay as-is, explicitly, with a
  code comment in `consult.py` pointing at this stage's proposal and
  naming stages 4/6 as where they change.

## Out of scope

- Migrating `_ROLE_SKILLS`'s key shape (stage 4).
- Removing the `roles/<role>.json` existence-check (stage 6, after
  `roles/*.json` itself is retired).
- Any change to `board-gate.sh` or `merge_gate.py`.

## How you'll know it worked

- `test/test_consult_no_rulebook_identity_regression.py` passes,
  proving no regression toward the pre-#1955 allowlist path.
- `docs/specs/consult-guidance-source.md` exists and its citations
  resolve against the current `consult.py`/`skills.py` line ranges.
- No behavior change to `consult.py`'s output for any existing caller
  (existing consult tests pass unmodified).

## Rollback

Revert the spec file and the new regression test; `consult.py` itself
is untouched by this stage's actual code changes (the regression test
only asserts existing behavior), so rollback has no runtime effect.

## Accumulation

`consult.py` already carries 10 inline subprocess/gh call sites,
none added by this stage — the new regression test exercises existing
call paths, adding no new ones. If a future stage needed N more
guidance-source assertions here, each should extend this stage's one
regression-test module rather than scattering N new ad hoc test files
making the same claim.

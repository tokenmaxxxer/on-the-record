files:
  - roles/interaction-design.json

## Request

`test_gates.py::t_new_roles_resolve_without_a_local_checkout` fails on main
in a clean worktree. Diagnose root cause and either fix the behavior or
correct the test, with reasoning recorded, so `python3 -m pytest -q` is
fully green.

## Constraints

- Pure bugfix per docs/issue-541/reports/implementation/survey.md — no
  design decision open, scout sweep skipped per scout-directive's skip
  condition.
- Must not touch the other two github-only roles
  (`defect-verification.json`, `issue-retrospective.json`), which already
  match the test's expectation.
- Must not weaken or delete the test — the test's docstring states its
  purpose (on-the-record's github-fallback path needs at least one real
  exercising case) still holds.

## Rationale

Root cause is `roles/interaction-design.json` carrying a `"path"` key,
added by commit `88baa3e` under the description "fixes
interaction-design.json's missing 'path' key" — that commit treated the
absence of `path` as an omission, not knowing this role was one of the
three intentional no-local-checkout exemplars the test locks in.

Two paths were open:
1. **Fix the behavior** — drop `"path"` from `interaction-design.json`,
   restoring the file to what the test (and `spawn.rulebook_source`'s
   github-fallback branch) already expects.
2. **Correct the test** — drop `interaction-design` from the test's role
   list, accepting that it now resolves via local checkout like the other
   40 roles.

Rejected (2) because the test's own docstring gives a load-bearing reason
for exactly three github-only roles: "github 폴백이 실제로 필요한 첫
사례이고, 없으면 on-the-record 가 계약 §3 의 아홉 줄 중 셋을 못 띄운다" — the
github-fallback code path in `spawn.py` needs at least one role actually
exercising it end-to-end, not just the two currently spared. Nothing in
issue #541 or the repo history says that requirement was deliberately
retired — commit `88baa3e`'s own message shows it was an accidental
side-effect of a batch role-spec pass, not an intentional design change.
Chose (1): a single-key removal that restores the previously-intended,
still-documented behavior.

## What will be done

- Remove the `"path"` key from `roles/interaction-design.json`, leaving
  `marketplace`/`repo`/the rest of the spec untouched, so it matches the
  shape of `defect-verification.json` / `issue-retrospective.json`.
- Record the root cause and decision in the phase-2 implementation record
  (docs/issue-541/reports/implementation.md).

## Out of scope

- Any change to `spawn.py`'s `rulebook_source`/`rulebook_dir` logic — it
  already handles the no-`path` case correctly.
- Any change to `defect-verification.json` or `issue-retrospective.json`.
- Any change to `test_gates.py` itself.

## How you'll know it worked

- `python3 -m pytest -q test_gates.py::t_new_roles_resolve_without_a_local_checkout`
  passes.
- `python3 -m pytest -q` is fully green in a clean worktree (acceptance
  criterion from issue #541).

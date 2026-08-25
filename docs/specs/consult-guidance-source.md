---
name: consult-guidance-source
---

# `consult.py`'s guidance-content source

## What this confirms

Every `consult.py` call site that decides which plugin/skill directories
to load for a role's guidance *content* resolves that content
unconditionally through `skills.resolve_role_source()`. There is no
branch anywhere in `consult.py` that reads a rulebook/plugin-repo
identity or an allowlist file to decide guidance content — issue #1955
already retired that path repo-wide.

This is stage 2 of the role-axis retirement program (#2241). It
confirms and regression-guards the state #1955 already put in place; it
does not change `consult.py`'s behavior.

## Call sites

`consult.py` calls `resolve_role_source()` at exactly three places:

- `consult.py:690` — inside `consult_cmd()`, resolving the plugin
  directories for a direct consult session:
  `plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]`
- `consult.py:964` — inside `_readonly_plugin_dirs()`, resolving the
  plugin directories a judge session mounts read-only:
  `out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])`
- `consult.py:1357` — inside the panel/messaging consult path, the same
  resolution as `consult_cmd()`'s:
  `plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]`

None of the three branches on whether `role` is present in
`_ROLE_SKILLS`, whether a local rulebook checkout exists, or any other
identity signal — each unconditionally calls `resolve_role_source()`
and uses its `skill_dirs`.

## The resolution function

`skills.py:354-376` defines `resolve_role_source()`. Its body:

- `skills.py:366` — `names = _sp._ROLE_SKILLS.get(role, [])`: a role
  absent from `_ROLE_SKILLS` resolves to an empty name list, not to a
  different (rulebook) source — "unmapped role" is not a distinct
  runtime state.
- `skills.py:367` — `skill_dirs = _sp.resolved_skill_dirs(",".join(names), repo_root)`:
  every name resolves against the skill-repository, unconditionally.
- `skills.py:368-373` — any resolved directory carrying a `hooks/`
  subdirectory fails closed (`sys.exit`) before a workspace/branch is
  created, enforcing the frozen skill-repository-is-guidance-only
  invariant (#1758) rather than falling back to a rulebook mount.
- `skills.py:374-376` — the return shape is always
  `{"source": "skill-repo", "skill_dirs": [...], "skills": [...],
  "skill_sha": ...}`; there is no `"source": "rulebook"` (or similar)
  value this function can ever return.

## What this does not change

- `_ROLE_SKILLS` (`skills.py:286-337`) — its key stays `role`, not skill
  name. Migrating that key is stage 4 of #2241, not this stage.
- The `roles/<role>.json` existence-check call sites in `consult.py`
  (five in total: `consult.py:403`, `consult.py:738`, `consult.py:864`,
  `consult.py:1203`, `consult.py:1352`) — these stay exactly as they
  are; removing them waits on stage 6, after `roles/*.json` itself is
  retired. A code comment at the first call site (`consult.py:397-402`)
  points back at this stage's proposal and names stages 4/6 as where
  they change.
- `consult.py`'s output for any existing caller — this stage adds no
  new call path and removes none; `resolve_role_source()` itself is
  untouched.

## Regression coverage

`test/test_consult_no_rulebook_identity_regression.py` guards against
this state regressing:

1. A static scan of `consult.py`'s source text for identifiers the
   #1955 commit (`5494b62b`) deleted from `spawn.py`
   (`rulebook_checkout`, `checkout_version`, `ensure_rulebook`,
   `rulebook_source`, `rulebook_dir`, `_role_source_allowlist`,
   `rulebook_version`) — none may reappear.
2. A behavioral check that `_readonly_plugin_dirs()` reaches
   `resolve_role_source()` the same way whether `role` is present in
   `_ROLE_SKILLS` or not — "mapped" and "unmapped" never diverge into
   different resolution code paths.

## Role identity — deferred, not fixed here

`role` stays exposed as the lookup key into `_ROLE_SKILLS` and as the
filename stem under `roles/*.json`. That exposure is not a defect this
stage fixes: renaming/removing that key is stage 4's and stage 6's
work (see `docs/issue-2241/proposals/2026-08-25-stage-2-consult-skill-source-confirmation.md`,
Rationale). This stage's scope is confirmation of guidance-*content*
resolution plus regression coverage, nothing else.

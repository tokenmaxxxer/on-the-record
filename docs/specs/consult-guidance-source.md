---
name: consult-guidance-source
description: >
  Confirms consult.py's guidance-content resolution is unconditionally
  skill-repository sourced for every role (issue #1955), and states
  that `role` identity staying exposed as a lookup key is a known,
  deferred concern — not a defect this stage fixes (issue #2241 stage
  2, stages 4/6 own the key-shape/removal work).
---

# consult.py's guidance source

## Claim

Every call site in `consult.py` that assembles the plugin directories
for a consult/judge/panel session resolves guidance content through
`skills.resolve_role_source()` (reached via `consult.py`'s `_sp` proxy
to `spawn.py`, which imports `skills`), unconditionally. There is no
allowlist branch, no rulebook checkout, and no plugin-repo identity
read in that path today.

- `skills.py:354-375` — `resolve_role_source(role, repo_root)` looks
  `role` up in `_ROLE_SKILLS` (`skills.py:286-336`), resolves the named
  skills against the skill-repository, and unconditionally returns
  `{"source": "skill-repo", ...}`. There is no second branch: an
  unmapped role resolves to zero skills, not to a different source.
- `consult.py:642` — `plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]`,
  the line consult_cmd() builds its plugin list with.
- `consult.py:916` — `out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])`,
  the same call inside _readonly_plugin_dirs() (used by the judge path).
- `consult.py:1309` — `plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]`,
  the same call again inside _run_panel_session(); its docstring
  (`consult.py:1294` mentions `resolve_role_source()`, through line
  1296) notes the call is deliberately identical to consult_cmd()'s to
  avoid the two paths drifting apart.

This is the state issue #1955 (phase 2, commit `ac4d56a0`) put in
place — it deleted `rulebook_checkout`, `_role_source_allowlist`,
`checkout_version`, and `docs/specs/role-source-allowlist.json`
entirely. Stage 2 does not change any of the above; it documents it
and adds a regression guard (`test/test_consult_no_rulebook_identity_regression.py`)
against the allowlist branch reappearing.

## What stays exposed, on purpose

`role` remains a lookup *key* in two places `consult.py` still touches
unconditionally in this stage:

- `_ROLE_SKILLS` (`skills.py:286-336`) — keyed by role name, not skill
  name.
- The roles/*.json existence check (`consult.py:355`, `690`,
  `816`, `1155`, `1304`) — still validates that a `role` string names a
  known `roles/*.json` file before doing anything else.

Neither is this stage's defect to fix. Per the frozen decision
`single-skill-axis` and the issue #2241 staging order, migrating
`_ROLE_SKILLS`'s key shape is stage 4's work and removing the
`roles/<role>.json` existence check (once `roles/*.json` itself is
retired) is stage 6's. `consult.py` carries an inline comment at the
first existence-check call site pointing back here.

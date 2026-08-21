---
status: proposed
files:
  - spawn.py
  - roles/accessibility.json
  - roles/api-design.json
  - roles/architecture.json
  - roles/brand-design.json
  - roles/capacity-planning.json
  - roles/conformance-review.json
  - roles/content-design.json
  - roles/customer-support.json
  - roles/data-engineering.json
  - roles/data-modeling.json
  - roles/defect-verification.json
  - roles/devrel.json
  - roles/execution-observation.json
  - roles/finance-unit-economics.json
  - roles/growth-analytics.json
  - roles/implementation.json
  - roles/incident-response.json
  - roles/interaction-design.json
  - roles/issue-retrospective.json
  - roles/knowledge-management.json
  - roles/legal-compliance.json
  - roles/localization.json
  - roles/market-analysis.json
  - roles/marketing.json
  - roles/ml-engineering.json
  - roles/observability.json
  - roles/partnerships-bd.json
  - roles/performance-engineering.json
  - roles/pr-communications.json
  - roles/pricing.json
  - roles/product-discovery.json
  - roles/refactoring-legacy.json
  - roles/release-engineering.json
  - roles/requirements-engineering.json
  - roles/risk-management.json
  - roles/sales.json
  - roles/secure-coding.json
  - roles/security-threat-model.json
  - roles/technical-feasibility.json
  - roles/technical-writing.json
  - roles/test-authoring.json
  - roles/upstream-defect-report.json
  - roles/user-discovery.json
  - roles/ux-engineering.json
  - docs/specs/role-source-allowlist.json
  - test/test_spawn_role_skill_resolution.py
---

## Request

Retire the transitional role-source-allowlist mechanism (issue #1758)
and the rulebook resolution path it wrapped in spawn.py, per the frozen
constraint in docs/issue-1758/proposals/role-skill-resolution.md ("this
mapping is explicitly removed in phase 5"), which the phase-5 cycle
(#1792-#1827) never actually picked up. After this change every role
resolves unconditionally from skill-repository; the rulebook
clone/mount path and the allowlist file disappear.

## Constraints

- Acceptance check 1: `python3 -m pytest
  test/test_spawn_role_skill_resolution.py
  test/test_spawn_skills_mount.py -q` must pass with
  `docs/specs/role-source-allowlist.json` deleted from the repo.
- Acceptance check 2: `grep -rn
  "role-source-allowlist\|rulebook_checkout" spawn.py` must return no
  role-resolution call sites; `core_root()`'s managed-clone machinery
  for tokenmaxxxer-core is exempt and untouched.
- `grep` over `roles/*.json` must find no `marketplace`, `repo`, or
  `path` key after the change.
- Roster/record entries must keep carrying the resolution source (now
  always skill-repo + sha) — no record-shape regression for consumers
  of `resolution_source`/`resolution_skills`/`resolution_skill_sha`.
- `core_plugin_dirs()`/`core_root()`/`core_version()` (the core
  managed-clone path) must be untouched — the issue text names this
  exemption explicitly.
- Write set is spawn.py + `roles/*.json` + the allowlist spec file +
  the allowlist-only test file. No other module reads these role-source
  fields (survey: `grep -rn "ROOT / \"roles\""` in spawn.py, its only
  live-path hit).

## Rationale

**Chosen approach**: make every role resolve unconditionally to
`{"source": "skill-repo", ...}` and delete
`_role_source_allowlist()`/`resolve_role_source()`'s rulebook branch,
`rulebook_checkout()`, `plugin_dirs()`, `checkout_version()`, and the
`docs/specs/role-source-allowlist.json` file, exactly as the issue's own
"Direction" section already specifies.

**Rejected alternative — fail-closed on a missing allowlist file**: keep
`resolve_role_source()`'s shape, but instead of the current "no mapping
-> rulebook" default, exit non-zero when a role has no allowlist entry.
This was the actual live alternative going into #1955 — it's what
"retire the allowlist file" could naively mean if read as "the file's
absence should now be an error" rather than "the file and its whole
mechanism go away." It's rejected because it does not retire the
transitional mechanism at all: it keeps `_role_source_allowlist()`,
keeps a role-resolution branch point, and keeps a distinguishable
"mapped" vs. "unmapped" code path — it just flips which branch is the
error case. The issue's own text calls this out directly: fail-closed
"would relocate the transitional mechanism's gatekeeping rather than
retire it." A future engineer reading `resolve_role_source()` under
fail-closed would still need to understand two sources and a gate
between them, which is precisely the surface #1758 promised to remove
in phase 5.

**Rejected alternative — leave `roles/*.json` marketplace/repo/path
fields in place, only stop reading them**: this would minimize the diff
(spawn.py-only change) but leaves 43 files carrying dead, misleading
fields that point at archived, read-only rulebook repos (survey: all 43
`tokenmaxxxer/*-rulebook` GitHub repos are archived, per the issue body)
— exactly the "silent-staleness vector" the issue is being filed to
close. Dead config that still looks live is worse than no config; the
issue's own item 2 explicitly asks for field removal, not deprecation-in-
place.

## What will be done

1. In spawn.py, `resolve_role_source()` drops the allowlist lookup and
   unconditionally returns `{"source": "skill-repo", "skill_dirs": [...],
   "skills": [...], "skill_sha": ...}` for every role, still routed
   through `resolved_skill_dirs()` for name-resolution and the existing
   `hooks/`-subdirectory fail-closed check (both already present in
   today's mapped branch — carried over unchanged, not reinvented).
2. `_role_source_allowlist()` is deleted; `docs/specs/role-source-
   allowlist.json` is deleted (already absent from the repo per the
   acceptance check's own premise, but this proposal also removes any
   reference to loading it).
3. `rulebook_checkout()`, `plugin_dirs()`, and `checkout_version()` are
   deleted — their only call sites are the `_spawn_one()` role-resolution
   branch this issue collapses to one path.
4. In `_spawn_one()`, the `mapped =` branch-condition and the `plugins =
   [] if mapped else plugin_dirs(...)` conditional collapse to always
   `plugins = []` for roles (rulebook plugin dirs never mount for a
   role again); the `rulebook_desc`/`rulebook_sha_value` conditional
   collapses to the mapped-branch's existing skill-repo string/None,
   dropping the `checkout_version()` call entirely.
5. `roles/*.json`: drop `marketplace`, `repo`, and `path` keys from all
   43 files — spawn.py is their only live consumer (survey-verified).
6. `_role_source_roster_fields()` keeps its current shape but its
   `rulebook`-source branch becomes unreachable dead code and is removed
   along with the `rulebook_sha` parameter, since `role_source["source"]`
   is now always `"skill-repo"`.
7. `test/test_spawn_role_skill_resolution.py` is deleted — every test in
   it targets a symbol being removed (`_role_source_allowlist`,
   `resolve_role_source`'s rulebook branch, the mapped/unmapped mount-
   layout distinction). Its acceptance-relevant coverage (mount layout has
   no rulebook plugin dir, fail-closed on unknown/hooked skill names,
   roster fields carry resolution_source) is preserved by adding
   equivalent unconditional-resolution assertions to
   `test/test_spawn_skills_mount.py` or a like-for-like replacement file
   — exact placement is a phase-2 implementation decision, not frozen
   here.
8. `spawn.py update` and `rulebook_version()` (survey: dead/reachable-
   only CLI surface reading the same `roles/*.json` fields, no live
   caller in the spawn path) are also removed in the same change — once
   `roles/*.json` loses `marketplace`/`repo`/`path`, they raise
   `KeyError` on next invocation, so leaving them in place would ship
   newly-broken CLI surface rather than retire it. `ensure_rulebook()`
   (survey: already zero call sites) is removed as the same class of
   now-fully-dead code.

## Accumulation

This touches all 43 `roles/*.json` files with the same one-shot edit
(drop `marketplace`/`repo`/`path`), and it is the last time this file
set needs that kind of edit: after this change no code path reads those
three keys, so a role added later (roles/*.json #44, #45, ...) never
carries them in the first place — nothing is left to accumulate on this
axis. If a future issue needs a different field removed or added across
all role files again, the right move is the same kind of direct
mechanical pass used here, not a new indirection layer introduced to
avoid touching 43 files — per this issue's own premise, an indirection
layer built "to avoid the accumulation" is exactly what produced the
allowlist mechanism this issue exists to retire.

## Out of scope

- `core_root()`, `core_version()`, `core_plugin_dirs()` and the
  tokenmaxxxer-core managed-clone path — explicitly exempted by the
  issue text.
- `doctor()` — unrelated probe-plugin mechanism, no role-source or
  rulebook symbol in its body (survey-verified).
- Any change to which skills map to which role, or to skill-repository
  content itself (e.g. `docs/issue-1758/...`, skill-repository commit
  pins) — this issue only removes the now-redundant conditional
  resolution logic, not the skill-repo guidance mapping already in
  effect for every role.
- Archiving or otherwise touching the 43 `tokenmaxxxer/*-rulebook`
  GitHub repos themselves — they stay archived and untouched; this issue
  only stops spawn.py from cloning/reading them.

## How you'll know it worked

- `python3 -m pytest test/test_spawn_role_skill_resolution.py
  test/test_spawn_skills_mount.py -q` passes with
  `docs/specs/role-source-allowlist.json` deleted from the repo — under
  this proposal `test_spawn_role_skill_resolution.py` itself is deleted
  in phase 2, so this check is satisfied by the file's absence plus
  `test_spawn_skills_mount.py`'s continued pass (and any replacement
  coverage added per item 7 above).
- `grep -rn "role-source-allowlist\|rulebook_checkout" spawn.py` returns
  no role-resolution call sites (core managed-clone references exempt).
- `grep` over `roles/*.json` finds no `marketplace`, `repo`, or `path`
  key.
- A dry-run spawn against a target repo with no
  `docs/specs/role-source-allowlist.json` resolves every role
  `source=skill-repo` and creates no `runs/rulebooks/<role-marketplace>`
  clone.

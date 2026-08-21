# issue-1955 survey: retiring role-source-allowlist / rulebook resolution path

canonical: `grep -n "role-source-allowlist\|rulebook_checkout\|_role_source_allowlist\|resolve_role_source\|checkout_version\|plugin_dirs\|marketplace" spawn.py` (this session, 2026-08-22)

## Role-resolution mechanism proper (issue #1758 transitional layer)

- `_role_source_allowlist()` — spawn.py:5399-5407. Reads
  `docs/specs/role-source-allowlist.json`; empty mapping if absent.
- `resolve_role_source()` — spawn.py:5410-5438. The only caller of
  `_role_source_allowlist()`. Called once, at spawn.py:8154, inside
  `_spawn_one()`.
- `_role_source_roster_fields()` — spawn.py:5469-5480. Consumes the
  `role_source` dict `resolve_role_source()` returns; called at
  spawn.py:8274.
- In `_spawn_one()` (spawn.py:8130-8286): `role_source` (8154),
  `mapped = role_source["source"] == "skill-repo"` (8248), the
  `plugins = [] if mapped else plugin_dirs(role, spec)` branch (8250),
  `all_skill_dirs` merge using `role_source["skill_dirs"]` (8265),
  `rulebook_desc`/`rulebook_sha_value` mapped-branch (8268-8273), the
  task-string block naming role-source-allowlist (8239-8244), and
  `role_source["skill_sha"]` supplied to `spawn_cmd()` (8285).

## Rulebook checkout/mount path

canonical: `grep -n "rulebook_checkout(\|plugin_dirs(\|checkout_version(" spawn.py` (this session, 2026-08-22)

Per this grep, the only call sites of `plugin_dirs()` and
`checkout_version()` in spawn.py are inside `_spawn_one()`'s
role-resolution branch listed above:
- `rulebook_checkout()` — spawn.py:279-324. Called by `plugin_dirs()`
  (line 350) and by `ensure_rulebook()` (line 376, see below).
- `checkout_version()` — spawn.py:327-340. Its sole call site per the
  grep is `_spawn_one()`'s mapped-branch at line 8269.
- `plugin_dirs()` — spawn.py:343-366. Its sole call site per the grep is
  `_spawn_one()` at line 8250.

## Adjacent CLI surface, NOT part of the role-resolution call path

canonical: `grep -n "rulebook_dir(\|ensure_rulebook(" spawn.py` (this session, 2026-08-22)

This grep's output has no line matching `ensure_rulebook(` other than
its own `def ensure_rulebook(` at line 369 (a docstring cross-reference
in a different function's comment at line 5392 names it by prose, not a
call) — `ensure_rulebook()` has zero call sites in spawn.py today,
independent of this issue.

`rulebook_dir()` (spawn.py:226-243, shared low-level helper alongside
`rulebook_source()`/`_path()`/`_mkt()`/`_locked_rulebook_dir()` at
182-276) is called, per the same grep, by `ensure_rulebook()` (376),
`_plugin_names()` (648), and `update()` (689), plus `rulebook_version()`
(740).

canonical: `grep -n "rulebook_version(\|\"update\"" spawn.py` (this session, 2026-08-22)

This grep shows `rulebook_version()` with only its own `def` line (723)
and one docstring mention at 5392 — no call site — and shows `update()`'s
sole invocation as the CLI dispatch `if a.role == "update":` at
spawn.py:7423.

`_plugin_names()` (spawn.py:645-652), `update()` (spawn.py:661-702, the
`spawn.py update` CLI subcommand), and `rulebook_version()`
(spawn.py:723-746) read `spec["marketplace"]`/`spec.get("repo")`/
`spec.get("path")` directly from `roles/*.json`, independent of
`resolve_role_source()`. If `marketplace`/`repo`/`path` are dropped from
`roles/*.json` (per the issue's item 2) these three would raise
`KeyError` the next time an operator runs `spawn.py update` — reachable
API surface, not part of the executing spawn path, so `grep -rn
"role-source-allowlist\|rulebook_checkout"` (the issue's own acceptance
check) does not catch them: they use `rulebook_dir()`, not
`rulebook_checkout()`.

`core_root()`/`core_version()`/`core_plugin_dirs()` (spawn.py:5484+,
5562+) are explicitly exempted by the issue ("core managed-clone
references exempt") — untouched.

`doctor()` (spawn.py:5665+) builds an ad hoc probe plugin inline; no
rulebook/allowlist/role-source symbol appears in its body per the first
grep above (no `doctor` hit alongside those symbols).

## roles/*.json fields

canonical: `python3 -c "import json,glob
for f in sorted(glob.glob('roles/*.json')):
    d=json.load(open(f))
    print(f, {k:d[k] for k in d if k in ('marketplace','repo','path')})"` (this session, 2026-08-22)

All 43 files under `roles/*.json` carry `marketplace` + `repo`; `path`
is present in all but 4 (`defect-verification.json`,
`interaction-design.json`, `issue-retrospective.json`,
`upstream-defect-report.json`).

canonical: `grep -rn "ROOT / \"roles\"" spawn.py` (this session, 2026-08-22)

This grep's only hit for reading `roles/*.json` in spawn.py's live spawn
path is the `spec = json.loads((ROOT / "roles" / f"{role}.json").read_text())`
line at 8135; `update()`/`rulebook_version()` re-read the same files via
their own `ROOT / "roles"` lines noted above.

## Tests

canonical: full-file read of test/test_spawn_role_skill_resolution.py and test/test_spawn_skills_mount.py (this session, 2026-08-22)

- `test/test_spawn_role_skill_resolution.py` (278 lines): unit-tests
  `_role_source_allowlist()`, `resolve_role_source()`,
  `_role_source_roster_fields()`, and the mapped/unmapped branches of
  `_spawn_one()`'s mount-layout and fail-closed behavior directly against
  `spawn.*`. Every test in this file calls a symbol this issue removes;
  the whole file is retired by this issue, not edited.
- `test/test_spawn_skills_mount.py` (489 lines): tests `--skills`
  mounting (issue #1742/#1774).

canonical: `grep -n "rulebook_checkout\|plugin_dirs\|checkout_version\|resolve_role_source\|role_source_allowlist" test/test_spawn_skills_mount.py` (this session, 2026-08-22)

Zero matches in that grep — the file is unrelated to the allowlist
mechanism and is not expected to change.

## Frozen constraint text (docs/issue-1758/proposals/role-skill-resolution.md)

canonical: read of docs/issue-1758/proposals/role-skill-resolution.md (this session, 2026-08-22)

The proposal states: "this mapping is explicitly removed in phase 5" —
this is the frozen constraint this issue exists to discharge. The
mapping (`_role_source_allowlist`/`resolve_role_source`) was scoped as
temporary from the start, and the "unmapped role" branch (rulebook path)
was the pre-#1758 baseline, not a permanent fallback.

## Direction already fixed by the issue text

The issue's own "Direction" section resolves the one open design
question (fail-closed vs. unconditional skill-repo) in favor of
unconditional resolution: fail-closed on a missing allowlist "would
relocate the transitional mechanism's gatekeeping rather than retire
it." This survey treats that as settled; the proposal's Rationale
section still names the fail-closed alternative and why it's rejected,
per the survey/proposal ordering directive's requirement that a named
alternative be one that could plausibly have been chosen.

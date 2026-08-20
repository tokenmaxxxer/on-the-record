---
status: proposed
files:
  - spawn.py
  - test/test_spawn_skills_mount.py
---

## Request

Issue #1742 (skill-axis program phase 1): give `spawn.py` an additive
`--skills a,b,c` flag that mounts named skills from a local
skill-repository checkout (`MUSTER_SKILL_REPO` env, or a sibling-clone
default) into the spawned session's workspace, alongside the existing
rulebook + core plugin-dir mounts. Requirements, verbatim from the
issue:

1. `--skills` mounts named skills into the session's workspace
   (`.claude/skills/` or a minimal plugin dir — implementer's choice);
   without `--skills`, spawn argv/env/workspace stay byte-identical to
   today.
2. An unknown skill name is a hard error before any session starts
   (fail-closed), listing available names.
3. When `--skills` is used, the roster entry and the co-injected
   directive text both carry the skill list + the skill-repository
   checkout's commit SHA.
4. Out of scope for this issue (later phases): hook promotion to core,
   rulebook-skill migration/archival, and any change to branch naming,
   APPROVE grammar, board records, or the role taxonomy.

## Constraints

- Zero-bug convention condition (operator hard constraint): without
  `--skills`, every code path this proposal touches must produce
  byte-identical argv, env, and workspace layout to pre-change
  `spawn.py`. No convention consumer (branch naming, APPROVE grammar,
  board, taxonomy) may be touched — confirmed nothing in the touched
  functions writes those surfaces (survey: spawn.py:343-366,
  spawn.py:5385-5455, spawn.py:7893-7901).
- Unknown skill name must fail before workspace/branch creation
  (spawn.py:7811 `plugin_dirs()` and the workspace/branch setup that
  precedes it in the `spawn` subcommand run before `spawn_cmd()` is
  called) — the skill-name validation must run at or before that same
  point, not after Popen.
- Reuse only the two in-repo patterns the issue's design-research line
  names: the `resolved_role_model(cli_model=None)` optional-trailing-
  parameter precedence shape (spawn.py:5367-5382), and the rulebook
  `--plugin-dir` local-mount shape (spawn.py:343-366). No new external
  mechanism.

## Rationale

**Mount location: `.claude/skills/` copy vs. a minimal `--plugin-dir`.**
Chosen: mount each named skill as a `--plugin-dir` pointing directly at
its directory inside the skill-repository checkout (same shape as
`plugin_dirs()`'s rulebook mount, spawn.py:343-366) — no copying, no
plugin.json synthesis. Rejected alternative: copy each skill's files
into a per-session `.claude/skills/<name>/` directory inside the
workspace. Rejected because it would require inventing a workspace
plugin.json/marketplace shape or a skills-loading convention that does
not exist anywhere in-repo yet (`grep -n "skills" spawn.py` found
nothing to extend), doubling the surface area phase 1 needs to touch,
where the issue explicitly scopes this to "reuses two in-repo proven
patterns; no new external mechanism introduced." A bare `--plugin-dir`
per named skill needs no new loading convention: Claude CLI already
loads a `--plugin-dir` argument the same way core and rulebook
directories are loaded today.

**Skill-repository resolution: env override + sibling-clone default vs.
new managed-clone bootstrap.** Chosen: `MUSTER_SKILL_REPO` env var
first, else a sibling directory next to the checkouts `core_root()`
already knows about (`$TOKENMAXXXER_RULEBOOKS/skill-repository`,
mirroring `_core_candidates()`, spawn.py:5117-5146). Rejected
alternative: teach `spawn.py` to `git clone` skill-repository on demand
like `rulebook_checkout()` does for role rulebooks (spawn.py:279-330).
Rejected because requirement 1 asks for "a local skill-repository
checkout" — it does not ask this issue to own bootstrapping one from
scratch, and adding a managed-clone path multiplies the new code's
network/locking surface (see `_locked_rulebook_dir`,
`ensure_rulebook`'s two-pass retry) for a mechanism phase 1 does not
need to prove yet. If no local checkout resolves, `--skills` fails
closed with a clear message (same "didn't find it — see env/sibling"
shape as `core_root()`'s failure message), rather than silently trying
to fetch one.

## What will be done

- `spawn.py`:
  - Add `--skills` to the shared `argparse` parser in `main()`
    (spawn.py:6797ff), default `None`, help text describing the
    comma-separated skill-name list.
  - Add a small resolver, `_skill_repo_root() -> Path | None`, mirroring
    `_core_candidates()`/`core_root()` (spawn.py:5117-5146): checks
    `MUSTER_SKILL_REPO` env, then the sibling-clone default path; no
    managed-clone fallback (per Rationale above).
  - Add `resolved_skill_dirs(skills_csv: str | None, repo_root: Path |
    None) -> list[Path]`: parses the comma-separated names, and for
    each, resolves `<repo_root>/<name>` (or the repo's declared skill
    layout, confirmed against skill-repository's actual directory
    shape before writing this, per the live-interface-check
    requirement). Any name that does not resolve to an existing skill
    directory triggers `sys.exit(...)` listing the available names
    (read from the repo root's directory listing) — before any
    workspace/branch mutation, matching where `plugin_dirs()` already
    runs relative to workspace setup (spawn.py:7811).
  - Extend `spawn_cmd(..., skill_dirs: list[Path] | None = None)`
    (spawn.py:5385) with one new optional trailing parameter, following
    the exact `resolved_role_model(cli_model=None)` precedent
    (spawn.py:5367-5382): when `skill_dirs` is falsy/`None`, argv/env
    construction is unchanged line-for-line; when present, append one
    `--plugin-dir` per skill directory (after the existing rulebook +
    core `--plugin-dir` entries) and add `MUSTER_SKILLS` /
    `MUSTER_SKILL_REPO_SHA` to the returned env dict.
  - Wire the call site (spawn.py:7811-7832): resolve skill dirs (or
    `None` when `--skills` is unset) before `spawn_cmd()` is called, and
    pass them through.
  - Compute the skill-repository checkout's commit SHA once (`git -C
    <repo_root> rev-parse --short=7 HEAD`, mirroring the existing
    `rulebook_version()` shape at spawn.py:723) only when skills are
    requested.
  - Record fields (requirement 3): when `--skills` is used, add
    `skills` (the resolved name list) and `skills_sha` to the
    `roster_register(...)` call's dict literal at both call sites
    (spawn.py:7893 and the second registration ~7979) — omitted keys
    when `--skills` is unset, so the JSON shape is unchanged in the
    no-flag case. Append one line to the co-injected `task` string
    (spawn.py:7799-7809) naming the skill list and SHA, only when
    `--skills` is set — appended after the existing paragraph, so the
    no-flag `task` string is unchanged byte-for-byte.
- `test/test_spawn_skills_mount.py` (new):
  - Byte-identical no-flag case: call the argv/env assembly path (via
    `spawn_cmd()` and/or the CLI arg parse) with and without the new
    parameter/flag, and assert the two are equal — this diffs the
    assembled argv+env directly rather than against a stored fixture
    file, since none exists on disk (confirmed in the survey).
  - `--skills a,b` case: assert the mounted `--plugin-dir` entries, env
    fields, workspace layout are as expected for two valid names.
  - Unknown-name case: assert non-zero exit and that no workspace/
    branch creation happened (mocking/stubbing the workspace-creation
    call so the test can assert it was never invoked).
  - Record-fields case: assert `roster_register()`'s payload and the
    co-injected task string both carry the skill list and SHA when
    `--skills` is used, and do not carry those keys/lines when it is
    not.

## Accumulation

This proposal adds the same two keys (`skills`, `skills_sha`) to both
existing `roster_register(...)` dict literals (spawn.py:7893 and the
second call site near spawn.py:7979) rather than factoring a shared
"base roster entry" helper — those two call sites already diverge in
several other fields today (survey found no shared constructor between
them), so adding a helper now would be a refactor of pre-existing
duplication, not something this issue's two new keys need. If a future
phase adds a third roster field on top of `skills`/`skills_sha`
(e.g. phase 2's hook-promotion or migration work), that is the trigger
to extract a shared `_base_roster_entry(...)` builder — this proposal
does not do so pre-emptively, per "don't design for hypothetical future
requirements." Two call sites, two new keys each: bounded, not an
open-ended accumulation.

## Out of scope

- Hook promotion to core, rulebook-skill migration/archival, any change
  to branch naming, APPROVE token grammar, board records, or the
  role taxonomy (issue's non-goals, requirement 4).
- A managed-clone bootstrap for skill-repository (see Rationale) —
  `--skills` fails closed if no local checkout resolves.
- Actually invoking a mounted skill inside a session, or verifying
  skill *content* correctness — this proposal covers the mount
  mechanism only.

## How you'll know it worked

- `test/test_spawn_skills_mount.py` passes locally (`python3 -m pytest
  test/test_spawn_skills_mount.py -v`), covering: byte-identical no-flag
  argv+env diff, valid `--skills a,b` mount (argv/env/workspace-layout
  assertions), unknown-name fail-closed (non-zero exit, no workspace/
  branch creation), and record-fields (roster entry + co-injected
  directive carry skill list + SHA only when `--skills` is used).
- Full existing `test_spawn_*` suite still passes, confirming no
  behavior change to the no-flag path.

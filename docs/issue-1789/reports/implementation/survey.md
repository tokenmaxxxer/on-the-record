---
subject: issue-1789
role: implementation
kind: survey
---

# Survey: spawn.py managed-clone mechanisms and `_skill_repo_root()`

## Scout skip record

Scouting (external sweep) skipped — skip condition "the spec literally
leaves no design decision open" applies. The issue's own
`design-research` line states the mechanism must reuse spawn.py's
existing managed-clone pattern for on-the-record/core checkouts; no new
external mechanism is in scope. This survey instead does the internal
current-state read the scout-directive requires before any design
decision (there is none to make — the shape is dictated by the existing
pattern), per contract v3 s19's rigor floor.

## Current `_skill_repo_root()` (spawn.py:5147-5163)

```python
def _skill_repo_root() -> Path | None:
    env_value = os.environ.get("MUSTER_SKILL_REPO")
    if env_value:
        p = Path(os.path.expanduser(os.path.expandvars(env_value)))
        if p.is_dir():
            return p
    sibling = os.path.expandvars("$TOKENMAXXXER_RULEBOOKS/skill-repository")
    if "$" not in sibling:
        p = Path(os.path.expanduser(sibling))
        if p.is_dir():
            return p
    return None
```

Two sources only, in order: env `MUSTER_SKILL_REPO`, then sibling
`$TOKENMAXXXER_RULEBOOKS/skill-repository`. Returns `None` (no managed
clone) when both miss — the docstring at spawn.py:5150-5151 names this
explicitly as issue #1742's deliberate phase-1 restriction. Every caller
of `_skill_repo_root()` (spawn.py:8044, 8058) treats `None` as "no
skill-repo source" and falls through to fail-closed messaging
(`resolved_skill_dirs()`, spawn.py:5166-5184, `sys.exit`s naming only the
two known sources).

## Existing managed-clone pattern (two instances, same shape)

### 1. `core_root()` (spawn.py:5422-5464) — single fixed clone, ad hoc

- Checks `_core_candidates()` (env `TOKENMAXXXER_CORE`, then sibling
  `$TOKENMAXXXER_RULEBOOKS/tokenmaxxxer-core`) for a local override first.
- Falls to a managed dir `ROOT / "runs" / "rulebooks" / "tokenmaxxxer-core"`.
- Wraps clone/pull in `_locked_rulebook_dir(d)` (spawn.py:255-276): an
  `fcntl.flock` on a sibling `.lock` file, serializing concurrent
  spawn.py processes; kernel releases the lock if the holder dies (no
  stale-lock recovery code needed, issue #773).
- Freshness/offline policy inside the lock:
  - If the managed dir already has a valid checkout (`plugin.json`
    present) and `_pull_is_fresh(d)` is false, runs `git pull -q
    --ff-only`, wrapped in `_run_net(...)` (spawn.py:87, catches network
    failure — on failure the existing local commit is kept and used
    as-is; this is the offline-reuse behavior requirement 1 needs).
  - `_mark_pulled(d)` (spawn.py:155) stamps the pull so repeated
    same-session/near-term spawns don't re-hit the network
    (`_pull_is_fresh`, spawn.py:141, reads a TTL from
    `_rulebook_ttl_min()`, spawn.py:123; `_migrate_legacy_ttl_marker`,
    spawn.py:164, handles an older marker format).
  - If the managed dir has no valid checkout yet, clones with
    `_run_net(["git", "clone", "-q", url, str(d)], label,
    timeout=CLONE_TIMEOUT)` (`CLONE_TIMEOUT = 180`, spawn.py:80).
    `_run_net` catches `OSError`/timeout; on failure `core_root()` falls
    through past the `with` block to a final `sys.exit` naming both
    local-override env vars — this realizes requirement 3's
    fail-closed-with-named-sources shape, for core's two sources.
  - Validity check used throughout: `(d / "core" /
    ".claude-plugin" / "plugin.json").is_file()` — core-specific marker
    for "this is a real, usable checkout," not just `is_dir()`.
- No `_RULEBOOK_CACHE`-style per-process cache; `core_root()` is called
  once per relevant path already, so the lock+TTL is the only
  memoization layer.

### 2. `rulebook_checkout(role, spec)` (spawn.py:279-324) — generic, multi-repo

- Same `_locked_rulebook_dir` + `_run_net` + `_pull_is_fresh` /
  `_mark_pulled` shape as `core_root()`, but parameterized over `spec`
  (arbitrary marketplace name + repo) instead of one hardcoded repo, and
  additionally keyed through `_RULEBOOK_CACHE: dict[str, Path]`
  (spawn.py:246) so a second call in the same process returns the first
  result without re-touching the lock.
- Local-override check first (`_path(spec)` + `_mkt(Path(p)).exists()`),
  same "check a local override, then fall to a managed dir under
  `runs/rulebooks/<name>`" order as `core_root()`.
- Validity check is `_mkt(d).exists()` — a marketplace-specific
  existence probe (not shown above; parameterized per rulebook), the
  generic-case analogue of `core_root()`'s `plugin.json` check.
- On clone failure (managed dir still invalid after clone attempt),
  `sys.exit`s naming the repo it tried and the git stderr — same
  fail-closed shape, scoped to the one repo being fetched (this
  function's caller supplies whichever local-override candidates it
  wants named).

### Shared primitives both instances reuse (import targets for the new code)

- `ROOT / "runs" / "rulebooks" / <name>` — the managed-checkout area
  (`runs/` is gitignored per `ledger_write`'s docstring, spawn.py:5124-5132
  — consistent with `runs/rulebooks/` holding pulled data, not source).
- `_locked_rulebook_dir(d)` — cross-process serialization, generic over
  `d`.
- `_run_net(args, label, timeout=...)` — network wrapper catching
  failure, generic over the git invocation.
- `_pull_is_fresh(d)` / `_mark_pulled(d)` / `_migrate_legacy_ttl_marker(d)`
  — TTL-gated freshness, generic over `d`.
- `CLONE_TIMEOUT` constant (180s).

Neither existing instance is itself a directly-callable
`clone_or_reuse(name, repo_url) -> Path` helper — each inlines the same
five-step sequence (check local override → check managed dir validity →
pull-if-stale-else-reuse → clone-if-absent → validity-recheck-or-exit)
around its own validity predicate. Extending `_skill_repo_root()` means
either inlining that same five-step sequence a third time (matching the
existing repetition — `core_root()` did not generalize
`rulebook_checkout()` either) or factoring a shared step-sequence helper
first. This is the one implementation-shape choice actually open; see
the proposal's Rationale.

## Callers of `_skill_repo_root()` and downstream shape (spawn.py:8044, 8058)

```python
skill_sources = resolved_skill_sources(skills, _skill_repo_root(), ...)   # 8044
role_source = resolve_role_source(role, Path(cwd), _skill_repo_root())    # 8058
```

- `resolved_skill_sources()` (spawn.py:5260-...) treats `repo_root is
  None` for the skill-repo source as "this source didn't match," not as
  a fatal error by itself — fail-closed only fires when a requested
  skill name matches zero sources total (or multiple).
- `resolve_role_source()` (spawn.py:5348-5376) is the mapped-role path
  the issue's live failure hit: `allowlist.get(role)` names skills, then
  calls `resolved_skill_dirs(",".join(names), repo_root)`
  (spawn.py:5166-5184), which is where today's literal fail-closed
  message lives: `"--skills: skill-repository 체크아웃을 못 찾았다 —
  MUSTER_SKILL_REPO 나 $TOKENMAXXXER_RULEBOOKS/skill-repository 를
  확인하라"` (spawn.py:5176-5177) when `repo_root is None`. Requirement 3
  asks this message to additionally name the managed-clone attempt.
- Identity fields: `skill_repo_sha(repo_root)` (spawn.py:5329-5334,
  `git rev-parse --short=7 HEAD`, "?" on failure) feeds both
  `resolved_skill_sources()`'s per-match `sha` field and
  `resolve_role_source()`'s `skill_sha` — this is already root-agnostic
  (any `Path` with a `.git` works), so a managed-clone root produces the
  same `source=skill-repo` + sha shape as an env/sibling root
  automatically, satisfying requirement 2 with no change needed in
  `skill_repo_sha()` itself.

## Existing test coverage adjacent to this surface

- `test/test_spawn_role_skill_resolution.py:175-204` — a
  `TestCase.setUp`/`tearDown` pattern that saves/restores
  `MUSTER_SKILL_REPO` around tests exercising `resolve_role_source()`
  with the env source set. No test currently exercises the sibling path
  or the `None` (fail-closed) path for `_skill_repo_root()` directly, and
  the test module named by the issue's acceptance checks (a new file
  under test/, not yet created) does not yet exist.
- `test/test_spawn_skills_mount.py` — covers `resolved_skill_dirs()` /
  `resolved_skill_sources()` shape, unrelated to root resolution itself.

## What this survey found open for the proposal

1. Whether to inline a third copy of the five-step managed-clone
   sequence into `_skill_repo_root()` (matching existing repetition) or
   extract a shared helper used by all three sites. The proposal answers
   this — see its Rationale.
2. What validity predicate marks a skill-repository managed clone as
   usable (core uses `plugin.json`; rulebooks use per-spec `_mkt()`).
   skill-repository's own repo root has no such marker file today — the
   proposal must pick one (plain `is_dir()` post-clone, or a directory
   probe like "has at least one non-dot subdirectory").
3. How the fail-closed message at spawn.py:5176-5177 (and any other
   `sys.exit` site reachable when `_skill_repo_root()` returns `None`)
   should name the managed-clone attempt per requirement 3.

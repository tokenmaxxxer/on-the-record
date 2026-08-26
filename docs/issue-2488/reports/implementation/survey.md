# issue-2488 — current-state survey

canonical: docs/issue-1774/proposals/plugin-skill-resolution.md,
docs/issue-1774/reports/implementation.md

Scout-directive: skip condition applies partially — see "Scout" section
below. This is not a pure bugfix (the issue explicitly requires
design-research on source priority/trust) so the survey itself was not
skipped, but the design question it raises turns out to already have a
frozen, documented answer from #1774 (cited above), found by reading
that issue's own proposal/report during this survey.

## What the issue claims
`resolved_skill_dirs()` only walks the skill-repository checkout, so
`--skills` fail-closes on any name that exists only in an installed
plugin, `~/.claude/skills`, or the target repo's `.claude/skills` — with
a refusal message that already claims to check all four sources.

## What the code actually does
canonical: skills.py:110-129, skills.py:205-271, spawn.py:2586-2589

- `skills.py:110-129` `resolved_skill_dirs()` — single-source (skill-repo
  only), exactly as the issue describes.
- `skills.py:205-271` `resolved_skill_sources()` — a second, newer
  function that resolves a `--skills` name across all four sources the
  issue names: skill-repo, installed plugins via
  `_installed_plugin_skill_dirs()`, `~/.claude/skills` via
  `_local_skill_dirs()`, target-repo `.claude/skills` via the same
  helper. Zero matches: fail-closed, message names all four sources
  (skills.py:254-257) — this is the exact string quoted in the issue
  body. Two-or-more matches (any combination, including two plugins
  colliding inside the plugin tier): hard fail-closed naming every
  matching source, no silent precedence (skills.py:258-262). A matched
  dir carrying `hooks/`: hard fail-closed, uniformly across all four
  sources (skills.py:264-268).
- `spawn.py:2586-2589` — `_spawn_one()`'s actual `--skills` CLI path
  calls `resolved_skill_sources()`, not `resolved_skill_dirs()`, before
  `issue_workspace()`/`checkout_issue_branch()` (ordering comment at
  spawn.py:2583-2585). The resolved `dir` from any of the four sources
  feeds `skill_dirs`, which flows into `spawn_cmd()`'s `--plugin-dir`
  list.
- `resolved_skill_dirs()` remains used only by `resolve_role_source()`
  (skills.py:354-376, frozen role→skill mapping axis, #1758/#1955) and
  `resolve_skill_source()` (skills.py:379-395, the `--skill` singular
  stage-0 path, #2241) — both intentionally skill-repo-only by design,
  both out of this issue's scope (the issue names `--skills`, plural,
  only).

derived: spawn.py:2589 assigns `skill_dirs = [m["dir"] for m in
skill_sources]`, and test/test_spawn_skills_mount.py:61-75
(`SpawnCmdSkillsMountTest.test_skill_dirs_appended_as_plugin_dirs_with_env_fields`)
asserts those dirs land in `spawn_cmd()`'s `--plugin-dir` argv — so a
plugin/tier-3/tier-4 match genuinely mounts into the spawned session,
not just resolves in memory.

## Live re-verification this turn
canonical: `python3 -m pytest -q test/test_spawn_skills_mount.py`, run
this turn
```
31 passed in 14.75s
```
Confirms `ResolvedSkillSourcesFourTierTest` (per-tier resolution alone,
all five cross-tier ambiguity pairings each naming every matching
source, `hooks/` refusal per tier) and `SkillRosterFieldsFourTierTest`
(per-source record-field shape) pass on this checkout right now, not
just in the historical record.

## Where this came from
canonical: `git log --oneline --all -S "def resolved_skill_sources" -- skills.py spawn.py`
```
4fa84f80 issue-2105 (7/N): extract skill-resolution ... (#2121)
677b9d74 issue-2105 (7/N): extract skill-resolution ... (#2121)
3ef8e887 issue-1774: --skills resolves across skill-repo, plugins, and local dirs (#1779)
3a2d6bd5 issue-1774: --skills resolves across skill-repo, plugins, and local dirs (#1779)
```
canonical: docs/issue-1774/proposals/plugin-skill-resolution.md (Rationale, Out of scope sections)

`docs/issue-1774/proposals/plugin-skill-resolution.md` is the frozen
four-tier design and already answers both questions #2488 asks for:
- **Collision priority**: none. The proposal's Rationale states the
  issue #1774 "SCOPE EXTENSION" comment superseded an earlier draft
  where skill-repo silently won over plugins; the frozen rule is "no
  tier silently wins ... a name resolved in two or more tiers is a
  hard, fail-closed ambiguity error naming every matching source."
  Rejected alternative (named in that Rationale): silent per-tier
  precedence (repo > plugin > tier-3 > tier-4) — rejected because it
  would let a same-named local skill silently shadow a curated one with
  no operator visibility.
- **Trust distinction**: the proposal's Out-of-scope section notes
  tiers 3-4 (`~/.claude/skills`, target-repo `.claude/skills`) already
  auto-load into interactive sessions today — `--skills` only makes
  them additionally, explicitly composable and recorded for a spawned
  session; it does not create a new trust boundary. Combined with the
  uniform `hooks/`-refusal (mount is guidance-only regardless of
  source), the frozen design treats all four sources identically at
  the mount-eligibility level.

canonical: docs/issue-1774/reports/implementation.md (frontmatter
`verdict: pass`, `loop_state: landed`; body's "Test plan / what ran"
section quotes `31 passed in 0.85s` for the same test file, at that
time)

## Gap analysis (what #2488 actually has left to fix)
derived: from the sections above — the mechanism #2488 asks for is
already built, tested, and landed (git log dates the #1774 commits
before `git log -1 --format='%H %ci' -- skills.py` = `1d29184b
2026-08-25 12:22:31 +0900`, itself before #2488's `createdAt:
2026-08-26T01:09:45Z` per `gh issue view 2488 --json createdAt`, run
this turn). Two concrete gaps remain, both mapping onto the issue's own
acceptance criteria:
1. **spawn.py:1507-1510** (`--skills` argparse help text) still
   describes only "skill-repository 체크아웃" — stale relative to
   `resolved_skill_sources()`'s actual four-source behavior. This is
   the kind of message/reality mismatch acceptance-check 5 targets,
   just in `--help` text rather than the refusal message (the refusal
   message itself, quoted above, already matches).
2. **No durable spec/decision doc** states the trust-distinction and
   collision-priority answers outside `docs/issue-1774/`'s own
   proposal/report — acceptance-check 3 and 4 ask for this to be
   "defined, documented" somewhere a future reader (such as whoever
   filed #2488) could find without independently re-discovering a
   closed issue's proposal file.

## Alternatives considered for closing these two gaps
canonical: docs/issue-1774/proposals/plugin-skill-resolution.md
(Rationale section, "Tie-break" subsection)

- **A — leave `resolved_skill_sources()` and its tests untouched, only
  fix the help text and add a `docs/decisions/` entry cross-referencing
  #1774's already-frozen rationale.** Chosen. The design decision does
  not need to be re-opened — #1774's proposal already surveyed and
  rejected the silent-precedence alternative with a documented reason,
  and it is still the right call: `--skills` composition is explicit
  opt-in by the operator spawning the session, not an implicit trust
  escalation, and uniform fail-closed-on-collision preserves operator
  visibility better than any priority order would.
- **B — re-run the full four-tier design from scratch as if #1774 never
  happened.** Rejected: would duplicate #1774's already-landed,
  already-passing code path (see "Live re-verification" above) for no
  behavioral gain, and directly contradicts the instruction against
  rewriting working code beyond what the task requires.
- **C — add a trust-tiered priority (skill-repo > plugin > local-user >
  local-repo) so collisions resolve silently instead of failing
  closed.** Rejected for the same reason quoted from #1774's proposal
  above: silent precedence hides a real naming collision from the
  operator, which is worse for an explicit `--skills` composition than
  a hard stop naming both sources.

## Scout
canonical: docs/issue-1774/proposals/plugin-skill-resolution.md (the
prior-art/rationale this survey reused instead of re-sweeping)

Scouting (external prior-art sweep) was skipped for this issue: the
open design question the issue raises is answered by the prior internal
decision cited throughout this survey (#1774), not by external
comparison, and sweeping "how other systems merge skill sources" would
not change the two mechanical gaps identified above. Skip condition per
scout-directive: design decision already resolved by an existing frozen
internal decision, found during the survey itself.

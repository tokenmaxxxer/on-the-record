---
id: skills-resolver-source-priority-and-trust
status: active
date: 2026-08-26
subject: issue-2488
origin: issue-1774 (2026-08-24/25), restated for issue-2488
---

# `--skills` resolver: source priority and trust distinction

## Status

Active (restates and cross-references a decision already frozen into
code and tests by issue #1774, `docs/issue-1774/proposals/
plugin-skill-resolution.md`). Written for issue #2488, which asked the
same two questions again without finding the #1774 record — this file
exists so the next reader finds the answer without re-discovering a
closed issue's proposal.

## Decision

`spawn.py --skills <name>[,<name>...]` resolves each name across four
sources, implemented in `skills.py:resolved_skill_sources()`:

1. the skill-repository checkout (curated, versioned by git sha),
2. installed plugins' `skills/<name>/` directories,
3. `~/.claude/skills/<name>/` (user-level local skills),
4. the target repo's own `.claude/skills/<name>/`.

**Collision priority: none.** A name matching in exactly one source
resolves to that source. A name matching in two or more sources — any
combination, including two distinct plugins colliding inside the plugin
source — is a hard, fail-closed error naming every matching source
(`skills.py:258-262`). There is no silent precedence order; the search
order above only decides where to look, never which match silently
wins when more than one actually matches. This was chosen over a
silent-precedence alternative (skill-repo always wins) because a silent
winner would let a same-named local skill shadow a curated one with no
operator visibility into the substitution — see #1774's proposal
Rationale for the fuller argument.

**Trust distinction: none, by design, at mount-eligibility.** All four
sources are treated identically for both the collision rule above and
the guidance-only guard: a resolved directory carrying a literal
`hooks/` subdirectory is refused, uniformly, regardless of source
(`skills.py:264-268`, and the same `(dir / "hooks").is_dir()` pattern in
`resolve_role_source()`/`resolve_skill_source()`). This is intended to
be safe for the same three reasons as before this record was corrected
below:
- Mounting is intended to be guidance-only — the `hooks/`-subdirectory
  guard exists specifically to keep a mounted directory to "text a
  session reads," not code the harness executes.
- `--skills` composition is explicit, operator-initiated opt-in at
  spawn time, not an implicit trust escalation the spawned session
  reaches for on its own.
- The two local sources (`~/.claude/skills`, target-repo
  `.claude/skills`) already auto-load into ordinary interactive
  sessions today; `--skills` only makes the same already-trusted
  directories additionally composable into a *spawned* session's roster
  and recorded there — it does not grant them any capability an
  interactive session didn't already have.

**Known gap in the guard itself (found during this record's own
before-landing hunt, 2026-08-26):** the `(dir / "hooks").is_dir()` check
only catches a literally-named `hooks/` subdirectory. A skill directory
whose `.claude-plugin/plugin.json` redirects the hook config elsewhere
(its own `"hooks"` key pointing at a differently-named file) passes this
guard and can fire a real hook headless via `--plugin-dir`, from *any*
of the four sources — reproduced live, see
`docs/issue-2488/reports/implementation/2026-08-26-hunt-skills-resolver-fix.md`.
This is a pre-existing gap in the guard shared by all three call sites
(`resolved_skill_sources`, `resolve_role_source`, `resolve_skill_source`),
not something #2488 introduced or is scoped to fix — the "guidance-only"
property above is this decision's *intent*, not yet a fully-enforced
guarantee. Tightening the guard (e.g. asking the CLI to validate the
directory, or parsing `plugin.json`'s `hooks` key) is out of scope here
and needs a dedicated follow-up.

Each mounted skill's resolved source is recorded per-skill in the spawn
roster (`skills.py:_skill_roster_fields()`/`_skill_source_roster_row()`)
— `skill-repo` carries the repo sha, `plugin` carries
`plugin@marketplace` + version, the two local sources carry their path
plus a `SKILL.md`-content sha256 — so the composition stays
reproducible and auditable regardless of which source won.

## Update (issue #2579, 2026-08-27)

Two corrections to the collision rule above, both in `resolved_skill_sources()`:

1. **A name matching in two-or-more sources is no longer automatically a
   collision when the underlying content is byte-identical** (e.g.
   `~/.claude/skills` symlinked to the same physical directory the
   skill-repository checkout resolves to — the reported bug: every one of
   273 skills "collided" with itself this way, blocking `--skills`
   entirely). `_collapse_identical_matches()` compares each match's
   `SKILL.md` bytes (via `_skill_identity_key()`, which never treats two
   *missing* `SKILL.md` files as equal — that would wrongly merge
   unrelated empty directories) and collapses to one match only when
   every match's content agrees. Matches whose content genuinely differs
   still hit the original hard fail-closed error unchanged — this
   decision's "no silent precedence" rule stands exactly as written above
   for that case.
2. **A source can now be named explicitly, always** — not only once a
   collision forces a choice — via `<source>:<name>`
   (`skill-repo`/`plugin`/`local-user`/`local-repo`), e.g.
   `--skills skill-repo:diagnose-first`. An unqualified name behaves
   exactly as before (resolves across all four sources, subject to the
   collision rule above). A qualifier pointing at a source that doesn't
   have that name fails closed naming both the source and the name. This
   makes every mount reproducible from a record alone — previously a
   name's source could only be inferred from search order, so "which
   `secure-coding` ran" was unrecoverable after the fact.

See `docs/issue-2579/reports/silent-failure-audit+diagnose-first-206898b1.md`
for the live reproductions.

## Consequences

- A future change proposing silent per-source precedence, or a
  differential trust tier that mounts one source's directories without
  the `hooks/` guard applied to another, intersects this decision and
  needs an explicit disposition, not a silent adoption.
- If a genuinely different trust boundary is ever needed (e.g. refusing
  to mount target-repo `.claude/skills` for a spawned session that
  doesn't already trust that repo), that is a new decision superseding
  this one, not a tweak to `resolved_skill_sources()`'s collision rule.

---
id: skills-resolver-content-identity-and-source-qualifier
status: active
date: 2026-08-27
subject: issue-2579
supersedes: skills-resolver-source-priority-and-trust (2026-08-26, partial — collision test only)
---

# `--skills` resolver: content identity before the collision rule, and an always-available source qualifier

## Status

Active. Refines (does not reverse) `docs/decisions/
2026-08-26-skills-resolver-source-priority-and-trust.md`'s collision
rule.

## Problem

`~/.claude/skills` is commonly a symlink into the same checkout
`MUSTER_SKILL_REPO` already points `skill-repo` at (measured live in
this environment: both resolve to `/home/jwjung/skill-registry/skills`).
`resolved_skill_sources()`'s `len(matches) > 1` test compared path
strings only, so every one of these — effectively all 273 skills in
this environment — was reported as a cross-source collision and
`--skills` was refused outright. The 2026-08-26 decision's "any
combination... is a hard, fail-closed error" language was written
against genuinely distinct sources, not this case: two path strings
that name the exact same bytes.

## Decision

**Content identity is checked before the collision rule, not instead
of it.** `resolved_skill_sources()` now computes a `content_sha256`
(`SKILL.md` bytes, sha256 — `_skill_content_identity()`) for every
match regardless of source tier (previously only the two local tiers
carried this field, per #1774; `skill-repo`/`plugin` matches now get it
too). Matches for a name are grouped by that hash
(`_dedupe_matches_by_content()`) before the `len(matches) > 1` check
runs. Two or more matches with identical content collapse to one —
the same skill reached by two paths, not two skills. Two or more
matches with genuinely different content are unchanged from
2026-08-26: hard fail-closed, naming every surviving group, still no
precedence — the non-goal in issue #2579 ("do not resolve collisions
by precedence order") stands, because this refinement never picks a
survivor among *differing* content; it only recognizes when there was
nothing to pick between in the first place.

**A `<source>:<name>` token qualifier is always legal**, not only when
a name collides. `_parse_skill_token()` splits a `--skills` name token
on `<source>:` when `<source>` is one of the four resolver labels
(`skill-repo`/`plugin`/`local-user`/`local-repo`); the resolver then
filters matches to that source before the content-dedup/collision
logic runs. This was the issue's central ask: a spawn's provenance
must be nameable and reproducible always, not only bolted on after an
operator hits a collision. A qualified name pointing at a source with
no match for that name fails closed, naming both the source and the
name. Branch/record slugs strip the qualifier (`_skill_token_name()`)
since git ref names can't hold `:`; the full qualified token still
reaches `resolved_skill_sources()` unchanged.

**The record states provenance unconditionally when `--skills` mounted
something.** `write_record_skeleton()` now stamps a `skills: <name>
(<source description>), ...` frontmatter line (via
`_stamp_additive_record_fields()`, the existing single call site for
additive stamped fields, issue #2241 stage 1) at bootstrap, using the
same `_describe_skill_match()` one-liner already used in the
task-injected "마운트된 스킬" text. Omitted entirely when no `--skills`
were mounted — byte-identical to before this issue for that path.

## Consequences

- Existing "ambiguity" tests in `test/test_spawn_skills_mount.py` used
  bare `mkdir()` fixtures with no `SKILL.md` — under content-hash
  dedup, two empty directories are byte-identical and would no longer
  collide. Those fixtures (`_make_pair()` and the two-distinct-plugins
  test) now write distinguishing `SKILL.md` content per tier so they
  still exercise a genuine cross-source collision.
- `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`'s
  "Collision priority: none" and "no precedence" statements are
  unchanged in substance; this record only narrows what counts as a
  collision in the first place. A future change that dedupes on
  anything looser than exact content equality (e.g. semantic
  similarity) would intersect this decision and needs its own
  disposition.

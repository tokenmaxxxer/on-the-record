---
status: proposed
files:
  - spawn.py
  - test/test_spawn_skills_mount.py
---

## Request
`--skills <name>` today resolves only against the skill-repository
checkout root. #1774, extended by the issue's SCOPE EXTENSION comment,
asks that a name also resolve against three further sources — explicit
opt-in only, fired only when `--skills` names something — in this
frozen four-tier model:

1. skill-repository root (unchanged, unique per-repo identity: git sha),
2. the consumer's installed plugins' `skills/<name>/` dirs
   (identity: `plugin@marketplace` + version/sha),
3. `~/.claude/skills/<name>/` — user-level local skills
   (identity: local path + content hash),
4. the target repo's own `.claude/skills/<name>/`
   (identity: local path + content hash).

A name matching in **more than one** of the four sources is a hard error
naming **all** matching sources — the search order above only decides
where to look first when exactly one tier matches; it is never a silent
tie-breaker once more than one tier actually matches. A name matching
nowhere still fails closed as today. Every source's mounted dir is
guidance-only (a `hooks/` subdirectory refuses), mirroring today's
skill-repository rule. Records carry each mounted skill's own source
identity, in the shape appropriate to its tier.

## Constraints
- No `--skills` flag: byte-identical argv/env, and none of
  `installed_plugins.json`, `~/.claude/skills/`, or `<target-repo>/
  .claude/skills/` is ever read (requirement 4; mirrors
  `resolved_skill_dirs`'s existing `not names -> return []` early exit,
  survey.md "Requirement-to-code mapping" item 4).
- No tier silently wins over another. The original (2-source) proposal's
  "repo always wins over plugin" rule is superseded by the issue's SCOPE
  EXTENSION comment: a name resolved in exactly one tier resolves to
  that tier; a name resolved in two or more tiers (any combination,
  including repo + plugin, repo + tier-3, tier-3 + tier-4, etc.) is a
  hard, fail-closed ambiguity error naming every matching source.
- Every source's mount is read-only (`--plugin-dir`, same mechanism as
  today for tier 1) — never copied/mutated, including tiers 3-4's local
  directories.
- Fail-closed timing preserved: all resolution/validation across all
  four tiers happens before `issue_workspace()` /
  `checkout_issue_branch()` (survey.md, existing `_spawn_one` ordering
  at spawn.py:7873).
- Record field additions are additive only — existing skill-repo-only
  compositions keep today's `skills`/`skills_sha` shape (issue empty-state
  requirement: "skill-repo-only compositions keep today's field shape").
- Tiers 3-4 have no repo sha and no plugin-registry version to record —
  their source identity is local path + content hash of the mounted
  skill dir, computed the same way for both tiers (survey.md "SCOPE
  EXTENSION" section).

## Rationale
Two questions needed a decision beyond the original proposal's plugin-only
scope.

**Tie-break: keep "repo wins" or make every multi-tier match an error?**
Rejected: keeping the original "repo silently wins over plugin" rule and
just adding tiers 3-4 underneath it in the same silent-precedence style.
Rejected because the issue's SCOPE EXTENSION comment explicitly
supersedes that: "no silent precedence between distinct matches —
precedence only orders the search, it never silently shadows an actual
conflict." A silent per-tier winner would mean a `~/.claude/skills/`
skill and a same-named skill-repository skill compose to "whichever tier
sorts first" with no operator visibility into the shadowing — exactly
the kind of undocumented precedence the extension rules out. Chosen:
multi-tier match is always a hard error, uniformly, regardless of which
tiers collide.

**Tier 3-4 identity: content hash of what, exactly?**
Considered: hash the skill directory's full file tree (recursive
manifest hash) for maximum fidelity. Rejected for this proposal in favor
of hashing `SKILL.md` alone (the one file every skill in this repo's own
convention treats as the skill's canonical definition — see
`~/.claude/skills/*/SKILL.md` and #323's scout-brief citations of that
same convention) because a full-tree hash would need to define a stable
traversal/exclusion policy (symlinks, `.gitignore`-style ignores,
ordering) that has no precedent anywhere else in `spawn.py`'s existing
sha/version identity fields, while `SKILL.md`-only hashing reuses the
same single-file read pattern the rest of the file already uses for
per-skill content and keeps the write set inside `spawn.py` +
`test/test_spawn_skills_mount.py` as scoped. If a skill's supporting
files (not `SKILL.md`) change without `SKILL.md` changing, the recorded
hash will not move — flagged here as a known fidelity gap for a future
issue, not solved by this one.

## What will be done
1. `_installed_plugin_skill_dirs()` (new, as in the original proposal):
   read `~/.claude/plugins/installed_plugins.json` (return `{}` if
   absent/unreadable), index each installed plugin's `skills/<name>/`
   subdirectory by name -> list of `(plugin_qualifier, dir_path,
   version_info)`.
2. `_local_skill_dirs(root: Path) -> dict[str, Path]` (new, shared by
   tiers 3 and 4): given a root directory (`Path.home() / ".claude" /
   "skills"` for tier 3, `<target-repo> / ".claude" / "skills"` for tier
   4), list its immediate subdirectories as candidate skill names ->
   `Path`, `{}` if the root does not exist. One function, two call
   sites — tiers 3 and 4 differ only in which root they pass.
3. `_skill_content_hash(skill_dir: Path) -> str`: `hashlib.sha256` over
   `skill_dir / "SKILL.md"`'s bytes (per Rationale), hex digest. Used
   only for tiers 3-4's record identity.
4. `resolved_skill_dirs(...)` extended to build all four tiers' indexes
   lazily (each tier's lookup is skipped entirely when every requested
   name already resolved in an earlier-checked tier — keeps the
   byte-identical / never-read constraint for the no-`--skills` case,
   and avoids reading `~/.claude/skills/` or the target repo's
   `.claude/skills/` when every name is a skill-repository hit). Per
   name: collect the set of tiers that match (repo, plugin(s),
   tier-3, tier-4); a matching-tier-count of 0 keeps today's "unknown"
   fail-closed message; a matching-tier-count of exactly 1 resolves to
   that source (if that source is "plugin" and more than one distinct
   plugin matches, that is itself a multi-match within tier 2 and
   included in the same hard-error path); a matching-tier-count of 2+
   (across any tiers, including two matches inside tier 2 alone) is a
   single fail-closed error naming every matching source. Return value
   carries per-name resolution records (source kind + path + identity
   fields), not bare `Path`s, so requirement 3's record fields can be
   built from the same structure the resolution loop already produced.
5. Guidance-only refusal (requirement 2, all four tiers): after
   resolving a name to a directory in any tier, apply the same
   `hooks/`-subdirectory check `resolve_role_source` already runs for
   skill-repository dirs (spawn.py:5226-5231), fail-closed before
   workspace/branch creation, identically for all four tiers.
6. Record fields (requirement 3): extend the roster entry and
   co-injected task string (spawn.py:7958-7967, 8079-8081, 8185-8188) so
   each mounted skill's row carries its own source:
   - tier 1: `{"name": ..., "source": "skill-repo", "sha": <7-char>}`
     (unchanged shape),
   - tier 2: `{"name": ..., "source": "plugin", "plugin":
     "<name>@<marketplace>", "version": "<version-or-sha>"}` (unchanged
     from the original proposal),
   - tiers 3/4: `{"name": ..., "source": "local-user" | "local-repo",
     "path": "<absolute or repo-relative path>", "content_sha256":
     "<hex digest>"}`.
   All additive alongside the existing flat `skills`/`skills_sha` keys
   (kept unchanged for skill-repo-only compositions per the empty-state
   requirement).
7. Tests in `test/test_spawn_skills_mount.py`, extended beyond the
   original proposal's plugin-only cases to cover all four tiers:
   resolution-order cases (each tier resolves alone when it is the only
   match), a multi-tier ambiguity case per meaningful pairing (repo +
   plugin, repo + tier-3, plugin + tier-4, tier-3 + tier-4, and the
   existing plugin-vs-plugin within-tier-2 case) each asserting the
   error names every matching source, a nowhere-found fail-closed case
   unchanged, a `hooks/`-dir refusal case for each of the four tiers, and
   record-field cases asserting per-skill source identity for all four
   shapes (skill-repo sha, plugin name+version, tier-3 path+hash, tier-4
   path+hash) vs. today's shape for a repo-only mount. All tests build
   synthetic fixtures (`installed_plugins.json`, plugin checkouts,
   `~/.claude/skills`-shaped and target-repo-`.claude/skills`-shaped
   directories) under `tempfile.TemporaryDirectory()` with `HOME`/repo
   root monkeypatched for the duration of the test — never touch the
   real `~/.claude/plugins/` or `~/.claude/skills/`.

Staged delivery inside phase 2 is fine per the reviewer's note (tiers 1-2
first, then 3-4) as long as this proposal freezes the full four-tier
model and its acceptance/test plan now — both stages land in this same
phase-2 PR before it closes the issue.

## Out of scope
- Any change to how the skill-repository root itself is discovered or
  its names enumerated (unchanged, tier 1 still searched first).
- Marketplace-level plugin install/update flows (`plugin_dirs`,
  `sync_rulebooks`, etc.) — this only reads already-installed/already-
  present state, read-only, for all four tiers.
- Widening the `hooks/`-refusal rule's scope beyond the mounted skill
  dir itself (no scan of the whole plugin, home directory, or repo).
- Changing `resolve_role_source`'s (#1758) unrelated role->skill mapping
  axis.
- Full-tree content hashing for tiers 3-4 (see Rationale) — `SKILL.md`-
  only hashing is the frozen identity for this proposal; a fidelity gap
  is named, not solved, here.
- Any change to Claude Code's own runtime auto-loading of `~/.claude/
  skills/` or `<repo>/.claude/skills/` into interactive sessions — this
  proposal only makes those same directories additionally *composable*
  and *recorded* via `--skills`, per the issue's own wording.

## Accumulation
`_installed_plugin_skill_dirs()` reads `installed_plugins.json` once per
`spawn.py` invocation and builds an in-memory name->matches index (as in
the original proposal); `_local_skill_dirs()` likewise does one
`os.listdir`-shaped read per root, called twice (tier 3 root, tier 4
root), not once per candidate name. None of the four tiers' lookups is a
per-plugin or per-skill inline `subprocess`/`gh` call accumulating one
call per entry, and none adds a new repeated-file-with-one-line-per-entry
pattern (no new `roles/*.json`-style per-item file). If N more consumer
plugins get installed, or N more skills accumulate under
`~/.claude/skills/` or `<repo>/.claude/skills/`, over time, the cost per
tier stays O(entries in that tier) dict/list entries built from one
directory listing or one JSON read — no additional code path, call site,
or file is added per plugin or per local skill. The multi-tier ambiguity
check is a single set-union-size comparison per requested name (bounded
by `--skills`'s own CSV, already user-bounded), not a per-tier-pair
special case that grows combinatorially as tiers are added. The
record-field shape (per-skill source row) is likewise one list entry per
*mounted* skill, not per available skill in any tier.

## How you'll know it worked
- `test/test_spawn_skills_mount.py` extended cases pass: resolution
  order across all four tiers, multi-tier ambiguity errors (every
  pairing named above) naming all matching sources, plugin/tier-3/tier-4
  `hooks/`-dir refusal, and record-fields cases for all four source-
  identity shapes — all in the same test file per the issue's own
  `check:` line.
- No-`--skills` byte-identical case (`SpawnCmdByteIdenticalNoFlagTest`)
  still passes unmodified, and asserts none of `installed_plugins.json`,
  `~/.claude/skills/`, or the target repo's `.claude/skills/` was read.
- `python3 -m pytest test/test_spawn_skills_mount.py -q` run clean before
  the phase-2 PR closes the issue.

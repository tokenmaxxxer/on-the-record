# Spawn directive assembly: single-phase signal + per-skill trigger lines

Issue #1978. Covers two additive mechanisms in `spawn.py`'s
`_spawn_one()` task-directive assembly.

## `--single-phase`

CLI flag, threaded through `_spawn_one(single_phase: bool = False)` the
same way `--despite-returned` is threaded. When set:

- `extra_env["CORE_BUILD_NOW"] = "1"` is added to the env dict
  `spawn_cmd()` returns for the spawned session.
- The authoritative single-phase contract line — mirrored verbatim from
  `directive.sh`'s existing "Build-now bypass (contract v3 s19a)" bullet
  in `tokenmaxxxer-core` — is appended to the assembled task text, before
  any per-skill trigger-line block (A before B).

`CORE_BUILD_NOW=1` itself is the pre-existing bypass channel from #1672;
this issue only wires an explicit spawn-time signal into it. The gating
and session-side honoring of the env var live in `tokenmaxxxer-core`
(`directive.sh`, `approval-gate.sh`) and are unchanged by this issue.

When the flag is absent, neither the env key nor the contract line is
added — the assembled task/env is byte-identical to a spawn that predates
this feature.

## Per-skill trigger lines

Replaces the #1960 generic "check your mounted skills" nudge (measured
1/9 organic invocation rate). For each mounted skill — both
`--skills`-resolved (`skill_sources`) and role-mapped
(`role_source["skill_dirs"]`, skill-repository #1955/#1758) — the
directive lists the skill's name followed by its `SKILL.md`
`description:` frontmatter's "Use ..." trigger sentence, extracted by
`_skill_trigger_line(skill_dir: Path) -> str | None`.

`_skill_trigger_line` reads only the frontmatter block, handles a folded
block scalar (`description: >-`), and returns `None` (never raises) when
the file, frontmatter, or a "Use ..." sentence is absent. A skill with no
extractable trigger line is still listed by name — never dropped.

A spawn with zero mounted skills produces a directive unchanged from
today.

## Out of scope here

`directive.sh`, `approval-gate.sh`, and the rest of the
`CORE_BUILD_NOW` gating/honoring chain live in `tokenmaxxxer-core`, not
this repo — see that repo's own docs for the other half of the channel.

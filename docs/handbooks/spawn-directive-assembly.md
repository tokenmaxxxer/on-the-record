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

## Checkpoint-commit line (issue #1981)

Unconditional, one sentence appended to `_spawn_one()`'s existing
preamble f-string, immediately after the push/PR paragraph and before the
headless-single-shot warning paragraph: make a checkpoint commit BEFORE
starting any long or backgrounded verification run, and amend it or add a
follow-up commit after. This inverts today's verify-then-commit habit,
which stranded two live sessions mid-verification on 2026-08-22 (#1959 s2,
#1978 ph2 — see `docs/issue-1978/reports/implementation.md`'s
finalization-deviation note).

Unlike `--single-phase` above, this line carries no flag gate: every
commit-capable `_spawn_one()` call gets it, always — the same audience as
the surrounding always-on preamble it extends, not an opt-in a spawner
must remember to request. It does NOT appear in `consult_cmd()`'s or
`panel_cmd()`'s assembled prompts — those are separate no-commit-mode
functions with independent prompt assembly (see their own docstrings) —
so the line naturally stays absent from consult/panel by construction,
not by a conditional check.

## Gate passing-shape contract (issue #2479)

`hook-contract.md` — unconditional, alongside `completion-and-landing.md`
and `repo-discovery.md` in `directive_section_files()` — states the exact
passing shape plus a worked example for two deny-only PreToolUse gates
that fire for every role session: `record-claim-guard.sh` (any Write/
Edit/MultiEdit under `docs/issue-*/reports/**`) and
`heredoc-command-refusal-gate.sh` (any role-session `git commit`/`gh
issue|pr create|comment` Bash call). Both worked examples are verified to
pass their respective gate's real check functions (`gates/record_lint.py`,
`on-the-record/hooks/heredoc-command-refusal-gate.sh`'s embedded guard) —
see `docs/issue-2479/reports/implementation.md`.

Motivation: observed live (issue-2379 conformance-review session) —
after opening its phase-1 PR, a follow-up commit hit both gates
back-to-back with no prior warning and the session ended
`progressed-dirty-tree`, unable to close out its own commit; watchdog
then treated the entry as dead and respawned it from scratch. Neither
gate's own refusal/deny logic changes — this only tells the passing
shape earlier, mirroring the `--single-phase`/checkpoint contract-line
mirroring pattern above (verbatim from the enforcing source, not a
hand-invented paraphrase, where the source text was itself concise
enough to mirror; `gates/record_lint.py`'s check docstrings are
per-function prose, not a single quotable shape, so this section
condenses them by hand instead — same content on both sides, checked
against the module's `_section_bounds` note about issue #2219's
whole-section (not fixed-3-line) evidence window).

## Out of scope here

`directive.sh`, `approval-gate.sh`, and the rest of the
`CORE_BUILD_NOW` gating/honoring chain live in `tokenmaxxxer-core`, not
this repo — see that repo's own docs for the other half of the channel.

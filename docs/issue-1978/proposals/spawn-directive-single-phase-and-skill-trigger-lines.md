---
status: proposed
files:
  - spawn.py
  - tests/test_spawn.py
  - docs/handbooks/spawn-directive-assembly.md
---

# Spawn directive assembly: single-phase signal + per-skill trigger lines

## Request

Two measured defects in `_spawn_one()`'s task-directive assembly
(`spawn.py`), fixed together, A before B:

(A) A spawn task whose text says "single-phase" (e.g. "single-phase
implement+record") still results in a two-phase session — the existing
`CORE_BUILD_NOW=1` bypass (contract v3 s19a, from #1672) is correctly
built and gated in `tokenmaxxxer-core`, but nothing in `spawn.py`
translates a single-phase signal into that env var, so it never fires.
Fix by wiring an explicit signal into `spawn.py` that sets
`extra_env["CORE_BUILD_NOW"] = "1"` and appends the authoritative
single-phase contract line to the assembled task text.

(B) The #1960 generic skill-check nudge (1/9 organic invocation rate) is
replaced with per-skill inlining: each mounted skill's name and its
`SKILL.md` "Use ..." trigger sentence, extracted from frontmatter,
appended to the task directive — so the trigger condition itself reaches
the session instead of asking the session to recall it unaided. The
injection must respect A's phase mode (single-phase sessions still get
skill lines; nothing about B changes based on A other than ordering in
the assembled text).

Plus: a written-only sketch of a guidance-reflection scoring rubric to
replace the Skill-call-count invocation metric, explicitly deferred (not
implemented this issue — flagged in the issue itself as needing its own
rubric work before it is testable).

## Constraints

- Reuse the existing `CORE_BUILD_NOW=1` bypass channel (#1672 s19a) —
  do not invent a second parallel escape channel. Confirmed by survey:
  the channel is intact and gated correctly in `tokenmaxxxer-core`; only
  the spawn-time wiring into it is missing.
- A spawn without the single-phase signal must produce a task directive
  byte-identical to today's (acceptance criterion 1) — the new code path
  must be strictly additive and only activate on an explicit signal.
- A spawn with zero mounted skills must produce a task directive
  unchanged from today (acceptance criterion 2) — same additive
  constraint for B.
- A skill whose `SKILL.md` lacks a `description`/trigger line must still
  be listed by name, never dropped silently (acceptance empty-state
  clause).
- A before B, sequential, inside one issue (per the issue's own
  sequencing note) — B's injection code must read A's phase-mode signal
  before deciding how to append its own block, but the two are otherwise
  independent text blocks and do not need to be merged into one function.
- Two-account/single-account approval and phase-2 gating semantics
  (contract v3 s19) are untouched — this issue only changes what text and
  env vars a spawn produces, not how PRs get approved.
- The rubric sketch is proposal text only — no scoring code, no new
  metric script, this issue.

## Rationale

**Signal shape — CLI flag vs. task-text pattern match vs. always-on for a
given role.** Considered inferring "single-phase" purely by scanning the
`task` string for the literal word "single-phase" and setting
`CORE_BUILD_NOW=1` whenever it appears. Rejected: the two live failures
happened with human/orchestrator-authored task text containing that
word, but string-matching arbitrary prose is fragile in both directions
— a task that quotes "not single-phase" or references the *concept* of
single-phase-ness without intending the bypass would false-positive, and
a differently-phrased authorization ("build and deliver in one go") would
false-negative. Chose instead an explicit `--single-phase` CLI flag
(mirroring the existing `--despite-returned`, `--unattended` boolean-flag
pattern at `spawn.py:6863-6939`) that the orchestrator/caller sets
deliberately, the same way `CORE_BUILD_NOW` itself is contract-documented
as "set by the spawner, never by you" — an explicit flag is the spawner
making that call structurally, not a heuristic reading of prose it also
authored. `_spawn_one()` gains a `single_phase: bool = False` parameter
threaded the same way `despite_returned` already is.

**Contract-line source — restate the rule vs. quote `directive.sh`
verbatim.** Considered writing a new, `spawn.py`-local sentence
describing the bypass. Rejected: `directive.sh:88-93` is the
authoritative wording contract v3 s19a already ships to every session
via the SessionStart hook; a second, differently-worded description of
the same rule risks drifting from it over future contract edits, and the
acceptance criterion explicitly asks for "the authoritative single-phase
contract line" (singular, definite article) — reusing the existing
wording, not paraphrasing it. The task-directive addition therefore
quotes/mirrors the same bypass-bullet text `directive.sh` emits (adjusted
from second-person "your issue" framing to spawn-time task-prefix
framing, matching how `_goal_pin_block()` already reuses issue text
verbatim rather than re-summarizing it, `spawn.py:7793-7818`), rather than
inventing new prose.

**Skill trigger extraction — parse full frontmatter YAML vs. regex the
"Use ..." sentence out of `description`.** Considered adding a YAML
parser dependency (or using one already imported) to fully parse
`SKILL.md` frontmatter and extract `description` as a structured field.
Rejected as more machinery than the acceptance criterion needs: the
criterion only requires the skill's name and its "Use when" trigger
line, not full frontmatter fidelity, and `SKILL.md` frontmatter across
this repo's observed skills (survey: `implementation-blueprint/SKILL.md`)
is not always single-line (`description: >-` folded block) — a full YAML
parse handles that correctly but a targeted extraction (read frontmatter
between `---` markers, then regex/split for a sentence starting "Use
" within the folded `description` block) is simpler, has no new
dependency, and directly matches the "Use ..." sentence pattern the
issue names. Chosen: targeted extraction function
`_skill_trigger_line(skill_dir: Path) -> str | None`, returning `None`
(not raising) when no "Use ..." sentence is found, satisfying the
"listed by name only, never dropped silently" empty-state clause.

**Where B reads directories for role-mapped skills.** Survey found
`role_source["skills"]` (skill-repository role mapping, #1955/#1758) is
names-only, no `dir`, unlike `--skills`-resolved `skill_sources`.
Considered leaving role-mapped skills out of the per-skill trigger-line
feature (name-only, as today). Rejected: the issue's acceptance
criterion says "a spawn with mounted skills" without distinguishing
`--skills` from role-mapped skills, and role-mapped skills are the more
common mount path in this repo's own role configs (survey: this issue's
own spawn prompt shows role-source skill-repository mapping for
`implementation`). Chosen: extend `role_source` construction (wherever it
resolves skill names, upstream of `spawn.py:7935`) to also carry each
skill's resolved `dir`, reusing the same skill-repo root resolution
`resolved_skill_sources()` already does — a small, additive field, not a
second resolution mechanism.

## What will be done

1. `spawn.py`: add `--single-phase` CLI flag; thread `single_phase: bool`
   through `_spawn_one()` the same way `despite_returned` is threaded.
2. `spawn.py`: when `single_phase` is true, (a) set
   `extra_env["CORE_BUILD_NOW"] = "1"` in the dict `spawn_cmd()` returns,
   and (b) append the single-phase contract line — sourced from
   `directive.sh`'s existing bypass-bullet wording — to the assembled
   `task` string in `_spawn_one()`. When false, `task`/`extra_env`
   assembly for this feature is skipped entirely (no new text, no new env
   key) — this is what keeps a spawn without the signal byte-identical.
3. `spawn.py`: add `_skill_trigger_line(skill_dir: Path) -> str | None`
   that reads `skill_dir / "SKILL.md"` frontmatter and extracts the
   sentence starting "Use " from the `description:` field; returns
   `None` if the file, frontmatter, or trigger sentence is absent.
4. `spawn.py`: extend the skill-listing block (`spawn.py:7930-7954`)
   to, for each mounted skill (both `--skills`-resolved `skill_sources`
   and role-mapped skills once `role_source` carries `dir`), append a
   line with the skill's name and its trigger line (or name only, per
   empty-state) — replacing the current generic #1960 nudge sentence.
   Ordering respects A: when `single_phase` is set, A's contract line is
   already in the task text before B's skill block is appended (A before
   B per the issue's sequencing).
5. `tests/test_spawn.py`: live-asserted tests per both acceptance
   checks — a spawn with `--single-phase` produces a directive containing
   the contract line and `CORE_BUILD_NOW=1` in extra_env; a spawn without
   it is byte-identical to a captured today's-output fixture; a spawn
   with a fixture skill dir (`SKILL.md` with a "Use when..." description)
   produces a directive containing the skill's name and trigger line; a
   fixture skill dir with no description is listed by name only; a spawn
   with zero mounted skills is unchanged from today.
6. `docs/handbooks/spawn-directive-assembly.md`: new handbook page
   documenting the `--single-phase` flag, the per-skill trigger-line
   mechanism, and pointers to `directive.sh`/`approval-gate.sh` as the
   channel's other half (cross-repo, not owned here).
7. Sketch (in this proposal document only, not a separate file — this
   issue's scope explicitly defers implementation) a guidance-reflection
   scoring rubric: instead of counting Skill-tool invocations, score
   whether a session's subsequent actions are consistent with a mounted
   skill's guidance (a reviewer or LLM-judge rubric reading the session
   transcript against the skill's stated method, scored per dimension the
   skill defines — e.g. did the session name the alternatives a
   design-pattern skill requires it to consider, even if it never called
   the Skill tool). This needs the skill-authoring side to define
   per-skill "what would following this look like" checkpoints before it
   is testable, which is out of this issue's scope per the issue's own
   deferral.

## Accumulation

Item 4 touches the same skill-listing block once per skill-mount source
(`--skills`-resolved and role-mapped) — two call sites, not a
per-role-file or per-skill repeated edit. If more skill sources are added
later (a hypothetical fifth tier), the trigger-line extraction helper
(`_skill_trigger_line`) is already shared and source-agnostic — a new
tier calls the same helper, it does not duplicate extraction logic. No
`roles/*.json`-style repeated one-line edits are introduced by this
change: the `--single-phase` flag and skill-trigger inlining are both
single code paths in `spawn.py`, not per-role or per-skill file edits, so
N more roles or N more skills adopting either feature costs zero
additional lines in this proposal's write set.

## Out of scope

- Any change to `directive.sh`, `approval-gate.sh`, or other
  `tokenmaxxxer-core` files — that repo's bypass mechanism is confirmed
  intact by the survey and needs no change.
- Implementing the guidance-reflection rubric itself (scoring code,
  transcript analysis, new measurement script) — sketch only, per the
  issue's explicit deferral.
- Changing `--skills` resolution semantics, the four-tier precedence
  rules, or the `hooks/`-forbidden check in `resolved_skill_sources()`.
- Any change to phase-2 approval gating, two-account/single-account
  detection, or PR trailer requirements.
- Retrofitting past spawns or existing open PRs to the new directive
  shape.

## How you'll know it worked

- `tests/test_spawn.py` live run: a spawn with `--single-phase` produces
  a task directive containing the authoritative single-phase contract
  line and sets `CORE_BUILD_NOW=1` in the returned `extra_env`; a spawn
  without the flag produces a task directive byte-identical to a fixture
  captured from today's code.
- `tests/test_spawn.py` live run: a spawn with a fixture skill directory
  (`SKILL.md` frontmatter carrying a "Use when..." sentence) produces a
  task directive containing that skill's name and its trigger line; a
  fixture skill directory with no description/trigger line is still
  listed by name, never dropped; a spawn with zero mounted skills
  produces a task directive unchanged from today.
- Both of the above match the issue's two acceptance `check:` bullets
  verbatim.

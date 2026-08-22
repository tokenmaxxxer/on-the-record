---
subject: issue-1978
kind: survey
---

# Survey: spawn directive assembly — single-phase signal + per-skill trigger lines

## Write surface

`_spawn_one()` in `spawn.py:7821-7954` assembles the task string handed to
the spawned session's stdin, and calls `spawn_cmd()` (`spawn.py:5434`) to
build the child process's argv/env. This is the only place in this repo
that builds the spawn-time task directive; the SessionStart directive text
quoted in this session's own context (containing "Build-now bypass
(contract v3 s19a)") is injected separately, by
`core/hooks/directive.sh` in the sibling `tokenmaxxxer-core` repo
(cloned locally at `/home/jwjung/tokenmaxxxer-core`, resolved at spawn
time via `core_root()`, `spawn.py:5179`).

## (A) Why the #1672 s19a bypass did not fire

canonical: `core/hooks/directive.sh:88-93` (read file:line, tokenmaxxxer-core
checkout) — states the bypass rule: "when the task that spawned this
session explicitly authorizes delivery-only — its environment carries
`CORE_BUILD_NOW=1`, set by the spawner, never by you". This is descriptive
text only; it does not itself set anything.

canonical: `core/hooks/approval-gate.sh:145-151` (read file:line) —
enforcement: `if os.environ.get("CORE_BUILD_NOW", "").strip() == "1":`
skips the phase-2 Approve gate. Both this and directive.sh read
`CORE_BUILD_NOW` only from the spawned session's own process environment,
which the contract text says must be "set by the spawner" — i.e. by
`spawn.py`, via the `extra_env` dict `spawn_cmd()` returns
(`spawn.py:5439`), applied at `spawn.py:7983-8002` before the child
`claude` process launches.

derived:
```
$ grep -rn "CORE_BUILD_NOW" --include="*.py" --include="*.sh" --include="*.md" . | grep -v "^docs/"
(no output)
```
`spawn.py` never sets `CORE_BUILD_NOW` in `extra_env`, and has no CLI
flag, task-text pattern match, or any other code path that could set it.
canonical: `spawn.py:6863-6939` (read file:line, `ap.add_argument` calls) —
every recognized CLI flag is listed there; none mention single-phase or
build-now.

canonical: `gh issue view 1978` (command run this session, "## Request"
paragraph A) — the issue body reports the two live failures (arcade-dodger
#6, #10, 2026-08-22): the spawn task text said "single-phase
implement+record" and both sessions still opened phase-1-only proposal
PRs. This survey did not re-run those two sessions; it takes their
occurrence as reported in the issue and traces the mechanism, below,
against the current code.

**Root-cause tracing:** the spawn task text carrying "single-phase" is
prose inside the `task` string parameter of `_spawn_one()`
(`spawn.py:7821`). canonical: `spawn.py:7919-7954` (read file:line, full
body of the task-assembly block in `_spawn_one`) — nothing in this block
parses `task` for a phase-mode signal or sets
`extra_env["CORE_BUILD_NOW"]`. A child session built from this code path
therefore always starts with `CORE_BUILD_NOW` unset regardless of what
the task prose says, so the `approval-gate.sh` bypass branch cannot take,
and the two-phase default applies — canonical:
`core/hooks/directive.sh:76-84` (read file:line): "Without
`CORE_BUILD_NOW=1` the default two-phase flow ... is unchanged". This
reads as a structural gap (no wiring exists), not a misfire of an
existing wire: the bypass mechanism itself is intact and correctly gated
in `tokenmaxxxer-core`; `spawn.py` simply never calls into it from task
text. Per the issue's own empty-state clause, this points the fix at
`spawn.py`'s missing wiring, not at the bypass's own semantics (which
need no change).

## (B) Why the #1960 skill nudge is ineffective

canonical: `spawn.py:7930-7954` (read file:line) — the block added for
#1742/#1774 and #1960 phase B does two things when skills are mounted:

1. `spawn.py:7930-7934` — lists mounted `--skills` names and their source
   descriptor (e.g. `implementation-blueprint (skill-repository(abc1234))`).
2. `spawn.py:7949-7954` — appends one generic sentence: "스킬 점검(이슈
   #1960): 실체 작업을 시작하기 전에, 위에 마운트된 스킬 목록을 이번
   과제와 대조하라. trigger 조건이 이번 과제에 그럴듯하게 들어맞는
   스킬이 있으면 Skill 도구로 호출하고, 없으면 검토했다는 사실만
   유념하고 넘어가라."

canonical: `gh issue view 1978` (command run this session, "## Request"
paragraph B) — the issue body reports the measured uptake, quoted
verbatim:
```
1/9 real sessions invoked a mounted skill; 0 even with an explicit
task pointer (measured with scripts/measure_skill_invocation.py
across today's arcade-dodger role chain)
```
This survey did not independently re-run that measurement script; the
figure is reported here only as the issue states it.

Each mounted skill's own trigger condition already exists and is
authoritative: `SKILL.md` frontmatter's `description:` field. canonical:
`skills/implementation-blueprint/SKILL.md:2-11` (read file:line, skill-repository
checkout at `/home/jwjung/tokenmaxxxer/rulebooks/skill-repository`):

```
description: >-
  Situational code-architecture selection backed by a queryable database and a
  deterministic CLI. Use whenever you are about to produce non-trivial code
  spanning multiple modules or files and need to decide structure — "how should
  I structure this", "what pattern should I use", "design the architecture",
  "이 코드 어떻게 구조화할까", "아키텍처 잡아줘" — or before fanning work out
  to parallel workers and needing the contract to freeze. Do NOT use for a
  single-file script, a one-line fix, or purely algorithmic work: run the
  classify step anyway if unsure — it vetoes structure for those cases.
```

The "Use ..." sentence (here starting "Use whenever you are about to
produce non-trivial code...") is the same trigger line the tool-search
skill listing surfaces for equivalent skills at the top of every session
(this session's own available-skills reminder shows, e.g.,
"implementation-design-pattern-selection: Use when deciding whether to
introduce a GoF-style design pattern..."). `spawn.py` currently discards
this text: canonical: `spawn.py:4987-5053` (read file:line, full body of
`resolved_skill_sources()`) — it never reads `SKILL.md`'s `description:`
field; each match dict carries only `name`/`source`/`dir` plus
source-identity fields (`sha`, `plugin`, `path`). Nothing extracts or
forwards the "Use ..." sentence into the spawn-time task directive. The
nudge sentence at `spawn.py:7949-7954` substitutes a generic "check
whether it fits" instruction for the actual per-skill trigger text — a
plausible mechanism for the low measured uptake cited above: the session
is asked to do the trigger-matching work itself from a skill list
carrying no trigger information, instead of being handed the match
condition directly.

## Skill mount plumbing relevant to both fixes

- canonical: `spawn.py:4987-5053` (read file:line) —
  `resolved_skill_sources()` resolves `--skills` names across four tiers
  (skill-repo, plugin, `~/.claude/skills`, repo `.claude/skills`) and
  returns one dict per name with a `dir: Path` pointing at the skill's
  directory. canonical: `spawn.py:4962-4971` (read file:line) —
  `_skill_content_hash()` reads `dir / "SKILL.md"` today for tier
  identity, so that read path is already proven to work per source tier.
- Role-mapped skills (skill-repository role mapping, #1955/#1758) are a
  separate list, `role_source["skills"]` (names only, no `dir`) — per
  canonical: `spawn.py:7935-7940` (read file:line), that block prints
  their names but the resolved directories are not threaded through to
  that print site the way `skill_sources` is. Per-skill trigger-line
  inlining for role-mapped skills needs either `role_source` to carry
  directories too, or a second resolve step against the same skill-repo
  root — an open design point the proposal addresses.

## Test-tier note

`.on-the-record/test-tiers.json` present at repo root; not run this
survey turn — no code changed yet, phase 1 is proposal-only, so there is
no diff to tier a test run against.

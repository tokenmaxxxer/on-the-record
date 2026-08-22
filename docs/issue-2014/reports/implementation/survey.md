---
subject: issue-2014
kind: survey
---

# Current-state survey — issue #2014 (artifact-gate phase 3, spawn-directive pairing)

## What exists today

- `gates/design_artifacts_gate.py::parse_declaration(body) -> list[str] | None`
  (issue #2013, `docs/issue-2013/reports/implementation.md`) parses a
  `design-artifacts:` tag line from an issue body into a list of declared
  paths, or `None` if the tag is absent. This is the only existing parser
  of the declaration; it is network-free (regex over the already-fetched
  body text) and byte-inert (returns `None`) when no tag exists.
  canonical: `gates/design_artifacts_gate.py:41-76`, read this session.
- `spawn.py::_spawn_one` (the function that assembles the task text handed
  to a spawned role session) already fetches the issue body once, at
  spawn.py:8081-8094, via `gh_rest.fetch_issue(Path(cwd), issue)` — used
  today only to extract cited-requirement IDs (`requirement_linkage
  .cited_requirement_ids`) and a goal-pin block. `body` is a local variable
  in scope through the rest of `_spawn_one`.
  canonical: `spawn.py:8078-8094`, read this session.
- `spawn.py::_skill_trigger_line(skill_dir) -> str | None` (issue #1978B)
  reads a mounted skill's `SKILL.md` frontmatter `description:` field and
  extracts the "Use ..." trigger sentence, returning `None` if the file,
  frontmatter, description, or trigger sentence is missing.
  canonical: `spawn.py:7923-7949`, read this session.
- `spawn.py::_tokenize` / `_cross_family_skill_matches` (issue #2001)
  already implement deterministic keyword-overlap scoring between a task
  text and a skill's trigger sentence (`_tokenize(task) & _tokenize(trigger)`,
  threshold `_CROSS_FAMILY_MIN_OVERLAP = 2`), used today to pick top-K
  skills from *outside* the role's own family. This is the only existing
  text-to-skill matching logic in spawn.py.
  canonical: `spawn.py:7952-7988`, read this session.
- The task-text assembly order inside `_spawn_one`, under `if issue is not
  None:`, is: base instructions → single-phase contract line (#1978A) →
  `--skills` roster line → role-mapped skill-repo roster line + cross-family
  add-on (#1978B/#2001) → issue #1960 skill-check nudge line. Each block is
  additive and gated so that its absence leaves the assembled text
  byte-identical to before that issue landed.
  canonical: `spawn.py:8110-8169`, read this session.
- Zero existing references to `design-artifacts` inside `spawn.py`.
  canonical: `grep -rn "design-artifacts" --include=*.py spawn.py`, run
  this session, zero matches.
- `docs/specs/design-artifacts-contract.md` (issue #2013) is the frozen
  spec for what a `design-artifacts:` declaration means: a tag line
  followed by a bulleted list or fenced block, one path per line; no
  further per-artifact typing or metadata (no "kind" field distinguishing
  a user-scenario doc from an IA/flow doc from an HTML demo) is declared
  in the syntax.
  canonical: `docs/specs/design-artifacts-contract.md`, read this session.

## What is missing / unknowns

- No code anywhere pairs a declared artifact path with a skill. The
  existing `_cross_family_skill_matches` scores task text against skill
  triggers, not artifact paths against skill triggers — the matching
  target differs (an artifact declaration line, e.g. `docs/issue-14/design
  /scenarios.md`, carries far fewer live tokens than a task description).
- The `design-artifacts:` syntax has no per-artifact "kind" tag (nothing
  marks `scenarios.md` as a user-scenario artifact vs `flow.md` as an
  IA/flow artifact) — the only text available to score against a skill's
  trigger sentence is the artifact's own file path (basename minus
  extension, e.g. `user-scenarios`, `flow`, `demo`).
- The issue's Acceptance text does not require a *unique* skill per
  artifact, nor does it require every artifact to find a match — the
  empty-state line ("directive lists mounted skills and (nothing about)
  artifacts separately; no pairing exists") describes today's behavior
  with no declaration or no match, implying pairing degrades gracefully
  per-artifact rather than failing the whole feature when one artifact has
  no matching mounted skill.

## Write surfaces for this delivery

- `spawn.py` (the only production file the issue's own `scope:` line
  names besides `tests/, test/, docs/`) — the pairing must live in
  `_spawn_one`'s task-text assembly, reusing `body` already fetched at
  spawn.py:8085 and reusing `_tokenize`/`_skill_trigger_line` (issue
  #2001/#1978B) rather than re-deriving matching logic.
- A test file under `test/` or `tests/` asserting both acceptance halves
  (paired line present when `design-artifacts:` exists and a mounted
  skill's trigger overlaps the artifact path; byte-identical directive
  with no `design-artifacts:` line).

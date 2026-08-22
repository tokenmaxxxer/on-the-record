---
status: proposed
files:
  - spawn.py
  - test/test_spawn_artifact_skill_pairing.py
---

# Proposal — pair each declared design artifact with its covering skill trigger (issue #2014, artifact-gate phase 3)

Scout skip: this delivery wires two already-landed internal contracts
together (design-artifacts declaration parsing, #2013; trigger-line
injection and cross-family scoring, #1978B/#2001) inside `spawn.py`'s own
directive-assembly code — no external product surface or prior-art field
applies; the only open design decision (how to score an artifact path
against a skill trigger) is answered by reusing an existing internal
pattern, not by surveying comparable products. Recorded per scout-directive
skip condition ("spec literally leaves no design decision open" beyond
which internal function to reuse).

## Request

Wire the `design-artifacts:` contract into the spawn directive: when the
issue body carries a `design-artifacts:` declaration, the assembled task
text lists, for each declared artifact path, one line pairing that path
with a mounted skill whose "Use ..." trigger sentence covers producing it
— so the spawned session sees artifact → skill → procedure as one unit,
instead of a skill roster and (today) nothing about artifacts at all. With
no `design-artifacts:` line, the directive stays byte-identical to today.

## Constraints

- Reuse, never re-derive: `parse_declaration` (#2013) for reading the
  declaration, `_tokenize`/`_skill_trigger_line` (#1978B/#2001) for
  scoring an artifact against a skill trigger. This delivery adds no new
  parsing or scoring primitive.
- Byte-identical with no `design-artifacts:` line (issue's own Acceptance
  text, second clause) — the new block must be additive and
  no-op-on-absence, the same shape every prior spawn-directive addition
  (#1978A, #1978B, #1960, #2001) already uses.
- Network-free at pairing time: the issue body is already fetched once at
  spawn.py:8085 for requirement-linkage/goal-pin; the pairing reuses that
  same `body` variable rather than issuing a second `gh` call.
- No per-artifact "kind" metadata exists in the declaration syntax
  (`docs/specs/design-artifacts-contract.md`) — matching an artifact to a
  skill must work from the artifact's file path text alone, not from an
  added tag, since changing the declaration contract is out of this
  issue's scope (`spawn.py` only, per the issue's own `scope:` line).

## Rationale

**Chosen approach:** score each declared artifact path's basename (minus
extension, tokenized the same way `_tokenize` already tokenizes task text)
against every mounted skill's trigger sentence, using the same
token-overlap function `_cross_family_skill_matches` already uses
internally, but applied per-artifact against the mounted-skill set rather
than once against the whole task text. Pick the mounted skill with the
highest overlap for each artifact (ties broken by skill name, matching
`_cross_family_skill_matches`'s existing sort key); an artifact with zero
overlap against every mounted skill gets no pairing line for itself (degrades
per-artifact, not all-or-nothing — matches the issue's empty-state
description, which is about the *absence of any pairing mechanism*, not
about every artifact necessarily resolving).

**Rejected alternative 1 — extend the `design-artifacts:` declaration
syntax with a per-artifact "kind" tag** (e.g. `- scenarios.md [kind:
user-scenario]`) and match on kind instead of path text. Rejected because
it requires changing `docs/specs/design-artifacts-contract.md` and
`gates/design_artifacts_gate.py`'s parser, both outside this issue's
`scope:` line (`spawn.py, tests/, test/, docs/` — the parser itself is
`gates/`, and the existence-gate's own frozen "Existence and minimal shape
only" principle, #2013, argues against growing the declaration syntax for
a directive-assembly concern).

**Rejected alternative 2 — a static lookup table mapping known artifact
filename patterns (`scenarios.md`, `flow.md`, `demo.html`) to skill
families**, hand-authored once. Rejected because it silently drifts from
whatever skill roster is actually mounted for a given role/repo (a skill
present in the table might not be mounted this run, and a newly-mounted
skill with a matching trigger would never be picked up without a code
change) — the existing #1978B/#2001 mechanism already solves exactly this
by scoring live trigger sentences of the skills actually mounted this run,
so reusing it keeps the pairing responsive to whatever skill set a given
spawn actually mounts, with no maintenance burden.

## Accumulation

This is the fifth additive block chained onto `_spawn_one`'s task-text
assembly (after #1978A single-phase line, #1978B/#2001 skill+trigger
roster, #1960 skill-check nudge) — each gated so its absence leaves prior
behavior byte-identical, the same shape this proposal's block follows. If
N more directive-assembly features land the same way, `_spawn_one` grows
one more `if <signal>: task = task + (...)` block per feature indefinitely,
with no shared helper for "append a gated, byte-identical-on-absence text
block." That growth is accepted here rather than fixed: introducing a
block-registration abstraction now, for a fifth instance, would be
premature generalization against a run of blocks that never needed one —
each existing block has distinct gating conditions and distinct source
data (skill roster vs single-phase flag vs artifact declaration), so a
shared abstraction would need to be general enough to swallow all of them,
which is exactly the over-abstraction failure mode. If a sixth or seventh
such block lands and the duplication (fetch signal → gate on presence →
format one line per item → append) becomes exact rather than merely
similar in shape, that is the point to extract a shared helper — not
before.

## What will be done

1. In `spawn.py`, inside `_spawn_one`, under `if issue is not None:`,
   after the existing issue #1960 skill-check block (spawn.py:8164-8169)
   and before the rulebook-mounting code, add: parse `design-artifacts:`
   from the already-fetched `body` via
   `gates.design_artifacts_gate.parse_declaration(body)`; if it returns a
   non-empty list, score each declared path's basename against the
   trigger sentences of all mounted skill dirs collected so far
   (`skill_dirs` from `--skills`, `role_source["skill_dirs"]`, and
   `cross_family_dirs`, deduplicated the same way `all_skill_dirs` already
   does a few lines below) and append one line per artifact that finds a
   match, in declaration order.
2. Each pairing line names the artifact path, the matched skill's name,
   and that skill's trigger sentence (reusing `_skill_trigger_line`)
   verbatim — the same "name — trigger sentence" shape the existing
   roster lines already use, so the new block reads as one family with
   them rather than a novel format.
3. If `parse_declaration(body)` returns `None` (no `design-artifacts:`
   tag) or an empty list, or if no declared artifact matches any mounted
   skill, no new block is appended — the assembled task text for those
   cases stays byte-identical to before this change.
4. Add `test/test_spawn_artifact_skill_pairing.py` asserting: (a) an issue
   body with a `design-artifacts:` declaration and a mounted skill whose
   trigger overlaps an artifact's basename produces one pairing line
   naming that artifact, that skill, and its trigger sentence; (b) an
   issue body with no `design-artifacts:` line produces a task text
   byte-identical to the same call with the tag stripped out — i.e. the
   new code path is a no-op when the tag is absent.

## Out of scope

- Any change to the `design-artifacts:` declaration syntax itself
  (`gates/design_artifacts_gate.py`, `docs/specs/design-artifacts-contract.md`)
  — out of this issue's `scope:` line.
- Guaranteeing every declared artifact finds a matching skill — an
  artifact whose basename shares no tokens with any mounted skill's
  trigger sentence gets no pairing line, per the Rationale's per-artifact
  degrade decision.
- Any new fetch of the issue body — the pairing reuses the `body` already
  fetched at spawn.py:8085 for requirement-linkage/goal-pin.

## How you'll know it worked

- For an issue with a `design-artifacts:` line and at least one declared
  path whose basename token-overlaps a mounted skill's trigger sentence,
  the assembled spawn directive contains a pairing line for that artifact
  naming the matched skill and its trigger sentence (Acceptance, first
  clause).
- For an issue with no `design-artifacts:` line, the assembled directive
  is byte-identical to the directive assembled today, before this change
  (Acceptance, second clause) — asserted by a unit test comparing the two
  call outputs.
- `test/test_spawn_artifact_skill_pairing.py` passes, covering both halves
  of the Acceptance text in one file (Acceptance's "unit tests assert
  both" clause).

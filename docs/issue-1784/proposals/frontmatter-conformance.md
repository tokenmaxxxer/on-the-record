---
status: proposed
files:
  - docs/issue-1784/reports/implementation.md
  - /tmp/skill-repository/scripts/check_skill_conformance.py
  - /tmp/skill-repository/scripts/normalize_skill_frontmatter.py
  - /tmp/skill-repository/skills/*/SKILL.md
---

## Request

skill-repository's 234 `skills/*/SKILL.md` files fail the SKILL.md
frontmatter convention: 11 have no frontmatter, 169 have only internal
fields (`axis:`, `rule_count_floor:`) with no `name:`/`description:`,
and 54 are already conformant. Build (a) a conformance checker,
`scripts/check_skill_conformance.py`, that fails loudly listing every
violator, and (b) a one-shot normalization pass that adds `name:` (==
dirname) and a when-to-use `description:` to the 180 non-conformant
skills while preserving `axis:`/`rule_count_floor:` and leaving every
existing body byte-identical. This is the mechanical layer only —
procedural-body rewriting is out of scope, no hooks, no changes to
spawn.py or the allowlist.

## Constraints

- Zero content loss: every skill's body (everything after the
  frontmatter block, or the whole file for the 11 no-frontmatter cases)
  must be byte-identical before and after normalization.
- No hooks of any kind — the checker is a standalone script, invoked
  manually or wired as a test entrypoint, never a PreToolUse/PostToolUse
  hook.
- `description:` must be non-empty and contain an actual usage/trigger
  clause, not a bare restatement of the title — the checker must reject
  a description that is just the title.
- `name:` must equal the skill's directory name exactly.
- The 54 already-conformant skills must not be touched at all (not even
  re-serialized) — re-emitting their frontmatter through a YAML dumper
  risks reordering keys or reflowing the multi-line `description: >-`
  blocks already in use, which would be a content change even if
  semantically equivalent.
- Work happens in the skill-repository checkout at /tmp/skill-repository
  and is delivered there as its own PR; this on-the-record repo only
  holds the survey/proposal/record docs under docs/issue-1784/.

## Rationale

**Chosen approach: text-level frontmatter surgery (regex-anchored
prepend/rewrite of only the frontmatter block), not full YAML
round-trip via a parser+dumper.**

Considered and rejected: parse the whole file with a YAML+Markdown
library (e.g. `python-frontmatter`), mutate the metadata dict, and
re-serialize. Rejected because PyYAML's dumper does not guarantee
byte-identical re-emission of the *existing* 54 conformant files'
frontmatter (key ordering, quoting style, and the `description: >-`
block scalar folding are dumper-version-dependent), and separately,
re-serializing the body Markdown even losslessly is unnecessary risk
against the frozen zero-content-loss requirement — the acceptance
criterion is checked by literal byte diff, so anything that touches
serialization of already-correct content is a strictly worse choice
than never opening that code path. Text-level surgery — read raw bytes,
locate the frontmatter delimiters (or their absence) with a plain
string scan, splice in a new frontmatter block only for the 180
non-conformant files, and copy the trailing bytes through unchanged —
makes the byte-identity property structural rather than something that
has to be verified after the fact and hoped for.

Also considered: deriving `description:` via an LLM call per skill for
richer prose. Rejected for this issue — the issue frames this as the
"mechanical layer only" with authoring quality as explicit follow-up
work, and a template-derived description (title + axis + a fixed
usage-clause pattern, e.g. "Use when applying <axis>-related rules for
<derived-domain>.") is mechanical, deterministic, and re-runnable,
matching the phase's scope.

## What will be done

1. `scripts/check_skill_conformance.py`: walk `skills/*/SKILL.md`,
   parse frontmatter (or note its absence), and for each file check
   `name == dirname` and `description` is non-empty and contains a
   usage/trigger indicator (heuristic: contains "use when", "use this",
   "trigger", or similar — refined during phase-2 build against the 54
   existing conformant descriptions as a corpus of what "real" looks
   like). Exits 0 with `"<n> skills checked"` on an all-conformant tree
   (including the vacuous `"0 skills checked"` case for an empty
   `skills/` dir), exits non-zero listing every violator (path + reason)
   otherwise.
2. `scripts/normalize_skill_frontmatter.py`: one-shot script, run once
   against the 180 non-conformant skills. For each: derive `name:` from
   the directory name, derive `description:` from the H1 title (present
   in all 234 files, confirmed in the survey) plus `axis:` (when
   present) via a fixed template, and splice a frontmatter block
   containing `name:`, `description:`, and any preserved `axis:`/
   `rule_count_floor:` in front of the untouched original bytes. Skips
   the 54 already-conformant files entirely (checker already passes on
   them).
3. Run the checker against the pre-change tree (non-zero, listing 180
   violators), run normalization, run the checker again against the
   post-change tree (zero), and run a byte-identity diff sweep
   (per-file body comparison, pre vs post) — all four executed live and
   pasted into the phase-2 implementation record.
4. Deliver as a PR against skill-repository's default branch, with this
   issue (#1784) referenced in the PR body.

## Out of scope

- Rewriting any skill body into trigger→steps→output procedural shape
  (explicit follow-up wave per the issue).
- Any hook wiring (PreToolUse/PostToolUse/etc.) invoking the checker
  automatically.
- Changes to `spawn.py` or the role-source allowlist.
- Touching the 54 already-conformant `SKILL.md` files.
- Deciding skill-repository's CI wiring beyond adding the script and
  documenting the invocation command; if a CI config file is discovered
  during phase-2 build, wiring it in is in scope, but no CI config was
  found during this survey.

## How you'll know it worked

- `python3 scripts/check_skill_conformance.py` exits non-zero on the
  pre-normalization tree, listing all 180 violators (11 no-frontmatter +
  169 axis-only), and exits 0 on the post-normalization tree — both runs
  pasted live in the phase-2 record.
- All 234 skills have `name:` == dirname and a non-empty, trigger-clause
  `description:` — checker output confirms this mechanically.
- A byte-identity sweep script diffs every skill's pre- and
  post-normalization body and reports zero differing files; its output
  is pasted live in the phase-2 record alongside the checker runs.

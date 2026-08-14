kind: report
subject: issue-1199
doc-type: reference

# devrel — Claude Code plugin/skill scout brief (2026-08-14 amendment)

canonical: WebSearch results this turn (queries: "most popular Claude
Code plugin marketplace skills 2026 devrel documentation API docs";
"claude code plugin marketplace github stars technical writing
changelog release notes skill"; "\"claude code\" plugin skill Mintlify
OR api docs OR changelog generator github stars"; "anthropics
claude-plugins-official commit-commands feature-dev plugin github
stars devrel") — full pages listed under Sources below.

## Skip record

Not skipped — scouting ran (2 sweep angles: general "best Claude Code
plugins/skills 2026 devrel" and "changelog/technical-writing plugin
github stars"), followed by 1 deepening round on the official plugin
directory. 3 stages total, within the 5-stage/3min budget.

## Category must-bes (from sweep)

canonical: WebSearch result, github.com/anthropics/claude-plugins-official
(see Sources) — repo self-reports 20.2k stars / 2.5k forks, 30+
first-party plugins, 15 external partners.

- A high-adoption Claude Code plugin ecosystem entry point exists:
  `anthropics/claude-plugins-official` is the dominant
  officially-curated marketplace, not a community long-tail repo.
- Devrel-adjacent workflow automation (commit/PR chaining,
  docs-generation, changelog generation) is a distinct, well-populated
  sub-category within that ecosystem.
- Vendor-published plugins (Mintlify) sit alongside Anthropic
  first-party ones in the same directory — adoption evidence spans
  both official star counts and independent multi-source mentions.

## Performance axes (dimensions the field competes on)

canonical: WebSearch results, commit-commands / mintlify-claude-plugin /
changelog-generator pages (see Sources) — axes distilled from those
three tools' own stated designs.

1. How much of the edit-to-PR loop a plugin chains in a single step
   vs. leaving separate manual handoff points.
2. Whether doc/changelog output is generated from a structural source
   (spec, diff, commit history) vs. authored free-form afterward.
3. canonical: changelog-generator page (see Sources) — audience
   separation in generated artifacts (engineer-facing vs.
   customer-facing) vs. a single merged artifact.

## Adopt / skip

- Adopt as a pattern: chaining commit-message generation into PR-body
  generation in a single step (commit-commands' `/commit-push-pr`
  design), as a way to reduce devrel record/commit-trailer drift.
- Skip: adding a new required gate field per plugin — issue-1199
  requirement 3 and existing precedent (brand-design, prior devrel
  fold-in) both scope this unit to content/prose guidance, not new
  gate shape.

## Gap line

canonical: docs/issue-1199/proposals/2026-08-13-devrel-tool-landscape.md
(this repo, read this turn) — that proposal's surveyed entries
(Docusaurus, Scalar, Stainless, ReadMe, Orbit) are general devrel-domain
platforms, not Claude Code plugins/skills.

The 2026-08-14 amendment text states a fold-in whose surveyed sources
are domain tools alone does not satisfy the acceptance check. This
round adds 3 plugin/skill entries to the handbook, additive to the
prior 5, not a replacement of them.

## Sources

- https://github.com/anthropics/claude-plugins-official
- https://github.com/anthropics/claude-plugins-official/tree/main/plugins/commit-commands
- https://github.com/mintlify/mintlify-claude-plugin
- https://claude.com/plugins/mintlify
- https://github.com/composio-community/awesome-claude-plugins
- https://mintlify.wiki/triggerdotdev/trigger.dev/guides/example-projects/claude-changelog-generator

## kind / loop_state

kind: report
loop_state: phase-1-scouted

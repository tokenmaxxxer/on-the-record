# Survey: skill-repository frontmatter conformance (issue-1784)

Subject: issue-1784
Upstream: skill-repository checkout at /tmp/skill-repository, branch `issue-1777-wave4-skill-migration` (clean, tracks `origin/issue-1777-wave4-skill-migration`), remote `git@github.com:tokenmaxxxer/skill-repository.git`.
canonical: `git status && git remote -v` (run in /tmp/skill-repository), executed live this session.

## What was checked

acceptance: `python3 <classification-script>` (run in /tmp/skill-repository, one-off inline script over `skills/*/SKILL.md`) — result:

```
total 234
no_fm 11
axis_only(no name/desc) 169
has_name_desc 54
other/error 0
```

Three distinct states exist across the 234 `skills/*/SKILL.md` files:

1. **No frontmatter at all (11 skills)** — file opens directly with an `# H1` title, e.g. `skills/accessibility-aria-and-contrast-rules/SKILL.md` starts `# Operational playbook: ARIA usage, contrast, and focus (issue-1174)`.
   canonical: `head -20 skills/accessibility-aria-and-contrast-rules/SKILL.md` (run in /tmp/skill-repository), executed live this session.
2. **Frontmatter with only internal fields (169 skills)** — `---\naxis: <slug>\nrule_count_floor: <int>\n---` followed by an `# H1` title and playbook body (research trail + numbered rules), e.g. `skills/api-design-error-design/SKILL.md`.
   canonical: `head -30 skills/api-design-error-design/SKILL.md` (run in /tmp/skill-repository), executed live this session.
3. **Frontmatter already carries `name:` (== dirname) and a description (54 skills)** — e.g. `skills/adversarial-review/SKILL.md`. These appear to be skills authored directly against the Claude Code SKILL.md convention rather than migrated from the rulebook; the proposal treats these as the byte-identical no-op case.
   canonical: `head -15 skills/adversarial-review/SKILL.md` (run in /tmp/skill-repository), executed live this session.

acceptance: same classification script as above — result: 0 entries in the `other/error` (malformed-YAML) bucket; all 234 files that have frontmatter parse cleanly under `yaml.safe_load`.

## Title/H1 availability for description derivation

acceptance: `python3 <H1-presence-scan-script>` (run in /tmp/skill-repository, scans first 5 body lines of every `skills/*/SKILL.md` for a `# ` line) — result: `0 []` (zero files missing an H1 in that window).

This title is the only reliably-present per-skill string besides `axis:` — it is the basis for deriving `name:`/`description:` text for the 180 non-conformant skills (11 no-frontmatter + 169 axis-only).

## Existing `scripts/` state

acceptance: `ls scripts/` (run in /tmp/skill-repository) — result: no output (directory empty or no matching entries).

There is no existing conformance checker and no existing normalization script. `scripts/check_skill_conformance.py` (required by acceptance criterion 1) does not yet exist; it is new to this issue, not a repair of an existing script.

## Body preservation constraint

For the 180 non-conformant skills, the "body" for byte-identity purposes is everything from byte 0 of the current file (no-frontmatter case) or everything after the closing `---\n` (axis-only case) through EOF. Normalization must prepend/rewrite only the frontmatter block and leave that trailing byte range untouched — this is directly checkable with a diff sweep comparing pre-change and post-change bodies per file, which is what acceptance criterion 2's "byte-identity sweep script" checks in phase 2.

## Open unknowns entering the proposal

- Whether `scripts/check_skill_conformance.py` should also become "the repo's test entrypoint" (acceptance criterion 1 says "wired as the repo's test entrypoint") — `ls scripts/` (cited above) shows no existing test runner config in this checkout's `scripts/`; the root of the checkout was not otherwise inspected for a CI config. The proposal names the wiring mechanism explicitly and treats CI-file discovery as a phase-2 step if a config surfaces.
- Description-text derivation is mechanical (title + axis + a fixed usage-clause template), not a rewrite of skill content — per the issue's "mechanical layer only" framing and the frozen no-content-loss principle.

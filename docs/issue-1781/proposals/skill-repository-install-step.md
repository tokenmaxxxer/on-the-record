---
status: proposed
files:
  - docs/handbooks/setup.md
  - README.md
---

# Setup docs: skill-repository install step

## Request

Add a skill-repository install step to `docs/handbooks/setup.md` (clone +
`MUSTER_SKILL_REPO` pointed at the checkout's `skills/` dir, plus the
fail-closed symptom for self-diagnosis), mention the third repo in
README's Quickstart with a link to setup.md, and document the four
`--skills` sources in one short paragraph. Bilingual (한국어/English),
matching the existing setup.md convention.

## Constraints

- Scope is exactly `docs/handbooks/setup.md` and `README.md` — no code
  changes (`_skill_repo_root()`, `resolved_skill_dirs()`,
  `resolved_skill_sources()` in `spawn.py` are unchanged; docs describe
  existing behavior only, per survey).
- Must state the fail-closed symptom (mapped role spawn refuses; exact
  message confirmed live in the survey) so a misconfigured consumer can
  self-diagnose without reading spawn.py source.
- Must warn against pointing `MUSTER_SKILL_REPO` at the checkout root
  (the #1761 operational note) — confirmed live in the survey to fail
  with a different, more confusing message ("모르는 스킬 ... 쓸 수 있는
  이름: docs, skills") than the "checkout not found" message, so it is
  worth calling out explicitly rather than leaving the user to guess from
  a symptom that doesn't obviously point at the root-vs-subdir cause.
- Bilingual mirroring: setup.md's existing sections are 한국어 then
  English, paragraph-for-paragraph. New content follows that pattern.

## Rationale

Two viable shapes for the install step, per the survey's "Alternatives
considered": (a) sibling-clone-as-default (`$TOKENMAXXXER_RULEBOOKS/skill-repository`,
zero-config, matching how rulebooks/core are documented today) or (b)
explicit `MUSTER_SKILL_REPO` export.

Rejected (a) alone: `_skill_repo_root()` genuinely supports the sibling
default and it's the lowest-friction path, but documenting *only* the
sibling clone would silently omit `MUSTER_SKILL_REPO`, which is the first
thing a consumer who cloned skill-repository somewhere else (their own
dev layout, a CI checkout path, etc.) needs to know exists — and it's the
env var actually named in the issue title and requirement 1
("MUSTER_SKILL_REPO points at skills/"). Documenting only the code path
that happens to need zero configuration would leave the override
undocumented for the reader who doesn't fit the zero-config case.

Chosen: document both, sibling-clone as the "if you follow this exact
layout, no env var needed" recommended default (mirrors how core/rulebooks
are already framed at setup.md:96-97, keeping voice consistent) and
`MUSTER_SKILL_REPO` as the explicit override for any other checkout
location — this is what the code actually supports, so docs shouldn't
pick one and hide the other.

## What will be done

1. `docs/handbooks/setup.md`: add a new numbered step to the existing
   "시작하기 / Getting started" per-target-repo (or machine-once, whichever
   reads more naturally next to the existing rulebook/core paragraph)
   section: clone `tokenmaxxxer/skill-repository` — either to the sibling
   path `$TOKENMAXXXER_RULEBOOKS/skill-repository` (zero-config) or
   anywhere else with `export MUSTER_SKILL_REPO=<checkout>/skills` pointed
   at the checkout's `skills/` subdirectory specifically (not the checkout
   root — call out the root-vs-`skills/` distinction explicitly, citing
   the confirmed-live symptom difference from the survey).
2. Same section: state the fail-closed symptom verbatim (the exact
   `sys.exit` message confirmed live in the survey) so a consumer hitting
   it can search-match and self-diagnose.
3. `docs/handbooks/setup.md`: add a short paragraph documenting the four
   `--skills` sources (skill-repository checkout, installed plugins'
   `skills/<name>/`, `~/.claude/skills/<name>`, target repo's
   `.claude/skills/<name>`) and the two fail-closed invariants (name found
   in >1 source; source directory carrying `hooks/`), near the existing
   `--skills` help-text area or as its own short subsection.
4. `README.md`: add one Quickstart line naming skill-repository as the
   third repo (alongside on-the-record itself and tokenmaxxxer-core, if
   those are already named — survey did not find core mentioned in
   README either; if so, follow the same pattern used for whatever is
   already there) with a link to the new setup.md step.
5. Bilingual mirroring for all setup.md additions, matching existing
   한국어-then-English paragraph pairs.

## Out of scope

- No change to `spawn.py`, `resolved_skill_dirs()`,
  `resolve_role_source()`, or any code path.
- No change to `docs/specs/role-source-allowlist.json` or skill mappings.
- No managed-clone auto-fetch for skill-repository (survey confirmed none
  exists today; adding one would be a code change, not a docs change).

## How you'll know it worked

Acceptance (from the issue): a fresh-install walkthrough following only
the updated docs reaches a successful mapped-role dry-run. The phase-2
record will paste the walkthrough commands and dry-run output executed
live from a clean-env simulation (unset `MUSTER_SKILL_REPO`, fresh temp
clone) — the survey already executed and pasted this walkthrough once
against the current (pre-doc-change) behavior; phase 2 re-runs it
following the updated doc text itself, word for word, to confirm the docs
as written actually produce the success path.

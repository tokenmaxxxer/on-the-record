# Conformance-review survey — issue-1790 (phase 1)

## Subject located

canonical: gh pr list --search "1790" --state all (run this session).
Phase-2 delivery under review: on-the-record commit `8fd565d7` ("issue-1790 phase-2: procedural-body authoring pilot wave record", PR #1798, MERGED), record at `docs/issue-1790/reports/implementation.md`.

canonical: gh pr view 7 --repo tokenmaxxxer/skill-repository (run this session, state=MERGED).
Upstream code artifact: `tokenmaxxxer/skill-repository` PR #7 ("Procedural-body authoring: pilot wave (upstream-defect-report + api-design)"), MERGED, commit `bb89bdc`.

## Acceptance surface (from issue #1790)

canonical: gh issue view 1790 (Acceptance section, read this session).
Two acceptance requirements, both `provenance: executed-live`:
1. All 9 pilot skills have Trigger/Procedure/Output-shape sections, a derived (non-template) `description:`, and every pre-existing rule line still present — check: checker run with the manifest (exit 0) plus a rule-retention sweep pasted in the record, executed live.
2. Non-pilot skills untouched and full-tree checker exits 0 — check: `git diff --stat` limited to the 9 pilot paths + checker/manifest, and a full-tree checker run, both pasted in the record.

## What the phase-2 record claims

canonical: docs/issue-1790/reports/implementation.md:70-231 (read this session).
`docs/issue-1790/reports/implementation.md` pastes: a manifest-mode checker run (234 skills, exit 0), a per-file rule-retention grep sweep (89 rule lines across 9 skills, all retained), a `git diff --stat` scoped to 11 files, and a full-tree checker run (234 skills, exit 0).

## Independent verification already performed this session

canonical: `python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt` (run in /tmp/skill-repo-verify, this session).
Re-cloned `tokenmaxxxer/skill-repository` fresh to `/tmp/skill-repo-verify` at commit `bb89bdc` and re-ran the manifest checker: 234 skills checked, exit 0 — matches the record's claim.

canonical: `python3 scripts/check_skill_conformance.py` (run in /tmp/skill-repo-verify, this session).
Re-ran the full-tree checker (no `--manifest`): 234 skills checked, exit 0 — matches.

canonical: `git diff --stat ad577a4 bb89bdc` (run in /tmp/skill-repo-verify, this session).
Re-ran `git diff --stat ad577a4 bb89bdc`: 11 files changed, 432 insertions, 9 deletions, exactly the 9 skill paths plus `scripts/check_skill_conformance.py` and `scripts/procedure_authored_skills.txt` — matches the record's pasted `--stat --cached` output.

canonical: `git diff ad577a4 bb89bdc -- skills/` (run in /tmp/skill-repo-verify, this session).
Ran `git diff ad577a4 bb89bdc -- skills/ | grep '^-' | grep -v '^---'`: output was exactly the 9 template `description:` lines, no line under any `## Rules` block — corroborates the record's rule-retention sweep by a different method (full removed-line diff vs. the record's per-line grep sweep).

canonical: skills/api-design-error-design/SKILL.md:1-40 (bb89bdc, read this session).
Spot-read `skills/api-design-error-design/SKILL.md` lines 1-40: Trigger/Procedure/Output-shape sections present, description rewritten away from the template form, Procedure steps cite rule numbers.

canonical: derived — sed-stripped-heading + checker rerun (this session, /tmp/skill-repo-verify, file restored from backup after).
Adversarially tested the checker: pointed `--manifest` at a file listing only `api-design-error-design` with its `## Trigger` heading stripped (via `sed`); the checker failed with `missing procedure section(s): ## Trigger`, exit 1 — the gate rejects a real violation, not a rubber stamp.

## Gaps / what remains for phase 2

canonical: this session's own command output cited in each bullet above (checker runs, diff --stat, removed-line diff, spot-read, adversarial test).
Every independently-reproduced check above matched the record's claims.

No design decision remains open: phase 2 is rendering a fixed-format per-requirement verdict from already-completed verification, not making a new judgment call — scout-directive skip condition (spec leaves no design decision open) applies and is restated in the proposal.

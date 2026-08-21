---
code_under_review:
  - docs/specs/role-source-allowlist.json
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# Phase-2 delivery: skill-axis phase-3 pilot (#1761)

## Summary of work

Delivered the two PRs named in the approved proposal
(docs/issue-1761/proposals/skill-axis-phase-3-pilot.md, approved via
`APPROVE issue-1761/implementation`):

1. **skill-repository content PR**:
   https://github.com/tokenmaxxxer/skill-repository/pull/1 — adds
   `skills/upstream-defect-report-subtraction/SKILL.md`,
   `skills/upstream-defect-report-comprehensibility/SKILL.md`,
   `skills/upstream-defect-report-convention/SKILL.md`, each byte-equal
   to the corresponding `/tmp/udr-rulebook/playbook/*.md` source file,
   no `hooks/` dir anywhere under the three new skill dirs. Merge sha at
   evidence-capture time: `3b0c5f5`.
2. **on-the-record allowlist PR** (this branch/PR, commit `64ae3c34`):
   adds `docs/specs/role-source-allowlist.json` mapping
   `"upstream-defect-report"` to the three skill names above, reusing
   #1758's `resolve_role_source()`/`_role_source_allowlist()` and
   #1742's `resolved_skill_dirs()`/`skill_repo_sha()` exactly as merged
   — no spawn.py code changed.

## Why

Per #1758's frozen phasing, `upstream-defect-report-rulebook` is the
per-rulebook-migration audit's only zero-hook rulebook, so no
enforcement question exists for it — the natural low-traffic-first
pilot for the skill-axis migration. See the proposal's Rationale for
why per-axis role-prefixed skill dirs were chosen over one umbrella
directory per rulebook, and why the equivalence evidence below is
produced by calling `resolve_role_source()`/`spawn_cmd()` directly
rather than via the CLI `--dry-run` flag (which does not itself call
either function — survey finding, unchanged by this delivery).

## Upstream / basis

docs/issue-1761/proposals/skill-axis-phase-3-pilot.md (approved),
docs/issue-1761/reports/implementation/survey.md,
docs/issue-1761/reports/implementation/hunt-skill-axis-phase-3-pilot.md

## Equivalence evidence (3-check acceptance, #1758's frozen phasing)

### Check 1 — byte-equal skill content (recursive diff, empty output)

canonical: `diff` invocations executed live this turn, working tree
`/tmp/udr-rulebook` (rulebook source) vs `/tmp/skill-repository`
(this issue's skill-repository clone, branch
`issue-1761-udr-skill-migration`, now PR #1 above)

derived: diff /tmp/udr-rulebook/playbook/subtraction.md /tmp/skill-repository/skills/upstream-defect-report-subtraction/SKILL.md; echo "exit:$?"
```
exit:0
```

derived: diff /tmp/udr-rulebook/playbook/comprehensibility.md /tmp/skill-repository/skills/upstream-defect-report-comprehensibility/SKILL.md; echo "exit:$?"
```
exit:0
```

derived: diff /tmp/udr-rulebook/playbook/convention.md /tmp/skill-repository/skills/upstream-defect-report-convention/SKILL.md; echo "exit:$?"
```
exit:0
```

All three diffs are empty (exit 0, no output) — the migrated
`SKILL.md` files are byte-equal to their rulebook sources. Per-file
diff, not a single directory-tree diff, because the source and target
directory layouts intentionally differ (proposal's Rationale: rulebook
uses `playbook/<axis>.md`, skill-repository uses one directory per
axis named `SKILL.md`).

derived: find /tmp/skill-repository/skills/upstream-defect-report-subtraction /tmp/skill-repository/skills/upstream-defect-report-comprehensibility /tmp/skill-repository/skills/upstream-defect-report-convention -iname hooks
```
(no output)
```
No `hooks/` directory under any of the three migrated skill dirs.

### Check 2 — pre/post `resolve_role_source()`/`spawn_cmd()` argv/env diff, plus one unrelated role byte-identical

Per the proposal's Constraints, the CLI `--dry-run` branch does not
itself call `resolve_role_source()` or `spawn_cmd()` (survey finding,
spawn.py lines 7232-7253 call only `role_settings()`), so this evidence
is produced by calling `resolve_role_source()`/`spawn_cmd()` directly —
the same level #1758's own test suite exercises — stated here plainly
rather than implying the bare CLI flag shows it.

Method: `docs/specs/role-source-allowlist.json` was moved aside to
capture the "pre" state (file absent — today's/pre-merge behavior),
then restored to capture "post" (file present, this PR's content),
with `MUSTER_SKILL_REPO=/tmp/skill-repository/skills` set for "post"
only (per the Constraints note: `resolved_skill_dirs()` requires skill
names as immediate children of `MUSTER_SKILL_REPO`, and
skill-repository's real layout nests skills one level under `skills/`,
so `MUSTER_SKILL_REPO` must point at the clone's `skills/`
subdirectory, not its root).

derived: python3 /tmp/evidence_full.py (a small ad hoc script calling `spawn.resolve_role_source()`/`spawn.spawn_cmd()` directly, per the proposal's Rationale — not committed to the write set)
```
### PRE mapped argv ###
["claude", "-p", "--settings", "settings.json", "--permission-mode", "bypassPermissions", "--output-format", "stream-json", "--verbose", "--model", "sonnet"]
### POST mapped argv ###
["claude", "-p", "--settings", "settings.json", "--permission-mode", "bypassPermissions", "--output-format", "stream-json", "--verbose", "--plugin-dir", "/tmp/skill-repository/skills/upstream-defect-report-subtraction", "--plugin-dir", "/tmp/skill-repository/skills/upstream-defect-report-comprehensibility", "--plugin-dir", "/tmp/skill-repository/skills/upstream-defect-report-convention", "--model", "sonnet"]
### argv equal (mapped)? ### False

### PRE mapped env ###
{"CLAUDE_ROLE": "upstream-defect-report", "GIT_TERMINAL_PROMPT": "0", "TOKENMAXXXER_SPAWNED": "1", "TOKENMAXXXER_UNATTENDED": "1"}
### POST mapped env ###
{"CLAUDE_ROLE": "upstream-defect-report", "GIT_TERMINAL_PROMPT": "0", "MUSTER_SKILLS": "upstream-defect-report-subtraction,upstream-defect-report-comprehensibility,upstream-defect-report-convention", "MUSTER_SKILL_REPO_SHA": "3b0c5f5", "TOKENMAXXXER_SPAWNED": "1", "TOKENMAXXXER_UNATTENDED": "1"}

### PRE unrelated (architecture) argv ###
["claude", "-p", "--settings", "settings.json", "--permission-mode", "bypassPermissions", "--output-format", "stream-json", "--verbose", "--model", "sonnet"]
### POST unrelated (architecture) argv ###
["claude", "-p", "--settings", "settings.json", "--permission-mode", "bypassPermissions", "--output-format", "stream-json", "--verbose", "--model", "sonnet"]
### unrelated argv byte-identical? ### True
### PRE unrelated env ###
{"CLAUDE_ROLE": "architecture", "GIT_TERMINAL_PROMPT": "0", "TOKENMAXXXER_SPAWNED": "1", "TOKENMAXXXER_UNATTENDED": "1"}
### POST unrelated env ###
{"CLAUDE_ROLE": "architecture", "GIT_TERMINAL_PROMPT": "0", "TOKENMAXXXER_SPAWNED": "1", "TOKENMAXXXER_UNATTENDED": "1"}
### unrelated env byte-identical? ### True
```

(`GH_TOKEN` was excluded from the printed env dicts by the capture
script since its value is a live credential, not a resolution-source
signal — it is set identically in every capture branch by
`_resolve_gh_token()`, unrelated to the allowlist mapping.)

Result: for the mapped role (`upstream-defect-report`), post-mapping
argv gains exactly three `--plugin-dir` flags (the three migrated skill
dirs) and post-mapping env gains exactly `MUSTER_SKILLS` and
`MUSTER_SKILL_REPO_SHA` — no other argv/env element changes. For the
unrelated, unmapped role (`architecture`), argv and env are
byte-identical pre/post (both `True` above) — the allowlist mapping
affects only the mapped role, exactly as acceptance 2 requires.

### Check 3 — roster/record field inspection

derived: `spawn._role_source_roster_fields(resolve_role_source("upstream-defect-report", root, skill_repo_root), rulebook_sha)` (same capture script, post-mapping state, `MUSTER_SKILL_REPO=/tmp/skill-repository/skills`)
```
{"resolution_skill_sha": "3b0c5f5", "resolution_skills": ["upstream-defect-report-subtraction", "upstream-defect-report-comprehensibility", "upstream-defect-report-convention"], "resolution_source": "skill-repo"}
```

`resolution_source` is `"skill-repo"`, `resolution_skills` lists
exactly the three migrated skill names, and `resolution_skill_sha`
(`3b0c5f5`) matches the skill-repository PR branch's own commit sha —
the roster/record fields carry skill-repo source+sha for the mapped
role, per #1758's `_role_source_roster_fields()` contract.

## What did not work

None.

## Out of scope (unchanged from the proposal)

canonical: `git show --stat 64ae3c34` (this branch's allowlist commit,
executed live this turn) and the skill-repository PR diff at
https://github.com/tokenmaxxxer/skill-repository/pull/1 — both
consulted this turn to confirm the write set actually landed.

derived: git show --stat 64ae3c34
```
 docs/specs/role-source-allowlist.json | 7 +++++++
 1 file changed, 7 insertions(+)
```

Per the frozen proposal's Out of scope section, this delivery's write
set touched only `docs/specs/role-source-allowlist.json` (this repo,
the single file in the commit shown above) and the three new
`SKILL.md` files under `skills/upstream-defect-report-*`
(skill-repository PR #1) — no other file in either repo:

- `upstream-defect-report-rulebook` was not archived, retitled, or
  otherwise modified — no commit against that repository was made this
  session.
- No other rulebook's skills were migrated.
- No `spawn.py` line changed (`--dry-run` branch, `resolve_role_source()`,
  `resolved_skill_dirs()`, or any other function) — the commit shown
  above touches only `docs/specs/role-source-allowlist.json`, no
  `spawn.py` hunk.

## Open findings

None.

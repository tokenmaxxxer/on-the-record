---
code_under_review:
  - spawn.py
  - test/test_spawn_skills_mount.py
type: feature
breaking: false
verdict: pass
loop_state: landed
---

# issue-1774 phase 2: --skills four-source resolution

## What was done
Implemented the frozen four-tier `--skills` resolution model from the
approved proposal (`docs/issue-1774/proposals/plugin-skill-resolution.md`,
approved via `APPROVE issue-1774/implementation`), in spawn.py:

- `_installed_plugin_skill_dirs()`: reads
  `~/.claude/plugins/installed_plugins.json`, indexes each installed
  plugin's `skills/<name>/` by name -> `(qualifier, dir, version)`.
- `_local_skill_dirs(root)`: lists a root's immediate subdirectories as
  candidate skill names -> `Path`; shared by the user-level
  (`~/.claude/skills`) and target-repo (`<target-repo>/.claude/skills`)
  local sources.
- `_skill_content_hash(dir)`: sha256 of `SKILL.md` bytes — the local
  sources' identity field (no repo sha or plugin version available).
- `resolved_skill_sources(skills_csv, repo_root, home=, target_repo_root=)`:
  resolves each requested name across the skill-repo, installed-plugin,
  user-local, and repo-local sources into one dict per name
  (name/source/dir plus source-specific identity fields). Zero matches:
  same fail-message shape as before. Two or more matches, any
  combination including two distinct plugins colliding inside the
  plugin source: a single hard exit naming every matching source, no
  precedence between them. A resolved `dir` carrying `hooks/`: hard
  exit, same guidance-only rule as the pre-existing skill-repo path,
  applied uniformly to all four sources. Empty `skills_csv`: returns
  `[]`, touches none of the four sources.
- `_skill_source_roster_row(m)` / `_skill_roster_fields(sources, sha)`:
  build the additive `skills_detail` list (per-skill source identity,
  shape depends on the source) plus the flat `skills`/`skills_sha` keys
  — the flat keys are added only when every resolved name is a
  skill-repo match, so a skill-repo-only composition's roster shape is
  unchanged from before this diff.
- `_spawn_one()` now calls `resolved_skill_sources()` instead of the
  prior `resolved_skill_dirs()` for the `--skills` path (the
  role-source-allowlist path, issue #1758, is untouched — out of this
  issue's scope), and threads the co-injected task string and both
  roster registration sites (the early fork-child entry and the main
  `roster_register` call) through `_skill_roster_fields()`.

`resolved_skill_dirs()` (skill-repo-only) is unmodified and still backs
`resolve_role_source()` — out of this issue's scope per the proposal's
Out of scope section.

## Why
Per the approved proposal: the issue's SCOPE EXTENSION comment
supersedes the original "repo silently wins" design — any name matching
more than one of the four sources must be a hard, uniform error, and
the two local sources (which already auto-load into interactive
sessions) become `--skills`-selectable and recorded, using local path
plus `SKILL.md` content hash as their identity since they carry no repo
sha or plugin version.

## Upstream basis
`docs/issue-1774/proposals/plugin-skill-resolution.md` (approved via
`APPROVE issue-1774/implementation`, issue comment) — the frozen
four-tier model, including the rejected-alternative rationale (silent
per-tier precedence; full-tree vs. `SKILL.md`-only content hashing).

## Test plan / what ran
New cases added to `test/test_spawn_skills_mount.py`:
`ResolvedSkillSourcesFourTierTest` (no-names reads nothing; each source
resolves alone; nowhere-found exit; the five ambiguity pairings, each
asserting the exit message names every matching source; `hooks/`
refusal for all four sources) and `SkillRosterFieldsFourTierTest`
(record-field shape per source, skill-repo-only flat-shape
preservation, mixed-source and empty-source cases).

canonical: python3 -m pytest -q test/test_spawn_skills_mount.py
```
31 passed in 0.85s
```

Also re-ran the project's fast test tier
(`.on-the-record/test-tiers.json`'s `fast` command) to check for
regressions:

canonical: python3 -m pytest -q -m "not slow"
```
2 failed, 2343 passed, 18 xfailed, 3 xpassed in 35.59s
```

The two failing tests (`test_gh_quota_guard.py::test_sweep_call_budget`,
`test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts`)
are `gh`-call-count assertions in board-sweep code this diff never
touches. They reproduce the same way on the unmodified tree:

canonical: git stash && python3 -m pytest -q tests/test_gh_quota_guard.py::test_sweep_call_budget "tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts" && git stash pop
```
FAILED tests/test_gh_quota_guard.py::test_sweep_call_budget
FAILED tests/test_spawn.py::PollHeartbeatMarkerRelocationTest::test_board_wide_sweep_issue_view_call_count_constant_across_subject_counts
```

Did not additionally run the `slow` test-tier command beyond the fast
tier and the fully-run (not `slow`-marked) `test_spawn_skills_mount.py`
within this turn's time budget — noting the tiering gap per the
session's test-tier directive.

## What did not work
None.

## Rationale for deviations
No divergence from the approved proposal's plan. One implementation
simplification within that plan's stated freedom: the per-name lazy
tier-skip the proposal described as an accumulation-cost optimization
was not implemented; `resolved_skill_sources()` always builds every
source's index once `--skills` names at least one skill, and checks
every name against every source (needed regardless, to catch
cross-source ambiguity). The only behavior-visible "never read"
constraint — the no-`--skills`-flag case — is unaffected:

canonical: python3 -m pytest -q test/test_spawn_skills_mount.py::ResolvedSkillSourcesFourTierTest::test_no_names_reads_nothing
```
1 passed
```

## Open findings
None.

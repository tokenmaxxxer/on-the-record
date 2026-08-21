# Current-state survey: skill-axis phase-3 pilot (issue #1761)

## Rulebook source (pilot target)

canonical: /tmp/udr-rulebook (local checkout of
git@github.com:tokenmaxxxer/upstream-defect-report-rulebook.git, HEAD
5a4c0ab)

derived: find /tmp/udr-rulebook -mindepth 1 -maxdepth 2 -not -path '*/.git*'
```
/tmp/udr-rulebook/README.md
/tmp/udr-rulebook/playbook
/tmp/udr-rulebook/playbook/comprehensibility.md
/tmp/udr-rulebook/playbook/convention.md
/tmp/udr-rulebook/playbook/subtraction.md
```

derived: find /tmp/udr-rulebook -iname hooks
```
/tmp/udr-rulebook/.git/hooks
```
Only the git-internal `.git/hooks` (sample hooks, never executed by
Claude CLI plugin mounting) — no plugin-level `hooks/` dir anywhere in
the checkout. This matches the issue's premise that this rulebook is
the audit's only zero-hook rulebook.

Each `playbook/*.md` file carries `axis:`/`rule_count_floor:`/`role:`
front matter for `gates/playbook_depth_gate.py` (parent repo).
canonical: /tmp/udr-rulebook/playbook/subtraction.md lines 1-5 (read via
Read tool) — front matter reads `axis: subtraction`,
`rule_count_floor: 5`, `role: upstream-defect-report`.

derived: wc -l /tmp/udr-rulebook/playbook/*.md
```
   65 /tmp/udr-rulebook/playbook/comprehensibility.md
   83 /tmp/udr-rulebook/playbook/convention.md
   79 /tmp/udr-rulebook/playbook/subtraction.md
  227 합계
```

`README.md` is repo-level scaffolding prose (why this repo exists, its
layout, program provenance), not itself a playbook rule file — the
issue's deliverable 1 phrase "the rulebook's skill content" is read
here as the three `playbook/*.md` files, not the README.

## Role spec (this repo)

canonical: roles/upstream-defect-report.json (read via Read tool)

`report_only: true`, `board_condition: N/A` per its own `use_when`
field — a report-only channel that does not go through the normal
spawn pipeline board gates. No `hooks/` reference in the role spec
either.

## role-source-allowlist mechanism (issue #1758, landed at 0bf2faa5,
already on this branch)

canonical: spawn.py (this branch's working tree, read via Read tool,
lines 5195-5245 and 7860-7900)

- `_role_source_allowlist(root)` (spawn.py:5195) reads
  docs/specs/role-source-allowlist.json (a path relative to `root`)
  under `root`; returns `{}` if the file is absent.
- `resolve_role_source(role, root, repo_root)`: unmapped role ->
  `{"source": "rulebook", "skill_dirs": [], "skills": [],
  "skill_sha": None}`; mapped role -> resolves the allowlist's skill
  names via #1742's `resolved_skill_dirs(csv, repo_root)` (fail-closed,
  `sys.exit` before workspace/branch mutation, on any unknown name),
  then fail-closed `sys.exit` if any resolved skill dir contains a
  `hooks/` subdirectory.
- `_spawn_one()` calls `resolve_role_source()` at the same point
  `--skills` already resolves (before `issue_workspace()`/
  `checkout_issue_branch()`), skips `plugin_dirs()`/`checkout_version()`
  entirely for a mapped role (`plugins = [] if mapped else
  plugin_dirs(...)`), and merges the mapped skill dirs additively into
  the same `--plugin-dir` list `--skills` builds.
- Roster entries always carry `resolution_source` (`"rulebook"` or
  `"skill-repo"`), plus `resolution_rulebook_sha` (unmapped) or
  `resolution_skills`/`resolution_skill_sha` (mapped) —
  `_role_source_roster_fields()`, wired at both the early and full
  roster-entry call sites.

derived: grep -n "def _role_source_allowlist\|def resolve_role_source\|def _role_source_roster_fields" spawn.py
```
5195:def _role_source_allowlist(root: Path) -> dict:
5205:def resolve_role_source(role: str, root: Path, repo_root: Path | None) -> dict:
5231:def _role_source_roster_fields(role_source: dict, rulebook_sha: str | None) -> dict:
```

Existing coverage of this mechanism is generic (synthetic role/skill
names), not scoped to any real role.
canonical: docs/issue-1758/reports/implementation.md's summary-of-work
section (read via Read tool) — lists mapped-role resolution, both
refusal cases, mount-layout assertions (no rulebook plugin dir for a
mapped role; byte-identical spawn_cmd() argv/env for an UNMAPPED role),
and roster record-fields shape for mapped/unmapped/empty-state, all
against synthetic fixtures created inside the test file, not any real
role. Issue #1761's 3-check acceptance reuses this same evidence shape
but must be produced against the real `upstream-defect-report` role and
its real migrated skills.

## `--skills`/`--dry-run` mechanics that bound the equivalence evidence

canonical: spawn.py (this branch's working tree, read via Read tool,
lines 5147-5184 and 7220-7261)

- `_skill_repo_root()` (spawn.py:5147): resolves via `MUSTER_SKILL_REPO`
  env, else `$TOKENMAXXXER_RULEBOOKS/skill-repository` sibling
  convention; `None` if neither exists.
- `resolved_skill_dirs(skills_csv, repo_root)` (spawn.py:5166): treats
  each name as an immediate child directory of `repo_root`
  (`repo_root.iterdir()` builds the "available" list).
  canonical: test/test_spawn_skills_mount.py lines 82-84 (read via Read
  tool) — its fixture creates `self.repo_root / "alpha"` directly, no
  intermediate `skills/` subdirectory inside the resolved root.
- The `main()` CLI `--dry-run` branch (spawn.py:7232-7253) calls
  `role_settings(a.role, a.cwd)` only. It does not call
  `resolve_role_source()`, `plugin_dirs()`, or `spawn_cmd()`.
  canonical: spawn.py lines 7232-7253 (read via Read tool, full branch
  body) — the only one of those four functions the branch calls is
  `role_settings()`.

Consequently the CLI `--dry-run` flag's current JSON output does not
itself surface a rulebook-vs-skill-repo resolution difference. Issue
#1758's own equivalence evidence instead exercised
`resolve_role_source()`/`spawn_cmd()` directly inside its test file, not
via the CLI `--dry-run` flag's printed output — issue #1761's acceptance
2 names `--dry-run` explicitly, which this survey flags as a gap
between the acceptance wording and today's `--dry-run` branch body: this
is not a phase-1 design decision to resolve so much as a boundary the
phase-2 equivalence evidence has to work around (produce the argv/env
diff at the `resolve_role_source()`/`spawn_cmd()` call level, the same
level #1758's own suite already exercised, and say so plainly in the
record rather than claiming the CLI flag itself already shows it).

## skill-repository target layout

canonical: `gh api repos/tokenmaxxxer/skill-repository/contents/` and
`gh api repos/tokenmaxxxer/skill-repository/contents/skills` (executed
live this turn)

derived: gh api repos/tokenmaxxxer/skill-repository/contents/
```
.gitignore, README.md, docs/, install.sh, skills/
```
derived: gh api repos/tokenmaxxxer/skill-repository/contents/skills
```
33 flat directories, e.g. diagnose-first, decision-brief, ... — none
role-prefixed
```
`skills/diagnose-first` contains `SKILL.md` + `references/` — the
repo's own convention for one skill unit is `<name>/SKILL.md` (+
optional supporting files), not a bare renamed copy of an arbitrary
source file.
canonical: gh api repos/tokenmaxxxer/skill-repository/contents/skills/diagnose-first
(executed live this turn) — listing returns exactly `SKILL.md` (file)
and `references` (dir).

No role-prefixed skill directory exists yet anywhere under
skill-repository's skills/ — this pilot is the first rulebook-to-
skill-repository migration under this mechanism. No naming convention
for a migrated rulebook's per-axis skill names is recorded anywhere in
this repo's docs/specs or in #1758's proposal/record — this is an open
design decision the proposal settles (see the proposal's Rationale).

## docs/specs/role-source-allowlist.json (target of this issue's PR 2)

derived: test -f docs/specs/role-source-allowlist.json && echo present || echo absent
```
absent
```
canonical: the `test -f` command above, executed live this turn — the
file this issue's second PR will add does not exist on this branch yet.
This is the acceptance-2 empty-state the issue itself names ("before
the allowlist PR merges, behavior is unchanged"): today
`_role_source_allowlist()` returns `{}` for the missing path, so every
role including `upstream-defect-report` resolves as
`"source": "rulebook"`.

## Write set (this repo, on-the-record) — per the issue's own scope line

- A JSON file at docs/specs (path role-source-allowlist.json,
  currently absent per above) — new — role/skill mapping for
  `upstream-defect-report`.
- docs/issue-1761/** — this survey, the proposal, and the phase-2
  implementation record carrying the 3-check equivalence evidence.

The skill-repository content copy (deliverable 1: the migrated
playbook files under skills/) lands in a separate GitHub repository
(tokenmaxxxer/skill-repository), outside this session's git working
tree and outside the issue's own declared scope line for this repo's
write set. This survey records what that migration is expected to
contain so the proposal's plan can name it precisely; the file write
itself happens as a separate PR against that other repository, from a
local clone of it, never as a docs/issue-1761/**-scoped commit in this
repo.

## Alternatives considered (for the proposal's Rationale)

1. One skill-repository directory per rulebook (skills/
   upstream-defect-report/ holding all three axis files together, plus
   an umbrella SKILL.md). Considered because it is the simplest
   possible mapping and keeps a single recursive diff straightforward
   to produce.
2. One skill-repository directory per axis, role-prefixed (skills/
   upstream-defect-report-subtraction/, -comprehensibility/,
   -convention/), each holding its one migrated file as SKILL.md.
   This matches the issue text's plural "names prefixed for the role"
   and the granularity role-source-allowlist.json's mapping already
   models (role -> a list of skill names) plus the roster's plural
   `resolution_skills` field — a per-axis split lets the roster/record
   fields show which specific axis-skills a session actually mounted,
   not just "the rulebook, packaged."

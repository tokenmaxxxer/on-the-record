---
subject: issue-2001
role: implementation
phase: 1-survey
---

# Current-state survey: cross-family skill mounting in spawn.py

## Family = role, fixed mapping

`_ROLE_SKILLS` (spawn.py:5068-5112) is the sole definition of "family":
a dict literal keyed by role name (`'implementation'`, `'architecture'`,
`'ux-engineering'`, ...) whose value is a fixed list of skill names for
that role. There is no separate family concept in code or docs — the
role name *is* the family key. `docs/issue-1764/proposals/keep-role-
family-classification.md` uses "family" for an unrelated older hook-
classification effort; it does not define this program's family
concept.

`resolve_role_source(role, repo_root)` (spawn.py:5115-5137) looks up
`_ROLE_SKILLS.get(role, [])` (spawn.py:5127), resolves each name to a
directory under the skill-repository checkout via `resolved_skill_dirs()`
(spawn.py:4892-4911), and fail-closes before any workspace/branch
mutation if a mapped skill carries a `hooks/` subdirectory (skill-repo is
guidance-only, issue #1758). It returns
`{"source": "skill-repo", "skill_dirs": [...], "skills": [...],
"skill_sha": ...}`.

## Where the family set becomes directive text and mount list

In `_spawn_one()` (spawn.py:7874+):

- `role_source = resolve_role_source(role, _skill_repo_root())` —
  spawn.py:7903.
- Directive text (spawn.py:8002-8015): iterates
  `role_source["skill_dirs"]`, appends each skill name plus
  `_skill_trigger_line(d)` (falls back to bare name if `None` — empty-
  state safe), and injects one paragraph into `task`:
  `"이 역할은 skill-repository(이슈 #1955, #1758)로 매핑됐다: 스킬 ... 가이던스만
  붙는다"`.
- `--skills` (ad-hoc, orthogonal to family) mounts assemble the same way
  at spawn.py:7993-8001, additive with family mounts.
- The actual `--plugin-dir` mount list handed to the CLI is built at
  spawn.py:8047-8048:
  `all_skill_dirs = list(skill_dirs) + [d for d in
  role_source["skill_dirs"] if d not in skill_dirs]` — `--skills` dirs
  plus family dirs, deduped, additive — flowing into `spawn_cmd()` at
  spawn.py:8058-8061.
- Byte-identical guarantee today: when there is no `--skills` and the
  role maps to `[]`, neither the `if skill_sources:` block (spawn.py:7993)
  nor the `if role_source["source"] == "skill-repo":` skill-listing block
  fires with non-empty content — the whole directive/mount path is a
  no-op addition on top of the pre-#1978 baseline. Covered today by
  `tests/test_spawn_directive_assembly.py::SkillTriggerLines
  ::test_zero_mounted_skills_directive_unchanged` (line 161).

## `_skill_trigger_line`: reusable trigger-sentence extraction

`_skill_trigger_line(skill_dir)` (spawn.py:7845-7871) already extracts
the "Use ..." trigger sentence from a `SKILL.md`'s YAML frontmatter
`description:` field (single-line or folded block scalar `>-`), using
`_SKILL_USE_SENTENCE_RE = re.compile(r"(Use\b[^.]*\.)", re.S)`
(spawn.py:7842). Returns `None` on any failure (missing file, missing
frontmatter, missing description, no "Use..." match) — never raises.
This is exactly the trigger-sentence text the issue asks the lexical
scorer to match task text against, and it is already the text rendered
in today's directive for the role's own family skills — reusing it keeps
the new cross-family line visually and mechanically consistent with the
existing family-skill line.

SKILL.md files live outside this repo, in the skill-repository checkout
resolved by `_skill_repo_root()` (spawn.py:4873-4891: env
`MUSTER_SKILL_REPO` > sibling `$TOKENMAXXXER_RULEBOOKS/skill-repository`
> managed clone). `resolved_skill_dirs()`'s `repo_root.iterdir()`
(spawn.py:4905) already gives the full candidate name/dir list to score
against for cross-family lookup — no new discovery mechanism needed.

## No existing lexical scorer — net new

Searched `scripts/` and `spawn.py` for a keyword/lexical scoring
utility: none exists.
`derived:`
```
$ grep -rln "def.*score\|def.*match\|def.*rank" scripts/*.py spawn.py
scripts/measure_skill_reflection.py
```
`scripts/measure_skill_reflection.py`'s matches are post-hoc judge-vote
scoring (`majority()`, `score_skill()`) for measuring skill *reflection*
after a session, unrelated to pre-spawn lexical trigger matching. The
top-K keyword scorer this issue needs is net-new code — only
`_skill_trigger_line`'s extraction (above) is reusable.

## Test fixture pattern to extend

`tests/test_spawn_directive_assembly.py`'s `DirectiveAssemblyBase`
(lines 13-78) is the load-bearing fixture: it mocks
`resolve_role_source`, `issue_workspace`, `spawn_cmd` (captures nothing,
returns `(["cat"], {})`), `subprocess.Popen` (captures `env`), and
`roster_register` (captures roster entries), then calls
`spawn._spawn_one(...)` directly and reads the delivered directive text
from the roster log path (lines 61-66). `_NO_SKILLS` (line 81) is the
empty-family baseline fixture. `SkillTriggerLines` (lines 117-169)
builds real temp `SKILL.md` files via `_skill_dir_with_trigger()` /
`_skill_dir_without_description()` and asserts `assertIn` (match case)
or exact string equality (byte-identical, no-match case) on the
delivered directive.

A cross-family test extends this directly: seed a fake skill-repository
root (`_skill_repo_root()`-shaped tmpdir) with (a) the role's family
skills plus (b) one or more "other family" skill dirs, one carrying a
`SKILL.md` whose "Use when ..." sentence lexically matches a fixture
task string, run `_spawn_one()` with that task text, and assert the
extra skill's name (+ trigger line) appears in the delivered directive
and in the mount list built at spawn.py:8047-8048. A second run with a
non-matching task string asserts the delivered directive and mount list
are byte-identical to a `role_source`-only baseline run (no `--skills`,
family set only) — matching the acceptance criterion's two-case shape
directly.

## `--skills` mounting: does not model this issue's need

`--skills` (spawn.py:7889-7901, tested in
`test/test_spawn_skills_mount.py`) is an operator-supplied CSV of skill
names, resolved unconditionally (not task-scored) and unknown names
fail-closed before any workspace mutation (spawn.py:4906-4909). It is a
different mechanism (explicit opt-in, not automatic task-aware
selection) and is additive with family mounts already — the issue's
cross-family K=2 selection sits alongside it, not on top of it.

## Replay-before-ship: session log / task-text availability

`_session_log_path()` (spawn.py:7696-7703) names each session's live
log `<workspace>.session.<ts>.<pid>.log`, one per spawn. Roster entries
(`roster_register`, spawn.py:1888+) do not store the raw task text used
at spawn time. The replay table therefore needs, per today's spawned
session: the issue number and role (present in roster/ledger), fed
through `gh issue view <n>` to recover the issue title/body text that
was the actual scoring input (mirroring how `_spawn_one()` itself builds
`task` from `gh issue view` output, spawn.py:7961-7963) — not a stored
verbatim task string, which does not exist today.

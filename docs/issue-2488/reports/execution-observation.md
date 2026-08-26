---
issue: 2488
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2488/reports/implementation.md
    sha: aa9f754c760ca86371d16e539f0bea66341151db
  - path: docs/issue-2488/reports/implementation/survey.md
    sha: aa9f754c760ca86371d16e539f0bea66341151db
  - path: docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md
    sha: 59bd1c5ad0ff5e23a28b49b507fe450744e20e01
  - path: spawn.py
    sha: 59bd1c5ad0ff5e23a28b49b507fe450744e20e01
  - path: skills.py
    sha: 1d29184b87fdc244a39f555b5900fc9010a48583
subject: PR #2497 (issue-2488/implementation, head aa9f754c760ca86371d16e539f0bea66341151db, base main)
test: issue #2488 Acceptance section — 5 check bullets, plus the PR's central claim that resolved_skill_sources() already resolved all four sources before #2488 was filed
result: passed
assertedBy: execution-observation, independently re-run and independently re-fixtured this turn (fresh fixtures, not the builder's own)
---

# issue-2488 — execution-observation record

Path convention: every `docs/issue-2488/reports/implementation*` and
`docs/decisions/2026-08-26-*` path cited below is **untracked on this
branch** (`issue-2488/execution-observation`, based on `origin/main` —
this branch carries no code changes, only this record); they exist only
on `issue-2488/implementation` at sha `aa9f754c`, read via an isolated
worktree (`git worktree add /tmp/pr2497-check aa9f754c`, removed after
use). `spawn.py`/`skills.py` citations below are also read from that
same worktree unless stated as pre-PR `main`. Verification scripts were
authored fresh this turn under `/tmp` (not the PR's own fixtures) and
removed after use.

## What was done

Independently re-derived all five `check` bullets of issue #2488's
Acceptance section against PR #2497, and separately re-verified the PR's
own headline claim — that `resolved_skill_sources()` already resolved
`--skills` across all four sources, landed by #1774, before #2488 was
filed — rather than citing the implementation record's claims as-is.

**Headline claim: did #1774 already fix the resolver before #2488 was filed?**

Confirmed independently, three ways:

1. Issue timestamps: `gh issue view 2488 --json createdAt` →
   `2026-08-26T01:09:45Z`. `gh issue view 1774 --json createdAt,closedAt` →
   opened `2026-08-21T04:30:18Z`, closed `2026-08-21T04:53:30Z`. #1774
   closed almost five days before #2488 was filed.
2. Merge commit dates: `git log --oneline --all | grep 1774` shows
   `3ef8e887`/`3a2d6bd5` ("issue-1774: --skills resolves across
   skill-repo, plugins, and local dirs (#1779)"), dated
   `2026-08-21 13:53:29 +0900` — already on `origin/main` before this
   session's own branch was cut, independent of anything PR #2497 did.
3. Code path, read directly on this session's own pre-PR checkout of
   `main` (not the PR branch), `skills.py:205-233`:
```
def resolved_skill_sources(skills_csv: str | None, repo_root: Path | None,
                            home: Path | None = None,
                            target_repo_root: Path | None = None) -> list[dict]:
    ...
    home = home or Path.home()
    plugin_index = _sp._installed_plugin_skill_dirs()
    tier3 = _sp._local_skill_dirs(home / ".claude" / "skills")
    tier4 = (_sp._local_skill_dirs(target_repo_root / ".claude" / "skills")
             if target_repo_root is not None else {})
```
   and `spawn.py:2586-2589` (also pre-PR, on `main`):
```
    with _timed("skill_resolve"):
        skill_sources = resolved_skill_sources(skills, _skill_repo_root(),
                                                target_repo_root=Path(cwd))
        skill_dirs = [m["dir"] for m in skill_sources]
```
   confirms `_spawn_one()`'s actual `--skills` CLI path was already wired
   to the four-source function, not the single-source
   `resolved_skill_dirs()`, before this PR touched anything.

derived: `git diff 5404164f aa9f754c --stat -- spawn.py skills.py
'test/*' 'docs/decisions/*' 'docs/issue-2488/*'`, independently re-run
this turn:
```
 ...26-skills-resolver-source-priority-and-trust.md |  95 +++++++
 docs/issue-2488/reports/implementation.md          | 274 +++++++++++++++++++++
 .../2026-08-26-hunt-skills-resolver-fix.md         |  70 ++++++
 .../20260826T022518461807-cdd489b5ec938317.md      |   1 +
 docs/issue-2488/reports/implementation/survey.md   | 159 ++++++++++++
 spawn.py                                           |  11 +-
 6 files changed, 607 insertions(+), 3 deletions(-)
```
`skills.py` does not appear in this file list at all — zero lines of it
changed by PR #2497. Combined with point 3 above (the four-source
function already present and already wired on pre-PR `main`), the
claim that #1774 already fixed the mechanism #2488 asked for, before
#2488 was filed, holds.

**Check 1 — plugin-only skill resolves and mounts, source recorded.**

acceptance: independently constructed a fresh plugin fixture (different
name/marketplace/version than the builder's own) and called the real,
unmocked `spawn.resolved_skill_sources()` — result:
```
CHECK1: [{'source': 'plugin', 'dir': PosixPath('/tmp/.../plugin-install/skills/my-plugin-skill'), 'plugin': 'acme@marketplace', 'version': '9.9.9', 'name': 'my-plugin-skill'}]
```
Matches the shape `_skill_source_roster_row()` requires for per-skill
source recording (`plugin` + `version` fields present).

**Check 2 — unknown name fails closed before workspace/branch.**

acceptance: same script, real resolver, previously-unused name — result:
```
CHECK2 SystemExit: --skills: 모르는 스킬 nope-does-not-exist — skill-repository, 설치된 플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills 어디에도 없다
```
canonical: `spawn.py:2585-2601` (`skill_resolve` block, calling
`resolved_skill_sources()`) precedes the first workspace-creating call
in `_spawn_one()` (`issue_workspace(cwd, issue, role)`, ~90 lines
later, same function) — read directly in the `aa9f754c` worktree,
confirming the ordering claim from the code itself, not just its
neighboring comment.
acceptance: `python3 -m pytest -q test/test_spawn_skills_mount.py -k UnknownSkillFailsClosedBeforeWorkspaceTest -v`, independently re-run — result:
```
1 passed
```

**Check 3 — name-collision behavior defined, documented, demonstrated.**

acceptance: independently constructed a plugin-vs-target-repo collision
on the same fixture name — result:
```
CHECK3 SystemExit: --skills: my-plugin-skill 가 둘 이상의 소스에서 겹친다 — plugin acme@marketplace@9.9.9, .claude/skills (/tmp/.../target-repo/.claude/skills/my-plugin-skill) (precedence 는 검색 순서일 뿐 충돌을 가리지 않는다)
```
canonical: `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
(untracked on this branch; read via the `aa9f754c` worktree), "Decision"
section:
```
**Collision priority: none.** A name matching in exactly one source
resolves to that source. A name matching in two or more sources — any
combination, including two distinct plugins colliding inside the plugin
source — is a hard, fail-closed error naming every matching source
```
States the chosen rule and, further down the same section, the rejected
alternative (silent skill-repo-always-wins precedence) with a stated
reason. Matches what the fixture above demonstrated.

**Check 4 — trust distinction stated explicitly.**

canonical: `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
(untracked on this branch; read via the `aa9f754c` worktree), "Trust
distinction" section:
```
**Trust distinction: none, by design, at mount-eligibility.** All four
sources are treated identically for both the collision rule above and
the guidance-only guard: a resolved directory carrying a literal
`hooks/` subdirectory is refused, uniformly, regardless of source
```
Explicit, not implied — satisfies the check's own criterion. The same
document also discloses, in a clearly-labeled "Known gap in the guard
itself" subsection, that the `hooks/`-subdirectory guard the trust
argument leans on is itself bypassable (see below) — a caveat on the
argument's soundness, not a failure to state the position.

**Check 5 — refusal message's source list matches what the resolver
checks.**

canonical: `skills.py:253-257`, read directly in the `aa9f754c`
worktree:
```
        if not matches:
            sys.exit(
                f"--skills: 모르는 스킬 {name} — skill-repository, 설치된 "
                f"플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills "
                f"어디에도 없다")
```
matches the four sources iterated immediately above it
(`skills.py:237-252`: `repo_root`, `plugin_index`, `tier3`, `tier4`) —
this was already true on `main` before PR #2497 (this string is
untouched by the PR's diff, confirmed by the diff-stat above showing
`skills.py` absent). The mismatch the issue actually reported was in
`spawn.py`'s `--help=` text; independently confirmed via `git show
59bd1c5a -- spawn.py`:
```
     ap.add_argument("--skills", default=None,
-                    help="쉼표로 구분한 스킬 이름 목록을 skill-repository 체크아웃"
-                         "(MUSTER_SKILL_REPO 또는 형제-클론)에서 마운트한다"
-                         "(이슈 #1742). 생략하면 스폰 argv/env 는 이전과 동일")
+                    help="쉼표로 구분한 스킬 이름 목록을 네 소스 — "
+                         "skill-repository 체크아웃(MUSTER_SKILL_REPO 또는 "
```
confirming the PR's 8-line diff at `spawn.py:1507-1516` (commit
`59bd1c5a`) rewrites the stale skill-repository-only help text to name
all four sources.

**Full targeted suite, independently re-run this turn, `aa9f754c` worktree:**
```
python3 -m pytest -q test/test_spawn_skills_mount.py
31 passed in 11.74s
```
Matches the record's own claimed 31 passed. `python3 -c "import spawn"`
— clean import, independently re-run, no output/error. `python3 -m
gates.frozen_decisions` — independently re-run:
```
ok: 10 decision(s), 2 frozen (single-enforcement-surface, single-skill-axis)
```

**Out-of-scope finding: `hooks/` guard bypass.**

The PR discloses (not fixed here, correctly) that
`(dir / "hooks").is_dir()` — the guard shared by
`resolved_skill_sources()`, `resolve_role_source()`, and
`resolve_skill_source()` — only catches a literally-named `hooks/`
subdirectory, not a `.claude-plugin/plugin.json` that redirects its
`"hooks"` key to a differently-named file. Independently confirmed by
code inspection, `skills.py:264`:
```
        if (m["dir"] / "hooks").is_dir():
            sys.exit(
                f"--skills: {name} ({_sp._describe_skill_match(m)}) 가 hooks/ "
```
and identically at `skills.py:368` and `skills.py:387` — the same
boolean is `False` for a directory shaped exactly as the hunt record
(`docs/issue-2488/reports/implementation/2026-08-26-hunt-skills-resolver-fix.md`,
untracked on this branch, read via the `aa9f754c` worktree) describes —
the Python-level half of the claim is directly verifiable from the
source and checks out. The other half (that the CLI actually honors a
manifest-redirected `hooks` key and fires it headless via
`--plugin-dir`) is a claim about the `claude` CLI's own behavior, not
this repo's code; I did not re-run the hunt record's `claude -p
--plugin-dir ... "say hi"` reproduction step myself this turn (a live
nested session, outside what this fix touches or needs to touch to
close #2488) — noted as read-verified, not independently re-executed.
This does not affect the verdict on #2488's own five acceptance checks,
none of which claim anything about the `hooks/` guard's own robustness;
it is correctly scoped out of the delivery and left as an open item for
the user to file.

## Why

Issue #2488's five acceptance checks (quoted in the issue body) ask
whether the resolver covers all four sources, fails closed correctly,
defines collision/trust behavior, and keeps its refusal message honest
— not about any specific code diff. canonical: `gh issue view 2488`
Acceptance section (re-verified check-by-check above, one subsection per
check). The independence value here is in not trusting the
implementation record's own pasted command output or its own claim that
#1774 already solved this: every acceptance-check demonstration above
was re-run against the real, unmocked resolver with fixtures built
fresh this turn (different names, versions, and directory layouts than
the builder used), and the "already fixed before #2488 was filed" claim
was checked three independent ways (issue metadata, commit dates, and
reading the pre-PR `main` checkout's code) rather than accepted from the
record's own narrative.

## What did not work

None — every independently-authored fixture and cross-check behaved as
its own hypothesis predicted on the first run this turn; no wording or
fixture-shape correction was needed.

## Upstream basis

- `docs/issue-2488/reports/implementation.md` (untracked on this
  branch; sha `aa9f754c760ca86371d16e539f0bea66341151db` on
  `issue-2488/implementation`) — the record under observation; its
  acceptance-evidence, "What was done", and "Rationale for deviations"
  sections were each independently re-derived above rather than cited
  as given.
- `docs/issue-2488/reports/implementation/survey.md` (untracked on this
  branch; same sha) — cross-checked its git-log/timestamp claims
  (`git log -1 --format='%H %ci' -- skills.py`, `gh issue view 2488
  --json createdAt`) by re-running them myself this turn; both matched
  the survey's own quoted values.
- `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
  (untracked on this branch; sha
  `59bd1c5ad0ff5e23a28b49b507fe450744e20e01`) — read in full; quoted
  and cross-referenced against `skills.py`'s actual behavior in the
  checks above.
- `spawn.py` (sha `59bd1c5ad0ff5e23a28b49b507fe450744e20e01` for the
  help-text diff; also read on pre-PR `main` at `5404164f` for the
  pre-existing `skill_resolve`/`resolved_skill_sources` wiring) — both
  states read directly and quoted above.
- `skills.py` (sha `1d29184b87fdc244a39f555b5900fc9010a48583`, read on
  pre-PR `main`; diff-scope evidence under "Headline claim" above, with
  its own `derived:` command and fence). Read in full for
  `resolved_skill_sources()`, `_installed_plugin_skill_dirs()`,
  `_local_skill_dirs()`, `resolve_role_source()`, `resolve_skill_source()`.

## Open findings

- The `hooks/`-guard bypass (see "Out-of-scope finding" above) is real
  by code inspection, correctly out of #2488's scope, and correctly left
  for the user to file as its own issue — resolution path: the user
  files it (role sessions cannot author issues, contract v3 s9).
- Minor, non-blocking, unresolved by this delivery or by me: the issue
  body's own repro text ("Observed live on a consumer session on a
  different machine this session") is not explained by anything in this
  PR. derived: `gh issue view 1774 --json closedAt` → `2026-08-21`,
  five days before `gh issue view 2488 --json createdAt` →
  `2026-08-26T01:09:45Z` — since `resolved_skill_sources()` was already
  wired since #1774, a session five days later hitting the
  single-source refusal message verbatim is not explained by the code
  history alone. One plausible account, not confirmed by any evidence
  gathered this turn: that machine's on-the-record checkout predated
  the #1774 merge. Does not affect the verdict on any of #2488's five
  acceptance checks, which are about the resolver's current behavior
  and documentation, not about explaining the original report's machine
  state — noted for completeness only, no resolution path opened here.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the five independently-executed Acceptance items
above — result:
```
check "plugin-only skill resolves and mounts, source recorded": independently-fixtured plugin (name/marketplace/version distinct from the builder's) resolved via real spawn.resolved_skill_sources(), source="plugin" with plugin+version recorded, this turn
check "unknown name fails closed before workspace/branch": independently-fixtured unknown name raised SystemExit with the four-source refusal message; code read confirms skill_resolve (spawn.py:2585) precedes issue_workspace() call; pytest -k UnknownSkillFailsClosedBeforeWorkspaceTest: 1 passed, this turn
check "name-collision behavior defined/documented/demonstrated": independently-fixtured plugin-vs-target-repo collision on the same name raised SystemExit naming both sources; decision doc states and justifies the no-silent-precedence rule, this turn
check "trust distinction stated explicitly": decision doc's "Trust distinction" section read in full — explicit "none, by design, at mount-eligibility" with three named reasons, plus an honest disclosed caveat about the hooks/ guard's own bypassability
check "refusal message's source list matches what the resolver checks": skills.py:253-257 read directly — the four iterated sources and the four named sources in the exit message match; the actual mismatch (spawn.py --help text) is what the PR's 8-line diff fixes, confirmed by reading the diff hunk and resulting help text
regression: python3 -m pytest -q test/test_spawn_skills_mount.py — 31 passed in 11.74s, independently re-run in the aa9f754c worktree, matching the record's own claimed count; python3 -c "import spawn" clean; python3 -m gates.frozen_decisions — ok: 10 decision(s), 2 frozen
```

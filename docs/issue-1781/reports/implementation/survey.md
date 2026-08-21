---
name: survey
subject: issue-1781
---

# Current-state survey: skill-repository install docs

## Scope

Write set per issue: `docs/handbooks/setup.md`, `README.md`. Docs-only —
skip conditions do not apply (this is not a bugfix and the spec leaves real
wording/placement decisions open), so scouting normally would run; but the
"best-in-class" comparison axis for install docs is this repo's own existing
`setup.md`/README voice, already surveyed below in full, not an external
product category — treating this survey as the scout sweep substitute per
scout-directive's "non-product roles scout the best of their own
deliverable's kind."

## What exists today

- `docs/handbooks/setup.md` (226 lines, bilingual 한국어/English mirrored
  sections) documents machine-once setup (`gh auth login`, plugin install)
  and per-target-repo setup (remote, `approvers.md`, branch protection).
  canonical: `grep -n "skill" docs/handbooks/setup.md` — zero matches.
- `README.md` (327 lines) Quickstart section.
  canonical: `grep -n "skill-repository" README.md` — zero matches.
- `spawn.py:5147-5163` (`_skill_repo_root()`) resolves the skill-repository
  checkout root: `MUSTER_SKILL_REPO` env first (must be a directory), else a
  sibling-clone default `$TOKENMAXXXER_RULEBOOKS/skill-repository`. No
  managed-clone fallback exists (unlike `tokenmaxxxer-core`, which
  auto-clones per `docs/handbooks/setup.md:96-97`) — the user must clone
  skill-repository themselves.
  canonical: spawn.py:5147-5163 (`_skill_repo_root`), read directly.

### Live clean-env walkthrough (executed this session, `/tmp/skill-repo-clean-test`, `TOKENMAXXXER_RULEBOOKS` unset so no sibling default exists on this machine)

canonical: shell transcript, this session, commands and output pasted verbatim below.

1. Fresh clone:
   ```
   $ git clone https://github.com/tokenmaxxxer/skill-repository.git skill-repo-clean-test
   $ ls skill-repo-clean-test
   README.md  docs  install.sh  skills
   ```
2. Fail-closed case — `MUSTER_SKILL_REPO` unset, no sibling default, calling
   the exact function `spawn.py`'s real (non-dry-run) spawn path calls at
   `spawn.py:8058`.
   canonical: `acceptance: env -u MUSTER_SKILL_REPO python3 -c "import spawn; spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())" — result: sys.exit as pasted below`
   ```
   $ env -u MUSTER_SKILL_REPO python3 -c "
   import spawn
   try:
       spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())
   except SystemExit as e:
       print('sys.exit ->', e)
   "
   sys.exit -> --skills: skill-repository 체크아웃을 못 찾았다 — MUSTER_SKILL_REPO 나 $TOKENMAXXXER_RULEBOOKS/skill-repository 를 확인하라
   ```
3. Root-vs-`skills/` anti-pattern (the #1761 note the issue cites) —
   `MUSTER_SKILL_REPO` pointed at the checkout root itself (not `skills/`).
   canonical: `acceptance: MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test python3 -c "import spawn; spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())" — result: sys.exit as pasted below`
   ```
   $ MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test python3 -c "..."
   sys.exit -> --skills: 모르는 스킬 implementation-complexity-coupling-management, implementation-design-pattern-selection, implementation-performance-data-structure-choice, implementation-blueprint — 쓸 수 있는 이름: docs, skills
   ```
   Cause: `_skill_repo_root()` accepts any existing directory (it does not
   itself check for a `skills/` layout), so the root path is accepted, but
   `resolved_skill_dirs()` then cannot find the mapped skill names directly
   under checkout root (only `docs`/`skills` exist there).
4. Correct case — `MUSTER_SKILL_REPO` pointed at the checkout's `skills/`
   subdirectory.
   canonical: `acceptance: MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test/skills python3 -c "import spawn; r = spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root()); print(r)" — result: as pasted below`
   ```
   $ MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test/skills python3 -c "
   import spawn
   r = spawn.resolve_role_source('implementation', spawn.Path('.'), spawn._skill_repo_root())
   print('source:', r['source']); print('skills:', r['skills']); print('skill_sha:', r['skill_sha'])
   "
   source: skill-repo
   skills: ['implementation-complexity-coupling-management', 'implementation-design-pattern-selection', 'implementation-performance-data-structure-choice', 'implementation-blueprint']
   skill_sha: 8021ada
   ```
   `implementation` is a real mapped role (not hypothetical) — canonical:
   `docs/specs/role-source-allowlist.json:272-277`.
5. `spawn.py --dry-run` itself, run with the same env.
   canonical: `acceptance: MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test/skills python3 spawn.py implementation "clean-env test" --issue 1781 --dry-run — result: exit 0, JSON settings printed`
   ```
   $ MUSTER_SKILL_REPO=/tmp/skill-repo-clean-test/skills python3 spawn.py implementation "clean-env test" --issue 1781 --dry-run
   { "sandbox": {...}, ... }
   (exit: 0)
   ```
   Note: `--dry-run` itself does not exercise `resolve_role_source()` — it
   returns from `role_settings()` before that call, which sits inside
   `_spawn_one()` on the real spawn path. canonical: spawn.py:7402-7419
   (dry-run early return) vs spawn.py:7422-7428 (`_spawn_one` call site) and
   spawn.py:8058 (`resolve_role_source` call site), read directly. Steps 2-4
   above reproduce the exact fail-closed/success symptom of that call
   without launching a live role session, which is out of scope for a
   docs-only issue and not the kind of thing to do irreversibly for a
   "clean-env simulation."

## Other facts

- `--skills` (issue #1774, `spawn.py:5263-5326`, `resolved_skill_sources()`)
  resolves across four sources in this order/shape: skill-repository
  checkout, installed Claude Code plugins' `skills/<name>/`,
  `~/.claude/skills/<name>`, and the target repo's own
  `.claude/skills/<name>`.
  canonical: spawn.py:5263-5326, read directly.
  A name found in more than one source is fail-closed (not silently
  resolved by precedence); a source directory carrying a `hooks/`
  subdirectory is also fail-closed (guidance-only invariant, issue #1758).
- `spawn.py --help`'s own one-line description of `--skills`: "쉼표로
  구분한 스킬 이름 목록을 skill-repository 체크아웃(MUSTER_SKILL_REPO
  또는 형제-클론)에서 마운트한다(이슈 #1742)."
  canonical: `python3 spawn.py --help`, output read directly, `--skills` line.

## Gaps this issue must close

1. No skill-repository clone/env step anywhere in setup.md (issue
   requirement 1).
2. README Quickstart never mentions the third repo or links setup.md
   (requirement 2).
3. No doc paragraph anywhere covers the four `--skills` sources
   (requirement 3).

## Alternatives considered (feeds proposal Rationale)

- **Sibling-clone-as-default vs. explicit `MUSTER_SKILL_REPO` step**: the
  code already supports a zero-config sibling clone
  (`$TOKENMAXXXER_RULEBOOKS/skill-repository`), matching the existing
  rulebook/core "no manual clone needed" pattern documented at
  `setup.md:96-97`. Two viable docs shapes exist: (a) tell the user to clone
  to the sibling path and skip the env var entirely, or (b) tell them to
  clone anywhere and export `MUSTER_SKILL_REPO`. Decision made in the
  proposal.

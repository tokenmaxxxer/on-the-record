---
issue: 2579
role: silent-failure-audit+diagnose-first-206898b1
author: silent-failure-audit+diagnose-first-206898b1
loop_state: landed
upstream:
  - path: skills.py
    sha: 848cf47ecb9fa0f8ff794d890a198e8f1f1db22a
  - path: docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md
    sha: same-commit
code_under_review:
  - skills.py
  - spawn.py
  - test/test_spawn_skills_mount.py
  - docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md
type: fix
breaking: false
verdict: pass
---

# issue-2579 — silent-failure-audit+diagnose-first-206898b1 record

skill-verdict: silent-failure-audit — applied: invoked; catalogued every `sys.exit()` branch in `resolved_skill_sources()` (skills.py) as Handled/Silently-Absorbed/Unreachable before writing the fix, and used that lens to reject a first-draft dedupe that would have silently absorbed "two directories, both missing SKILL.md" into a false match — guarded against in the shipped code (see `_skill_identity_key()`, skills.py:192-202, quoted below) and covered by `test_missing_skill_md_on_both_sides_still_refuses`.
skill-verdict: diagnose-first — applied: invoked; read the live symlink and env var before writing any code to confirm the two colliding matches were the same physical directory, rather than guessing at a fix from the issue text alone. canonical: `readlink -f ~/.claude/skills` output — `/home/jwjung/skill-registry/skills`; `printenv MUSTER_SKILL_REPO` output — `/home/jwjung/skill-registry/skills` (same physical directory reached two ways).

## What was done

derived: `git diff --stat` (this commit) — result:
```
 skills.py                                                              |  88 +++++++++++-
 spawn.py                                                               |  29 ++++-
 test/test_spawn_skills_mount.py                                       | 118 ++++++++++++++
 docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md |  30 ++++
```

Two fixes in `resolved_skill_sources()` (skills.py), plus one fix found only by live-dispatching the second one:

**1. Symlink-as-collision.** Before this commit, `skills.py` line 336
(`if len(matches) > 1:`) fired whenever a name matched in two or more of
the four sources, with no check for whether those matches were the same
underlying content. Added `_skill_identity_key()` and
`_collapse_identical_matches()`:
```python
def _skill_identity_key(skill_dir: Path) -> object:
    try:
        data = (skill_dir / "SKILL.md").read_bytes()
    except OSError:
        return object()
    return hashlib.sha256(data).hexdigest()
```
called on every match before the `len(matches) > 1` check; matches whose
identity keys all agree collapse to one (skills.py:335,
`matches = _sp._collapse_identical_matches(matches)`), matches that
disagree fall through to the original, unmodified fail-closed exit at
skills.py:336-342.

**2. Source qualifier.** Added `_split_skill_qualifier()` (skills.py:208-217)
parsing `<source>:<name>` out of each `--skills` entry, and used it in
`resolved_skill_sources()` to scope resolution to one source when given,
failing closed naming both source and name when that source lacks the
name (skills.py:326-334). Unqualified entries are untouched
(`_split_skill_qualifier` returns `(None, raw)` when no known-source
prefix is present).

**3. Branch-slug colon (found live, not planned).** `spawn.py`'s `--skills`
CLI block built the branch/role slug by joining the raw, still-qualified
tokens. Extracted `skill_branch_slug()` (skills.py:220-227) which strips
the qualifier before joining, and switched `spawn.py`'s `if a.skills:`
block (spawn.py:1807) to call it. See "What did not work" for how this was
found.

derived: `python3 -m pytest test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py test/test_spawn_skill_invocation.py test/test_branch_naming_dual_scheme.py -q` — result: `66 passed in 0.96s`

`test/test_spawn_skills_mount.py` gained two new test classes,
`SymlinkCollapseAndSourceQualifierTest` and `SkillBranchSlugStripsQualifierTest`
— derived: `python3 -m pytest test/test_spawn_skills_mount.py -k "SymlinkCollapseAndSourceQualifierTest or SkillBranchSlugStripsQualifierTest" -q` — result: `10 passed`.
Subtracting those 10 from the 66 above, the pre-existing tests in all four
files pass unchanged at 56 (56 + 10 = 66, matching the total quoted two
lines up).

## Why

Content-identity (SKILL.md byte equality), not path-identity
(`Path.resolve()` equality), decides "same match" because it directly
answers what the issue asks ("is this one thing or two things") even for
a future case that reaches identical content through two genuinely
separate physical checkouts — path-identity would treat that as still
ambiguous. The empty/missing-SKILL.md guard in `_skill_identity_key()`
(returning a fresh `object()` rather than a shared "empty" hash) exists
because a first draft without it broke this repo's own existing ambiguity
tests — derived: `git stash && python3 -m pytest test/test_spawn_skills_mount.py -q ; git stash pop` run against the pre-guard draft (content hash of a missing file, `b""`, shared across all matches) — result: `5 failed, 26 passed`, all five in `ResolvedSkillSourcesFourTierTest` (the tier fixtures create bare, SKILL.md-less directories to simulate distinct sources, and the pre-guard hash-of-empty-bytes treated them as identical).

`<source>:<name>` (colon) was chosen over `<name>@<source>` (already used
for plugin identity, `name@marketplace`) to avoid a three-part ambiguity
if a plugin name ever needs its own disambiguation, and over `source/name`
because `/` already separates branch segments
(`issue-<n>/<skill>-<lease>`, per
docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md).
The qualifier is legal unconditionally (not only under collision) per the
issue's own framing:

canonical: `gh issue view 2579 --repo tokenmaxxxer/on-the-record` output —
```
Naming the source must be possible always, not only when forced. A spawn that says which source it drew from is reproducible; one that does not is a claim about a name.
```

## Upstream basis

Builds on `skills.py` as it stood at this branch's pre-edit HEAD
(`848cf47e`) and the collision-priority decision in
`docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`,
which this commit amends in place with an "Update (issue #2579)" section
rather than rewriting the original "Decision" section — the original's
"no silent precedence" rule is unchanged for genuinely-different-content
matches (verified in "Live reproductions" below).

## Live reproductions (acceptance evidence)

canonical: `readlink -f ~/.claude/skills` output — `/home/jwjung/skill-registry/skills`; `printenv MUSTER_SKILL_REPO` output — `/home/jwjung/skill-registry/skills`. Same physical directory reached two ways — this machine reproduces the issue's exact reported bug (all skill-repository skills "collide" with themselves pre-fix).

**check 1 — real dispatch through the symlinked path (must not: `--dry-run`):**

acceptance: `python3 spawn.py --skills silent-failure-audit "<harmless probe task>" --issue 2579 --no-wait` — result:
```
[silent-failure-audit-7c0d0a9c] 격리 작업 디렉토리: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2579-silent-failure-audit-7c0d0a9c  (브랜치 issue-2579/silent-failure-audit-7c0d0a9c)
[silent-failure-audit-7c0d0a9c] directive composition: total=3535B (base-task=147B, issue-preamble-index=1602B, single-phase-contract=504B, mounted-skills=289B, role-skill-triggers=473B, skill-obligations-index=520B)
[silent-failure-audit-7c0d0a9c] bootstrap_timing admission=0.388 skill_resolve=0.021 workspace=3.464 branch=0.613 returned_pr_gate=0.001 auto_sweep=0.002 rulebook=0.000 core=0.000 gh_token=0.020 settings=0.003 cross_family=8.703 issue_fetch=0.001 directive_write=0.003 design_bearing=0.000 spawn_cmd=0.001 board_snapshot=0.081 total=13.299
```
Branch: `issue-2579/silent-failure-audit-7c0d0a9c`. Record path
(untracked here — lives only in that spawned session's own separate
workspace clone, not this repository's tree):
`docs/issue-2579/reports/silent-failure-audit-7c0d0a9c.md` (untracked).
derived: `ls /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2579-silent-failure-audit-7c0d0a9c/docs/issue-2579/reports/` — result: `silent-failure-audit-7c0d0a9c.md`.
Pre-fix, this exact invocation exits non-zero before workspace/branch
creation — the same code path this session ran without the fix, on this
same machine, hits skills.py:336-342 naming `skill-repository(297e350)`
and `~/.claude/skills/silent-failure-audit` as colliding.

canonical: `gh pr view 2582 --repo tokenmaxxxer/on-the-record --json state,comments` output — `state: CLOSED`, one comment from `JiwonJung94` (this role's human operator): "Closing — this branch carries only a consult-trace file, not the issue's deliverable." This probe's relay PR was closed by the human operator, independently of this role session (this role session cannot close PRs itself — a `gh pr close` attempt on this PR was refused by this session's own `gh-guard` hook, per contract v3 s8's two-account model).

**check 2 — two sources with genuinely different content still refuse:**

acceptance: `python3 -m pytest test/test_spawn_skills_mount.py -k test_genuinely_different_content_still_refuses -q` — result: `1 passed`. That test's refusal message, reproduced standalone against this session's real `skill-repository(297e350)` data with a fabricated differing-content local-user match:
```
--skills: silent-failure-audit 가 둘 이상의 소스에서 겹친다 — skill-repository(297e350), ~/.claude/skills (/tmp/tmpphes7n3p/home/.claude/skills/silent-failure-audit) (precedence 는 검색 순서일 뿐 충돌을 가리지 않는다 — 소스를 <source>:silent-failure-audit 형태로 지정해 골라라, 예: skill-repo:silent-failure-audit)
```

**check 3 — explicit source, no collision, spawn works:**

acceptance: `python3 spawn.py --skills skill-repo:diagnose-first "<harmless probe task>" --issue 2579 --no-wait` — result:
```
[diagnose-first-3b503f8e] 격리 작업 디렉토리: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2579-diagnose-first-3b503f8e  (브랜치 issue-2579/diagnose-first-3b503f8e)
[diagnose-first-3b503f8e] directive composition: total=3572B (base-task=172B, issue-preamble-index=1590B, single-phase-contract=498B, mounted-skills=319B, role-skill-triggers=473B, skill-obligations-index=520B)
```
Branch: `issue-2579/diagnose-first-3b503f8e` (colon-free — see "What did
not work" for the pre-fix attempt at this same command). Record path
(untracked here — separate workspace clone):
`docs/issue-2579/reports/diagnose-first-3b503f8e.md` (untracked).
derived: `ls /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2579-diagnose-first-3b503f8e/docs/issue-2579/reports/` — result: `diagnose-first-3b503f8e.md`.
canonical: `wc -c runs/active.json` (this repo's roster file, queried after the session ended) — result: `2` bytes, contents `{}` — i.e. the roster entry was removed cleanly, no crash. `gh pr list --repo tokenmaxxxer/on-the-record --head issue-2579/diagnose-first-3b503f8e --state all` — result: empty, no PR was opened for this dispatch.

**check 4 — the spawned session's record states which source each skill
came from.** The exact line `_spawn_one()` (spawn.py:3231-3239) injects
into the spawned session's task text, reconstructed by calling the same
functions the check-3 dispatch used, against that dispatch's real
resolved source:

acceptance: `python3` invoking `spawn.resolved_skill_sources("skill-repo:diagnose-first", spawn._skill_repo_root(), target_repo_root=Path.cwd())` then the same `skill_lines` join spawn.py:3231-3237 uses — result:
```
마운트된 스킬(--skills, 이슈 #1742/#1774): diagnose-first — Use whenever the user wants to reduce a cost, speed something up, fix a recurring problem, decide between options, or figure out where to focus — a gated problem-solving procedure that forces diagnosis before action. (skill-repository(297e350))
```
This is also this session's own preamble, verbatim: this session was
itself spawned with `--skills silent-failure-audit,diagnose-first`, which
is why the two `skill-verdict:` lines above exist at all.

**check 5 — unqualified, unambiguous name still works unchanged:**

acceptance: `python3 -m pytest test/test_spawn_skills_mount.py -k test_unqualified_unambiguous_name_still_works -q` — result: `1 passed`. That test resolves a name present only in a fixture `target_repo/.claude/skills/gamma` directory, with no CLI qualifier, and asserts `result[0]["source"] == "local-repo"`.

**check 6 — qualified name pointing at a source lacking that skill fails
naming both:**

acceptance: `python3 -m pytest test/test_spawn_skills_mount.py -k test_qualified_name_missing_from_source_names_both -q` — result: `1 passed`. Reproduced standalone against this session's real skill-repository data (the target repo's own `.claude/skills` has no `diagnose-first` in it):
```
--skills: local-repo:diagnose-first — 소스 local-repo 에 스킬 diagnose-first 이 없다 (다른 소스에서는 발견: skill-repository(297e350), ~/.claude/skills (/home/jwjung/.claude/skills/diagnose-first))
```
Names both the requested source (`local-repo`) and the skill
(`diagnose-first`).

**empty state** (issue's own trailing note, quoted from
`gh issue view 2579`: "a source with zero skills is not an error; naming
a skill from it is — quote both"): in check 6's reproduction above, this
repository's own `.claude/skills` (the `local-repo` source) has zero
entries in it — derived: `ls .claude/skills 2>&1` — result: `No such file or directory` (an empty/absent source). That absence alone caused no error in any of the three `--skills` dispatches run this session (checks 1 and 3 above, plus the standalone reproductions); it became an error only once `diagnose-first` was explicitly asked *of* that empty source, i.e. check 6's exact quote above.

## Open findings

- canonical: `gh pr view 2582 --repo tokenmaxxxer/on-the-record --json comments` output, comment body from `JiwonJung94`: "the relay path appears to re-derive a slug rather than carrying the session's own" (referring to the check-1 probe's relay branch `silent-failure-audit-7c0d0a9c` vs. this session's own identity `silent-failure-audit+diagnose-first-206898b1`). Flagged by the human operator, not this session; not a defect in the `--skills` resolver this issue is about. No resolution path opened here — needs its own issue.
- `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`'s original "Decision" section text is left as-written; the correction is appended below it as "Update (issue #2579)" rather than an edit in place, matching that file's own precedent (it already restates rather than rewrites #1774's frozen decision). Noting the choice so a future reader does not mistake the un-edited original paragraph for still being complete on its own — the Update section is the authoritative statement of current behavior for the collision case.

## What did not work

- Expected `<source>:<name>` parsing to be additive with no effect outside `resolved_skill_sources()`. It broke `spawn.py`'s branch/role-slug construction: the CLI's `if a.skills:` block joined the raw qualified token (colon included) into the branch name. Found by running check 3's dispatch before the fix — acceptance: `python3 spawn.py --skills skill-repo:diagnose-first "<probe>" --issue 2579 --no-wait` (pre-fix run) — result:
```
브랜치 issue-2579/skill-repo:diagnose-first-5db414e4 로 못 갈아탔다: fatal: 'issue-2579/skill-repo:diagnose-first-5db414e4'은(는) 올바른 브랜치 이름이 아닙니다.
```
Left an unreachable workspace directory with a colon in its path
(`on-the-record-issue-2579-skill-repo:diagnose-first-5db414e4`); removed
via `rm -rf` after confirming no process referenced it — derived:
`ps aux | grep 5db414e4` — result: no matching process. Fixed by
extracting `skill_branch_slug()` (skills.py:220-227) and switching
`spawn.py`'s slug construction to call it; check 3's quoted output above
is the post-fix re-run of the identical command, which succeeded.
- The check-1 probe session itself completed with no commits — derived:
`tail -c 2000` on that session's live log — result: a `result` event with
`"total_cost_usd":0.058...`, no tool calls logged, no PR — but the spawn
framework's own self-heal watcher (`watch --follow --self-heal`,
unrelated to this issue's code) auto-respawned it once, and that second
attempt produced an empty `consult-trace` commit and opened PR #2582 — a
side effect of probing a real dispatch, not something this fix controls.
The human operator closed it independently, per the "Open findings"
citation above.

## Next steps

None outstanding for this issue's two acceptance halves — derived:
`python3 -m pytest test/test_spawn_skills_mount.py test/test_spawn_role_skill_resolution.py test/test_spawn_skill_invocation.py test/test_branch_naming_dual_scheme.py -q` — result: `66 passed in 0.96s` (same run cited under "What was done"), plus the six live acceptance checks quoted under "Live reproductions" above. `loop_state: landed`.

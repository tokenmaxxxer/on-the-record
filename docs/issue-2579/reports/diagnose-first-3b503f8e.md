---
issue: 2579
role: diagnose-first-3b503f8e
author: diagnose-first-3b503f8e
loop_state: complete
upstream:
  - path: skills.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: directive_assembly.py
    sha: same-commit
---

# issue-2579 — diagnose-first-3b503f8e record

## What was done

Two changes in `skills.py`/`spawn.py`/`directive_assembly.py`, commits
`0763ccb8` and `0d7eb7ce` on this branch (derived: `git show --stat
0763ccb8 0d7eb7ce` — result: 5 files changed across the two commits,
listed in the Acceptance evidence section below).

1. `resolved_skill_sources()` now computes a `content_sha256` for every
   match regardless of source tier (`_skill_content_identity()`,
   skills.py:220-229 — previously only the two local tiers,
   `local-user`/`local-repo`, carried this field per issue #1774) and
   groups matches by that hash (`_dedupe_matches_by_content()`,
   skills.py:232-241) before the `len(matches) > 1` collision check
   runs (skills.py:307-317). Matches whose content is byte-identical
   collapse to one — the symlink-aliasing case reported in the issue
   (`~/.claude/skills` resolving into the same checkout `skill-repo`
   already reads) is no longer a collision. Matches with genuinely
   different content are still refused, unchanged from #1774/the
   2026-08-26 decision — no precedence order is introduced.
2. Every `--skills` name token now accepts an optional
   `<source>:<name>` qualifier (`_parse_skill_token()`, skills.py:210-219;
   `_SKILL_SOURCE_LABELS = {skill-repo, plugin, local-user,
   local-repo}`), legal at all times, not only when a name collides. A
   qualified name filters matches to that source before the
   content-dedup/collision logic runs (skills.py:301-306); a qualified
   name whose source has no match for that name fails closed naming
   both the source and the name (skills.py:302-306). Branch/record
   slugs strip the qualifier (`_skill_token_name()`, spawn.py:1797)
   since git ref names can't hold `:`.
3. `write_record_skeleton()`/`_stamp_additive_record_fields()`
   (directive_assembly.py:546-577) now stamp a `skills: <name> (<source
   description>), ...` frontmatter line at bootstrap whenever
   `--skills` mounted at least one skill, reusing the same
   `_describe_skill_match()` one-liner already used in the
   task-injected "마운트된 스킬" text — omitted entirely when no
   `--skills` were mounted (byte-identical to before this issue for
   that path).
4. Added a decision record,
   `docs/decisions/2026-08-27-skills-resolver-content-identity-and-source-qualifier.md`,
   narrowing (not reversing) the 2026-08-26 collision-priority
   decision.
5. Extended `test/test_spawn_skills_mount.py` with 8 new tests covering
   the symlink/content-identity collapse, the genuine-collision
   survival, the three qualifier behaviors, and the record-skeleton
   provenance line; updated the pre-existing ambiguity fixtures
   (`_make_pair()`, the two-distinct-plugins test) to write
   distinguishing `SKILL.md` content per tier, since under content-hash
   dedup their prior bare-`mkdir()` fixtures would no longer collide
   (both empty, both hash to the same value). derived: `python3 -m
   pytest test/test_spawn_skills_mount.py -q` — result: 39 passed.

## Why

canonical: `docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
(read in full before designing the fix).

The reported bug (`skills.py:258`'s pre-fix `len(matches) > 1`
comparing path strings, now at skills.py:307 post-fix) made `--skills`
unusable in this environment: measured live (derived: `printenv |
grep -i SKILL` and `ls -ld ~/.claude/skills` — result:
`MUSTER_SKILL_REPO=/home/jwjung/skill-registry/skills` and
`~/.claude/skills -> /home/jwjung/skill-registry/skills`), so every
skill in the repository was reported as colliding between the
`skill-repo` and `local-user` tiers. Content-hash comparison fixes
this precisely: two matches are the same skill iff their `SKILL.md`
bytes are the same, regardless of which of the four tiers found them
or whether one path reaches the other through a symlink (derived:
`skills.py:220-241`, `_skill_content_identity`/
`_dedupe_matches_by_content`) — without touching the collision rule
itself for the case the issue explicitly asked to keep (two sources
that really differ; see Acceptance evidence item 2 below for a live
refusal).

The qualifier syntax was designed to be always-legal rather than
collision-gated because the issue's core complaint was structural: "any
disambiguation syntax added *only* for the collision case is a syntax
nobody uses until something breaks." Reusing the four internal source
labels (`skill-repo`/`plugin`/`local-user`/`local-repo`) as the
qualifier vocabulary was chosen over inventing new names because those
labels are already the vocabulary `_describe_skill_match()` and the
2026-08-26 decision record use everywhere else — no second vocabulary
to keep in sync.

Stamping provenance into the record skeleton (rather than relying on
the already-existing task-injected "마운트된 스킬" line) was chosen
because that injected text lives in the session's context/transcript,
not in the record file itself — a record naming only the skill, with
no source, cannot be re-judged later purely from the record. The
skeleton-stamp reuses `_stamp_additive_record_fields()`
(directive_assembly.py:546), the extraction point issue #2241 stage 1
explicitly named as future additive stamps' call site (canonical: that
docstring, quoted at directive_assembly.py:549-551 pre-change), keeping
this and `author:` on one code path instead of a second inline write in
`write_record_skeleton()`.

Rejected alternative: resolving collisions by fixed tier precedence
(skill-repo always wins). Explicitly out of scope per the issue's own
non-goals and the 2026-08-26 decision's Rationale — a silent winner
hides a same-named local skill shadowing a curated one from the
operator. Not used here.

## Upstream basis

Issue #2579 body (verbatim in the spawn prompt) and
`docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
(canonical: read in full before designing the fix — quoted and
narrowed in the new 2026-08-27 decision record referenced above).

## Acceptance evidence (executed live)

**1. Real dispatch through the symlink, refusal gone.**
acceptance: `timeout 90 python3 spawn.py --skills silent-failure-audit
"이슈 #2579 실측 디스패치 스모크 테스트 — 심볼릭 링크 충돌 수정 확인용,
실제 작업 불필요" --issue 2579` — result:
```
[silent-failure-audit-e4fb75df] 격리 작업 디렉토리: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2579-silent-failure-audit-e4fb75df  (브랜치 issue-2579/silent-failure-audit-e4fb75df)
[silent-failure-audit-e4fb75df] bootstrap_timing admission=0.450 skill_resolve=0.025 workspace=3.695 branch=0.578 returned_pr_gate=0.000 auto_sweep=0.002 rulebook=0.000 core=0.000 gh_token=0.024 settings=0.005 cross_family=0.000 issue_fetch=0.001 directive_write=0.004 design_bearing=0.000 spawn_cmd=0.001 board_snapshot=0.093 total=4.876
```
Branch: `issue-2579/silent-failure-audit-e4fb75df`. Record path
(untracked — throwaway workspace, removed after capture below):
`docs/issue-2579/reports/silent-failure-audit-e4fb75df.md`. No
`--dry-run` used — this is a real workspace clone + branch checkout +
record-skeleton write, past the point the pre-fix code exited at.
The dispatched session was killed (`spawn.py kill
silent-failure-audit-e4fb75df --issue 2579`) immediately after
bootstrap to bound this smoke test's footprint; its own landing
attempt then failed cleanly on its own (derived: tail of
`*.watcher.log` — result: `session-end: {'outcome': 'errored',
'reason': 'pull request create failed: GraphQL: No commits between
main and issue-2579/silent-failure-audit-e4fb75df (createPullRequest)'}`
— nothing had been committed yet), leaving no stray PR (acceptance:
`gh pr list --repo tokenmaxxxer/on-the-record --head
issue-2579/silent-failure-audit-e4fb75df` — result: empty). The
throwaway clone directory and its empty remote branch are the only
residue; the workspace directory was removed with `rm -rf` after
capture (untracked).

**2. Genuinely different content across two sources still refuses.**
Constructed a real collision — `/tmp/fake-target-repo/.claude/skills/
silent-failure-audit/SKILL.md` (untracked scratch file, outside this
repo, removed after the check) with fabricated content different from
the skill-repository's real `silent-failure-audit/SKILL.md`.
acceptance: `python3 -c "import spawn; from pathlib import Path;
spawn.resolved_skill_sources('silent-failure-audit',
spawn._skill_repo_root(), target_repo_root=Path('/tmp/fake-target-repo'))"`
— result:
```
REFUSED: --skills: silent-failure-audit 가 둘 이상의 소스에서 겹친다 — skill-repository(297e350), .claude/skills (/tmp/fake-target-repo/.claude/skills/silent-failure-audit) (precedence 는 검색 순서일 뿐 충돌을 가리지 않는다, 내용이 서로 다르다 — <source>:silent-failure-audit 로 소스를 명시하라)
```
`resolved_skill_sources()` is the exact function `spawn.py`'s
`--skills` branch calls before any workspace/branch mutation
(canonical: `spawn.py:2876`, inside `_spawn_one()`) — this is the same
pre-workspace gate a live CLI dispatch would hit.

**3. Qualified source works even with no collision — real dispatch.**
acceptance: `timeout 90 python3 spawn.py --skills
skill-repo:silent-failure-audit "이슈 #2579 실측 디스패치 스모크 2 —
소스 명시 문법(비-모호 상황)이 실제로 동작하는지 확인, 실제 작업 불필요"
--issue 2579` — result:
```
[silent-failure-audit-12be14eb] 격리 작업 디렉토리: /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2579-silent-failure-audit-12be14eb  (브랜치 issue-2579/silent-failure-audit-12be14eb)
[silent-failure-audit-12be14eb] bootstrap_timing admission=0.425 skill_resolve=0.024 workspace=2.458 branch=0.567 returned_pr_gate=0.000 auto_sweep=0.002 rulebook=0.000 core=0.000 gh_token=0.022 settings=0.005 cross_family=12.272 issue_fetch=0.001 directive_write=0.004 design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.096 total=15.877
```
`skill-repo:silent-failure-audit` — the qualifier is accepted even
though, post-fix, `silent-failure-audit` unqualified already resolves
without ambiguity (item 1 above) — the qualified form is not
collision-gated. Branch: `issue-2579/silent-failure-audit-12be14eb`.
Record path (untracked — throwaway workspace, removed after capture):
`docs/issue-2579/reports/silent-failure-audit-12be14eb.md`. Same
kill/cleanup as item 1 afterward, same clean stranded-relay outcome
(derived: `*.watcher.log` tail — result: same `pr-create-failed` /
`No commits between main` pattern, no PR created).

**4. The spawned session's record states each skill's source.**
canonical: `docs/issue-2579/reports/silent-failure-audit-e4fb75df.md`
(untracked — throwaway workspace, read directly right after bootstrap,
before removal), frontmatter line:
```
skills: silent-failure-audit (skill-repository(297e350))
```
Same line, byte-identical, in item 3's record (untracked —
`silent-failure-audit-12be14eb.md`, same throwaway-workspace caveat) —
confirming the qualified form produces the identical provenance stamp
as the unqualified one.

**5. Unqualified, unambiguous name still works unchanged.** Item 1's
own dispatch above — `--skills silent-failure-audit` (no qualifier)
resolved through the symlink alias to a single `skill-repo` match and
dispatched, unchanged in surface syntax from before this issue.

**6. Qualified name pointing at a source lacking that skill fails
naming both.**
acceptance: `python3 -c "import spawn;
spawn.resolved_skill_sources('plugin:silent-failure-audit',
spawn._skill_repo_root(), target_repo_root=None)"` — result:
```
REFUSED: --skills: silent-failure-audit 는 소스 plugin 에 없다 — silent-failure-audit 를 실제로 들고 있는 소스: skill-repository(297e350), ~/.claude/skills (/home/jwjung/.claude/skills/silent-failure-audit)
```
Names the requested source (`plugin`) and the skill
(`silent-failure-audit`) in the same message, and additionally lists
which sources actually do have it.

**Empty state (issue body, non-goal-adjacent bullet): a source with
zero skills is not an error; naming a skill from it is.**
acceptance: `python3 -c "import spawn, tempfile, os; from pathlib
import Path; d = tempfile.mkdtemp();
os.makedirs(os.path.join(d,'.claude','skills'));
spawn.resolved_skill_sources('local-repo:silent-failure-audit',
spawn._skill_repo_root(), target_repo_root=Path(d))"` — result:
```
REFUSED: --skills: silent-failure-audit 는 소스 local-repo 에 없다 — silent-failure-audit 를 실제로 들고 있는 소스: skill-repository(297e350), ~/.claude/skills (/home/jwjung/.claude/skills/silent-failure-audit)
```
Constructing the empty `local-repo` tier itself (an existing,
skill-less `.claude/skills` directory) raised nothing — only the
explicit `local-repo:` naming of a skill that source doesn't have is
refused, matching "empty state is not an error; naming a skill from it
is."

**Full regression run.**
acceptance: `python3 -m pytest test/ -q` — result: `13 failed, 259
passed in 1.73s`. derived: `git stash && python3 -m pytest test/ -q &&
git stash pop` on the pre-fix tree — result: `13 failed, 251 passed in
1.27s`, and the failing test names plus one shared assertion's exact
numbers (`14774`/`8390`, `test_local_dependency_env.py`) matched
between both runs — all 13 pre-exist this branch's commits (unrelated
sandbox `git fetch`/source-position fixtures). 251 before, 259 after
(the 8 new tests added in `test/test_spawn_skills_mount.py`).

## Open findings

None — all six acceptance bullets and the empty-state check above were
each exercised against the real function/CLI (derived: acceptance
evidence section above, every item carries its own `acceptance:`/
`derived:` command and pasted result), not mocked.

## Next steps

None — loop_state is terminal (`complete`); derived: `python3 -m
pytest test/ -q` — result: `13 failed, 259 passed` (same 13
pre-existing failures as the pre-fix baseline, 0 new failures), and the
six acceptance bullets above are each backed by an executed command in
this same record.

## What did not work

None.

skill-verdict: silent-failure-audit — not-applicable: this session's own
delivered change is a name-resolution/collision-detection fix in
`skills.py`/`spawn.py`, not error-handling code with try/except or
result-type failure paths to audit — the skill's silent-failure
catalog (empty catch blocks, swallowed exceptions) doesn't have a
target in this diff; every `sys.exit(...)` call added here is itself
the explicit, loud failure path the skill would otherwise be checking
for.
skill-verdict: implementation-audit — not-applicable: single-session
build-now delivery (`CORE_BUILD_NOW=1`), no separate builder/evaluator
session split to run the two-session audit protocol against.
skill-verdict: work-in-english — applied: invoked; this record, the
decision record, commit messages, and code comments were written in
English per the policy; only the end-of-turn summary to the user is in
Korean.

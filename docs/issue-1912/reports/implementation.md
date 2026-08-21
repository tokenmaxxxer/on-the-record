---
code_under_review:
  - /tmp/skill-repository-1912/skills/sales-objection-handling/SKILL.md
  - /tmp/skill-repository-1912/skills/sales-pitch-scoping-and-messaging-handoff/SKILL.md
  - /tmp/skill-repository-1912/skills/sales-qualification-and-discovery/SKILL.md
  - /tmp/skill-repository-1912/scripts/procedure_authored_skills.txt
loop_state: landed
type: change
breaking: false
verdict: pass
---

# Implementation record: issue-1912 (sales family, wave 2a)

## What was done

Applied the frozen procedural-body recipe (docs/issue-1790/reports/implementation.md,
WAVE RECIPE section) to the 3 `sales-*` skills in
`tokenmaxxxer/skill-repository`:

- `skills/sales-objection-handling/SKILL.md` — inserted `## Trigger`,
  `## Procedure` (7 steps citing rules 1-6), `## Output shape`;
  rewrote `description:` from the new Trigger content.
- `skills/sales-pitch-scoping-and-messaging-handoff/SKILL.md` — same
  three sections (6 procedure steps citing rules 1-6); `description:`
  rewritten.
- `skills/sales-qualification-and-discovery/SKILL.md` — same three
  sections (6 procedure steps citing rules 1-6); `description:`
  rewritten.
- Appended `sales-objection-handling`,
  `sales-pitch-scoping-and-messaging-handoff`,
  `sales-qualification-and-discovery` to
  `scripts/procedure_authored_skills.txt` (after the prior 163
  entries, 166 total).

canonical: `git -C /tmp/skill-repository-1912 rev-parse HEAD`,
2026-08-21: `9003b39f2fcb5a4996cf640f3845a3a04c6361ac` — committed on
branch `issue-1912-wave2a-sales` in the skill-repository checkout
`/tmp/skill-repository-1912`, executed live this turn.

canonical: git -C /tmp/skill-repository-1912 push github issue-1912-wave2a-sales
The push above ran live this turn and returned `* [new branch]
issue-1912-wave2a-sales -> issue-1912-wave2a-sales`, so the branch now
exists at `github.com:tokenmaxxxer/skill-repository.git`. PR-opening is
addressed separately below (Rationale for deviations).

## Why

Requirement 1 of issue #1912: author the 3 `sales-*` skills per the
frozen wave-2a recipe, extend the manifest, deliver as a
skill-repository PR + this record. The approved phase-1 proposal
(docs/issue-1912/proposals/sales-wave.md) named this as the sole
approach (recipe reuse verbatim) after finding no structural gap the
recipe fails to cover for this family.

## Upstream / basis

- docs/issue-1912/proposals/sales-wave.md (approved)
- docs/issue-1912/reports/implementation/survey.md
- docs/issue-1790/reports/implementation.md (WAVE RECIPE section)

## Four checks — executed live, skill-repository checkout `/tmp/skill-repository-1912`

canonical: commands run directly in `/tmp/skill-repository-1912` on
branch `issue-1912-wave2a-sales`, this session, this turn.

### (a) Manifest checker

```
$ python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt
234 skills checked
$ echo $?
0
```

canonical: python3 scripts/check_skill_conformance.py --manifest scripts/procedure_authored_skills.txt (exit 0, transcript fenced directly above, run live this turn)

### (b) Rule-retention sweep (all 18 pre-change rule lines present post-change)

The sweep scopes the grep to content under the `## Rules` heading
specifically (not the whole file), since the new `## Procedure`
section's own numbered steps also match a bare `^[0-9]+\.` pattern —
the same caveat noted in the marketing wave's record
(docs/issue-1900/reports/implementation.md).

```
== check 2: rule-retention sweep ==
--- sales-objection-handling --
pre=6 post=6 missing=0
--- sales-pitch-scoping-and-messaging-handoff --
pre=6 post=6 missing=0
--- sales-qualification-and-discovery --
pre=6 post=6 missing=0
```

canonical: git show HEAD^:path (baseline extraction) piped through a for-loop grep sweep against post-change skills/sales-*/SKILL.md ## Rules numbered lines (missing=0 for all 3 files, transcript fenced directly above, run live this turn)

### (c) `git diff --stat` scoped to the 3 skill paths + manifest

```
$ git diff --stat
 scripts/procedure_authored_skills.txt              |  3 ++
 skills/sales-objection-handling/SKILL.md           | 35 +++++++++++++++++++++-
 .../SKILL.md                                       | 31 ++++++++++++++++++-
 skills/sales-qualification-and-discovery/SKILL.md  | 31 ++++++++++++++++++-
 4 files changed, 97 insertions(+), 3 deletions(-)
```

(The truncated middle line is `skills/sales-pitch-scoping-and-messaging-handoff/SKILL.md` — git's own column-width truncation of the long path, not a distinct file. 4 files total: 3 `sales-*` skill bodies + the manifest, matching Acceptance criterion 2 exactly — no other path touched.)

canonical: git -C /tmp/skill-repository-1912 diff --stat HEAD^ HEAD (4 paths only — 3 sales-* SKILL.md files + the manifest, transcript fenced directly above, run live this turn)

### (d) Full-tree checker (no `--manifest` flag)

```
$ python3 scripts/check_skill_conformance.py
234 skills checked
$ echo $?
0
```

canonical: python3 scripts/check_skill_conformance.py (exit 0, transcript fenced directly above, run live this turn)

## What did not work

None. canonical: docs/issue-1912/reports/implementation/survey.md,
"Shape classification" section (all 3 skills classified Shape B, no
no-op case in this family) — the recipe applied to all 3 skills with no
divergence, and the four checks above ((a)-(d)) each returned their
recorded result on the first run.

## Open findings

None.

## Rationale for deviations

The approved proposal's build-steps section, step 5, called for opening
a skill-repository PR carrying the 3 skill-file diffs and the manifest
diff. That step did not occur this session: `gh pr create --repo
tokenmaxxxer/skill-repository ...` was refused. canonical:
`/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-1912-implementation/on-the-record/hooks/upstream-defect-scope-guard.sh`
(read this turn, `in_scope()` function) — the hook denies any `gh pr
create` call carrying an explicit cross-repo `--repo` target that
differs from this role session's own git origin
(`tokenmaxxxer/on-the-record`); it cannot structurally tell this wave's
own cross-repo delivery PR apart from the upstream-defect channel's
disallowed PR path (issue #1131 req#4 / #1171 scoping) and refuses
either way.

This sits outside this role session's frozen write set
(docs/issue-1912/proposals/, docs/issue-1912/reports/), so it is filed
rather than inline-fixed per the deviation-loop's SCOPE-EXCEEDED rule.
The commit and push (see the section above this one, both executed live
this turn) stand as-is; only PR-opening remains, left for external
relay per this run's own fallback instruction ("push/PR 이 네트워크로
막히면 커밋까지는 해 둬라: on-the-record 가 밖에서 릴레이한다"). Once
opened, the PR will be at:
`https://github.com/tokenmaxxxer/skill-repository/pull/new/issue-1912-wave2a-sales`.
Logged in docs/reports/deviation-log.md.

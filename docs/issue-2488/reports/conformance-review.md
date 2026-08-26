---
issue: 2488
role: conformance-review
author: conformance-review
loop_state: complete
upstream:
  - path: aa9f754c760ca86371d16e539f0bea66341151db:docs/issue-2488/reports/implementation.md
    sha: aa9f754c760ca86371d16e539f0bea66341151db
  - path: aa9f754c760ca86371d16e539f0bea66341151db:docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md
    sha: aa9f754c760ca86371d16e539f0bea66341151db
subject: PR #2497 (issue-2488/implementation)
test: aa9f754c760ca86371d16e539f0bea66341151db:test/test_spawn_skills_mount.py; independent live re-derivation against skills.resolved_skill_sources()
result: passed
assertedBy: conformance-review (independent re-run, this session)
---

# issue-2488 — conformance-review record

## What was done

Builder-blind conformance review of PR #2497 (`issue-2488/implementation`,
head `aa9f754c760ca86371d16e539f0bea66341151db`, hereafter `aa9f754c`)
against issue #2488's own Acceptance section, never against the PR's own
account of itself.

derived: `git worktree add /tmp/pr2497-review origin/issue-2488/implementation`
(fetched this session) — result:
```
작업 트리 준비 중 (분리된 HEAD aa9f754c)
HEAD의 현재 위치는 aa9f754c입니다 issue-2488: append deviation-log entry for hooks-guard bypass finding
```

**Premise check (required before verifying the fix, per this review's own
brief):** PR #2497 claims issue #2488's premise was partly wrong —
`resolved_skill_sources()` (four-tier: skill-repo, plugins,
`~/.claude/skills`, target-repo `.claude/skills`), not the single-tier
`resolved_skill_dirs()` the issue names, is what `spawn.py`'s real
`--skills` CLI path actually calls, landed by issue #1774 before #2488
was filed. Verified independently, not taken on the builder's word:

derived: `git log --format='%H %ci %s' --all -S "def resolved_skill_sources" -- skills.py spawn.py`
(run this session) — result:
```
3a2d6bd54466640844363601a7c3bed23670ed66 2026-08-21 13:53:29 +0900 issue-1774: --skills resolves across skill-repo, plugins, and local dirs (#1779)
```
(earliest of four hits; the other three are its co-commit and two later
pure-move extractions.)

derived: `gh issue view 2488 --repo tokenmaxxxer/on-the-record --json createdAt -q .createdAt`
(run this session) — result: `2026-08-26T01:09:45Z`.

derived: `git log -1 --format='%H %ci' -- skills.py` (on `main` before
this PR, run this session) — result: `1d29184b87fdc244a39f555b5900fc9010a48583 2026-08-25 12:22:31 +0900`.

2026-08-21 13:53 (issue #1774 lands `resolved_skill_sources()`) precedes
both 2026-08-25 12:22 (`skills.py`'s pre-#2488 tip) and 2026-08-26 01:09
(#2488 filed) — the premise correction is independently reproducible
from `git log`/`gh issue view` timestamps alone, not just asserted by
the builder.

canonical: `aa9f754c:skills.py:205-271` (`resolved_skill_sources()`, read
directly in `/tmp/pr2497-review`) — iterates `repo_root`,
`_installed_plugin_skill_dirs()`, `_local_skill_dirs(home/.claude/skills)`,
`_local_skill_dirs(target_repo_root/.claude/skills)`: all four sources
the issue names, fail-closed on zero matches (`skills.py:253-257`),
fail-closed on 2+ matches naming every source (`skills.py:258-262`), a
uniform `hooks/`-subdirectory refusal (`skills.py:264-268`).

canonical: `aa9f754c:spawn.py:2586-2594` (read directly) — `_spawn_one()`'s
actual `--skills` path calls `resolved_skill_sources(...)`, not
`resolved_skill_dirs`, before `issue_workspace()`/`checkout_issue_branch()`
(comment at `spawn.py:2588-2590` and code order both confirm this).

The premise correction holds up under independent re-derivation: the
mechanism issue #2488 asks for already existed pre-filing, and only two
real gaps (stale `--help` text, an undocumented frozen decision) remain
for PR #2497 to close. The five requirement checks below verify the
*current* behavior of `resolved_skill_sources()` plus the two things PR
#2497 actually changed (`spawn.py`'s help text; the new decision doc),
not code this PR wrote from scratch.

The issue's five `check:` bullets are already singular, one-obligation
statements — conformance-review-requirement-extraction rule 1 checked
directly against `gh issue view 2488`'s body: none bundle "and"/"또한"
across independent clauses, none restate 3+ sub-points already listed
elsewhere (rule 3, n/a), none lack an observable success condition (rule
2, n/a — all five name a `provenance` and a `must not`). They map 1:1 to
REQ 1 through REQ 5 below, each dimension-tagged per rule 6.

### REQ 1 — Present

verification method: Demonstration (qualitative functional claim, per
conformance-review-verification-method-selection rule 3), reusing
Test-method evidence per rule 4 from the shipped suite
(`ResolvedSkillSourcesFourTierTest.test_tier2_plugin_resolves_alone`,
`test_hooks_refusal_tier2_plugin`;
`SpawnCmdSkillsMountTest.test_skill_dirs_appended_as_plugin_dirs_with_env_fields`).

- requirement: "a skill name that exists only in an installed plugin's
  `skills/` (not in the skill-repository checkout) resolves successfully
  via `--skills` and is mounted into the spawned session — demonstrate
  live with a real such skill on a machine that has one"
- spec_ref: issue #2488 Acceptance, bullet 1 (dimension: functional
  behavior)
- canonical: `aa9f754c:skills.py:242-244` (plugin-tier match branch, read
  directly in `/tmp/pr2497-review`)
```
        for qualifier, plugin_skill_dir, version in plugin_index.get(name, []):
            matches.append({"source": "plugin", "dir": plugin_skill_dir,
                             "plugin": qualifier, "version": version})
```
- canonical: `aa9f754c:skills.py:398-419` (`_skill_source_roster_row`/
  `_skill_roster_fields` record the resolved source per skill into
  `skills_detail`), wired at `aa9f754c:spawn.py:3263` and
  `aa9f754c:spawn.py:3396` — satisfies this bullet's `must not`: every
  mounted skill's resolved source reaches the spawn record, not just an
  in-memory match.
- empty-state check, independently run this session (not taken from the
  record):
derived: `python3 -c "import json; from pathlib import Path; d=json.loads((Path.home()/'.claude'/'plugins'/'installed_plugins.json').read_text()); print(list(d['plugins'].keys()))"`
— result: `['on-the-record@tokenmaxxxer']`
derived: `find ~/.claude/plugins -maxdepth 4 -iname skills -type d` —
result: (no output; zero matches). This host genuinely has no installed
plugin exposing a `skills/` directory, matching the bullet's own stated
empty state ("not applicable — depends on the host's actually-installed
plugin skills, stated in the record") and the implementation record's
identical finding at `aa9f754c:docs/issue-2488/reports/implementation.md`
lines 258-259.
- acceptance: with no real plugin skill available on this host either,
  an independently constructed fixture (not copied from the PR body:
  isolated `tempfile.TemporaryDirectory`, a plugin-shaped `skills/<name>/`
  directory read via `_sp._installed_plugin_skill_dirs()`) plus the
  shipped suite run live in `/tmp/pr2497-review` — `python3 -m pytest -q
  test/test_spawn_skills_mount.py` — result:
```
31 passed in 7.97s
```
- rationale: `resolved_skill_sources()` resolves the plugin tier through
  the same code branch as the other three tiers, the roster wiring
  records `source: plugin` per skill into the actual spawn record, and
  `SpawnCmdSkillsMountTest` (in the 31-passed run above) independently
  confirms a resolved dir reaches `spawn_cmd()`'s `--plugin-dir` argv —
  together this satisfies "resolves successfully... and is mounted,"
  with the live-real-plugin demonstration correctly substituted by the
  bullet's own stated empty-state accommodation once this host's actual
  plugin inventory was independently confirmed empty (derived commands
  above).

### REQ 2 — Present

verification method: Demonstration (forced condition — an unresolvable
name — exercised directly against the real resolver, not a mock).

- requirement: "a name that exists in NO source is still refused
  fail-closed before any workspace/branch is touched — regression check"
- spec_ref: issue #2488 Acceptance, bullet 2 (dimension: error-handling)
- canonical: `aa9f754c:spawn.py:2588-2594` (comment states, and code
  order confirms, `resolved_skill_sources()` runs before
  `issue_workspace()`/`checkout_issue_branch()`)
- canonical: `aa9f754c:skills.py:253-257` (zero-match `sys.exit`)
- acceptance: independently run in `/tmp/pr2497-review` this session
  against the real, unmocked resolver —
```
>>> skills.resolved_skill_sources('totally-unknown-name-xyz', None, home=home, target_repo_root=repo)
SystemExit: --skills: 모르는 스킬 totally-unknown-name-xyz — skill-repository, 설치된
플러그인, ~/.claude/skills, 타깃 저장소 .claude/skills 어디에도 없다
```
- canonical: `aa9f754c:test/test_spawn_skills_mount.py` class
  `UnknownSkillFailsClosedBeforeWorkspaceTest` — included in, and passing
  under, the 31-passed live run cited under REQ 1 above (same
  `pytest -q test/test_spawn_skills_mount.py` invocation, this session).
- rationale: the resolver raises `SystemExit` (fail-closed) before
  `_spawn_one()` reaches workspace/branch creation, confirmed both by
  reading the call order and by an independent direct call that never
  touched a workspace. `git show 59bd1c5a --stat -- spawn.py` (run this
  session) shows only the `help=` string changed in `spawn.py`, so this
  is a regression check against pre-existing, unmodified behavior,
  matching the bullet's own framing.

### REQ 3 — Present

verification method: Demonstration (constructed same-name collision
across two tiers, exercised directly against the real resolver).

- requirement: "name-collision behavior (the same skill name present in
  two sources) is defined, documented, and demonstrated — state the
  chosen priority and why"
- spec_ref: issue #2488 Acceptance, bullet 3 (dimension: edge-case)
- canonical: `aa9f754c:skills.py:258-262` (2+-match hard fail-closed,
  naming every matching source, no precedence)
- canonical: `aa9f754c:docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
  lines 36-46 ("Collision priority: none... chosen over a
  silent-precedence alternative... because a silent winner would let a
  same-named local skill shadow a curated one with no operator
  visibility")
- acceptance: independently constructed collision fixture this session
  (`~/.claude/skills/dup-skill` and target-repo `.claude/skills/dup-skill`,
  same name, two different tiers) called directly against the real
  resolver in `/tmp/pr2497-review` —
```
SystemExit: --skills: dup-skill 가 둘 이상의 소스에서 겹친다 — ~/.claude/skills (...),
.claude/skills (...) (precedence 는 검색 순서일 뿐 충돌을 가리지 않는다)
```
- canonical: `aa9f754c:test/test_spawn_skills_mount.py` class
  `ResolvedSkillSourcesFourTierTest`, cross-tier ambiguity methods
  `test_ambiguity_repo_and_plugin_hard_error_names_both`,
  `test_ambiguity_repo_and_tier3_hard_error`,
  `test_ambiguity_plugin_and_tier4_hard_error`,
  `test_ambiguity_tier3_and_tier4_hard_error`,
  `test_ambiguity_two_distinct_plugins_within_tier2` — all included in
  the 31-passed run cited under REQ 1 above.
- rationale: priority is explicitly and consistently "none" — every
  combination of 2-or-more matching sources hard-fails naming all
  matches, both in the independently-reproduced code behavior and the
  decision doc's stated rationale — this satisfies "defined, documented,
  and demonstrated" and the bullet's `must not` (the `sys.exit` message
  itself names which sources collided, so resolution is never silent or
  unrecorded).

### REQ 4 — Present

verification method: Inspection (a static/structural property — does
the decision doc's prose make an explicit trust-distinction statement —
per conformance-review-verification-method-selection rule 1, matching
the bullet's own `provenance: read`).

- requirement: "state explicitly what trust distinction (if any) is
  applied between the curated skill-repository and a target repo's local
  `.claude/skills`, and why that choice is safe — per the consult's
  flagged concern"
- spec_ref: issue #2488 Acceptance, bullet 4 (dimension: scope-boundary
  / design statement)
- canonical: `aa9f754c:docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
  lines 48-67 ("Trust distinction: none, by design, at
  mount-eligibility" — three named reasons: mounting is guidance-only,
  `--skills` is explicit operator opt-in, the two local sources already
  auto-load into interactive sessions today), read directly in
  `/tmp/pr2497-review` this session.
- canonical: same file, lines 69-83 ("Known gap in the guard itself") —
  the doc does not overclaim: it names, in the same commit, that the
  `hooks/`-subdirectory guard enforcing "guidance-only" is itself only a
  literal-name check, and states this is intent, not yet a
  fully-enforced guarantee.
- rationale: the bullet's `must not` is "informational, but the stated
  position must be explicit rather than implied" — the decision doc
  states a position (no trust tier at mount-eligibility) and a reason
  (three enumerated arguments, cited above), and additionally narrows its
  own claim once a gap in the enforcing mechanism was found — a stronger
  compliance than a bare explicit statement, since it avoids overclaiming
  a guarantee the code does not yet fully provide.

### REQ 5 — Present

verification method: Inspection (message/reality string comparison,
matching the bullet's own `provenance: read`).

- requirement: "the refusal message's source list matches what the
  resolver actually checks (they currently disagree)"
- spec_ref: issue #2488 Acceptance, bullet 5 (dimension: scope-boundary /
  consistency)
- canonical: `aa9f754c:skills.py:253-257` (runtime refusal message names
  skill-repository, 설치된 플러그인, `~/.claude/skills`, 타깃 저장소
  `.claude/skills`)
- canonical: `aa9f754c:spawn.py:1507-1514` (post-fix `--help` text) —
  re-derived live this session in `/tmp/pr2497-review`:
```
$ python3 spawn.py --help | grep -A6 -- "--skills SKILLS"
  --skills SKILLS       쉼표로 구분한 스킬 이름 목록을 네 소스 — skill-repository
                        체크아웃(MUSTER_SKILL_REPO 또는 형제-클론), 설치된 플러그인의 skills/,
                        ~/.claude/skills, 타깃 저장소 .claude/skills — 에 걸쳐 해석해
                        마운트한다(이슈 #1742/#1774/#2488). 이름이 둘 이상의 소스에서 겹치면 fail-
                        closed(우선순위 없음, docs/decisions/2026-08-26-skills-
                        resolver-source-priority-and-trust.md). 생략하면 스폰
```
- canonical: `git show 59bd1c5a --stat -- spawn.py` (run this session in
  `/tmp/pr2497-review`) — result: `1 file changed, 8 insertions(+), 3
  deletions(-)`, confirmed a string-literal-only edit by reading the same
  commit's diff body (`git show 59bd1c5a -- spawn.py`), which touches
  only the `help=` argument.
- acceptance: `python3 -c "import spawn"` (run this session) → clean
  import, no output; `python3 -m gates.frozen_decisions` (run this
  session) — result:
```
ok: 10 decision(s), 2 frozen (single-enforcement-surface, single-skill-axis)
```
- rationale: before this PR, the runtime refusal message already named
  all four sources while `--help` named only the skill-repository
  checkout — the exact mismatch the issue quotes. `--help` now names the
  same four sources and the collision rule; the disagreement the issue
  flagged is resolved.

## Why

Builder-blind method chosen — worktree checked out independently from
`origin/issue-2488/implementation` (`derived:` command quoted under
"What was done" above), every citation re-derived rather than trusted
from `aa9f754c:docs/issue-2488/reports/implementation.md` — because a
self-review by the implementing session cannot be trusted to surface its
own gaps, and the premise-correction claim above is exactly the kind of
self-serving conclusion an implementer benefits from being right about
(it converts "build a merge mechanism" into "fix two small gaps"). The
premise check was done first, independently, using only
`git log`/`gh issue view` timestamps and a direct read of
`skills.py`/`spawn.py` (all `derived:`/`canonical:` tags quoted under
"What was done" above), before accepting any other claim in the
implementation record.

Demonstration was selected for REQ 1, REQ 2, and REQ 3 (functional,
error-handling, and edge-case claims respectively, each needing the
actual resolver exercised, per conformance-review-verification-method-selection
rule 3), reusing the shipped test suite
(`aa9f754c:test/test_spawn_skills_mount.py`, 31 passed — `derived:`
command and result quoted under REQ 1 above) as Test-method evidence per
rule 4, rather than re-deriving a parallel manual suite. Inspection was
selected for REQ 4 and REQ 5 (static prose/string-consistency
properties, per rule 1), matching each bullet's own stated `provenance`
field in `gh issue view 2488`'s body.

No persistent test files were authored by this review (verify-at-landing
convention, per this role's own protocol) — every acceptance
re-derivation quoted above is an executed command against the real,
unmocked resolver in the disposable worktree `/tmp/pr2497-review`
(removed at the end of this session), with command and output quoted
inline rather than paraphrased.

conformance-review-sampling-derivation is not applicable here: issue
#2488's Acceptance section names exactly five `check:` bullets
(`gh issue view 2488`'s body, read this session), all five independently
checkable in one PR touching four files (`git show 59bd1c5a --stat`,
quoted under REQ 5 above) — full enumeration, not a derived sample.
conformance-review-severity-classification is likewise not applicable —
this review's scope was ordinary fidelity-checking against #2488's own
five bullets, never extended into risk-weighting a recorded finding.

## Upstream basis

- `aa9f754c:docs/issue-2488/reports/implementation.md` — the delivery's
  own account, used only as a pointer to check, never as evidence in
  itself; independently re-derived in full above (every REQ block cites
  its own direct read/execution, not this file's claims).
- `aa9f754c:docs/decisions/2026-08-26-skills-resolver-source-priority-and-trust.md`
  — the new decision doc, read directly (REQ 3, REQ 4 above).
- `aa9f754c:skills.py` (confirmed unmodified by this PR — `git show
  59bd1c5a --stat -- spawn.py`, quoted under REQ 5 above, shows zero
  `skills.py` lines touched): `resolved_skill_sources()` (205-271),
  `_skill_source_roster_row()`/`_skill_roster_fields()` (398-419).
- `aa9f754c:spawn.py`: `--skills` CLI path (2586-2594, unmodified
  behavior), `--help` text (1507-1514, the one behavior-free string edit
  this PR makes).
- `git log --all -S "def resolved_skill_sources" -- skills.py spawn.py`
  and `gh issue view 2488 --json createdAt` (both `derived:`, quoted
  under "What was done" above) — external-to-the-PR evidence used to
  independently verify the premise correction.
- Issue #2498, `skills.py's guidance-only hooks/ guard is bypassable via
  .claude-plugin/plugin.json hook-path redirect` —
derived: `gh issue list --repo tokenmaxxxer/on-the-record --search "hooks/ guard" --limit 10`
(run this session) — result includes: `2498 OPEN skills.py's
guidance-only hooks/ guard is bypassable via .claude-plugin/plugin.json
hook-path redirect (all three resolver entry points)`. The out-of-scope
hooks/-guard finding PR #2497 surfaced (and could not file itself, per
contract v3 s9) reached the tracker rather than being lost.

## Open findings

None against issue #2488's own five acceptance checks — all five verify
Present above, independently, against the real code and a disposable
worktree.

Not an open finding of this review, but worth recording for a future
reader: the `hooks/`-subdirectory guard bypass PR #2497 surfaced during
its own before-landing warrant-hunter pass is real, sanity-checked here
against `aa9f754c:pipeline.py:446-455` and `aa9f754c:pipeline.py:651`
(read directly in `/tmp/pr2497-review` this session) — the "headless 에서
그대로 발화" claim the hunt record
(`aa9f754c:docs/issue-2488/reports/implementation/2026-08-26-hunt-skills-resolver-fix.md`)
cites is grounded in existing, documented CLI-behavior comments already
in `pipeline.py`, not fabricated for this PR. It is correctly
out-of-scope for #2488 (pre-existing since #1774, not touched by this
PR's diff per `git show 59bd1c5a --stat`, quoted under REQ 5 above), and
is already tracked as issue #2498, OPEN (`derived:` `gh issue list`
quoted under "Upstream basis" above) — so it is not re-opened here as a
finding against this PR.

## Next steps

None — loop_state is terminal (`complete`) for this record: all five of
issue #2488's Acceptance bullets are verified Present against
`aa9f754c`, each with its own independently-executed `derived:`/
`acceptance:` evidence quoted under "What was done" above, and the one
out-of-scope defect this review sanity-checked is already tracked as
issue #2498 (`derived:` `gh issue list`, quoted under "Upstream basis"
above) rather than left dangling.

## Skill verdicts

skill-verdict: conformance-review-requirement-extraction — applied:
invoked; checked issue #2488's five bullets (`gh issue view 2488`,
this session) for bundled obligations, missing acceptance thresholds,
and redundant summary lines — none found, per "What was done" above —
before mapping them one-to-one onto REQ 1 through REQ 5.
skill-verdict: conformance-review-verification-method-selection —
applied: invoked; selected Demonstration for REQ 1, REQ 2, and REQ 3 and
Inspection for REQ 4 and REQ 5, matching each bullet's own stated
`provenance` field, and reused the shipped
`aa9f754c:test/test_spawn_skills_mount.py` suite (31 passed, `derived:`
quoted under REQ 1 above) as Test-method evidence rather than
re-deriving a parallel manual check.
skill-verdict: conformance-review-verdict-assignment — applied: invoked;
assigned Present to every REQ block above only after independently
re-deriving each behind the builder's account (worktree checkout, direct
code reads, live re-execution — all `derived:`/`canonical:` tags cited
per-REQ above), per the rule against asserting Present from the
builder's own description.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every REQ cites file:line-range plus the commit sha
(`aa9f754c`) actually read in `/tmp/pr2497-review`, and REQ 1's evidence
cites both `skills.py` (resolution) and `spawn.py` (roster wiring) as
separate links per contributing file.
skill-verdict: conformance-review-finding-record — applied: invoked;
this record's five REQ blocks each carry requirement/spec_ref/verdict/
evidence/rationale, written to
`docs/issue-2488/reports/conformance-review.md` only, with no verdict
written without an evidence pointer and spec_ref.
skill-verdict: conformance-review-sampling-derivation — not-applicable:
full enumeration was used, per the "Why" section above.
skill-verdict: conformance-review-severity-classification —
not-applicable: this review's scope was not extended into risk-weighting
a recorded finding, per the "Why" section above; the one out-of-scope
defect noted has its own tracked issue (#2498) for that issue's own
review to band.
skill-verdict: verify-finding-record — not-applicable: this task is a
fresh conformance review against an issue's acceptance criteria, not a
reproduction-attempt outcome for a defect-verification record.
skill-verdict: adversarial-review — not-applicable: this session is
already the structurally independent evaluator this protocol calls for
(a separate builder-blind conformance-review session against a
separately-authored PR, worktree-isolated, no shared context with the
implementation session), not a case requiring the cross-family protocol
to be separately invoked.
other mounted skills: not triggered — no chart/dataviz work, no config
changes, no scheduling or keybinding work fell inside this review's
scope this session.

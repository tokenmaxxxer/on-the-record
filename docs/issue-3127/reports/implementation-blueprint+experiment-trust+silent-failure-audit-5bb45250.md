---
issue: 3127
role: implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250
author: implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250
skills: implementation-blueprint (skill-repository(c05de12)), experiment-trust (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
loop_state: terminal
code_under_review: pipeline.py::_cross_family_candidate_corpus
type: fix
breaking: false
verdict: blocker A fixed and verified live -- the skills-off arm's dispatch no longer sys.exits on the cross-family tier conflict; unqualified-name fail-closed behavior unchanged (test + live-reproduction confirmed)
upstream:
  - path: pipeline.py
    sha: same-commit
  - path: directive_assembly.py
    sha: same-commit
  - path: consult.py
    sha: same-commit
  - path: spawn.py
    sha: same-commit
  - path: test/test_spawn_cross_family_skill_selection.py
    sha: same-commit
---

# issue-3127 — implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250 record

## What was done

canonical: this session's own live command transcript below — each numbered
step names the exact command it derives from.

Fixed issue #3127 blocker A: `pipeline.py::_cross_family_candidate_corpus()`
(called unconditionally from `directive_assembly.py::_bm25_cross_family_scores()`
on every dispatch) `sys.exit`s whenever a skill name resolves to diverging
content across more than one tier, even when the caller already pinned that
name to one source via `--skills <source>:<name>` (issue #2579's qualifier
syntax) the same way the *primary* `--skills` resolution
(`resolved_skill_sources()`, `skills.py:302-417`) already respects.

1. derived: reproduced the blocker live, before any code change, with a
   throwaway two-tier fixture (one skill dir under a stub `skill-repo`
   root, a second, content-diverging copy of the same name under a fake
   `home/.claude/skills`):
   ```
   REPRODUCED sys.exit: cross-family 후보 스킬 product-discovery-hypothesis-preregistration 가 둘 이상의 소스에서 겹친다 — skill-repo(/tmp/tmphd4xyfp9/skill-repo/product-discovery-hypothesis-preregistration), local-user(/tmp/tmphd4xyfp9/home/.claude/skills/product-discovery-hypothesis-preregistration) (이슈 #2055: 네 소스 중 어느 tier 도 다른 tier 를 조용히 가리지 않는다)
   ```
   — same shape and same skill name as the failure PR #3172's record
   cites at `pipeline.py:1423-1490`/`directive_assembly.py:756`. That
   record's own path is not in repo on this branch — it lives on PR
   #3172's own, not-yet-merged branch, fetched read-only this session via
   `git fetch origin pull/3172/head:pr-3172-view` and read from
   `pr-3172-view`, never checked out or merged here.

2. Read the resolution chain: `pipeline.py::_cross_family_candidate_corpus()`
   builds a four-tier candidate pool (skill-repo/plugin/local-user/local-repo)
   for BM25 cross-family matching and fails closed on any name with
   diverging content across tiers (`pipeline.py:1477-1494`, unchanged
   shape) — it never learned about the `<source>:<name>` qualifier that
   `skills.py::resolved_skill_sources()` (the primary `--skills` resolver)
   already parses via `_split_skill_qualifier()` (`skills.py:251-260`) and
   uses to narrow a name to one source before ever comparing tiers
   (`skills.py:391-400`).

3. Fix: added an optional `skills_csv` parameter to
   `_cross_family_candidate_corpus()` (`pipeline.py:1423-1503`). It parses
   `skills_csv` with the same `_sp._split_skill_qualifier()` the primary
   resolver uses, building a `name -> pinned source` map; when a name in
   the corpus has a pin AND more than one tier match, the match list is
   narrowed to the pinned source's entry before the identical-content
   collapse / fail-closed check runs. A name with no pin, or a pin that
   matches none of the discovered tiers, falls through unchanged to
   today's fail-closed behavior — verified live below.
   Threaded `skills_csv` through the full call chain so the real spawn
   dispatch path (not just direct unit calls) carries it:
   `directive_assembly.py::_bm25_cross_family_scores()` /
   `_cross_family_skill_matches()` (both gained a `skills_csv=None` kwarg,
   passed straight through) and `consult.py::_cross_family_skill_matches_with_consult()`
   (gained `skills_csv=None`, passed to both of its internal
   `_bm25_cross_family_scores()` calls — the initial score and the
   fast-path phrase-stripped re-score). `spawn.py`'s own dispatch call
   site (`spawn.py:3941-3945`, inside `_spawn_one()`) now passes
   `skills_csv=skills` — the raw `--skills` CLI value already in scope
   there, which is exactly the string carrying any `<source>:<name>`
   qualifier the operator (or this harness) typed.

4. derived: `python3 -m pytest test/test_spawn_cross_family_skill_selection.py -q`
   — result: `25 passed in 1.55s` (23 pre-existing + 2 new). One
   pre-existing test's mock stub (`stub_with_consult()` in
   `SpawnOneCrossFamilyAcceptanceTest._run()`) needed a `skills_csv=None`
   parameter added to keep matching the real function's new signature —
   without it two acceptance tests failed with
   `TypeError: stub_with_consult() got an unexpected keyword argument 'skills_csv'`,
   confirmed via `python3 -m pytest test/test_spawn_cross_family_skill_selection.py::SpawnOneCrossFamilyAcceptanceTest -q`
   before the stub fix.

5. Added two tests to `FourSurfaceCandidateCorpusTest`
   (`test/test_spawn_cross_family_skill_selection.py`):
   `test_explicit_source_qualifier_pins_the_named_skill_and_skips_conflict`
   (stub repo + real diverging skill under a fake `home/.claude/skills`,
   `skills_csv="skill-repo:dup-skill"` — dispatch resolves to exactly the
   skill-repo entry, no exit) and
   `test_unqualified_name_with_diverging_tiers_still_fails_closed_when_pins_given`
   (same two-tier conflict, but the pin in `skills_csv` names a *different*
   skill — the unqualified `dup-skill` name must still raise `SystemExit`,
   proving the relaxation is scoped to explicitly-pinned names only).

6. derived: `timeout 550 python3 -m pytest test/ tests/ -q` — result:
   `917 passed, 3 xfailed, 2 warnings in 32.06s`. The 2 warnings are a
   pre-existing, unrelated `pinned-fixture-divergence` UserWarning from
   `tests/test_skill_candidates_floor.py` (dated 2026-09-01, about BM25
   score drift against today's live skill corpus — unrelated to this
   session's change, not a failure).

7. Ran the real harness dispatch this issue's spawning instructions asked
   for: `run_consumer_pair.py` has no per-arm CLI selector (checked its
   `argparse` block, `scripts/issue-3127/run_consumer_pair.py:946-1056` —
   no `--arm`/`--only-off` flag), so per the fallback instruction, built a
   stub skill-repo directly with the harness's own
   `build_stub_skill_repo()` and dispatched `spawn.py` directly against
   the pre-provisioned sandbox `JiwonJung94/study-companion`, issue 20
   (pair `01-study-groups`'s skills-off arm, per the orchestrator-supplied
   issue map `01-study-groups:19:20`):
   derived: `MUSTER_SKILL_REPO=/tmp/issue-3127-skills-off-live-cs285bkf python3 spawn.py lint --issue 20 -C /home/jwjung/study-companion` — `이슈 #20 lint: 위반 없음`.
   derived: `MUSTER_SKILL_REPO=/tmp/issue-3127-skills-off-live-cs285bkf python3 spawn.py --skills skill-repo:product-discovery-hypothesis-preregistration "$(cat scripts/issue-3041/tasks/01-study-groups.txt)" --issue 20 --model sonnet -C /home/jwjung/study-companion`
   — dispatched successfully: `[product-discovery-hypothesis-preregistration-e8595864] 스폰은 리턴했지만 세션은 계속 돈다 — 상태는 spawn.py ps` (no
   `cross-family` `sys.exit`, unlike the pre-fix reproduction in step 1).
   derived: `python3 spawn.py ps -C /home/jwjung/study-companion` —
   `RUNNING product-discovery-hypothesis-preregistration-e8595864 issue-20  0분  pid 1066237`
   — confirms the session is genuinely alive. Per this session's own
   spawning instructions ("do not wait for it to finish"), the session
   was left running and not watched to completion.

   Note: the stub skill-repo for this live dispatch also had to include a
   frontmatter-only `work-in-english` stub — the *separate*,
   already-diagnosed-and-fixed-elsewhere policy-skill-stub defect
   (`resolve_static_policy_source()` resolving `_STATIC_POLICY_SKILLS`
   unconditionally from the same `MUSTER_SKILL_REPO`, PR #3172's own
   finding, fixed there in commit `1deb6198` on an unmerged branch not
   in repo on this branch). That defect is out of this session's scope
   (blocker A only); the manual stub was scaffolding to reach blocker A's
   own code path for a clean live reproduction, not a code change.

## Why

The minimal, targeted fix per the spawning consult's own guidance
(`experiment-trust`, `runs/consult-logs/20260902T125610799701-948846.log`):
honor the explicit source qualifier in
`_cross_family_candidate_corpus()` exactly the way primary `--skills`
resolution already does, rather than either (a) weakening the fail-closed
check globally (would remove a real safety property PR #3172's own
session explicitly declined to weaken — every session on this machine
that has a name-colliding skill under `~/.claude/skills` would silently
lose the cross-tier-divergence guard, not just the harness's stub-vs-real
case), or (b) mutating machine-shared state (temporarily moving the real
skill aside) to force the harness's manipulation condition, which PR
#3172's session already rejected as risking other concurrently-running
sessions reading the same path. Reusing the existing
`_split_skill_qualifier()` parser (rather than writing a second parser)
keeps the two resolution paths' understanding of `<source>:<name>`
syntax identical by construction — a future change to the qualifier
syntax only needs to update one function.

`silent-failure-audit` invoked this session (Skill tool) — applicable
because the change touches a fail-closed `sys.exit` safety check
directly, and the issue's own spawning instructions explicitly warned
against silently weakening it. Verified live (not just by reading) that:
(1) an unqualified name with diverging tiers still raises `SystemExit`
unchanged (test
`test_unqualified_name_with_diverging_tiers_still_fails_closed_when_pins_given`
+ a live repro reusing the pre-fix reproduction fixture); (2) a pin that
names a source with no match for that skill at all falls through to
today's fail-closed behavior rather than silently dropping the conflict
— reproduced live this session:
```
OK: still fail-closed when pin matches nothing: cross-family 후보 스킬 dup-skill 가 둘 이상의 소스에서 겹친다 — skill-repo(...), local-user(...) (이슈 #2055: ...)
```
(3) no new `try`/`except` was introduced anywhere in the diff — the pin
logic is a plain list filter (`pinned = [(source, d) for source, d in ms
if source == pin]`) with an `if pinned:` guard before it is used, so an
empty match list is a no-op, never a swallowed error.

`implementation-blueprint` mounted, not invoked — not applicable. This
change is a parameter threaded through an existing, already-fixed call
chain (four functions gain one optional kwarg each, no new module, no
new abstraction, no structural decision to freeze before fanning out
work); it is not "about to write non-trivial code spanning multiple
modules and need to decide structure" in the sense the skill's own
trigger describes.

`experiment-trust` mounted, not invoked — not applicable. This session
does not interpret, report, or act on an A/B experiment result; it fixes
a harness *dispatch* defect that was blocking the skills-off arm from
running at all. The actual H1 manipulation-check / SRM / pre-registration
concerns belong to whichever session next runs `run_consumer_pair.py`'s
own paired comparison and reads its output.

## What did not work

None.

## Upstream basis

- PR #3172's record (title: "issue-3127: consumer-path measurement --
  both skills-on arms landed, both skills-off arms blocked by a new
  dispatch defect", read this session via `git fetch origin
  pull/3172/head:pr-3172-view` + `git show pr-3172-view:<path>`, not in
  repo on this branch) — "Open findings" item 1 named the exact blocker
  this session fixes and its resolution path, which this session followed.
- `docs/issue-3127/decisions/pre-registration.md` (read but not modified
  this session; unchanged) — the pair/issue-map identity
  (`01-study-groups:19:20`) this session's live dispatch reused.
- `skills.py::resolved_skill_sources()`/`_split_skill_qualifier()`
  (`skills.py:251-417`, read, not modified this session) — the primary
  `--skills` resolution this fix mirrors for the qualifier-parsing rule.

## Open findings

None new. PR #3172's other three open findings (H1 directive-bytes
construct-validity gap, `spawn.py watch` roster-lookup false-negative,
`verify_preregistration.py` squash-merge git-ancestry defect) are
unrelated to blocker A and out of this session's scope — unchanged by
this session.

## Next steps

loop_state is terminal for this session's own scope (blocker A). The
harness's actual paired-comparison run (both arms of both pairs,
`consumer-path-results.json` populated end to end) is a separate,
larger unit of work than this blocker fix and was not attempted here —
this session dispatched exactly one skills-off arm live to prove the
fix, per its own spawning instructions, and left it running rather than
waiting for or reporting its result.

skill-verdict: silent-failure-audit — applied: invoked; verified the
fail-closed sys.exit for unqualified names is unchanged and that a
non-matching pin falls through rather than silently absorbing the
conflict, both live-reproduced this session (see "Why")
skill-verdict: implementation-blueprint — not-applicable: parameter
threaded through an existing call chain, no new structure to freeze
skill-verdict: experiment-trust — not-applicable: this session fixes a
dispatch defect, it does not interpret or act on an experiment result
other mounted skills: not triggered

---
issue: 2507
role: conformance-review
author: conformance-review
loop_state: reported
upstream:
  - path: docs/issue-2507/reports/conformance-review/survey.md
    sha: a3ae2ecda156a90c9d05d0ca30ab38fe8bad8076
  - path: docs/issue-2507/proposals/conformance-review.md
    sha: a3ae2ecda156a90c9d05d0ca30ab38fe8bad8076
  - path: spawn.py
    sha: ad7a3d026e379dc0817735a70a9c35b1781dcec7
  - path: skills.py
    sha: ad7a3d026e379dc0817735a70a9c35b1781dcec7
  - path: pipeline.py
    sha: ad7a3d026e379dc0817735a70a9c35b1781dcec7
subject: issue #2507's `## Acceptance` (R1.1-R1.8/R1-empty-state/R1-must-not,
  R2-R2d, R3-R3c, R4-R4c per the survey's requirement split) checked against
  commit ad7a3d026e379dc0817735a70a9c35b1781dcec7 (PR #2532, head of
  origin/issue-2507/implementation)
test: independent re-derivation per survey's "Verification method per
  requirement" — Inspection+Analysis for R1/R4 (direct grep/Read against a
  worktree of ad7a3d02), Demonstration for R2/R2b/R2d (direct calls into the
  production `consult._cross_family_skill_matches_with_consult`, two task
  shapes chosen by this role, not reused from PR #2532's body), Analysis for
  R2c, judgment-call Unverifiable for R3/R3b/R3c (live-spawn blast-radius
  analysis, reasoned below)
result: cantTell
assertedBy: conformance-review (issue-2507/conformance-review branch, this
  session)
---

# issue-2507 — conformance-review record

canonical: `docs/issue-2507/reports/implementation.md`, sha
`ad7a3d026e379dc0817735a70a9c35b1781dcec7` — untracked on this
`conformance-review` branch (this branch is based on `main`, pre-`ad7a3d02`);
read this session via `git show origin/issue-2507/implementation:docs/issue-2507/reports/implementation.md`.
Every bare mention of "the implementation record" below refers to that
same file at that same sha, not a local path on this branch — the same
"untracked, remote-only path" the survey's own "Board / approval state"
section already reproduced a live `PreToolUse` denial against.

## What was done

Every one of the 4 acceptance bullets (R1 split into its own 8-item
enumeration, R1-empty-state, R1-must-not, plus R2-R2d/R3-R3c/R4-R4c per the
survey) got an independently re-derived verdict against `ad7a3d02`, not
taken from the implementation record's own self-report at face value.

### R1 — the 8 deferred-remainder items: removed or explicitly re-scoped, none silently dropped

canonical: `git diff origin/main...origin/issue-2507/implementation --stat`
(executed this session against the same two refs the survey used) — 10
files changed; `roles/`, `board.py`, `consult.py`, `gates/gates.py`,
`gates/roles_due.py`, and the three named hooks do not appear in that
file list, confirming the survey's "R1.1/R1.4/R1.5/R1.6/R1.7 received zero
code changes" finding still holds at this same sha.

- **R1.1 `roles/`/`roles/specs/` deletion** — verdict: **Present**
  (re-scoped-with-reason, a permitted outcome under R1's own wording).
  evidence: `git ls-tree -d origin/issue-2507/implementation roles` (this
  session) — result: `040000 tree 9bd956ed... roles` (directory intact,
  not deleted). rationale: the stated reason (stage 4 of
  `docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md` not
  landed; deleting now would violate that proposal's own Constraints,
  quoted in the implementation record's "Investigation" section) is
  independently confirmed below (R1-must-not).
- **R1.2 `spawn.py`'s `ROLES` tuple** — verdict: **Present**. evidence:
  `git grep -n "_sp\.ROLES" origin/issue-2507/implementation -- board.py`
  (this session) — result:
  ```
  717:    known = {f"{r}.md" for r in _sp.ROLES}
  744:        roles = {r: _sp.frontmatter(rep / f"{r}.md") for r in _sp.ROLES
  770:            for r in _sp.ROLES:
  782:            for r in sorted(r for r in roles if r not in _sp.ROLES):
  788:            missing = [r for r in _sp.ROLES if r not in roles]
  ```
  plus `git grep -n "spawn.ROLES\|POLL_HEARTBEAT_PATROL_ROLES"
  origin/issue-2507/implementation -- on-the-record/monitors/poll-heartbeat.sh`
  (this session) — result: `181:print(' '.join(spawn.ROLES))`, consumed at
  line 295 of the same file. rationale: both citations in the
  implementation record's Investigation section are real, live reads, not
  stale comments — removing `ROLES` today would silently empty
  `board.py`'s record-discovery set and the patrol loop (fail-open, not an
  error), matching the record's own stated reason.
- **R1.3 `_ROLE_SKILLS`/`resolve_role_source()`** — verdict: **Present**
  (the one item with an actual code change: removed from the spawn-mount
  path, re-scoped for its 4 remaining callers). evidence: `skills.py` diff
  (`git diff origin/main...origin/issue-2507/implementation -- skills.py`,
  read this session) adds `resolve_static_policy_source()` and
  `merge_composed_skill_source()`, both role-agnostic (see R2c below);
  `git grep -n "resolve_role_source(role" origin/issue-2507/implementation
  -- consult.py pipeline.py` (this session) — result:
  ```
  consult.py:690:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
  consult.py:964:    out = list(_sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"])
  consult.py:1357:    plugins = _sp.resolve_role_source(role, _sp._skill_repo_root())["skill_dirs"]
  pipeline.py:1652:        role_source = _sp.resolve_role_source(role, _sp._skill_repo_root())
  ```
  derived: the fenced grep result immediately above — 4 live call sites,
  matching the implementation record's "5 real calls total, not the
  issue's 6" re-derivation (the 6th was a bare re-export alias, not a
  call). rationale: the mount-path removal is a real, verified code change
  (see R2 below); the 4 remaining sites are re-scoped with a stated,
  independently-plausible reason (task text not threaded through
  `_consult_cmd_and_env`; migrating blind risks degrading consult/judge/panel
  guidance quality with no live-verification path available, unlike the
  spawn-mount path).
- **R1.4 `consult.py` existence checks, `pipeline.py::role_settings()`,
  `board.py`'s `_sp.ROLES` iteration** — verdict: **Present**. evidence:
  the R1.2 `board.py` citation above (live `_sp.ROLES` reader) and the
  R1.5 enforcement-chain citation below (same `roles/`-shaped content)
  independently confirm `pipeline.py`/`board.py` are live, non-stub
  readers of role-spec content, not just `consult.py`'s own 4 sites
  already cited under R1.3. rationale: one shared root cause across
  R1.2/R1.4/R1.5 (`roles/<role>.json` spec content is still the live
  enforcement/identity mechanism), not 3 independently-invented excuses.
- **R1.5 `gates/gates.py` enforcement functions + `gates/record_lint.py`/`gates/ci.py`
  callers** — verdict: **Present**. evidence: `git grep -n "def record_enums\|def role_scope\|def record_refusal_reasoned"
  origin/issue-2507/implementation -- gates/gates.py` (this session) —
  result: `309:def record_enums`, `362:def record_refusal_reasoned`,
  `864:def role_scope`; callers — `git grep -n
  "record_enums\|role_scope\|record_refusal_reasoned"
  origin/issue-2507/implementation -- gates/ci.py gates/record_lint.py`
  (this session) — result:
  ```
  gates/ci.py:614:            bad += gates.role_scope(repo, branch)
  gates/ci.py:617:    bad += record_lint.record_enums(repo, {})
  gates/record_lint.py:1466:        diff_scoped += gates.record_enums(root, {})
  gates/record_lint.py:1467:        diff_scoped += gates.record_refusal_reasoned(root, {})
  ```
  rationale: real, unstubbed callers into fail-closed enforcement code —
  changing the read without the stage-4 replacement is the exact worst
  outcome R4c's own `must not` clause names ("a stale reference that fails
  only when a rare branch executes"), so re-scoping (not touching it) is
  the correct-per-acceptance choice, not an excuse.
- **R1.6 `gates/roles_due.py` + `spawn.py`'s `roles-due` CLI** — verdict:
  **Present**. evidence: `git grep -n '"roles-due"'
  origin/issue-2507/implementation -- spawn.py` (this session) — result:
  `1731:    if a.role == "roles-due":`, dispatching into
  `gates/roles_due.py` which reads `roles/specs/*.spec.json` (a subtree
  this session leaves untouched, confirmed via the same `git ls-tree`
  above). rationale: no forcing reason to touch it while `roles/specs/`
  itself stays live — re-scoping with "left as-is" is accurate, not a
  dodge.
- **R1.7 3 named hooks** (`record-scaffold.sh`, `quality-bar-gate.sh`,
  `accumulation-claim-guard.sh`) — verdict: **Present**. evidence: `git
  grep -n "roles/\|record_fields\|BAR_ROLES"
  origin/issue-2507/implementation -- on-the-record/hooks/record-scaffold.sh
  on-the-record/hooks/quality-bar-gate.sh` (this session) — result:
  ```
  record-scaffold.sh:50:record_fields = role_cfg.get("record_fields", {})
  record-scaffold.sh:52:for field in record_fields:
  quality-bar-gate.sh:115:BAR_ROLES = [
  quality-bar-gate.sh:213:for role in BAR_ROLES:
  quality-bar-gate.sh:214:    spec_path = os.path.join(CHECKOUT, "roles", "specs", role + ".spec.json")
  ```
  and `accumulation-claim-guard.sh:114:    return bool(re.match(r"^roles/[^/]+\.json$", check_rel))`
  (git grep, same command family, this session). rationale: each hook
  reads real `roles/`-shaped content for real enforcement decisions (record
  field validation, bar-role spec lookup, accumulation-shape
  classification) — none are stubs, matching the record's claim.
- **R1.8 `CLAUDE_ROLE`** — verdict: **Present**, with the issue's own
  count treated as stale (matching the implementation record's own
  correction, independently reproduced). derived: `grep -rl "CLAUDE_ROLE"
  --include=*.sh on-the-record/hooks/ | grep -v test_ | wc -l` (this
  session, run against this branch's own checked-out tree of
  `on-the-record/hooks/`, which does not differ between `main` and
  `ad7a3d02` for that directory — confirmed via `git diff
  origin/main...origin/issue-2507/implementation --stat -- on-the-record/`,
  empty output, this session) — result: `24`, exactly matching the
  implementation record's own re-derived count (not the issue's stale
  "25").
- **R1-empty-state** — verdict: **Present** (a permitted, not mandatory,
  outcome; no item this session checked claimed "no live callers" for a
  sub-item that in fact has one — every disposition above cites a real
  caller, per the R1.1-R1.8 evidence blocks above).
- **R1-must-not** (`roles/` not deleted while any listed consumer still
  reads it) — verdict: **Present**. evidence: same `git ls-tree -d
  origin/issue-2507/implementation roles` citation above (directory
  present) plus the R1.2-R1.8 live-caller citations above (consumers still
  read it). rationale: the must-not is not violated by omission — nothing
  in the diff assumes a partial deletion.

### R2/R2b/R2c/R2d — task-composed skills on the spawn-mount path

Verified via direct calls into the exact production function
`consult._cross_family_skill_matches_with_consult` (the same function
`spawn._spawn_one()` calls, aliased as `spawn._cross_family_skill_matches_with_consult`)
inside a disposable `git worktree` of `origin/issue-2507/implementation`
(created and removed this session, no branch/file left behind — `git
worktree add /tmp/cr-2507-verify origin/issue-2507/implementation
--detach` then `git worktree remove /tmp/cr-2507-verify --force`, both
executed this session), on two task shapes chosen by this role, distinct
from the three shapes quoted in the implementation record/PR #2532's own
body (perf/db, perf/ds, secure-coding):

```
$ python3 -c "...task='이 REST API 엔드포인트가 에러 응답 포맷을 일관성 없이
리턴한다 -- 에러 코드 체계와 버저닝 전략을 점검하고 스펙을 정리해줘.'; k=5"
shapeA (api-design) outcome= completed took 21.1 s
['api-design-error-design']
$ python3 -c "...task='이 모달 다이얼로그가 스크린리더에서 포커스를 못 받고
색 대비도 낮다 -- 접근성 이슈를 점검해줘.'; k=5"
shapeB (accessibility) outcome= no-candidates took 0.0 s
[]
```

- **R2** (a spawn arrives carrying task-selected skills) — verdict:
  **Present**. shapeA above shows a real, task-matched pick
  (`api-design-error-design`) that role `conformance-review`'s own
  pre-change `_ROLE_SKILLS` entry (7 conformance-review-* skills, none
  api-design-shaped — canonical: this role's own spawn prompt at the top
  of this session, which quotes those 7 names verbatim as this session's
  own mounted skills) could not have produced — the same demonstration
  shape PR #2532's own body used, independently reproduced on a topic the
  PR never tried.
- **R2b** (demonstrated live on >=2 task shapes, resolved list quoted from
  actual output) — verdict: **Present**. Two shapes above, quoted
  verbatim from this session's own stdout (the fenced block above), not
  copied from PR #2532's body: shapeA (a real match) and shapeB (a
  legitimate no-match — BM25 found no candidate worth advising on for an
  accessibility-shaped task under `k=5`; this is a genuine negative
  result, the same "no-match is not a failure" pattern PR #2532's own
  shape1 demonstrated for a different task).
- **R2c** (must not reintroduce a fixed role-keyed table under a
  different name) — verdict: **Present**. evidence: `skills.py`'s
  `resolve_static_policy_source(repo_root)` and
  `merge_composed_skill_source(role_source, matched_dirs)` (read this
  session, both function signatures take no `role` parameter) — neither
  function performs a role-keyed lookup; `resolve_static_policy_source`
  unconditionally resolves the fixed 1-item `_STATIC_POLICY_SKILLS` set
  (`work-in-english`), which is not role-varying and predates this issue
  (issue #2208). rationale: no new `_ROLE_SKILLS`-shaped structure exists
  anywhere in the diff.
- **R2d** (must not let a spawn silently arrive with zero skills where it
  previously got some) — verdict: **Present**. derived:
  ```
  $ python3 -c "
  import spawn
  role_source = spawn.resolve_static_policy_source(spawn._skill_repo_root())
  print('static-only:', role_source['skills'])
  merged_empty_match = spawn.merge_composed_skill_source(role_source, [])
  print('merged with zero cross-family matches:', merged_empty_match['skills'])
  "
  static-only: ['work-in-english']
  merged with zero cross-family matches: ['work-in-english']
  ```
  (this session, same worktree) — even shapeB's zero cross-family matches
  above still merge with a non-empty `work-in-english` policy skill; the
  total mount list is never empty. This is a stronger result than the
  implementation record itself claims (it does not run this specific
  check) — a genuine independent finding, not a repeat of the builder's
  own evidence.

Self-correction to this role's own phase-1 survey: canonical: this role's
own `docs/issue-2507/reports/conformance-review/survey.md` (sha
`a3ae2ecda156a90c9d05d0ca30ab38fe8bad8076`), "Notable surface for phase 2"
section — it claimed the mount-condition change (from
`role_source["source"] == "skill-repo"` to unconditional `if issue is not
None`) was "a behavior change beyond the mount-path swap... cross-family
matching now also runs for roles that previously had zero `_ROLE_SKILLS`
entries." That claim does not survive a re-read of `resolve_role_source()`
itself this session:

```python
# skills.py, resolve_role_source() — always returns a hardcoded literal,
# regardless of whether `names` (the role's mapped skill list) is empty
return {"source": "skill-repo", "skill_dirs": skill_dirs,
        "skills": [d.name for d in skill_dirs],
        "skill_sha": _sp.skill_repo_sha(skill_dirs[0].parent) if skill_dirs else None}
```
(`skills.py`, `origin/issue-2507/implementation`, read this session, full
function body).

canonical: `git grep -n "test_unmapped_role_still_reaches_resolve_role_source"
origin/issue-2507/implementation -- test/test_consult_no_rulebook_identity_regression.py`
(this session) — match found, confirming the "no unmapped-role state"
invariant (issue #1955/#1758) is itself test-pinned in this same tree, not
just asserted in a docstring. Because `role_source["source"]` was
`"skill-repo"` unconditionally pre-change, the old condition `issue is not
None and role_source["source"] == "skill-repo"` was already equivalent to
`issue is not None` for every role, mapped or not. The widened condition
is dead-code cleanup, not a behavior change — this role's own phase-1
finding was wrong, and there is nothing here PR #2532's body needed to
disclose that it did not.

### R3/R3b/R3c — bootstrap_timing from >=5 post-change spawns vs. baseline

verdict: **Unverifiable**, for all three (R3b/R3c both depend on R3's own
data existing). This role's own approved phase-1 proposal committed to
running ">=5 real spawns off `ad7a3d02`" independently, on the stated
premise that this session (unlike `issue-2507/implementation`) does not
share that session's own branch-collision constraint. That premise is
correct as far as it goes, but canonical: `spawn.py`'s `_spawn_one()`,
`origin/issue-2507/implementation`, read this session in full — it
undersold a second, independent hazard visible only once the actual
dispatch code is read (quoted below), not once considered in the survey's
own risk analysis:

```python
# spawn.py, origin/issue-2507/implementation, _spawn_one(), the fork point
# immediately after bootstrap_timing prints (issue-scoped, bounded spawn):
child_pid = os.fork()
if child_pid == 0:
    ...  # child continues past this point completely independently
if child_pid > 0:
    is_parent_return = True
    # ...스폰 자신이 `spawn.py watch --follow` 를 detached 프로세스로 띄우고
```
(`spawn.py:3247-3266`, `origin/issue-2507/implementation`, read this
session in full; the surrounding comment at that line explicitly states
the child is placed in its own session via `setsid` specifically so that
"부모가 속한 프로세스 그룹에 신호가 가도 자식은 안 죽는다" — signals to
the parent's process group do not kill the child).

A real, non-`--dry-run`, `--issue`-scoped spawn does not run synchronously
inside the invoking `spawn.py` process — the parent prints
`bootstrap_timing` and returns almost immediately after `fork()`, while
the child is deliberately detached (`setsid`) into an independent,
autonomous coding-agent session with full tool access, specifically
immune to signals sent to the wrapper that launched it. Getting 5 samples
this way means launching 5 such detached sessions this single headless,
single-turn review session has no way to bound, supervise, or reliably
stop once launched — the same hazard the implementation record itself
named for its own end-to-end spawn ("a spawned child gets full tool
access with no way for this headless, single-turn session to bound or
review its actions before they land"), which this review session in fact
shares, contrary to this role's own phase-1 proposal's premise that it did
not. Per this repo's own guidance on hard-to-reverse, shared-state actions
(new branches/PRs opened autonomously under this identity, real compute
cost, no real-time human confirmation available inside a single headless
turn), this session chose not to execute that plan rather than proceed on
the strength of a phase-1 approval that did not have this specific hazard
in front of it when it was granted.

unverifiable: 5 real post-change `bootstrap_timing` stderr lines from
`spawn.py <role> <task> --issue <n>` invocations against `ad7a3d02` (or a
successor commit) — reason: none exist anywhere in this repo's session
logs yet, since that commit is not on `main` and no spawn has run against
it (derived: `grep -l "bootstrap_timing" ~/.tokenmaxxxer/work/*.log |
xargs grep -l "issue-2507/implementation" 2>/dev/null | wc -l` — result:
`0`, this session), and this session judged launching 5 detached,
unsupervised agent sessions unsafe for the reason quoted above. The
201-log baseline population the survey found (`grep -l "bootstrap_timing"
~/.tokenmaxxxer/work/*.log`) is entirely pre-change by construction, so
R3b's "compared against baseline" and R3c's "states plainly whether
overhead grew" cannot be completed by this session either — both are
chained to R3's missing numerator.

### R4/R4b/R4c — grep survivors

canonical: this record's own R1.2/R1.4/R1.5/R1.6/R1.7 evidence blocks
above (Stratum A citations) and `docs/issue-2507/reports/conformance-review/survey.md`'s
"Sampling scope" section (sha `a3ae2ecda156a90c9d05d0ca30ab38fe8bad8076`,
Stratum B definition — `docs/issue-167/`/`docs/issue-170/`
rulebook-skeleton asset copies plus `tests/`/`gates/test_*.py`
`monkeypatch.setenv("CLAUDE_ROLE", ...)` fixtures).

- **R4** (`grep -rn "roles/" --include=*.py --include=*.sh` returns only
  intentional survivors, each named) — verdict: **Present**, with a count
  correction to this role's own survey (see "Open findings"). Stratum A
  (gates/hooks/core spawn/consult/board path) is the same full set cited
  under R1.2/R1.4/R1.5/R1.6/R1.7 above — every Stratum A hit traces to one
  of those named, live, intentional consumers; no orphaned Stratum A hit
  was found. Stratum B is a class-level summary per the survey's approved
  sampling scope (cited above), not re-enumerated line-by-line this
  session — consistent with, not a shortfall against, that approved
  scope.
- **R4b** (`CLAUDE_ROLE` grep, same shape) — verdict: **Present**, same
  reasoning; live producers exist too — derived: `git grep -n
  "CLAUDE_ROLE" origin/issue-2507/implementation -- consult.py` (this
  session) — result: matches at lines 707, 1016, 1375, confirming the
  implementation record's own citation.
- **R4c** (no reference resolves at runtime to a now-deleted path) —
  verdict: **Present** (trivially, on the current diff). evidence: same
  `git ls-tree -d origin/issue-2507/implementation roles` citation above —
  `roles/` was never deleted in this diff, so nothing in Stratum A or B
  can resolve to a path that does not exist.

## Why

This role's own write_scope is verdict-only — it never edits `spawn.py`,
`skills.py`, `pipeline.py`, `roles/`, or the implementation record.
canonical: `git status --short` (this session, run before this write) —
result: only this record file untracked; no other file this session
touched. Every verdict above is re-derived from this role's own direct
reads/greps/live calls against `ad7a3d02`, not accepted from the
implementation record's own account — per this role's phase-1 proposal's
own Rationale, and matching the finding-record skill's rule that a
verdict comes from looking at the artifact, not the builder's account of
it.

The one place this role deviated from its own approved phase-1 plan (R3's
committed ">=5 real spawns") is explained in R3's own block above with a
concrete, code-cited reason — not a silent gap. This mirrors exactly the
posture the operator's own issue comment asked this review to take toward
PR #2532's deferred items: a re-scoping is acceptable when it states its
reason and does not silently drop the obligation. This role holds itself
to the same bar it applies to the artifact under review.

Two claims the operator specifically asked this role to check
independently, both confirmed:

- (a) The spawn-mount path does arrive with task-selected skills, and
  nothing arrives with zero skills where it previously got some — see R2
  and R2d above, independently demonstrated, not copied from the PR body.
- (b) `scripts/related_files.py 2507 --keyword roles --keyword CLAUDE_ROLE
  --keyword skills`, re-run this session — derived: same command, result:
  2080 output lines, of which the `roles` keyword alone contributes 1150
  lines and only 1 of those 1150 lines is under `docs/` (`grep -c "^docs/"`
  on the tool's own output returns 1, `grep -vc "^docs/"` returns 2079) —
  the bulk (`README.md`, `bench/run.py`, `board.py`, `consult.py`,
  `docs/decisions/*.md`, `docs/handbooks/*.md`, ...) is exactly the
  broad, non-targeted hit set the implementation record described as
  "almost all `docs/issue-*/` historical report/proposal prose" — the
  honest characterization is closer to "broad keyword noise across the
  whole repo" than narrowly `docs/issue-*/`-scoped, but the substance of
  the negative result (it did not save targeted lookups for this task
  shape) is confirmed, independently reproduced.

## Upstream basis

- `docs/issue-2507/reports/conformance-review/survey.md` (sha
  `a3ae2ecda156a90c9d05d0ca30ab38fe8bad8076`) — this role's own phase-1
  requirement extraction, sampling scope, and verification-method
  assignment; two factual corrections to it are logged under "Open
  findings" below.
- `docs/issue-2507/proposals/conformance-review.md` (same sha) — this
  role's own approved phase-1 plan; R3's deviation from it is explained
  above with a concrete, newly-found reason.
- `ad7a3d026e379dc0817735a70a9c35b1781dcec7` (`spawn.py`, `skills.py`,
  `pipeline.py`, plus `docs/issue-2507/reports/implementation.md` —
  untracked on this branch, lives only on `origin/issue-2507/implementation`
  at that sha, same as the top-of-file note above) — the artifact under
  review, head of `origin/issue-2507/implementation`, PR #2532.
- Issue #2507's body — canonical: `gh issue view 2507` output (read
  directly this session) — the `## Acceptance` text is the spec this
  record checks against; the operator's own issue comment (`gh issue view
  2507 --comments`, read this session) scopes what a PARTIAL delivery may
  legitimately defer.

## Open findings

1. **R3/R3b/R3c could not be completed this session** — see the R3 block
   above for the full reasoning (fork+`setsid`-detached child sessions this
   review cannot safely bound). Resolution path: a follow-up session with
   real-time human supervision (able to watch and, if needed, intervene on
   each spawned child as it runs) executes the >=5-spawn
   `bootstrap_timing` collection against `ad7a3d02` or its successor, and
   compares against the pre-change baseline this role's own survey already
   located (201 logs carrying `bootstrap_timing`, none yet parsed for
   values). A narrower alternative worth considering: a purpose-built
   harness that monkeypatches `spawn.py`'s child-launch point
   (immediately after the `bootstrap_timing` print, before `os.fork()`
   hands control to an autonomous agent) to capture the same timing data
   without ever letting a child session run — this was not attempted this
   session for lack of time to validate such a harness would not itself
   distort the very timing it is measuring, but is a safer shape than a
   live, unsupervised 5x spawn.
2. **This role's own phase-1 survey mis-stated the `roles/` grep count as
   "non-`docs/` only."** derived: `git grep -n "roles/"
   origin/issue-2507/implementation -- '*.py' '*.sh' | wc -l` — result:
   `170` (this session) — matches the survey's own "170" figure, but that
   figure is the **total**, not "non-`docs/` hits only" as the survey's
   "Sampling scope" section states; `git grep -n "roles/"
   origin/issue-2507/implementation -- '*.py' '*.sh' | grep -v ":docs/" |
   wc -l` (this session) — result: `135` non-`docs/`, `35` under `docs/`.
   Similarly for `CLAUDE_ROLE`: `git grep -l "CLAUDE_ROLE"
   origin/issue-2507/implementation -- '*.py' '*.sh' | wc -l` — result:
   `111` total, of which `77` are non-`docs/` (`grep -v ":docs/\|^docs/"`)
   — the survey's "60+ ... outside docs/" figure is directionally
   consistent (77 >= 60) but the `roles/` figure was a real mislabel, not
   just an approximation. This does not change any R4/R4b verdict above
   (both were assigned from the Stratum A/B live-consumer citations, not
   from the raw counts), but the survey's own count language should be
   read as corrected by this entry, not as originally written.
3. **Merging PR #2532 as currently framed (`Closes #2507`) would
   auto-close issue #2507 while R3's completion-bar leg remains
   Unverifiable**, per this record's own R3 verdict above — not a defect
   in the PR (the phase-1/phase-2 trailer split contractually requires a
   delivery PR to carry `Closes`, and `Closes` is correct process-wise for
   a PR that is itself a deliberate, disclosed partial landing), but an
   observation the operator may want in view before merging: closing the
   issue does not by itself mean the operator's own 3-point completion bar
   is fully met — the implementation record and this review both
   independently found the `bootstrap_timing` leg still open. Resolution
   path: operator decision — merge and track Open finding 1 as a follow-up,
   or hold `Closes` off this PR until R3 lands. This role reports, it does
   not decide.
4. **The approval-gate's Bash-hook over-block on `docs/issue-<n>/
   reports/*.md` paths** — carried forward from this role's own phase-1
   survey ("Board / approval state" section, two live `PreToolUse`
   denials reproduced there), not independently re-confirmed this session
   (out of this role's `write_scope`, and the phase-1 evidence already
   stands on its own two live reproductions). Resolution path: unchanged
   from phase-1 — a candidate Open Finding for a different issue/role to
   file, not this review's own subject matter.

No other open findings — every R1.1-R1.8/R1-empty-state/R1-must-not/
R2-R2d/R4-R4c item above reached a Present verdict from independently
re-derived evidence (canonical: this record's own R1-R4 blocks above).

## Next steps

- Operator/human: decide on Open finding 3 (whether `Closes #2507` should
  land with R3 still Unverifiable, or be held for a follow-up).
- A follow-up session (human-supervised in real time, or built around a
  monkeypatched no-agent-launch timing harness) executes Open finding 1's
  `bootstrap_timing` collection.
- This record's own `loop_state` is `reported` — this role's terminal
  state per `roles/specs/conformance-review.spec.json` — no further work
  is expected from this role on issue #2507 absent a dispute of a specific
  finding above.

skill-verdict: conformance-review-verdict-assignment — applied: invoked;
used throughout "What was done" above to choose Present wherever cited
evidence is implemented and reachable (rule 1) and Unverifiable for
R3/R3b/R3c, naming the specific missing evidence location in that block
rather than a favorable or unfavorable guess (rule 3); rule 4
(carry-forward) did not apply — canonical: `gh pr list --head
issue-2507/conformance-review --state all` returned no prior PR for this
branch (survey.md, "Board / approval state" section) — no prior
conformance-review record exists for issue #2507 to carry a verdict
forward from.
skill-verdict: conformance-review-finding-record — applied: invoked; every
verdict block above carries requirement/verdict/evidence/rationale inline
(no `spec_vs_built` field needed since no Incorrect verdict was assigned
this session — canonical: the R1-R4 verdict labels above are every one
Present or Unverifiable, never Incorrect); no verdict was written without
an evidence pointer or spec_ref, per the skill's own refusal rule.
skill-verdict: conformance-review-traceability-and-evidence — applied:
invoked; every evidence citation above pins file:line plus the exact
`git grep`/`git diff`/direct-call command run this session against
`ad7a3d02` (rule 1), multi-file requirements (R1.4/R1.5) cite each
contributing file separately (rule 2), and R1.8's `CLAUDE_ROLE` figure is
checked against the issue's own stated "25" before being re-derived (rule
3, backward-trace).
other mounted skills: not triggered this session —
conformance-review-requirement-extraction,
conformance-review-sampling-derivation, and
conformance-review-verification-method-selection were invoked in this
role's own prior phase-1 session (see their skill-verdict lines already
recorded in `docs/issue-2507/reports/conformance-review/survey.md`, not
repeated here); conformance-review-severity-classification: not-applicable
— this review's scope was not extended into risk-weighting a recorded
finding, only ordinary fidelity-checking against the issue's own
acceptance text; adversarial-review: not-applicable — this session's own
method (independent re-derivation from primary sources against a
disposable worktree, never accepting the builder's self-report at face
value, per the phase-1 proposal's own Rationale) already is the
structurally-independent-evaluator posture that skill exists to induce;
spinning up a second, separate blind-evaluator session on top of an
already-independent review role would not add a distinct check here.

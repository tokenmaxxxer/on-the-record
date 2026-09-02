---
issue: 3127
role: adversarial-review+silent-failure-audit+test-depth-audit-aa60d15a
author: adversarial-review+silent-failure-audit+test-depth-audit-aa60d15a
skills: adversarial-review (skill-repository(c05de12)), silent-failure-audit (skill-repository(c05de12)), test-depth-audit (skill-repository(c05de12))
verifies_subject: true  # independent, builder-blind verification of PR #3174's cross-family skills_csv fix against the 5 attack angles named in this session's task
loop_state: done
code_under_review: pipeline.py::_cross_family_candidate_corpus (PR #3174 head 6dd2e88e48ea72ba22e6ba0310ea60388cd16a, base main cad779163dd9704ad109c153f2a2d1d5bd050f9e)
type: verification
breaking: false
verdict: PR #3174 is Present for the real-world scenario the fix targets,
  confirmed via the real spawn.py dispatch on both branches -- on main the
  scenario still sys.exits even after the operator correctly pins the
  source via --skills; on the PR branch the identical scenario dispatches
  clean. The unqualified/wrong-source/mixed-list fail-closed angles are
  Present but for a different reason than claimed -- admission_gate's
  pre-existing resolved_skill_sources() check intercepts every one of them
  before the cross-family stage runs at all, which makes the new
  corpus-level pin-narrowing code's own fail-closed branches dead code in
  the live pipeline (unit-reachable only). The all-callers angle is
  Surface -- consult.py's own consult_cmd/judge_cmd/panel_cmd path does not
  thread skills_csv, though it is not currently exploitable since that
  path never parses a source qualifier to begin with. The live-harness
  angle is Present -- the claimed session, its RUNNING ps snapshot, and the
  frontmatter-only stub skill all independently verified from the
  session's own workspace and event log.
---

# issue-3127 — adversarial-review+silent-failure-audit+test-depth-audit-aa60d15a record

## What was done

canonical: this session's own live command transcript below — each derived:
line names the exact command it comes from.

Independent, builder-blind verification of PR #3174 (`tokenmaxxxer/on-the-record`,
head `6dd2e88e48ea72ba22e6ba0310ea60388cd16a`, branch
`issue-3127/implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250`)
against the attack angles named in this session's spawning instructions.
Read the PR's own record (path
`docs/issue-3127/reports/implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250.md`
on PR #3174's own branch — not in repo on this branch, fetched read-only via
`git show pr-3174-review:docs/issue-3127/reports/implementation-blueprint+experiment-trust+silent-failure-audit-5bb45250.md`)
and diff first, then attacked the shipped code with live fixtures — not by
re-reading the builder's own claims.

**Fail-closed angles — real dispatch, not the unit call.** The repo's own
new tests (both added on PR #3174's branch, method names
`test_unqualified_name_with_diverging_tiers_still_fails_closed_when_pins_given`
and `test_explicit_source_qualifier_pins_the_named_skill_and_skips_conflict`
in `test/test_spawn_cross_family_skill_selection.py`'s
`FourSurfaceCandidateCorpusTest`) call `spawn._cross_family_candidate_corpus()`
directly — a unit call, not `_spawn_one()`. `test/test_spawn_cross_family_skill_selection.py`
itself is in repo on this branch already (pre-dating this PR); the two
methods above exist only on PR #3174's own branch. The repo's own existing
acceptance test on that same file, class `SpawnOneCrossFamilyAcceptanceTest`,
stubs `_cross_family_skill_matches_with_consult` entirely via
`stub_with_consult` (its `_run()` helper) — that stub accepts a
`skills_csv` keyword argument but never forwards it to the inner
`spawn._cross_family_skill_matches(task_text, skill, repo_root, k=k)` call
it makes — so that acceptance test provides no coverage of the pin
behaviour through a real `_spawn_one()` call either.

Built a standalone probe (`/tmp/pr3174_live_dispatch_probe.py`, not part of
the repo, run against a `git worktree` checkout of the PR branch and,
separately, of `main`) that calls the real `spawn._spawn_one()` — the exact
function `main()`'s CLI entry point calls (`spawn.py`'s `role_dispatch`
branch: `return _spawn_one(a.cwd, a.role, a.task, ..., skills=a.skills,
...)`) — stubbing only workspace/roster/ledger/subprocess side effects
unrelated to this check (the same set `SpawnOneCrossFamilyAcceptanceTest`
stubs) and, unlike that test, leaving `_cross_family_skill_matches_with_consult`
real. Fixture: a `dup-skill` under a fake `skill-repo` tier and a
content-diverging `dup-skill` under a fake `home/.claude/skills` tier
(`local-user`), plus a non-conflicting `solo-skill` under `skill-repo`
only, against `target_repo_root` = a real `git init`'d repo.

derived: `python3 pr3174_live_dispatch_probe.py` against the PR worktree —
outcome per case:
```
[unqualified name, diverging tiers] SystemExit: --skills: dup-skill 가 둘 이상의 소스에서 겹친다 — ...
[qualified pin, source does not carry dup-skill] SystemExit: --skills: local-repo:dup-skill — 소스 local-repo 에 스킬 dup-skill 이 없다 ...
[qualified pin, typo'd/nonexistent source name] SystemExit: --skills: 모르는 스킬 totally-bogus-source:dup-skill — ...
[mixed list: skill-repo:solo-skill,dup-skill (dup-skill unqualified)] SystemExit: --skills: dup-skill 가 둘 이상의 소스에서 겹친다 — ...
[control: qualified pin naming the CORRECT source -> should NOT exit here] NO EXIT, rc=0
```
An instrumented spy on `_cross_family_candidate_corpus` recorded its own
call count and arguments across every case above:
```
CORPUS_CALLS = [
  {"skills_csv": "skill-repo:dup-skill", "names": ["dup-skill", "solo-skill"], "raised": null}
]
```
derived: only the control case's call is in that list — the spy fired
exactly once total, confirming the other four cases never reached the
cross-family stage at all: their `SystemExit` came from `admission_gate`'s
pre-existing `_admission_check_directive_completeness` (`pipeline.py:1720`,
calling `skills.py::resolved_skill_sources()`), which runs before
workspace creation and independently already validates every name
literally present in `--skills` — including the qualifier syntax, since
issue #2579, well before this PR. Confirmed by message wording: derived:
`grep -n "겹친다" pipeline.py skills.py` on the PR worktree — `skills.py:404`'s
conflict message reads `"--skills: {name} 가 둘 이상의 소스에서 겹친다"`;
`pipeline.py:1515`'s (the corpus's own, pre-existing message, unchanged
context by this PR) reads `"cross-family 후보 스킬 {name} 가 둘 이상의
소스에서 겹친다"` — the unqualified-name and mixed-list cases' captured
messages above are the `skills.py:404` wording, not `pipeline.py:1515`'s.

derived: same probe against a `git worktree` of `main`
(`cad779163dd9704ad109c153f2a2d1d5bd050f9e`, pre-PR) for the control case
only (the only case that reaches the cross-family stage on the PR branch):
```
[control: qualified pin naming the CORRECT source -> should NOT exit here] SystemExit: cross-family 후보 스킬 dup-skill 가 둘 이상의 소스에서 겹친다 — skill-repo(...), local-user(...) (이슈 #2055: ...)
```
This is the load-bearing comparison: on `main`, an operator who correctly
pinned `--skills skill-repo:dup-skill` (which `admission_gate` accepts
without complaint, since primary resolution already understood the
qualifier) still gets a spurious `sys.exit` from the *separate*,
qualifier-blind cross-family BM25 stage when `dup-skill` also happens to be
auto-matched against the task text — reproducing blocker A live, through
the real dispatch path, not a unit call. On the PR branch the identical
scenario dispatches clean (`rc=0`, corpus spy shows `dup-skill` narrowed to
the `skill-repo` entry, no exit). This is a stronger, live confirmation of
the fix than either the PR's own record or its two new unit tests supply
— both of those call `_cross_family_candidate_corpus()` directly, and the
record's own quoted reproduction lines use the exact `pipeline.py:1515`
wording, confirming those were unit-level calls too.

**Finding (fail-closed angles, Present-but-not-for-the-claimed-reason):**
the fail-closed guarantee for an unqualified name, or a pin naming a
source that does not carry the skill, holds at the system level on both
branches identically (`admission_gate` always catches it first for any
name literally present in `--skills`) — no regression, no weakening. But
this means the new pin-narrowing code's own defensive branches
(`pipeline.py`, the `if pin is not None and len(ms) > 1: ... if pinned: ms
= pinned` block, for the case where `pinned` ends up empty) are
unreachable in the live pipeline for any name present in `--skills`:
`admission_gate` always exits first with a different message before the
cross-family stage's own check on that name is ever evaluated. For a name
not present in `--skills` (BM25-only match), `source_pins.get(name)` is
always `None` by construction (parsing only produces entries for names
literally in the csv), so the narrowing branch never activates for it
either. The only way the new code's successful-narrowing branch fires in
the live pipeline is exactly the control case's shape: a name present in
`--skills` with a valid qualifier that is also independently BM25-matched
— confirmed working above. The "still fail closed when the pin doesn't
match" sub-branch is real, correctly written, and unit-tested, but dead
code end-to-end in the actual dispatch pipeline.

**All-callers angle.** Enumerated every caller of
`_cross_family_candidate_corpus`/`_bm25_cross_family_scores`/
`_cross_family_skill_matches`/`_cross_family_skill_matches_with_consult` in
the PR-branch tree (excluding docstring mentions and test mocks) via
derived: `grep -rn "_cross_family_candidate_corpus\|_bm25_cross_family_scores\|_cross_family_skill_matches\b\|_cross_family_skill_matches_with_consult" --include='*.py' .`:
- `spawn.py`'s `_spawn_one()` real dispatch call site — threaded, fixed,
  confirmed live above.
- `consult.py`'s `rank_skills()` (the `--skill-candidates` preview) — NOT
  threaded. Moot: `rank_skills()`/`--skill-candidates` has no
  `--skills`/qualifier input at all to thread in the first place (its
  `spawn.py` call site passes no `skills_csv`-shaped argument — derived:
  read of the `a.skill_candidates` branch confirms only `task_text`,
  `issue`, `cwd`, `home`, `target_repo_root`, `use_judge` are passed).
- `consult.py`'s `_composed_consult_skill_source()` (called from
  `_consult_cmd_and_env()`, which is `_skill_judge_consult()`'s own call
  chain, and from `consult_cmd`/`judge_cmd`/`panel_cmd`'s own skill mount)
  — NOT threaded. derived: `grep -n "_split_skill_qualifier" skills.py
  pipeline.py` on the PR branch shows `resolve_consult_skill_source()`
  (the resolver `_composed_consult_skill_source()` calls for
  consult/judge/panel's own single `skill` argument) never calls
  `_split_skill_qualifier()` — so `spawn.py consult <skill> "<question>"`/
  `judge`/`panel` never parse a source qualifier on their own skill
  argument to begin with, and have no `--skills`-csv-shaped input either.
  There is currently no way to construct "a pinned skill" through these
  entry points, so the instruction's trigger ("an untouched caller that
  still exits on a pinned skill is Incorrect") does not fire here — graded
  Surface, not Incorrect, but noted because these paths remain exactly as
  exposed to blocker A's original, unconditional cross-family `sys.exit`
  after this PR as they were before it: any BM25-matched, tier-diverging
  skill name still unconditionally exits a `consult`/`judge`/`panel`
  session with zero recourse.
- `_respawn_or_cap()` (`lifecycle.py`) calls `_spawn_one(..., bounded=True)`
  recursively — goes through the same, now-fixed call site, not a separate
  caller of the corpus function.

**Live-harness angle.** The PR's record (on PR #3174's own branch, not in
repo on this branch) claims a live dispatch of the skills-off arm for
`JiwonJung94/study-companion` issue 20, session
`product-discovery-hypothesis-preregistration-e8595864`, confirmed
`RUNNING` via `spawn.py ps`.

derived: `python3 spawn.py ps -C /home/jwjung/study-companion` (run this
session, after the PR's own commits) — no longer shows that session as
`RUNNING`; only unrelated `claim-only` roster-mismatch warnings for other
sessions.
derived: `find / -maxdepth 6 -iname '*e8595864*'` located the session's own
workspace and event log outside this repo (under
`/home/jwjung/.tokenmaxxxer/work/`, a session-workspace root, not a path
in this repo's git history). The event log shows a `session-start` event
whose pid matches the exact pid the PR record's own `spawn.py ps` output
cites, then real progress (an `Edit` on that session's own report file, a
`gh pr create` that opened a real PR on the target repo), then a
`gate-refusal` (a heredoc-shaped Bash call the `pretooluse-dispatcher.sh`
board-gate refused) and a `session-end` event tagged
`"progressed-dirty-tree"`. derived: comparing that session-end timestamp
against the PR's own commit timestamps (`gh pr view 3174 --json commits`)
— the session had already ended, for the unrelated gate-refusal reason,
before the PR's own last (deviation-log) commit landed, and about a minute
after the PR's own record commit. The record's claim ("left running per
instructions, not watched to completion") is accurate as a snapshot at the
time it was written; the session had already finished, for an unrelated
reason, by the time the PR's own last commit landed. Not a
misrepresentation — the record never claims it stayed running — but the
session's actual outcome (`progressed-dirty-tree`, not a clean completion)
is left unstated in the PR's record.

derived: grepped that session's own transcript log for its `Skill` tool
calls and results — confirmed the skill it actually mounted really is a
frontmatter-only stub matching the PR record's own claim:
```
SKILL CALL: {'skill': 'product-discovery-hypothesis-preregistration'}
RESULT: Launching skill: product-discovery-hypothesis-preregistration
...
---
name: product-discovery-hypothesis-preregistration
description: issue #3127 skills-off arm stub -- frontmatter only, no procedure body, so the named skill resolves (fail-closed unknown-skill rejection never fires) but carries no actual guidance content.
---
```
— not the real `product-discovery-hypothesis-preregistration` skill.

**silent-failure-audit applied** (Skill tool invoked this session):
canonical: the PR diff itself (`gh pr diff 3174`) — enumerated every
`try`/`except` added by it: none. The diff (`pipeline.py`, `consult.py`,
`spawn.py`) adds one kwarg threaded through four call sites plus a plain
list-comprehension + `if pinned:` guard in
`_cross_family_candidate_corpus()` — zero new error-handling sites, zero
catch-and-drop patterns, confirming the PR's own no-new-error-handling
claim.

**test-depth-audit applied** (Skill tool invoked this session): both new
tests (`test_unqualified_name_with_diverging_tiers_still_fails_closed_when_pins_given`,
`test_explicit_source_qualifier_pins_the_named_skill_and_skips_conflict`)
are Genuine Assertion — one uses `assertRaises(SystemExit)`, the other
`assertEqual(matches, [("dup-skill", d_repo, "skill-repo")])` on a real
return value — not decorative. But both are unit-level (direct
`_cross_family_candidate_corpus()` calls, bypassing `admission_gate`/
`_spawn_one()` entirely) — per the finding above, that is exactly the
altitude at which the new pin-narrowing code's fail-closed branches are
actually reachable, so the tests are not wrong, just the only tests in the
suite that exercise this change at any altitude. derived: `grep -rn
"_spawn_one\|admission_gate" test/test_spawn_cross_family_skill_selection.py`
on the PR branch shows no such call inside either new test. This session's
own probe is the only thing that has exercised the fix through
`_spawn_one()`/a real dispatch, for either branch.

derived: `timeout 300 python3 -m pytest test/ tests/ -q` on the PR
worktree — result:
```
917 passed, 3 xfailed, 2 warnings in 31.82s
```
matches the PR record's own claimed test-plan line exactly; the 2 warnings
are the pre-existing, unrelated `pinned-fixture-divergence` UserWarning
from `tests/test_skill_candidates_floor.py`.

## Why

Adversarial-review's premise (structurally independent evaluator, no
access to the builder's intent) is why this session read the diff and
tried to break it before reading the builder's record in full — the
"reproduced live" claims in that record turned out, on inspection of their
own quoted message text, to be direct/unit-level calls rather than the
real dispatch the spawning instructions specifically asked this session to
use instead. Building a probe against the real `_spawn_one()` (rather than
trusting the existing acceptance test's stub, which silently drops
`skills_csv`) was the only way to find that the new code's own defensive
branches are dead in the live pipeline — a unit test alone cannot show
that, since a unit test by definition never routes through
`admission_gate`.

Running the identical probe against both the PR branch and a `main`
worktree (rather than only the PR branch) was necessary to establish that
the control case's scenario is a genuine regression-fix, not a
pre-existing non-issue: `main` provably still exits on the exact scenario
the operator would hit (a correctly-pinned name that is also BM25-matched),
the PR branch provably does not.

## What did not work

canonical: this session's own probe iteration, described here because it
changed conclusions mid-session, not because it is an open problem.

An initial version of the probe patched `_cross_family_candidate_corpus`
with a spy whose own keyword arguments didn't tolerate the pre-PR (`main`)
function signature, which lacks `skills_csv` entirely — that version threw
a `TypeError` on the `main` worktree run instead of showing the real
pre-fix behaviour, and, on the PR worktree, appeared to show every probe
case exiting "correctly" without revealing which code path actually
produced the exit. Rewriting the spy to forward `**kwargs` rather than a
fixed keyword list, and adding a `CORPUS_CALLS` recorder, fixed both:
derived: the corrected `python3 pr3174_live_dispatch_probe.py` run quoted
above shows the spy firing exactly once (the control case) rather than
once per case, which is what revealed that `admission_gate`, not the
cross-family stage, produces the other four cases' exits.

## Upstream basis

- PR #3174 (`tokenmaxxxer/on-the-record`, head
  `6dd2e88e48ea72ba22e6ba0310ea60388cd16a`, base main
  `cad779163dd9704ad109c153f2a2d1d5bd050f9e`, fetched read-only this
  session via `git fetch origin pull/3174/head:pr-3174-review` into a
  `git worktree`, never checked out on this branch, never merged, never
  edited) — the subject of this verification.
- The builder's own record on PR #3174's own branch — not in repo on this
  branch — read for claims to attack, not trusted for their truth value.
- `test/test_spawn_cross_family_skill_selection.py` (in repo on this
  branch pre-dating this PR; PR #3174 adds two methods to it on its own
  branch) — read to find the gap (`SpawnOneCrossFamilyAcceptanceTest`'s
  stub dropping `skills_csv`) this session's own probe fills.

## Open findings

1. (Surface, not blocking) `consult.py`'s own `consult_cmd`/`judge_cmd`/
   `panel_cmd` dispatch paths remain exactly as exposed to the original
   blocker-A cross-family `sys.exit` as before this PR — any BM25-matched,
   tier-diverging skill name unconditionally exits those sessions, with no
   qualifier syntax available to work around it (`resolve_consult_skill_source()`
   never calls `_split_skill_qualifier()` — derived: `grep -n
   "_split_skill_qualifier" skills.py pipeline.py` on the PR branch, see
   "All-callers angle" above). Not in this PR's stated scope ("spawn.py's
   real dispatch call site") and not currently reachable as "a pinned
   skill still exits" per the audit instruction's own trigger condition,
   since no pin can be constructed there — but a real, identical latent
   defect for a future session that adds `--skills`-style qualifiers to
   those commands. Resolution path: a follow-up issue against `consult.py`'s
   own skill-mount composition, out of this session's scope.
2. (Informational) The new pin-narrowing code's own "pin matches nothing,
   fall through to fail-closed" branch (`pipeline.py`, the `if pinned:`
   guard's false case) is unreachable in the live `_spawn_one()` pipeline
   for any name present in `--skills` (`admission_gate` always intercepts
   first) and never activates for names absent from `--skills` (no pin
   exists for them) — derived: the `CORPUS_CALLS` spy above, one call
   total across five cases. It is correctly written and unit-tested, just
   dead code end-to-end. No action needed — noted for whoever next edits
   this function, since removing `admission_gate`'s check without noticing
   this dependency would silently re-expose the branch.

## Next steps

derived: `timeout 300 python3 -m pytest test/ tests/ -q` on the PR
worktree (quoted in full above, "test-depth-audit applied") and the
`CORPUS_CALLS`/two-worktree comparison above are this session's own
completed, executed acceptance evidence — loop_state is `done` for this
session's own scope (verification of PR #3174). No further action from
this session — PR #3174 was not merged, approved, or edited, per the
spawning instructions.

skill-verdict: adversarial-review — applied: invoked; built an independent
probe against the real `_spawn_one()` dispatch rather than trusting the
PR's own "reproduced live" claims, which on inspection were unit-level
calls (see "Why")
skill-verdict: silent-failure-audit — applied: invoked; enumerated the
diff's error-handling sites (zero new `try`/`except` — canonical: `gh pr
diff 3174` read in full this session), confirmed the PR's own
no-new-error-handling claim
skill-verdict: test-depth-audit — applied: invoked; classified both new
tests as Genuine Assertion but flagged that neither, nor any other test in
`test/`/`tests/`, exercises the fix through a real dispatch — this
session's own probe is the only thing that has
other mounted skills: not triggered

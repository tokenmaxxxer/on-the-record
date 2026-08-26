---
issue: 2402
role: implementation
loop_state: landed
upstream:
  - path: (none — build-now delivery, contract v3 s19a; no prior proposal round)
    sha:
code_under_review:
  - spawn.py
  - pipeline.py
  - watchdog.py
  - on-the-record/directive/merge-gates.md
type: fix
breaking: "none — purely additive (`spawn.py recut-corrupted` subcommand, one new merge-gates.md bullet, one extended watchdog print line); no existing regex/CLI/function signature changed, no existing call site touched"
verdict: pass
---

# issue-2402 — implementation record

## What was done

Added a sanctioned repair path for issue #2379's corrupted-merge-base
branches that keeps them mapped to their `issue-<n>/<role>` subject,
instead of the ad hoc `fix/...` rename the orchestrator improvised this
session (per #2402's own repro).

- `spawn.py` (`_recut_corrupted_branch`, next to the existing
  `_recut_absorbed_branch`): checks out `br` from `origin/br`, finds
  `merge-base(br, base)` (the corrupted, stale parent), and `git rebase
  --onto base <old-merge-base> br` — replaying exactly the branch's own
  commits onto the correct base while keeping the branch's name
  unchanged.

canonical: `spawn.py`, `_recut_corrupted_branch` (added this delivery,
sits directly after `_recut_absorbed_branch`).

- `pipeline.py` (`recut_corrupted_cli`, next to the existing
  `recut_if_absorbed_cli`): the orchestrator-facing entry point. Fetches
  `origin/issue-<n>/<role>` and the current base, calls
  `_recut_corrupted_branch`, then `git push --force-with-lease origin
  issue-<n>/<role>:issue-<n>/<role>` — same branch name in, same branch
  name out.

canonical: `pipeline.py`, `recut_corrupted_cli` (added this delivery,
sits directly after `recut_if_absorbed_cli`).

- `spawn.py` CLI: new `recut-corrupted` subcommand — `spawn.py
  recut-corrupted --issue <n> --role <role> [-C <cwd>]` — wired next to
  the existing `recut-if-absorbed` dispatch.

canonical: `spawn.py`'s argparse dispatch block, the `if a.role ==
"recut-corrupted":` branch added directly below the existing `if a.role
== "recut-if-absorbed":` branch.

- `watchdog.py`'s per-PR "subject 매핑 실패" line (issue #2196's
  once-per-PR dedup, left structurally untouched — same
  `_watchdog_note_unmappable_pr` gate, same suppression behavior) now
  also names the fix.

canonical: `watchdog.py`, the `print(...)` call inside the `elif
_sp._watchdog_note_unmappable_pr(root, prn):` branch — see the Executed
evidence section below for the exact new string.

- `on-the-record/directive/merge-gates.md`: new bullet next to the
  existing ABSORBED-BRANCH RECUT one, stating the convention and its
  rationale.

canonical: `on-the-record/directive/merge-gates.md`, the new bullet
titled "CORRUPTED-MERGE-BASE RECUT STAYS ON-NAME (issue #2402, repair
path for #2379)", inserted directly after the existing "ABSORBED-BRANCH
RECUT (issue #784, ...)" bullet.

## Why

**Decision: a `spawn.py` subcommand that recuts under the *same* name,
not a second accepted branch pattern.** The issue's acceptance text
offered both options. The same-name subcommand wins because branch-name
mapping is not centralized in this repo — it is duplicated across every
layer that needs to answer "which subject does this branch belong to":

canonical: `grep -n "issue-(\\\\d+)/\|_HEAD_REF_SUBJECT_RE\|_BRANCH_SUBJECT_ROLE_RE\|_ISSUE_ROLE_BRANCH\|_BRANCH_RE\b" watchdog.py gates/spawn_on_approve.py gates/ci.py gates/flows.py gates/roles_due.py` (grep read during this session, before writing `_recut_corrupted_branch`) found five independent regexes, each keying on the literal `issue-<n>/<role>` shape:

- `watchdog.py` — `_HEAD_REF_SUBJECT_RE` (board-sweep narrowing)
- `gates/spawn_on_approve.py` — `_BRANCH_SUBJECT_ROLE_RE` (phase-2
  auto-spawn's own branch discovery)
- `gates/ci.py` — `_ISSUE_ROLE_BRANCH`
- `gates/flows.py` — `_BRANCH_RE`
- `gates/roles_due.py` — `_subject_from_branch` (a `re.match`, not a
  module-level compiled pattern, but the same shape)

Teaching the sweep a second accepted pattern (e.g. `issue-<n>/<role>-v2`
or a `fix/issue-<n>-<role>` shape) means finding and updating every one
of those sites, verifying none of them diverge in how they'd parse the
new shape, and living with two "what does a branch name mean" rules
going forward — exactly the kind of new steady-state surface the
operator-frozen constraint on this issue (2026-08-25 comment: "no added
per-spawn overhead or steady-state load, no new conflict surfaces")
rules out. Recutting onto the *same* name needs zero changes to any of
those sites — they already all handle `issue-<n>/<role>`, so a
corrupted-then-recut branch is, to every one of them, indistinguishable
from a branch that was never corrupted. Demonstrated live in Executed
evidence below (the same `watchdog._HEAD_REF_SUBJECT_RE` and
`gates.spawn_on_approve._candidate_branches` this repo already runs,
called directly against a recut branch).

**Why the force-push here does not violate merge-gates.md's existing
"never force-push over absorbed history" rule (#784):**

canonical: `on-the-record/directive/merge-gates.md`'s pre-existing
ABSORBED-BRANCH RECUT bullet — "Recut the branch off updated base
(`spawn.py`'s `_recut_absorbed_branch` shape) before committing — never
force-push over the absorbed history." That rule's own justification
(same bullet) is that base already absorbed the branch's commits via a
concurrent *merge* — i.e. the commits already reached main through a
real PR merge, so other workspaces may have since forked from that
merged state. A branch corrupted at cut time (issue #2379: its
merge-base is a stale/unrelated ancient commit, not a merge target) was
never itself merged anywhere — nothing legitimate can have forked from a
branch state that was wrong from the moment it was cut. `_recut_corrupted_branch`
also never discards the branch's own commits the way `_recut_absorbed_branch`
resets to base — it rebases them onto a new parent, so the delivered
content survives; only the bogus parent-commit range is dropped.

**Why `git rebase --onto` rather than diff/cherry-pick scripting:** the
branch's own commits are exactly `(old_merge_base, br]` by definition —
`rebase --onto <base> <old_merge_base> <br>` replays precisely that
range onto `<base>` and moves `br` to point at the result, in one git
primitive, preserving each commit's authorship/message. No custom
diff-application logic to get subtly wrong. Demonstrated live below:
content byte-identical before/after.

## What did not work

None.

## Upstream basis

None. Build-now delivery (`CORE_BUILD_NOW=1`, contract v3 s19a): no
phase-1 proposal round ran for this issue.

## Open findings

- Issue #2379 itself (the corrupted-merge-base root cause at branch-cut
  time) stays open — this delivery is the repair path for its output,
  not a fix for the cut-time race. Resolution path: #2379's own
  acceptance (branch-cut merge-base freshness check).

## Next steps

None.

## Executed evidence

acceptance: `python3 -c "import ast; ast.parse(open('spawn.py').read());
ast.parse(open('pipeline.py').read()); ast.parse(open('watchdog.py').read())"`
— result:

```
OK
```

acceptance: `python3 -m pytest tests/test_spawn_on_approve.py
tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py
tests/test_watchdog_heartbeat_noise.py tests/test_spawn_pipeline.py -q`
(existing suites covering the mapping/dispatch/heartbeat-noise code this
delivery sits next to, run unmodified) — result:

```
136 passed in 17.84s
```

**Live demonstration — a real corrupted-merge-base branch, recut, and
re-mapped (acceptance bullets 1 and 2), in a disposable local git
sandbox** (bare `origin.git` + clones under `/tmp/otr-2402-demo`; no
network/real-GitHub writes — this is a synthetic fixture, untracked and
outside this repo).

acceptance: build `main` with a root commit then three more commits
(simulating time/concurrent spawns passing after a branch is first cut),
then cut `issue-304/execution-observation` from the *old* main tip (the
#2379 corruption) with one commit carrying a board-record fixture file
(untracked sandbox path, not part of this repo), push it, and check its
merge-base against current main — result:

```
OLD_MAIN=026bfb0c7d0c803f95760065c68673d4b5d47cb2
NEW_MAIN=cdcacd3cd7985214717604be9aef3040b4a1e645
...
--- merge-base BEFORE recut (should be OLD_MAIN, the corruption) ---
026bfb0c7d0c803f95760065c68673d4b5d47cb2
```

(`git merge-base origin/issue-304/execution-observation origin/main`,
run from a fresh `worker` clone before any recut — equals `OLD_MAIN`,
confirming the fixture reproduces #2379's corrupted-merge-base shape.)

acceptance: `python3 spawn.py recut-corrupted --issue 304 --role
execution-observation -C /tmp/otr-2402-demo/worker` (the real CLI added
this delivery, run against the sandbox) — result:

```
[recut-corrupted] issue-304/execution-observation 를 origin/main 위로 재컷하고 push 했다 — 브랜치 이름/PR 은 그대로라 subject 매핑이 유지된다.
```

acceptance: re-check the merge-base and content after the recut —
`git merge-base origin/issue-304/execution-observation origin/main`,
`git rev-parse origin/main`, `git show
origin/issue-304/execution-observation:<sandbox-fixture-path>` — result:

```
--- merge-base AFTER recut ---
cdcacd3cd7985214717604be9aef3040b4a1e645
cdcacd3cd7985214717604be9aef3040b4a1e645
--- content preserved ---
---
issue: 304
role: execution-observation
```

Merge-base now equals `NEW_MAIN` (clean); the fixture's board-record
content survived unchanged; the branch is still named
`issue-304/execution-observation` — no `fix/...` rename ever happened at
any point in this run.

acceptance: subject-mapping checked live with the repo's actual
predicates (`watchdog._HEAD_REF_SUBJECT_RE`, the literal regex
board-sweep's narrowing runs every tick, and
`gates.spawn_on_approve._candidate_branches`, the literal branch
discovery `ready_for_phase2` uses), contrasted against the old `fix/...`
workaround name — result:

```
board-sweep _HEAD_REF_SUBJECT_RE match: <re.Match object; span=(0, 10), match='issue-304/'> -> subject issue-304
same regex against the pre-fix invented name 'fix/issue-304-execution-observation': None
spawn_on_approve._candidate_branches(worker) contains ('issue-304','execution-observation')? True
all candidates found: {('issue-304', 'execution-observation')}
```

The recut branch is mapped by the same regex board-sweep already runs;
the `fix/...` shape the orchestrator used to invent still fails that
regex (unchanged by design — nothing routes through that name anymore
once this fix's path is used instead).

**Reproducing the issue-304 duplicate-spawn scenario against the fix
(acceptance bullet 3)**, calling the real `gates/spawn_on_approve.py`
(`ready_for_phase2`) — the function behind the `tokenmaxxxer-core#316`
incident the issue text describes — against two states of the same
sandbox, with `_ci._approved_roles_on_issue` mocked to
`{"execution-observation"}` (the one gh-network call this function
makes) and `issue_states={304: "OPEN"}` held constant across both runs:

acceptance: *before* — mirrors the actual incident: the role's real
delivery sits (hypothetically) on a branch board-sweep can't map, so it
never merges, so `board()` never sees it; `pr_index` reflects only the
original phase-1 branch, `OPEN` forever because nothing routes traffic
to the content — result:

```
board() BEFORE fix (real delivery stuck on an unmapped fix/... branch, never merged): {}
ready_for_phase2 (BEFORE fix, i.e. the fix/... workaround): {'issue-304': ['execution-observation']}
```

acceptance: *after* — this fix: the branch was recut under the same
name (step above), then fast-forward-merged into `main` like any
compliant branch (`git checkout -B main origin/main` after pushing the
recut branch's tip onto origin's main ref in the sandbox) — result:

```
board(): {'issue-304': {'execution-observation': {'issue': '304', 'role': 'execution-observation', 'loop_state': 'terminal'}}}
ready_for_phase2 (AFTER fix, role delivered via recut+merge): {}
```

Same function, same mocked inputs — only the branch's provenance
differs (hypothetical unmapped rename vs. this delivery's same-name
recut). `ready_for_phase2` goes from proposing the exact duplicate-spawn
shape the issue-304 incident produced (`{'issue-304':
['execution-observation']}`) to proposing nothing, because `role in
b.get(subject, {})` is now true — the recut branch's content is visible
to `board()` once it merges normally, which it can only do because it
stayed mapped.

**Unmapped-branch messaging (acceptance bullet 4)**: dedup behavior
unchanged (still once per PR per repo state — the pytest run above
reruns issue #2196's suite unmodified); the message text itself now
names the fix —

canonical: `watchdog.py`, inside the per-PR mapping-failure branch (`elif
_sp._watchdog_note_unmappable_pr(root, prn):`), the `print(...)` call's
new f-string:

```
[watchdog] board-sweep: PR #<n> 변경 감지했으나 subject 매핑 실패 (브랜치=<repr>, issue-<n>/<role> 형식 아님) — 이 PR 은 narrowing 에서 무시. issue-<n>/<role> 산출물을 잘못된 base 에서 다시 잡아온(#2379) 브랜치라면 `spawn.py recut-corrupted --issue <n> --role <role>`(#2402)로 같은 이름 아래 재컷하라 — 그 밖의 브랜치라면 board 와 무관한 PR 이니 무시해도 된다
```

**No persistent test file added**: per verify-at-landing, this delivery
relies on the executed sandbox evidence above plus the existing suites
it sits beside (`test_spawn_on_approve.py`, `test_watchdog_heartbeat_noise.py`)
rather than a new committed test asserting sandbox-only paths (the
`issue-304` sandbox fixture paths above are untracked, disposable
`/tmp` paths — not part of this repo).

## skill-verdict

skill-verdict: implementation-blueprint — not-applicable: two small
functions (`_recut_corrupted_branch`, `recut_corrupted_cli`) added
directly beside their exact structural precedent
(`_recut_absorbed_branch`/`recut_if_absorbed_cli`, issue #784) plus one
CLI dispatch line and one doc bullet — no multi-module structure
decision was open to make.
skill-verdict: implementation-complexity-coupling-management —
not-applicable: no coupling/cohesion metric crossed a threshold; the new
functions call existing helpers (`_base`, `subprocess.run`) the same way
their neighbors already do, no new cross-module import direction.
skill-verdict: implementation-design-pattern-selection — not-applicable:
no GoF-pattern indirection question — this is a git-plumbing sequence
(checkout, merge-base, rebase, push), not a class-shape decision.
skill-verdict: implementation-performance-data-structure-choice —
not-applicable: no data structure or algorithm choice in play; the
change is a handful of sequential subprocess calls, not a loop or cache.
skill-verdict: work-in-english — applied: invoked; this record, the
commit message, and the PR are in English. New comments/docstrings/print
text inside `spawn.py`/`pipeline.py`/`watchdog.py` were written in
Korean to match those files' existing (Korean-dominant) convention per
the project-convention-conflict guard; the one new bullet in
`on-the-record/directive/merge-gates.md` was written in English to match
that file's existing (English-only) convention. Flagging per the
skill's guard: this is a real per-file convention split within one
delivery, not an oversight.
other mounted skills: not triggered.

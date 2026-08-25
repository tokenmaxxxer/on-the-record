---
issue: 2402
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2402/reports/implementation.md
    sha: 6adf70c049536e5a8a511d842a567588353eafc1
  - path: docs/issue-2402/reports/implementation/2026-08-26-hunt-recut-corrupted-branch-safety.md
    sha: 6adf70c049536e5a8a511d842a567588353eafc1
subject: PR #2446 (issue-2402/implementation, head 6adf70c049536e5a8a511d842a567588353eafc1, base main); cross-checked against PR #2456's conformance-review disclosure
test: issue #2402 Acceptance section — 4 check bullets
result: passed
assertedBy: execution-observation, independently re-run this turn
---

# issue-2402 — execution-observation record

Path convention for this record: every file cited below with an explicit
`<sha>:<path>` prefix lives on `issue-2402/implementation` at sha
`6adf70c0`, not on this record's own branch
(`issue-2402/execution-observation`, based on `origin/main`). Bare paths
(no sha prefix) refer to this branch. Any bare path under
`docs/issue-831/` below is an untracked sandbox fixture under
`/tmp/eo-2402-demo`, since removed — not part of this repo.

## What was done

Independently re-ran PR #2446's acceptance evidence rather than citing its
claims, in an isolated worktree (`git worktree add /tmp/otr-2402-eo
origin/issue-2402/implementation`, since removed with `git worktree
remove` after use) and a fresh disposable git sandbox distinct from both
prior sessions' fixtures (implementation's own `/tmp/otr-2402-demo`
`issue-304` fixture; conformance-review's `/tmp/rev-2402-demo`
`issue-999` fixture) — this session used `/tmp/eo-2402-demo`, an
`issue-831` fixture, since removed after use.

acceptance: `python3 -c "import ast; ast.parse(open('spawn.py').read());
ast.parse(open('pipeline.py').read());
ast.parse(open('watchdog.py').read())"`, run this turn in the `6adf70c0`
worktree — result: `OK` (matches the record's own claim).

acceptance: `python3 -m pytest tests/test_spawn_on_approve.py
tests/test_spawn_on_pr.py tests/test_spawn_on_pr_park.py
tests/test_watchdog_heartbeat_noise.py tests/test_spawn_pipeline.py -q`,
run this turn in the `6adf70c0` worktree — result:
```
136 passed in 8.97s
```
Same suite set, same 136 count as the record's own `136 passed in
17.84s` and the conformance-review's own `136 passed in 35.78s` — pass
count identical across all three independent runs; wall-clock differs
under each session's own host load (derived: hand count "136" above
equals pytest's own "136 passed" summary line).

**Live demonstration — acceptance bullets 1 and 2 (recut path exists,
board-sweep maps the recut branch)**, fresh sandbox, this turn:

acceptance: built a bare `origin.git` with `trunk` as its default branch
(`git symbolic-ref HEAD refs/heads/trunk` on the bare repo — avoided
naming the sandbox's default branch `main`, since `spawn.py`'s own
`_base()` reads `origin/HEAD` dynamically rather than hardcoding `main`,
so this is a faithful exercise of the real base-resolution path, not a
special case), cut `issue-831/execution-observation` from the old trunk
tip with one fixture commit at (untracked sandbox path)
`docs/issue-831/reports/execution-observation.md`, advanced trunk two
more commits, then checked `git merge-base
origin/issue-831/execution-observation origin/trunk` from a fresh clone
— result:
```
OLD_TRUNK=596e1b08f47775db3fd52e360a4f5df76481e3d8
NEW_TRUNK=773494054ef442b5a62ee537d9240f62b18ad836
--- merge-base BEFORE recut (expect OLD_TRUNK) ---
596e1b08f47775db3fd52e360a4f5df76481e3d8
```
Equals `OLD_TRUNK` — the corrupted-merge-base shape reproduced.

acceptance: `python3 /tmp/otr-2402-eo/spawn.py recut-corrupted --issue 831
--role execution-observation -C /tmp/eo-2402-demo/worker` (the real CLI
this delivery added, run this turn against the sandbox) — result:
```
[recut-corrupted] issue-831/execution-observation 를 origin/trunk 위로 재컷하고 push 했다 — 브랜치 이름/PR 은 그대로라 subject 매핑이 유지된다.
```
`base` resolved to `origin/trunk` dynamically (not a hardcoded `main`),
confirming `_base()`'s `origin/HEAD` read path is what the CLI actually
uses.

acceptance: re-checked merge-base/content/branch-name after the recut —
result:
```
--- merge-base AFTER recut ---
773494054ef442b5a62ee537d9240f62b18ad836
773494054ef442b5a62ee537d9240f62b18ad836
```
Equals `NEW_TRUNK` — clean. `git show origin/issue-831/execution-observation:`
followed by the same untracked sandbox path above returned the fixture
content byte-identical to what was committed before the recut; `git
ls-remote origin | grep 831` showed only
`refs/heads/issue-831/execution-observation` — no `fix/...` rename ever
happened.

acceptance: `watchdog._HEAD_REF_SUBJECT_RE` (imported fresh this turn
from the `6adf70c0` worktree, not copied from either prior session's
paste), matched against the recut branch name and the old `fix/...`
workaround shape — result:
```
recut branch match: <re.Match object; span=(0, 10), match='issue-831/'> -> subject issue-831/
old fix/... workaround match: None
```
The same regex board-sweep's narrowing runs every tick maps the recut
branch; the pre-fix workaround shape still fails it (unchanged by
design).

**Live demonstration — acceptance bullet 3 (no duplicate spawn)**, this
turn: this is the one demonstration conformance-review's own session
(PR #2456) attempted but did not complete — its independent re-run of
the mocked `ready_for_phase2` before/after scenario hit a transient
`ENOSPC` tooling failure mid-run and fell back to citing the
implementation record's own transcript plus a direct, unmodified-source
read of the dedup guard (`gates/spawn_on_approve.py:147-197`) instead
(canonical: `6adf70c0:docs/issue-2402/reports/conformance-review.md` —
not present at this sha; see note below — cited instead from `gh pr view
2456 --json body`, read this turn, and the PR's own "## What did not
work" transcript). This session re-attempted that specific re-run, in a
fresh sandbox distinct from both prior fixtures (`issue-304` in the
implementation record, `issue-999` in conformance-review's incomplete
attempt).

First attempt at the "before" state reused the same worker clone the
recut CLI had just run in — that clone's working tree was left checked
out on `issue-831/execution-observation` itself (a side effect of
`_recut_corrupted_branch`'s own `git checkout -B br origin/br`), so
`board()` saw the fixture record even in the "before" case and both
runs returned `{}` (canonical: this session's own first mocked run this
turn, both printed lines read `{}`). Corrected by cloning a second,
untouched checkout (`worker-before`, explicitly on `trunk`, never passed
to the CLI) to represent "delivery stuck on an unmapped branch, never
merged" purely via `board()`'s literal filesystem read, and a third
checkout (`worker-after`, `trunk` locally merged with the now-clean
`issue-831/execution-observation`) to represent the fix's outcome — a
defect in this session's own first sandbox construction, not in the
PR's code, disclosed here rather than silently redone.

acceptance: calling the real `gates.spawn_on_approve.ready_for_phase2`
against both corrected roots, `_ci._approved_roles_on_issue` mocked to
`{"execution-observation"}` (the one gh-network call this function
makes) and `issue_states={831: "OPEN"}` held constant across both calls
— result:
```
BEFORE (delivery stuck, board() sees nothing): {'issue-831': ['execution-observation']}
AFTER  (same-name recut merged normally, board() sees the record): {}
```
Same function, same mocked inputs, same wall-clock session — only the
branch's provenance and the resulting `board()` visibility differ.
`ready_for_phase2` proposes the exact duplicate-spawn shape the
issue-304 incident produced when the delivery's `board()` record is
invisible, and proposes nothing once the recut branch's content is
visible via a normal merge — canonical: the two-line result block
directly above, this turn's own execution. This closes the demonstration
gap conformance-review's own PR body disclosed as incomplete for its R3
check (`gh pr view 2456 --json body`, read this turn: "One demonstration
... could not be completed this session due to intermittent host-level
`ENOSPC` tooling failures").

**Acceptance bullet 4 (unmapped-branch messaging)**: read
`6adf70c0:watchdog.py:1011-1017` directly this turn (not copied from
either prior record) — the per-PR mapping-failure branch is
structurally unchanged (`elif _sp._watchdog_note_unmappable_pr(root,
prn):`, issue #2196's once-per-PR dedup gate untouched); the print
string names the branch (`브랜치={branch!r}`) and gives an action for
both sub-cases (`spawn.py recut-corrupted --issue <n> --role
<role>`(#2402) for corrupted-merge-base recuts, "그 밖의 브랜치라면 ...
무시해도 된다" for the generic case) — matches both prior records'
citations verbatim (canonical: `6adf70c0:watchdog.py:1011-1017`, read
this turn via the `/tmp/otr-2402-eo` worktree).

**Diff scope**: `git diff --stat origin/main...HEAD` from the `6adf70c0`
worktree, this turn — result:
```
docs/issue-2402/reports/implementation.md          | 329 ++
...026-08-26-hunt-recut-corrupted-branch-safety.md |  71 ++
on-the-record/directive/merge-gates.md             |  25 ++
pipeline.py                                        |  51 ++
spawn.py                                           |  38 ++-
watchdog.py                                         |   6 +-
6 files changed, 518 insertions(+), 2 deletions(-)
```
No file under `gates/` appears — confirms `gates/spawn_on_approve.py`,
`gates/ci.py`, and `gates/flows.py` (the mapping-duplication sites the
"Why" section's five-site claim names) are unmodified, corroborating
both prior records' "purely additive" characterization independently
(canonical: the diffstat block directly above, this turn's own run).

`on-the-record/directive/merge-gates.md` (canonical:
`6adf70c0:on-the-record/directive/merge-gates.md`, `grep -n
"CORRUPTED-MERGE-BASE\|ABSORBED-BRANCH"` run this turn, matched lines 4
and 11) carries the new "CORRUPTED-MERGE-BASE RECUT STAYS ON-NAME (issue
#2402, repair path for #2379)" bullet next to the pre-existing
"ABSORBED-BRANCH RECUT (issue #784, ...)" bullet, as both prior records
describe.

## Why

Both PR #2446's own implementation record and PR #2456's independent
conformance-review already assert all four of issue #2402's acceptance
checks are satisfied. Re-derived each check from scratch in a fresh
worktree and a fresh sandbox rather than treating either prior record's
transcripts as sufficient — ran the ast-parse and pytest suites myself,
built an independent corrupted-merge-base fixture and ran the real
`recut-corrupted` CLI against it myself, matched the real mapping regex
against the recut branch myself, and — targeting the one gap
conformance-review's own session disclosed as incomplete — attempted an
independent fresh re-run of the mocked `ready_for_phase2` before/after
duplicate-spawn scenario, in a sandbox distinct from both prior
sessions' fixtures. canonical: the "What was done" section above holds
every executed transcript this paragraph summarizes (ast-parse OK,
pytest 136 passed, the recut CLI live demo, the regex match, and the two
`ready_for_phase2` result lines) — this turn's own runs, not either
prior record's numbers.

Considered and rejected: treating conformance-review's Present verdict
on R3 (resting on unmodified-source reading plus the implementation
record's own executed transcript) as license to skip attempting the
re-run myself — rejected, since this role's own value is independent
re-execution where it's possible, and conformance-review's own record
explicitly left that door open as non-blocking future work. The first
attempt reproduced a sandbox-construction mistake of this session's own
making (documented above under acceptance bullet 3), not the prior
session's `ENOSPC` host condition; correcting it and re-running produced
the two-line before/after result cited above under "What was done".

## Upstream basis

- `6adf70c0:docs/issue-2402/reports/implementation.md` — the delivered
  work's own account; re-derived rather than cited, per this role's
  independent-execution mandate.
- `6adf70c0:docs/issue-2402/reports/implementation/2026-08-26-hunt-recut-corrupted-branch-safety.md`
  — the after-proposal warrant-hunt record (4 stances: checkout/local-edit
  safety, no-op rebase safety, force-with-lease staleness,
  silent-returncode-swallowing; verdict NO FINDING on all four); not
  independently re-run this turn (these are git-plumbing safety stances
  cross-checked by conformance-review's own R5 finding against the
  unmodified subprocess-returncode-checking code, not one of issue
  #2402's four acceptance checks this record targets).
- PR #2456 (`issue-2402/conformance-review`) — read via `gh pr view 2456
  --json body` this turn for its disclosed "What did not work" gap (the
  R3 re-execution it could not complete), which this session
  specifically targeted to close.
- `6adf70c0:spawn.py`, `6adf70c0:pipeline.py`, `6adf70c0:watchdog.py`,
  `6adf70c0:on-the-record/directive/merge-gates.md` — the actual code
  and doc changes, read directly this turn via the `/tmp/otr-2402-eo`
  worktree.

## Open findings

None. All four of issue #2402's acceptance checks were independently
re-derived this turn against fresh fixtures and matched both prior
records' claims; the one demonstration gap conformance-review's own
record disclosed as incomplete (R3's mocked before/after re-run) was
independently re-attempted this turn and produced the two-line result
cited under "What was done" above.

## What did not work

The first sandbox construction for acceptance bullet 3's before/after
comparison was wrong: reusing the worker clone the `recut-corrupted` CLI
had already run in left that clone checked out on
`issue-831/execution-observation` itself, so `board()` saw the fixture
record in both the "before" and "after" calls and `ready_for_phase2`
returned `{}` for both (canonical: this session's own first mocked run
this turn — both printed result lines read `{}`, not the differing
`{'issue-831': [...]}` / `{}` pair expected). Root cause and fix are
recorded under "What was done"'s acceptance-bullet-3 section above,
including the executed transcript from the corrected sandbox. Two draft
passes of this file were also rejected by the record-claim-guard and
record-shape hooks before this version: bare (non-annotated) references
to the untracked `docs/issue-831/...` sandbox path, and several OUTCOME
sentences in "Why" lacking an in-section `canonical:`/`derived:` tag —
both fixed above by annotating every sandbox-path mention and attaching
an explicit `canonical:` pointer to this turn's own transcript wherever
an outcome is asserted.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the four independently-executed checks above —
result:
```
ast-parse: OK (this turn)
full targeted suite: 136 passed (this turn; matches both prior sessions' 136)
recut CLI live demo: clean merge-base + preserved content + unchanged branch name (this turn, fresh issue-831 fixture)
mapping regex live: recut branch matches, fix/... shape does not (this turn)
ready_for_phase2 before/after: {'issue-831': ['execution-observation']} -> {} (this turn, completing the re-run conformance-review's session could not finish)
watchdog messaging: names branch + gives action for both sub-cases (this turn, direct read)
diff scope: no gates/*.py touched (this turn, direct diff)
```

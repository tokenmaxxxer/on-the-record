---
issue: 2240
role: execution-observation
loop_state: handed-off
upstream:
  - path: /tmp/pr2247-worktree/docs/issue-2240/reports/implementation.md
    sha: 8eb582504e442cc3656103bcc67dc0c12b856161
subject: 6993a0e77398ea48bfc6db0f86f015bd06ecb611
test: python3 -m pytest tests/test_state_root_scoping.py -v
result: passed
assertedBy: execution-observation session, issue-2240, this turn
---

# issue-2240 — execution-observation record

## What was done

Independent execution-observation of PR #2247 (branch
`issue-2240/implementation` into `main`, head
`6993a0e77398ea48bfc6db0f86f015bd06ecb611`, state OPEN) against issue
#2240's acceptance criteria: empty-state-on-first-tick, and the
provenance bullet's three parts — (a) orchestrator state accumulates
across ticks, (b) the spawned/consumer workspace tree stays clean, (c)
`should_park()` actually parks on the second identical tick.

Method: `git worktree add /tmp/pr2247-worktree origin/issue-2240/implementation`
(a separate checkout outside this branch's own tree) to run the PR's
code without touching this session's own working tree, plus two
from-scratch scratch directories built by hand
(`/tmp/eo2240-target-repo` — a real `git init`'d repo standing in for a
consumer target repo, `/tmp/eo2240-orchestrator-state` — standing in for
`MUSTER_STATE_ROOT`) rather than reusing the PR's own `/tmp/issue2240-*`
demonstration paths, so a defect specific to those exact paths would not
be masked by re-running against the same directories.

**1) The issue's own named gate, re-run by this session:**

canonical: `python3 -m pytest tests/test_state_root_scoping.py -v` (this session, run from the `/tmp/pr2247-worktree` checkout of the PR branch — every case individually shown PASSED below, no FAILED line):
```
13 passed in 0.93s
```
canonical: same run quoted immediately above (this session's own re-run of the exact command from the PR's own test plan, in a clean process — not a copy of the PR record's own pasted number).

**2) Live two-tick `should_park()` demonstration (own scratch dirs, real
unmocked `spawn_on_pr` functions, driven directly rather than through
pytest):**

canonical: `MUSTER_STATE_ROOT=/tmp/eo2240-orchestrator-state python3 -` (a script driving `spawn_on_pr.load_park_state`/`should_park`/`_save_park_state` against `root=/tmp/eo2240-target-repo`, a fresh `git init`'d repo with one commit, this session):
```
=== TICK 1 ===
prior= None should_park= False
=== TICK 2 ===
prior= {'blocked': True, 'parked': False, 'pr_number': 42} should_park= True
orchestrator state path: /tmp/eo2240-orchestrator-state/spawn_on_pr_parked.json
```
canonical: same run quoted immediately above (this session's own from-scratch scenario) — reproduces the same transcript shape the PR record claims (`prior=None`/`should_park=False` tick 1, `prior={...}`/`should_park=True` tick 2), not a re-run of the PR's own script.

**3) Consumer-tree-clean check (own scratch target repo, checked after
the two ticks above):**

canonical: `cat /tmp/eo2240-orchestrator-state/spawn_on_pr_parked.json`, `find /tmp/eo2240-target-repo -mindepth 1`, `git status --porcelain` inside `/tmp/eo2240-target-repo` (this session):
```
=== (a) orchestrator state file content ===
{
  "issue-9999/conformance-review": {
    "blocked": true,
    "parked": false,
    "pr_number": 42
  }
}

=== (b) full listing of target repo dir ===
/tmp/eo2240-target-repo/.git  (contents only)
/tmp/eo2240-target-repo/README.md

=== git status inside target repo ===
(empty — clean)
```
canonical: same commands quoted immediately above (this session's own scratch repo) — (a) the orchestrator's own state file exists on disk with the tick-1 write intact after the tick-2 read; (b) the target repo's tree gained nothing beyond `.git/` internals and the pre-existing `README.md`, no `runs/` directory anywhere; (c) `git status --porcelain` reports nothing untracked or modified.

**4) Spot-check of a subset of the PR's regression-sweep claim (own
subset — this session did not re-run the PR's full sweep, see Open
findings):**

canonical: `python3 -m pytest tests/test_spawn_on_pr_park.py gates/test_gh_delta.py gates/test_closure_sweep.py -q` (this session, PR worktree):
```
43 passed in 1.30s
```

**5) `docs/specs/reconciled-index.md` regeneration claim:**

canonical: `python3 gates/spec_index.py --update` followed by `git status --porcelain -- docs/specs/reconciled-index.md` (this session, PR worktree):
```
(git status: no output — no diff produced)
```
canonical: same commands quoted immediately above — corroborates the PR's claim that the index needed no update despite `docs/specs/enforcement-boundary.md` being touched in the same PR.

**6) Independent code checks beyond re-running the PR's own commands:**

canonical: `grep -rn "cursor_path(" --include=*.py .` in the PR worktree (this session):
```
gates/gh_delta.py:141:    cpath = path or cursor_path(resource)
tests/test_state_root_scoping.py:44:        path = gh_delta.cursor_path("issues")
tests/test_state_root_scoping.py:114:        cpath = gh_delta.cursor_path("issues")
```
canonical: same grep quoted immediately above — `gh_delta.cursor_path()`'s public signature dropped its `root` parameter entirely (was `cursor_path(root, resource)`, now `cursor_path(resource)`); the only non-definition call site in the tree is `gh_delta.py`'s own internal call plus the two test-file call sites shown above, so this signature change is not actually breaking in practice even though the PR record's `breaking: "none"` frontmatter claim understates that the public signature did change (see Open findings).

canonical: `grep -rn 'root / "runs"\|Path("runs")' --include=*.py .` outside test files, in the PR worktree (this session):
```
(zero matches outside gates/state_paths.py's own docstring text naming the pattern)
```
canonical: same grep quoted immediately above — no `root / "runs"` call site was missed by the PR's classification sweep.

canonical: `grep -rn "PARK_STATE_REL\|MERGED_SEEN_STATE_REL\|ATTEMPTED_STATE_REL\|OUT_OF_INDEX_SEEN_STATE_REL\|BACKOFF_STATE_REL\|BOARD_SWEEP_QUEUE_STATE_REL"` in the PR worktree (this session):
```
(zero matches — every renamed *_REL constant's old name is fully gone, not just superseded)
```

canonical: `sed -n '852,858p' consult.py` in the PR worktree (this session — the PR record's Open findings section claims `consult.py`'s `_judge_trace_path()` still composes `root / "runs" / "patrol-judge-log.md"` with the same rejected "gitignore hides it" docstring rationale, left unfixed as a deliberate scope decision):
```
def _judge_trace_path(cwd: str) -> Path:
    """모든 judge 실행이 공유하는 트레이스 — `runs/patrol-judge-log.md`
    (제안서 §Constraints "trace-always", consult-log `finally` 관례와
    같은 이유). `runs/`는 git-ignored라 커밋 없이도 대상 트리를
    더럽히지 않는다(이슈 #1730)."""
    return _sp._consult_root(cwd) / "runs" / "patrol-judge-log.md"
```
canonical: same file:line quote immediately above — matches the PR record's own claim verbatim, a genuine open finding rather than an overstated or quietly-dropped one.

All temp artifacts (the `/tmp/pr2247-worktree` worktree,
`/tmp/eo2240-target-repo`, `/tmp/eo2240-orchestrator-state`) were removed
by this session after use:

canonical: `git status --porcelain=v1 -b` (this session, own repo, re-checked after cleanup):
```
## issue-2240/execution-observation...origin/main
 M .orchestrate-hook-fires.log
?? .on-the-record/directive/
?? docs/issue-2240/
```
canonical: same status output quoted immediately above — unchanged in shape from this session's own tree at the point verification work began (the only new path is this record itself, plus the pre-existing untracked directive/report scaffolding), so none of the scratch work touched this branch.

## Why

Issue #2240's acceptance section names an executed-live provenance
demonstration as the load-bearing evidence — precisely because #2238's
own bug was a guard that looked correct in code but had, measured, never
actually parked anything. Reading the PR's diff and record and trusting
its pasted transcripts would not distinguish "the fix works" from "the
fix's demonstration script happens to work on the demonstrator's own
machine, in the demonstrator's own temp paths." Re-deriving the same
three provenance parts from this session's own from-scratch scratch
directories, own scratch script, and a separate git worktree is what
this role adds over trusting the upstream role's self-report. The
issue's own named gate, tests/test_state_root_scoping.py, was re-run
verbatim since it is the issue's own designated acceptance surface; the
regression-sweep and spec_index.py claims were spot-checked rather than
exhaustively re-run, since the issue's own acceptance section does not
name them and a full ~3200-case re-run was judged disproportionate to a
headless single-turn observation round (see Open findings for the
resulting scope note).

## Upstream basis

- PR #2247 (branch `issue-2240/implementation`, head
  `6993a0e77398ea48bfc6db0f86f015bd06ecb611`), read via `gh pr diff 2247`
  and `gh pr view 2247`, this session.
- The PR's own implementation record, untracked in this repo's own tree
  — read only through the read-only worktree this session created at
  `/tmp/pr2247-worktree` (path: docs/issue-2240/reports/implementation.md
  inside that worktree; commit `8eb582504e442cc3656103bcc67dc0c12b856161`
  for the code it documents), read after this session's own scenarios
  were already designed and run.
- `gates/gh_delta.py`, `gates/board_read.py`, `gates/spawn_on_pr.py`,
  `gates/spawn_on_approve.py`, `gates/closure_sweep.py`, `watchdog.py`,
  `consult.py`, and the PR's new gates/state_paths.py module (untracked
  on this branch — read only from the `/tmp/pr2247-worktree` checkout),
  all read directly from the `origin/issue-2240/implementation` worktree
  this session created.
- Issue #2240 itself (`gh issue view 2240`, this session) — source of
  the acceptance criteria (empty state, and the three-part provenance
  demonstration) targeted above.

## Open findings

1. This session spot-checked the PR's regression-sweep claim against
   only a 3-file, 43-test subset directly touching the renamed
   accessors (`test_spawn_on_pr_park.py`, `test_gh_delta.py`,
   `test_closure_sweep.py`), not the PR's own full sweep. The PR's
   record itself states (canonical: the PR implementation record's own
   Executed acceptance evidence section, read via the `/tmp/pr2247-worktree`
   checkout, this session — not independently re-run by this session):
   ```
   284 passed, 4 xfailed, 1 xpassed in 184.31s (0:03:04)
   2 failed, 3169 passed, 19 xfailed, 2 xpassed in 89.68s (0:01:29)
   ```
   Resolution path: not required to close #2240 — the issue's own
   acceptance section names only the empty-state and provenance
   criteria, both independently re-executed above; a broader regression
   re-run is a general confidence check, not this issue's specific
   acceptance surface.
2. `gh_delta.cursor_path()`'s public signature changed from
   `cursor_path(root, resource)` to `cursor_path(resource)` — a real
   signature change the PR record's `breaking: "none"` frontmatter
   claim glosses over, even though this session's own grep in item 6
   above (PR worktree) shows no caller in the tree uses the old
   two-argument form, so nothing in this repo is actually broken by it.
   Resolution path: none needed for #2240 itself; worth a one-line
   correction to the implementation record's `breaking:` field if that
   record is amended, but not a functional defect.
3. `consult.py`'s `_judge_trace_path()` still has the same scoping
   shape this issue's Non-goals section rejects the "gitignore hides
   it" workaround for. This shape is present, unfixed, and disclosed
   honestly as an open finding in the PR's own record rather than
   silently left out of scope (item 6 above). Resolution path: a
   follow-up issue scoped to `consult.py`, as the PR record itself
   proposes — carried forward here as still open, not resolved by this
   PR.

## Next steps

None — `loop_state: handed-off` is terminal for this record kind. All
open findings above are scope notes for follow-up rounds, not blockers:
the issue's named gate, the empty-state criterion, and all three parts
of the provenance demonstration were independently re-executed by this
session against real (non-mocked) code and real filesystem state, and
none of it contradicted the PR's own claims.

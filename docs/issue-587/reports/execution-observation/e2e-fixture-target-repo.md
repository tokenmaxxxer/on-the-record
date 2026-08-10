# Issue #587 step 3 — e2e fixture-target-repo drive (phase 2, re-verification round)

This file supersedes the round-1 drive below for event 4 only; the PR-opened, verdict-synthesized,
remediation-routed, and escalation events are carried forward from that round rather than
re-executed, per the reasoning in "## Scope of this round".

## Scope of this round

The prior execution-observation record's own resolution path
(`git show 7e7b54f:docs/issue-587/reports/execution-observation.md`, "## Resolution path") scoped
re-verification to "re-runs the same fixture-drive Scenario A step 4 and confirms a 'Remediation
merged' comment appears in gh.log" — i.e. event 4 only, since the other four events were already
confirmed firing on the shipped code and this remediation round's write set
(`docs/issue-587/reports/implementation.md`, PR #603) did not touch their code paths.

Confirmed via diff, not re-execution, this session:

```
$ git show 8ab9940 --stat
 docs/issue-587/reports/implementation.md       | 158 ++++++++++++++-----------
 on-the-record/hooks/delegated-judgment-gate.sh |   1 +
 spawn.py                                       |  71 +++++++++++
 test_spawn.py                                  |  93 +++++++++++++++
 4 files changed, 254 insertions(+), 69 deletions(-)

$ git show 8ab9940 -- spawn.py | grep -n "^@@\|^-def \|^+def "
18:@@ -1100,6 +1100,25 @@ def _pr_open_or_merged_for_branch(root: Path, branch: str) -> int | None:
22:+def _merged_pr_for_branch(root: Path, branch: str) -> int | None:
44:@@ -2084,6 +2103,58 @@ def _roster_reconcile_unreported(issue: int | None = None) -> int:
51:+def _remediation_merge_sweep(root: Path, issue: int) -> int:
```

`spawn.py | 71 +++++++++++` is pure insertion (zero `-` lines in that file's hunk headers) — both
hunks insert a brand-new function body immediately after an existing one
(`_pr_open_or_merged_for_branch`, `_roster_reconcile_unreported`); `roster_reconcile()`, `main()`,
and every other call site the already-verified events depend on is untouched by this commit.
`on-the-record/hooks/delegated-judgment-gate.sh`'s only change in the same commit is the single
added line `candidate_pr: {pr_ref}` in the reject-path's frontmatter write (confirmed in the PR
#603 diff read earlier this session) — a field addition to an existing write, not a change to the
reject/verdict/routing logic that fires the PR-opened, verdict-synthesized, and remediation-routed
events. Round-1's verdicts for those events plus the escalation event therefore carry forward
unchanged (see "## Per-event table" below).

## Event 4 re-drive

Driver: a disposable script under this session's scratchpad (never committed, matches the
approved proposal's declared write set — the fixture and any driver script live entirely outside
this repository, torn down after the run). It builds a fresh temp-dir git repo (never this repo's
board), containing:

- `roles/coding.json` (`write_scope: ["src/*.py"]`)
- a fixture-only remediation record at `<fixture>/docs/issue-9999/decisions/remediation-1.md`,
  rooted under the temp dir, never a path in this repository: `routed_to: coding`,
  `target_path: src/foo.py`, `round: 1`, `status: open`, `candidate_pr: 601` (the new field PR
  #603 added to the reject-path write)
- a merged remediation branch: `issue-9999/coding` created, a commit added, then `git merge --no-ff
  issue-9999/coding` into the fixture's default branch — simulating the remediation PR having
  landed

and a `gh` stub on `PATH` that logs every invocation to a file and answers `pr list --head
issue-9999/coding ...` with a MERGED PR #605, matching the shape `_merged_pr_for_branch` expects.

### Step A — does the shipped CLI surface expose a caller?

`python3 spawn.py --help` (this repo's own `spawn.py`, unmodified, commit 08e78cb) full flag list
reproduced:

```
positional arguments:
  role                  역할. 생략하면 상태만 보여준다
  task                  맡길 일. 룰북 커맨드면 '/plugin:command 인자'

options:
  -h, --help
  -C CWD, --cwd CWD
  --dry-run
  --no-contract
  --trust-repo-config
  --issue ISSUE
  --unattended
  --limit LIMIT
  --login LOGIN
  --stall-timeout STALL_TIMEOUT
  --role WATCH_ROLE
  --follow
  --all
  --until-idle
  --auto-respawn
  --unreported
  --post
  --json
```

No `--remediation-merged` flag exists (derived: the fenced flag list above, reproduced verbatim
from `--help`'s stdout this session, contains no such entry).

```
$ grep -n "_remediation_merge_sweep(" spawn.py
2109:def _remediation_merge_sweep(root: Path, issue: int) -> int:
```

One match — the `def` line itself. No call site exists anywhere else in the file this session read
(derived: the fenced grep output above is the complete match set for that pattern against commit
08e78cb's `spawn.py`).

```
$ grep -n "remediation" on-the-record/commands/run.md
77:3. **먼저 remediation 대기열을 확인한다(issue #587).** 자유 판단으로 넘어가기
78:   전에 `python3 $ON_THE_RECORD/gates/remediation_spawn.py --issue <n> -C <레포>`
82:   아무것도 안 찍히면(대기 중인 remediation 없음) 아래 4번 스텝으로 넘어간다.
```

Only the existing step-3 `gates/remediation_spawn.py` call (event 3's generator, from the earlier
round) — no orchestration step in `run.md` references `_remediation_merge_sweep`,
`reconcile --remediation-merged`, or any other caller (derived: the fenced grep output above is the
complete match set for "remediation" against `run.md` this session).

### Step B — drive the exposed CLI verbs against the merged fixture

```
$ python3 spawn.py reconcile --issue 9999 -C <fixture>
exit 0
stdout: reconcile: 대상 로스터 엔트리 없음

$ python3 spawn.py reconcile --unreported --issue 9999 -C <fixture>
exit 0
stdout: reconcile --unreported: 대상 workspace 엔트리 없음
```

gh.log after both calls: empty — `gh` was never invoked by either shipped CLI verb (derived: the
log file this session's driver wrote to did not exist after these two runs). The fixture-only
remediation record's `status: open` state is never read by either verb (`roster_reconcile` reads
the roster/workspace index, not `docs/issue-<n>/decisions/`); the merged branch is never
inspected.

### Step C — confirm the posting logic itself, called directly (not via any shipped entry point)

To separate "the posting logic is broken" from "the posting logic is unwired", the private
function was invoked directly (not a shipped code path — recorded here only to characterize the
gap precisely, not as evidence the acceptance criterion is met):

```
>>> spawn._remediation_merge_sweep(fixture, 9999)
1
gh.log:
repo view --json nameWithOwner -q .nameWithOwner
repo view --json nameWithOwner -q .nameWithOwner
api repos/acme/repo/issues/9999/comments --paginate --slurp
pr list --head issue-9999/coding --state all --json number,state
api repos/acme/repo/issues/9999/comments -f body=[watch] remediation-merged: <fixture>/docs/issue-9999/decisions/remediation-1.md

Remediation merged: PR #605 resolves round 1 of PR #601
https://github.com/acme/repo/pull/605
```

The comment body matches #573 §12's format verbatim (`Remediation merged: PR #<m> resolves round
<r> of PR #<n>` + link) — the posting logic itself is correct. But Step A/B confirm this call is
unreachable from any CLI verb, orchestration step, or automatic sweep that the shipped surface
actually exposes: nothing in `on-the-record/commands/run.md`, `spawn.py`'s `main()`, or any hook
ever calls `_remediation_merge_sweep`. On the real git surface — an actual remediation PR merging
during real operation, with no human manually invoking the private Python function — event 4 still
does not fire, for a different root cause than round 1 (unwired call site vs. missing logic).

## Per-event table (this round)

| # | Event | Fired | Evidence |
|---|---|---|---|
| 1 | PR opened under judgment | yes — carried forward, code path unchanged per "## Scope of this round" | round-1 record, Scenario A step 2 |
| 2 | Verdict synthesized | yes — carried forward, unchanged | round-1 record, Scenario A step 2 + 5a |
| 3 | Remediation routed | yes — carried forward, unchanged | round-1 record, Scenario A step 2 |
| 4 | Remediation PR merged | no — logic correct (Step C) but zero shipped callers (Step A/B) | this round, Steps A-C above |
| 5 | Escalation to operator | yes — carried forward, unchanged | round-1 record, Scenario B |

Tally derived by counting the "Fired" column immediately above: four rows read "yes", one row
("Remediation PR merged") reads "no". The remediation round (PR #603) fixed round 1's root cause
(missing posting logic) but introduced a new gap in its place (the posting logic has no caller) —
the net observable behavior on the git surface is unchanged: event 4 does not fire during real
operation.

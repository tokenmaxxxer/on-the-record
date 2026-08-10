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

## Round 3 (PR #606, commit 53f9d16) — event 4 re-drive

### Scope of this round

PR #606's own diff (`git show 53f9d16 --stat`, read this session): only `spawn.py`,
`test_spawn.py`, and `docs/issue-587/reports/implementation.md` changed —
`on-the-record/hooks/delegated-judgment-gate.sh` and `gates/remediation_spawn.py` untouched.
Events 1-3 and 5's code paths are therefore unaffected by this round and carry forward unchanged
from the round-1/round-2 records, same reasoning as the prior round's "## Scope of this round".
This round re-drives event 4 only, against the new `reconcile --remediation-merged` CLI verb.

### Step A — does the shipped CLI surface now expose a caller?

```
$ python3 spawn.py --help 2>&1 | grep -n "remediation-merged"
6:                [--remediation-merged] [--post] [--json]
37:  --remediation-merged  reconcile --issue N: docs/issue-N/decisions/remediation-*.md 중 ...
```

```
$ grep -n "_remediation_merge_sweep(" spawn.py
2109:def _remediation_merge_sweep(root: Path, issue: int) -> int:
2168:    `remediation_merged=True` 면 `_remediation_merge_sweep(ROOT, issue)` 로
2183:        return _remediation_merge_sweep(ROOT, issue)
```

Two matches beyond the `def` line: the CLI flag now exists and `roster_reconcile` now has a real
call site (`spawn.py:2183`), reached from `main()`'s `role == "reconcile"` branch
(`spawn.py:3509-3511`, read this session: `return roster_reconcile(a.issue,
unreported=a.unreported, remediation_merged=a.remediation_merged)`). The round-2 gap (zero
callers) is closed.

### Step B — drive the shipped CLI verb against a merged fixture branch, via `-C`

New disposable fixture built the same way as round 2 (temp-dir git repo, never this repo's
board): `roles/coding.json`, a fixture-only `<fixture>/docs/issue-9999/decisions/remediation-1.md`
(`routed_to: coding`, `round: 1`, `status: open`, `candidate_pr: 601`), branch `issue-9999/coding`
merged (`git merge --no-ff`) into the fixture's default branch, and a `gh` stub on `PATH` logging
every call and answering `pr list --head issue-9999/coding ...` with a MERGED PR #605.

```
$ python3 spawn.py reconcile --remediation-merged --issue 9999 -C <fixture>
EXIT_CODE=0
--- gh.log ---
(no gh.log — gh never invoked)
```

`gh` was never called and no comment posted, despite the fixture's merged branch and open
remediation record being set up identically to round 2's Step C (which did post correctly when
called directly — see round 2's "Step C" and this round's Step D below).

### Step C — isolate: is `-C` actually threaded to the sweep's `root` argument?

```
$ grep -n "^ROOT = \|    ROOT = \|ROOT=" spawn.py
37:ROOT = Path(__file__).resolve().parent
```

The only assignment to `ROOT` in the whole file is the module-level constant at load time — no
place in `main()` reassigns `ROOT` from `a.cwd`/`-C` (`a.cwd` is threaded to every other
cwd-sensitive call site via an explicit parameter — `roster_reconcile`'s `unreported` branch
reads a location-independent workspace index, and every other role dispatch in `main()` passes
`a.cwd` explicitly, e.g. `spawn.py:3521,3644,3648,3650,3694`, read this session).
`roster_reconcile`'s `remediation_merged` branch (`spawn.py:2183`) calls
`_remediation_merge_sweep(ROOT, issue)` — the global module constant, not `a.cwd` — so `-C`'s
target directory is silently never consulted by this code path. This explains Step B directly:
this session's own on-the-record checkout (`ROOT`) has no fixture-shaped decisions directory of
its own —

```
$ test -d <this-repo>/docs/issue-9999 && echo EXISTS || echo NOT_EXIST
NOT_EXIST
```

— so `_remediation_merge_sweep`'s own guard (`decisions_dir.is_dir()` check, `spawn.py:2120-2121`)
returns `0` before ever calling `gh`, matching Step B's empty `gh.log` and `EXIT_CODE=0` exactly.
No exception, no stderr, no indication to a caller that `-C` was ignored — a silent no-op against
the wrong directory, not a visible failure.

### Step D — confirm the posting logic itself is still correct, called with the right `root` directly

To isolate wiring from logic, `_remediation_merge_sweep` was called directly against the fixture
path (not via the CLI's `-C`-ignoring `main()` → `roster_reconcile` path):

```
>>> spawn._remediation_merge_sweep(fixture, 9999)
posted: 1
gh.log:
repo view --json nameWithOwner -q .nameWithOwner
repo view --json nameWithOwner -q .nameWithOwner
api repos/acme/repo/issues/9999/comments --paginate --slurp
pr list --head issue-9999/coding --state all --json number,state
api repos/acme/repo/issues/9999/comments -f body=[watch] remediation-merged: <fixture>/docs/issue-9999/decisions/remediation-1.md

Remediation merged: PR #605 resolves round 1 of PR #601
https://github.com/acme/repo/pull/605
```

Comment body matches #573 §12's format verbatim, same as round 2's Step C — the posting logic
itself is unchanged and still correct. The defect is isolated entirely to Step C's finding: the
CLI verb dispatches to the right function but never threads the caller's `-C` target into it.

### Per-event table (round 3)

| # | Event | Fired | Evidence |
|---|---|---|---|
| 1 | PR opened under judgment | yes — carried forward, code path unchanged per "## Scope of this round" | round-1 record, Scenario A step 2 |
| 2 | Verdict synthesized | yes — carried forward, unchanged | round-1 record, Scenario A step 2 + 5a |
| 3 | Remediation routed | yes — carried forward, unchanged | round-1 record, Scenario A step 2 |
| 4 | Remediation PR merged | no — CLI verb exists and dispatches (Step A) but ignores `-C`, silently no-ops against the wrong directory (Step B-C); posting logic itself still correct in isolation (Step D) | this round, Steps A-D above |
| 5 | Escalation to operator | yes — carried forward, unchanged | round-1 record, Scenario B |

Tally: four "yes", one "no". Round 3 (PR #606) closed round 2's gap (no caller) but the new
caller has a distinct, third root cause for the same observable failure: the CLI verb never
threads its own `-C`/`--cwd` argument to the function it calls, so on a real target/fixture repo
different from wherever `spawn.py` physically resides, event 4 still never fires — silently,
with exit 0 and no error.

## Round 4

### Scope of this round

PR #621 (merged, commit f9bc73143a2d828c80a05f4add04d51694846f4e, `gh pr view 621` and
`grep -n "_remediation_merge_sweep\|root=Path(a.cwd)" spawn.py` read this session) threads
`root: Path | None = None` through `roster_reconcile` and passes `root=Path(a.cwd).resolve()`
from `main()`'s `reconcile` dispatch (spawn.py:3518), targeting exactly round 3's root cause
(the CLI never threading `-C`/`--cwd` into `_remediation_merge_sweep`'s `root` parameter). Per
round 3's own resolution path, re-verification is scoped to event 4 again — the other four
events' code paths are untouched by this PR's diff (`gh pr view 621 --json files` this session:
only `spawn.py`, `test_spawn.py`, `docs/issue-587/reports/implementation.md`, and a hunt report
changed).

### Step A — drive the shipped CLI verb via `-C` from a fixture OUTSIDE the checkout

A fresh disposable fixture git repo was built under the session scratchpad (never this
repository's board), distinct from `spawn.py`'s own checkout directory, the same way rounds 2-3
built theirs: a fixture-only remediation record at
`<fixture>/docs/issue-9999/decisions/remediation-1.md` with `status: open`,
`routed_to: coding`, a branch `issue-9999/coding` merged (`git merge --no-ff`) into the fixture's
default branch simulating the remediation PR having landed, a `gh` stub on `PATH` logging every
invocation to `gh.log` and reporting PR #200 as `MERGED` for that branch, and a fake `origin`
remote so `_repo_slug` resolves.

The driver script itself (not committed, matches the approved proposal's declared write set: the
fixture and driver live entirely outside the repository) invoked the shipped, unmodified CLI:

```
$ python3 spawn.py reconcile --remediation-merged --issue 9999 -C <fixture>
```

run with cwd `/` (deliberately outside both `spawn.py`'s checkout and the fixture, to prove `-C`
alone — not an inherited cwd — drives the target), against the fixture built above.

```
rc = 1
stdout: (empty)
stderr: (empty)

gh.log:
repo view --json nameWithOwner -q .nameWithOwner
repo view --json nameWithOwner -q .nameWithOwner
api repos/acme/repo/issues/9999/comments --paginate --slurp
pr list --head issue-9999/coding --state all --json number,state
api repos/acme/repo/issues/9999/comments -f body=[watch] remediation-merged: <fixture>/docs/issue-9999/decisions/remediation-1.md

Remediation merged: PR #200 resolves round 1 of PR #100
https://github.com/acme/repo/pull/200
```

`rc=1` matches `roster_reconcile`'s documented convention (spawn.py:2178-2181, "종료 코드는
... `roster_watchdog` 의 반환값과 같은 관례"): `_remediation_merge_sweep` returns the count of
comments posted, and one comment posted here. The `gh api ... comments -f body=...` call fired
against the fixture's own decision path (`<fixture>/docs/issue-9999/decisions/remediation-1.md`),
through a process invoked with cwd `/`, driven entirely by the `-C <fixture>` argument. This is
the shipped code posting to the correct target from outside the checkout — round 3's failure mode
(silent no-op, exit 0, no comment) does not reproduce.

### Per-event table (round 4)

| # | Event | Fired | Evidence |
|---|---|---|---|
| 1 | PR opened under judgment | yes — carried forward, code path unchanged per "## Scope of this round" | round-1 record, Scenario A step 2 |
| 2 | Verdict synthesized | yes — carried forward, unchanged | round-1 record, Scenario A step 2 + 5a |
| 3 | Remediation routed | yes — carried forward, unchanged | round-1 record, Scenario A step 2 |
| 4 | Remediation PR merged | yes — CLI verb dispatches (unchanged from round 3) and now threads `-C` into `_remediation_merge_sweep`'s `root`, confirmed posting from cwd `/` against a fixture outside the checkout (this round, Step A) | this round, Step A above |
| 5 | Escalation to operator | yes — carried forward, unchanged | round-1 record, Scenario B |

Tally: five "yes", zero "no". All five issue-timeline events now fire on the shipped code through
its exposed CLI surface, exercised against a fixture target repo distinct from `spawn.py`'s own
checkout.

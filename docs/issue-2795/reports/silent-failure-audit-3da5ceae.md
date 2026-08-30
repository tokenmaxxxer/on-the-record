---
issue: 2795
role: silent-failure-audit-3da5ceae
author: silent-failure-audit-3da5ceae
skills: silent-failure-audit (skill-repository(c05de12))
verifies_subject: false  # flip to true only if this record is an independent verification of this subject's own deliverable -- see docs/handbooks/observer-verification.md
code_under_review:
  - board.py
  - watchdog.py
  - spawn.py
  - test/test_unrecovered_commit_count.py
type: fix
breaking: false
verdict: landed
loop_state: landed
upstream:
  - path: gh issue view 2795 (title, Ask, Acceptance)
    sha: same-commit
---

# issue-2795 — silent-failure-audit-3da5ceae record

## What was done

Replaced the unpushed-commit check behind `DEAD-UNRECOVERED-COMMITS` with
a remote-aware one, and added a third, explicitly-reported state for when
the remote can't be consulted.

canonical: `board.py` (this commit, working tree), the new functions:
```python
UNPUSHED_STATUS_UNKNOWN = "unknown"


def _remote_branch_head(cwd: str, remote: str, branch: str) -> str | None:
    c = subprocess.run(
        ["git", "-C", cwd, "ls-remote", "--heads", remote, branch],
        capture_output=True, text=True,
    )
    if c.returncode != 0:
        return None
    line = c.stdout.strip()
    return line.split()[0] if line else ""


def _unrecovered_commit_count(cwd: str, before_head: str | None, after_head: str | None,
                               branch: str, remote: str = "origin") -> int | str:
    if not _is_new_commit(cwd, before_head, after_head):
        return 0
    remote_sha = _remote_branch_head(cwd, remote, branch)
    if remote_sha is None:
        return UNPUSHED_STATUS_UNKNOWN
    if remote_sha == after_head:
        return 0
    if remote_sha == "":
        rng = f"{before_head}..{after_head}" if before_head else after_head
    else:
        anc = subprocess.run(
            ["git", "-C", cwd, "merge-base", "--is-ancestor", remote_sha, after_head],
            capture_output=True, text=True,
        )
        if anc.returncode != 0:
            return UNPUSHED_STATUS_UNKNOWN
        rng = f"{remote_sha}..{after_head}"
    c = subprocess.run(["git", "-C", cwd, "rev-list", "--count", rng],
                        capture_output=True, text=True)
    if c.returncode != 0:
        return UNPUSHED_STATUS_UNKNOWN
    try:
        return int(c.stdout.strip())
    except ValueError:
        return UNPUSHED_STATUS_UNKNOWN
```

- `_unrecovered_commit_count()` replaces `_session_commit_count()`
  (renamed — old name described exactly the bug: it counted commits
  "since spawn", never asking whether they'd been pushed). It asks the
  real remote via `git ls-remote --heads` and returns one of three
  shapes: `0` (nothing unrecovered), a positive int (genuinely unpushed
  count), or `UNPUSHED_STATUS_UNKNOWN` (remote state undeterminable —
  never guessed as either of the other two).
- `watchdog.py::diagnose_health()` now branches on that sentinel before
  the existing `if commit_count:` branch, returning a new state
  `DEAD-REMOTE-STATE-UNKNOWN` (`next_action: "manual-review"`) instead of
  falling into `DEAD-ERRORED` (would silence a possibly-real strand) or
  `DEAD-UNRECOVERED-COMMITS` (would repeat this exact false-positive
  shape on every network hiccup).
- Both call sites (`board.py`'s roster/ps sweep, `watchdog.py`'s
  poll-report dead-entry check) now pass the workspace's **actual
  checked-out branch** — `_current_branch()` (`git symbolic-ref --short
  HEAD`), not `Path(work).name`. This mattered: `issue_workspace()`
  names the workspace directory `<repo>-issue-<n>-<skill>` (dashes,
  filesystem-safe) while the git branch is `issue-<n>/<skill>` (slash) —
  confirmed live in this very session's own workspace, see Why below.
  Passing the directory name to `ls-remote` would have queried a branch
  that never exists and reintroduced this issue's exact false positive
  through a different door.
- `spawn.py` re-exports (`_current_branch`, `_unrecovered_commit_count`,
  `UNPUSHED_STATUS_UNKNOWN`) so `watchdog.py`'s `_sp`-indirection pattern
  keeps working, and one existing alias (`_session_commit_count`) was
  removed since nothing calls it anymore.
- Added `test/test_unrecovered_commit_count.py`: both required
  directions (false-positive silenced / genuine strand still reported),
  the no-upstream-branch case, the query-fails-so-report-unknown case,
  and the same four through `diagnose_health()`'s full state output —
  all built against a real bare-repo clone + real `git` subprocess calls,
  no mocking of git itself. derived: `python3 -m pytest
  test/test_unrecovered_commit_count.py -v` — result: `7 passed in
  0.93s`.

## Why

canonical: `gh issue view 2795` body, "Ask" section:
```
The likely mechanism is worth stating so it can be checked rather than
guessed: the unpushed-commit check appears to compare against a tracking
ref that the workspace never set (`git log @{u}..HEAD` returns nothing
at all here, because there is no upstream configured), so "no upstream"
is being read as "nothing pushed".
```
skill-verdict: diagnose-first — applied: invoked; the issue's own
mechanism guess (`@{u}` tracking ref) turned out **not** to match the
code. derived: `grep -n "@{u}" spawn.py board.py watchdog.py` — result:
zero matches (checked before writing any fix). The real comparison,
traced by reading `board.py::_session_commit_count()` (pre-fix) and its
two callers (`board.py:1451`, `watchdog.py:1665`, pre-fix line numbers),
was `before_head..after_head` against **only the local git history** —
no remote reference of any kind, cached or live. Root cause confirmed by
intervention (diagnose-first Gate G2's counterfactual test): the old
function reproduced the exact reported false positive live —

acceptance: reproduce the issue's own reported bug against the pre-fix
function — checked:
```
python3 - <<'PY'
import subprocess, importlib.util, sys
old_src = subprocess.run(["git","show","origin/main:board.py"],
                          capture_output=True, text=True, check=True).stdout
spec = importlib.util.spec_from_loader("board_old", loader=None)
board_old = importlib.util.module_from_spec(spec)
sys.modules["board_old"] = board_old
exec(compile(old_src, "board_old.py", "exec"), board_old.__dict__)
# ... clone+push two commits, then call board_old._session_commit_count(work, before, after)
PY
```
— result: `OLD _session_commit_count() git subprocess calls: 2` (a
`merge-base --is-ancestor` and a `rev-list --count`, both purely local),
`result: 1 (BUG: reports 1 even though already pushed)`. Both commits had
already been pushed to the bare remote before this call — the function
never checked, so it reported them as unrecovered anyway. This matches
the issue's own live report (`git ls-remote` head == local `HEAD`, yet
`DEAD-UNRECOVERED-COMMITS` fired).

skill-verdict: silent-failure-audit — applied: invoked; classified the
pre-fix failure mode against the skill's catalog. The guarded operation
is the `rev-list`/`merge-base` `subprocess.run()` calls in
`_session_commit_count()`; the pre-fix catch sites (`board.py`, old
version) were:
```python
    if not _is_new_commit(cwd, before_head, after_head):
        return 0
    rng = f"{before_head}..{after_head}" if before_head else after_head
    c = subprocess.run(["git", "-C", cwd, "rev-list", "--count", rng], ...)
    if c.returncode != 0:
        return 0
```
Classification: **Silently Absorbed** — pattern "default-value
substitution without recording" (catalog category d): a `rev-list`
failure and "zero unpushed commits" both collapse to the same return
value `0`, with nothing to tell `diagnose_health()`'s caller which one
happened. Forward trace: `0` → `diagnose_health()`'s `if commit_count:`
is falsy → falls to plain `DEAD-ERRORED`, same bucket as "no commits at
all" → an operator reading `[poll-report] ... DEAD-ERRORED` cannot
distinguish "confirmed nothing lost" from "couldn't check." This trace
directly shaped the fix: `_unrecovered_commit_count()` and
`_remote_branch_head()` never collapse an unresolved query into `0` —
every git-command failure returns `UNPUSHED_STATUS_UNKNOWN` instead, and
`diagnose_health()` reports that as its own named state
(`DEAD-REMOTE-STATE-UNKNOWN`) rather than folding it into either
neighbor. This is the same shape #2792 fixed for `issue_state_index_all()`
(a success flag paired with absent data, per `gh issue view 2792` body)
— solved here by adding the missing third value rather than overloading
one of the existing two.

**Design decision — query the remote directly, not the tracking ref.**
I considered making the workspace set an upstream (`git branch
--set-upstream-to`) during bootstrap and reading `@{u}..HEAD` instead of
adding `ls-remote`. Rejected: `gh issue view 2795`'s must-not says
exactly this ("Do not paper over it by setting an upstream during
bootstrap unless that is independently correct; the detector should be
right about a workspace regardless of how its refs are configured") — a
cached tracking ref is also just a local ref that can go stale between
fetches, which is the same class of bug (comparing against a stand-in
instead of the real remote) one level removed. `git ls-remote --heads`
hits the actual remote every time, at the cost of one network
round-trip per already-TTL-gated dead-entry check (see Standing
invariant 3 below).

## Upstream basis

`gh issue view 2795` (verbatim, title/Ask/Acceptance/must-not sections
quoted above and in Acceptance below) — same-commit, read directly
before any edit.

## Acceptance — executed live

All three named checks plus the four standing invariants, run against
this branch's `HEAD` (derived: `git rev-parse HEAD` — result:
`31ceac1e8b3d7312204283aa4c422c3c13bebc99`) after the code+test commit.

### Bullet 1 — crash a session after a successful push, show the poll-report line

acceptance: synthetic dead roster entry, real git clone/push, driven
through the real `spawn.diagnose_health()` (re-exported from
`watchdog.py`) — checked:
```
[poll-report] issue-9001/demo: DEAD-ERRORED — issue-9001/demo: pid 999999999 부재, PR 없음, 커밋 없음, session_verdict='crashed'
```
— result: no `DEAD-UNRECOVERED-COMMITS`. Two commits were made and both
pushed before the synthetic crash; `_unrecovered_commit_count()` returned
`0`; `diagnose_health()` fell through to plain `DEAD-ERRORED` ("커밋
없음" = no unrecovered commits), matching the issue's required empty
state.

### Bullet 2 — crash a session after committing and before pushing, show the line

acceptance: same workspace, one further commit made but never pushed —
checked:
```
[poll-report] issue-9001/demo: DEAD-UNRECOVERED-COMMITS — issue-9001/demo: pid 999999999 부재, PR 없음, branch=on-the-record-issue-9001-demo 에 push 안 된 커밋 1개 — 복구 필요 (session_verdict='crashed')
```
— result: still alarms, count is exact (1 commit, matching the 1 commit
actually made-and-unpushed in this step). canonical: this is the
direction `gh issue view 2795`'s must-not calls out as the one that
matters ("losing the true positive to silence the false one trades a
noisy alarm for a blind spot") — confirms the fix did not silence it.

### Bullet 3 — the command the detector runs, and its output with no upstream configured

acceptance: fresh branch, one commit, never pushed, no `--set-upstream`
ever run — checked:
```
command: git -C /tmp/tmpi7hl4rex/on-the-record-issue-9001-demo ls-remote --heads origin issue-9002/no-upstream
returncode: 0 | stdout: '' | stderr: ''
resulting count (correctly treated as genuinely unrecovered, not silenced): 1
```
— result: the detector runs `git ls-remote --heads origin <branch>`
— not `git log @{u}..HEAD`, canonical: `gh issue view 2795` body quoted
above, which the issue's author confirmed by direct test would silently
report nothing for exactly this workspace shape. An empty-but-successful
`ls-remote` (branch legitimately doesn't exist on the remote yet) is
read as "fully unrecovered," matching the issue's named scenario ("a
branch that does not exist yet") — correctly alarmed, not silenced.

### Extra — remote query itself fails (must not fail open)

acceptance: same setup as bullet 2, then `git remote set-url origin
/nonexistent/path/that/does/not/exist.git` before the check — checked:
```
[poll-report] issue-9001/demo: DEAD-REMOTE-STATE-UNKNOWN — issue-9001/demo: pid 999999999 부재, PR 없음, branch=on-the-record-issue-9001-demo 의 원격 push 상태를 확인 못함(ls-remote 실패 또는 조상 관계 판단 불가) — 수동 확인 필요 (session_verdict='crashed')
```
— result: neither `DEAD-ERRORED` (fail-open, would hide a possible real
strand) nor `DEAD-UNRECOVERED-COMMITS` (fail-closed, would repeat this
issue's own false-positive shape on every transient network failure) —
a third, distinctly-named, still-printed state, satisfying `gh issue
view 2795`'s must-not ("Do not make the check fail open when it cannot
determine the remote state").

### Standing invariant 1 — no return of the retired role axis

acceptance: `git diff origin/main..HEAD -- board.py spawn.py watchdog.py
| grep -inE '^\+.*\brole\b'` — checked, result: no output (zero matches;
`grep` exit code 1). `test/test_unrecovered_commit_count.py` checked the
same way (`grep -inE '\brole\b' test/test_unrecovered_commit_count.py`),
zero matches.

### Standing invariant 2 — no new bug, failing-test set vs origin/main as SETS OF NAMES

acceptance: full suite run twice, once in a `git worktree add` of
`origin/main` (derived: `git rev-parse origin/main` — result:
`174909fbb5dea02629a771fc89378ff05b810a66`), once on this branch's
`HEAD`, both `python3 -m pytest test/ -q`, failing names extracted and
sorted — checked:
```
$ diff <(sorted failing names, origin/main worktree) <(sorted failing names, this branch)
IDENTICAL SETS (baseline vs this branch)
```
Both runs: `15 failed, 432 passed, 3 xfailed` (this branch) / `15 failed`
(baseline, same names) — derived: `python3 -m pytest test/ -q`. All 15
pre-existing failures are `fetch 실패 — fatal: 'origin' does not appear
to be a git repository` in unrelated spawn-pipeline tests (sandboxed
CI has no real `origin` remote) — present identically before this
change; none are in `board.py`, `watchdog.py`, or the new test file's
own namespace. The new test file's own suite — derived: `python3 -m
pytest test/test_unrecovered_commit_count.py -v` — result: `7 passed in
0.93s`.

### Standing invariant 3 — no overhead increase

acceptance: `subprocess.run` call-count comparison, old function
(loaded from `origin/main:board.py` via `exec`) vs new, same two
scenarios — derived: instrumented `subprocess.run` wrapper counting
`git`-prefixed calls, driven through both functions with an identical
real clone+push fixture (see Why's reproduction command for the harness
shape) — result:
```
already-pushed case (the common case this issue is about):
  OLD calls=2 (merge-base + rev-list), result=1 [the bug]
  NEW calls=2 (merge-base + ls-remote), result=0 [fixed, same call count]

genuinely-unpushed case (the true positive that must keep firing):
  OLD calls=2, result=1
  NEW calls=4 (merge-base + ls-remote + merge-base + rev-list), result=1
```
Honest result: the dominant case this issue reports — a dead entry whose
commits are already on the remote — costs the **same** two git
subprocess calls as before (one now goes to the network via
`ls-remote` instead of staying local, but the count is unchanged), and
now returns the correct answer instead of the wrong one. Only the rarer
true-positive path (genuinely stranded commits) costs two additional
local git calls. Both figures are inside the same pre-existing gate —
canonical: `watchdog.py` (unchanged by this fix), `if
_sp.ledger_check_and_stamp(f"poll-report-dead-check:{key}"):` — a
per-dead-entry, TTL-gated, one-shot check, not a new per-tick or
per-poll-interval cost. No new call site runs outside that existing
gate.

### Standing invariant 4 — monitor/watch machinery unbroken and NOT QUIETER

Every state this fix can produce is still printed through the exact
`[poll-report]` line the issue quotes — canonical: `watchdog.py`'s
`reported_terminal`-tracked print block, `dead_label = "COMPLETED" if
dead_health["state"] is None else dead_health["state"]` followed by
`print(f"[poll-report] {key}: {dead_label} — ...")`, unconditional on
which state value it is — none of the three outcomes (`DEAD-ERRORED`,
`DEAD-UNRECOVERED-COMMITS`, `DEAD-REMOTE-STATE-UNKNOWN`) is suppressed
relative to before. The genuine-strand alarm (bullet 2 above) still
fires with an unchanged message shape. The new `DEAD-REMOTE-STATE-UNKNOWN`
state is strictly additive reporting — a case that used to be silently
misclassified as one of the other two now surfaces under its own name —
so true reporting increased, not decreased. `next_action` vocabulary is
open, not a closed enum, for `diagnose_health()` specifically — derived:
`grep -n "next_action" spawn.py watchdog.py` — result: the only
"닫혀 있다" (closed-set) docstring language is at `spawn.py:853` and
describes `reconcile()`'s own separate `divergences` list, not
`diagnose_health()`'s return; the new value `"manual-review"` reuses an
existing vocabulary word — same grep shows it already used at
`spawn.py:827`, `spawn.py:910`, `spawn.py:918` for the same "a human
needs to look" meaning.

## Open findings

- `diagnose_health()`'s own internal `branch = Path(work).name if work
  else None` (`watchdog.py`, unchanged by this fix) feeds the *displayed*
  `branch=` text in every dead-entry detail line, and also feeds
  `_pr_open_or_merged_for_branch(root, branch)`/`_pr_state_from_index()`
  for PR-completion lookups on the non-bulk-index fallback path. Per the
  same directory-vs-branch mismatch demonstrated live in Why above, this
  value is not the real git branch — canonical: `gates/closure_sweep.py`
  line 176 docstring, `_pr_index_all()`: "브랜치 이름 -> `{number, state,
  body}` 사전" (branch NAME -> ..., keyed by GitHub's own `head.ref`),
  while `Path(work).name` produces the dash-form directory name per
  `spawn.py::_workspace_target_path()`'s `work = work_base /
  f"{repo_name}-issue-{issue}-{skill}"` formula. Whether the PR-lookup
  path is actually affected in production (vs. always served by the
  bulk `pr_index` branch, which this finding did not check) is
  unverified and is a plausible separate issue, not undertaken here —
  out of #2795's scope (a different check, computing PR completion
  rather than the unpushed-commit count this issue's Acceptance names).

## Next steps

None — acceptance and all four standing invariants executed live above;
`loop_state: landed`.

## What did not work

None.

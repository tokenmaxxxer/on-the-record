---
issue: 2443
role: execution-observation
author: execution-observation
loop_state: done
upstream:
  - path: docs/issue-2443/reports/implementation.md
    sha: 81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd
  - path: lifecycle.py
    sha: 81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd
  - path: spawn.py
    sha: 81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd
subject: PR #2450 (issue-2443/implementation, head 81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd, base main)
test: issue #2443 Acceptance section — 3 check bullets + 1 design-statement bullet
result: passed
assertedBy: execution-observation, independently re-run this turn
---

# issue-2443 — execution-observation record

Path convention: every file cited below with a `pr2450-verify:` or
`pr2450-runtime:` prefix was read/executed from a scratch copy at
`/tmp/pr2450-verify` (files only, via `git show FETCH_HEAD:<path>`) or
`/tmp/pr2450-runtime` (a full copy of this checkout with the two changed
files swapped in, so sibling modules like `deviation_log`/`roster`
resolve on import) — both removed after use. Bare paths refer to this
branch (`issue-2443/execution-observation`, based on `origin/main`) or to
the real `~/.tokenmaxxxer/work`.

## What was done

Independently re-derived all three of issue #2443's acceptance checks
plus its design-statement bullet against PR #2450, rather than citing the
implementation record's own claims.

**Setup:** `git fetch origin pull/2450/head` (FETCH_HEAD =
`81c1e4f4d3c2c97ae876f0ef8a1b2180875914dd`, head of
`issue-2443/implementation`). `git merge-tree $(git merge-base FETCH_HEAD
origin/main) origin/main FETCH_HEAD` — no `<<<<<<<` conflict markers;
canonical: `/tmp/mergetree.out` (475 lines, removed after use) — the
PR's base is behind current `origin/main` (missing #2417's
`_spawn_capacity_check`/`_workspace_clone_incomplete` and #2431/#2446's
`recut-corrupted` additions to `spawn.py`), but those are additive,
non-overlapping regions — clean auto-merge, not a landing blocker. Copied
`lifecycle.py`/`spawn.py` at that sha into a full runtime copy of this
checkout (`/tmp/pr2450-runtime`) so the module imports resolve; syntax
verified (`python3 -c "import ast; ast.parse(...)"` on both files —
result: `syntax OK`).

**Acceptance bullet 1 — synthetic fixture, old+orphaned set pruned.**
Authored my own fixture (`verify1_fixture.py`, distinct from the PR's own
script) covering 5 groups in one pass: fully-orphaned+old (2 groups, one
plain-suffix, one `.session.<ts>.<pid>.log` pattern) must be removed;
orphaned+fresh must survive; paired-workspace-dir-present+old must
survive; and one group with siblings at mixed ages (one 20-day-old file,
one 1-day-old file, no live/dir protection) to independently confirm the
record's claim that group age = max(mtime) rather than any single file's
mtime.

acceptance: `python3 verify1_fixture.py` (in `/tmp/pr2450-runtime`) —
result:
```
before: ['g1-repo-issue-1-coding.events.jsonl', 'g1-repo-issue-1-coding.task.txt', 'g1-repo-issue-1-coding.watcher.log', 'g2-repo-issue-2-coding.events.jsonl', 'g3-repo-issue-3-coding', 'g3-repo-issue-3-coding.watcher.log', 'g4-repo-issue-4-coding.events.jsonl', 'g4-repo-issue-4-coding.task.txt', 'g5-repo-issue-5-coding.session.20260101T000000.999.log']
outcome: {'removed': 4, 'kept': 3, 'failed': 0}
after: ['g2-repo-issue-2-coding.events.jsonl', 'g3-repo-issue-3-coding', 'g3-repo-issue-3-coding.watcher.log', 'g4-repo-issue-4-coding.events.jsonl', 'g4-repo-issue-4-coding.task.txt']
ALL INDEPENDENT ASSERTIONS PASSED (fixture 1: age/orphan/mixed-age-group)
```
g1 (2 files) and g5 (1 file) removed = 4 files removed across 2 groups,
matching `outcome['removed']`; g2/g3/g4 (3 groups) survive intact,
derived from the `before:`/`after:` lists in the code fence directly
above. The mixed-age group (g4) survived whole — both its old and fresh
sibling files remained in the `after:` list — confirming the
whole-set-max-mtime age rule the record claims, not a per-file check
that would have deleted only the old sibling.

**Acceptance bullet 2 — active-spawn protection, no false-positive
removal.** canonical: fixture 1's own code fence above — g3
(`g3-repo-issue-3-coding.watcher.log`, paired dir, 20 days old) is present
in the `after:` list, covering paired-workspace-directory protection.
Separately authored a live-pid-roster fixture (`verify2_liveroster.py`)
with **no paired directory at all** — the harder case, since protection
here depends entirely on the roster lookup, not directory existence: a
sidecar set 30 days old, workspace directory absent, but a fake `ROSTER`
(`active.json`) registering that exact workspace path against
`os.getpid()` (a real, alive pid).

acceptance: `python3 verify2_liveroster.py` — result:
```
outcome: {'removed': 0, 'kept': 1, 'failed': 0}
remaining: ['repo-issue-42-coding.events.jsonl', 'repo-issue-42-coding.watcher.log']
ALL INDEPENDENT ASSERTIONS PASSED (fixture 2: live-pid roster protection, no paired dir)
```
Both files survived a 30-day age past the 14-day default threshold,
solely on the live-roster signal — derived from `outcome`/`remaining`
above (`removed: 0`, both files still listed).

**Acceptance bullet 3 — live demonstration against the real backlog.**
Wrote my own read-only counting script (`verify3_livecount.py`,
independent of the PR's inline one-liner) grouping every file directly
under `_workspace_base()` by `_sidecar_workspace_name()`, skipping groups
whose paired dir exists or whose path resolves into
`_live_workspaces()`, summing files in groups older than
`_clean_max_age_days()`.

acceptance: `python3 verify3_livecount.py` (real
`~/.tokenmaxxxer/work`, this turn) — result:
```
workspace_base=/home/jwjung/.tokenmaxxxer/work max_age_days=14.0 live_entries=0
total sidecar groups scanned: 571
BEFORE eligible groups (orphaned+old): 0
BEFORE eligible files (orphaned+old): 0
```
The implementation record's own live run already pruned the backlog from
339 to 0 earlier this session (2026-08-25) — canonical:
`81c1e4f4:docs/issue-2443/reports/implementation.md`, acceptance check 3
section, `prune outcome: {'removed': 339, 'kept': 546, 'failed': 0}`. By
the time this independent check ran (2026-08-26), the count was still 0
per the code fence above — no re-accumulation of orphaned+old sidecars in
the interim, and 571 groups now on disk (up from the implementation
session's own 546 kept) are all either paired-with-a-directory or
younger than 14 days.

acceptance: ran the actual prune function against the real backlog
(`lifecycle._prune_orphaned_sidecars(_sp._workspace_base(),
_sp._clean_max_age_days())`, this turn) — result:
```
LIVE PRUNE RUN outcome: {'removed': 0, 'kept': 571, 'failed': 0}
```
`removed: 0` matches the `BEFORE eligible files: 0` count exactly (no
false positives beyond what the read-only count predicted), `failed: 0`
(no permission/OS errors against the real, current 571-group corpus),
and `kept: 571` accounts for every scanned group — derived from the code
fence directly above plus the `total sidecar groups scanned: 571` line
two fences up. `git status --porcelain` in this checkout immediately
after — result:
```
?? .orchestrate-hook-fires/07d8ddbcfdeccda8ed5b757a.log
?? .orchestrate-hook-fires/59f9a2f54732573c668e2080.log
?? docs/issue-2443/
```
— confirms the prune touched only files under `~/.tokenmaxxxer/work`,
not anything tracked in this git tree (only the pre-existing untracked
hook-fire logs and this record's own directory show up).

Net: this turn's independent live numbers are 0 -> 0 (already-near-zero,
staying near-zero), not a fresh 339 -> 0 — the acceptance bullet's
original-magnitude demonstration was already executed by the
implementation session (canonical: same implementation.md section cited
above) and is not reproducible a second time at that scale without a
second synthetic corpus, which bullets 1 and 2's own code fences above
already supply (5 and 2 synthetic cases respectively). Re-running the
real prune this turn is still meaningful: it shows the effect persisted,
no regression re-accumulated the backlog, and the 571 real, heterogeneous
current-day sidecar groups (derived: `total sidecar groups scanned: 571`
above) produced zero false-positive deletions and zero errors.

**Design-statement bullet — cadence reused as-is.** Confirmed via direct
line lookups against the PR's own file — canonical: `grep -n "^def
_clean_max_age_days\|^def _live_workspaces" /tmp/pr2450-verify/lifecycle.py`
— result: `569:def _live_workspaces() -> dict[Path, dict]:` /
`948:def _clean_max_age_days() -> float:`, matching the exact lines the
implementation record cites. canonical: `sed -n '2589,2621p'
/tmp/pr2450-runtime/spawn.py` (full closure body, read this turn) — the
sidecar-prune call sits inside the same `_run_auto_sweep()` closure as
the pre-existing `auto_sweep()` call, under the same
`try`/`except`-and-`return` exception-swallow contract, started from the
same `threading.Thread(target=_run_auto_sweep, daemon=True, ...)` call at
`spawn.py:2621` — no new trigger point, no new cron/timer, no new feature
flag beyond the pre-existing `_clean_auto_enabled()` gate `auto_sweep()`
already sits behind.

**Cross-check on the hunt-record's open finding** (cross-checkout roster
blind spot): canonical: `grep -n "_workspace_clean_state\|_live_workspaces\b\|ROSTER\s*=" /tmp/pr2450-verify/lifecycle.py /tmp/pr2450-verify/spawn.py`
— `auto_sweep()`'s own pre-existing call (`lifecycle.py:983`,
`_workspace_clean_state(w, live)`) consumes the identical
`_sp._live_workspaces()` dict this new sidecar-prune reuses; `ROSTER =
STATE_ROOT / "active.json"` (`spawn.py:898`) and `STATE_ROOT` defaults to
`ROOT / "runs"` (`ROOT = Path(__file__).resolve().parent`,
`spawn.py:44`, i.e. per-checkout) unless `MUSTER_STATE_ROOT` is set —
canonical: `printenv | grep -i MUSTER` this session, no
`MUSTER_STATE_ROOT` entry present. This substantiates the record's
"pre-existing, not introduced by this change" characterization rather
than accepting it unverified.

## Why

The implementation record already asserts all three acceptance checks
and the design-statement bullet are satisfied. Re-derived each from
scratch — a full runtime copy with the PR's exact file contents, my own
fixture wording distinct from the PR's own scripts, and a fresh read-only
count plus a fresh live prune run against the real, current backlog —
rather than treating the implementation record's transcripts as
sufficient. canonical: the "What was done" section above holds every
executed transcript this paragraph summarizes — this turn's own runs.

Considered and rejected: re-running only the PR's own inline scripts
verbatim (would confirm the PR's own script text runs, but not that the
function behaves correctly under independently-worded fixtures — in
particular the mixed-age-group case I added in fixture 1 was not present
in the PR's own bullet-1 script, and is the case most likely to catch a
"checks one file's mtime instead of the whole group's" regression).
Considered and rejected: treating the real-backlog re-run as
uninformative because it starts from an already-drained 0 — rejected,
because idempotency-and-no-regression against 571 real, heterogeneous,
present-day groups is itself acceptance-relevant evidence (`must not:
prune ... still active/alive`, `must not: delete files unrelated to
spawn sidecars`), even though it cannot reproduce the original 339 -> 0
magnitude a second time without fabricating a synthetic corpus — canonical:
bullets 1 and 2's own code fences above already supply that synthetic
coverage (5 and 2 cases respectively).

## Upstream basis

- `81c1e4f4:docs/issue-2443/reports/implementation.md` — the delivered
  work's own account; re-derived rather than cited, per this role's
  independent-execution mandate.
- `81c1e4f4:lifecycle.py`, `81c1e4f4:spawn.py` — the actual code changes,
  read and imported directly this turn via the `/tmp/pr2450-runtime`
  copy.
- Issue #2443's live body (`gh issue view 2443`, fetched this turn) — the
  real Acceptance text this record's checks are derived from.
- The real, current `~/.tokenmaxxxer/work` (571 sidecar groups scanned
  this turn, per `verify3_livecount.py`'s output above) — used for the
  live-backlog re-check and live prune re-run.

## Open findings

- Same finding the implementation record already discloses (cross-
  checkout `ROSTER`/`_live_workspaces()` scoping — a workspace registered
  alive only in a *different* checkout's roster is invisible to this
  check): independently confirmed above (see "Cross-check on the
  hunt-record's open finding", with its own `canonical:` grep citations)
  as pre-existing and shared identically by `auto_sweep()`'s own
  directory-prune path, not introduced by this change. No new resolution
  path opened here beyond the implementation record's own (file a
  follow-up issue against `_live_workspaces()`/`ROSTER` scoping) —
  concur with that scope judgment rather than duplicate it.
- None beyond the above.

## What did not work

None — every independently-authored fixture and live re-run matched the
implementation record's claims on the first attempt; no fixture needed
correction or a second attempt this turn.

## Next steps

None — loop_state set to `done`.

acceptance: summary of the three independently-executed checks plus the
design-statement bullet — result:
```
bullet 1 (synthetic fixture, 5 groups incl. mixed-age-within-group): {'removed': 4, 'kept': 3, 'failed': 0} — matches record's shape (this turn, independently-worded fixture)
bullet 2 (live-pid roster, no paired dir): {'removed': 0, 'kept': 1, 'failed': 0} — matches record's shape (this turn, independently-worded fixture)
bullet 3 (real backlog): before 0 eligible / after prune {'removed': 0, 'kept': 571, 'failed': 0} — persisted near-zero, 0 false positives, 0 errors, against 571 real current-day groups (this turn; original 339 -> 0 magnitude was the implementation session's own prior run, not repeatable a second time at that scale)
design-statement bullet (cadence reused as-is): confirmed — same _clean_max_age_days()/_live_workspaces(), same _run_auto_sweep() closure/thread/exception contract, no new trigger (this turn, direct line/sed reads)
```

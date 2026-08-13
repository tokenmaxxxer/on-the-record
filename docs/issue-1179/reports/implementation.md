---
code_under_review:
  - spawn.py
  - gates/test_clean_reconcile_safety.py
  - docs/handbooks/setup.md
  - docs/issue-1179/decisions/shared-checkout-dedup.md
type: feature
breaking: false
verdict: unreviewed
loop_state: landed
---

# Implementation record — issue-1179

## What was done

Wired `roster_clean()`'s existing safe-delete logic (spawn.py:4894, unchanged behavior) into an
automatic, default-on, spawn-time sweep, per northpole req#7 and issue-1179's four requirements:

1. **Automatic lifecycle cleanup**: extracted the per-workspace safety check
   (`_workspace_clean_state()`) and the archive-or-delete step (`_delete_workspace()`) out of
   `roster_clean()` into shared functions. Added `auto_sweep(wb, max_age_days, max_bytes, now)`, which
   calls the same safety check, and wired one call into `_spawn_one()`'s `issue is not None` branch
   (right before `issue_workspace()` creates the new clone), wrapped in `try/except` so a sweep failure
   never blocks a spawn.
2. **Bound policy**: two-stage bound — reap safe workspaces older than `MUSTER_CLEAN_MAX_AGE_DAYS`
   (default 14) unconditionally, then if the remaining safe workspaces still total more than
   `MUSTER_CLEAN_MAX_BYTES` (default 5GiB), reap the oldest remaining ones until under bound.
   `MUSTER_CLEAN_AUTO` (default on) disables the automatic path without touching the manual `clean` CLI
   verb.
3. **Safety preserved**: the automatic path and `roster_clean()` call the identical
   `_workspace_clean_state()`/`_delete_workspace()` functions — a live session (roster pid alive) or a
   dirty tree (uncommitted changes or commits not on any remote) is never touched by either path; sibling
   session logs whose ledger outcome is outside `LANDED_OUTCOMES` are archived to `.archived-logs/`, not
   deleted, by both paths.
4. **Shared-checkout dedup decision**: recorded in `docs/issue-1179/decisions/shared-checkout-dedup.md`
   — accept `git clone --reference <mirror>` for `issue_workspace()`'s target-repo clone as the direction,
   reject `git worktree` (breaks the per-workspace remote isolation `issue_workspace()` exists for), defer
   the actual build to a follow-up issue (requirement 4 is phase-1-scoped per the issue text).

## Why

northpole req#7: a plugin-only, default-on consumer install must not require the operator to know about
or run a cleanup command. The operator hit real disk exhaustion (measured 11GB/317 dirs on this
machine) because `spawn.py clean` was manual-only. Reusing `roster_clean()`'s existing safety logic via
extraction — rather than writing a second, parallel safe-delete implementation for the automatic path —
means one future safety fix or test covers both the manual and automatic call sites, instead of the two
drifting apart (see the proposal's Rationale for the two rejected alternatives: a separate `auto-clean`
CLI verb, and an age-only bound with no size cap).

## Upstream / basis

docs/issue-1179/proposals/automatic-lifecycle-cleanup.md (commit 57b391f)

## Accumulation

See the proposal's `## Accumulation` section — `auto_sweep()`/`_delete_workspace()` are single shared
functions called once per spawn.

## What did not work

Reopen continuation (2026-08-13): the first attempt at the stale-remote-tracking-ref regression test
used `git update-ref` on the bare origin repo to plant a commit object that only existed in the
workspace's own object store — `update-ref` refused with "trying to write ref ... with nonexistent
object" since the object was never transferred. Replaced with pushing the workspace's commit to the
origin under a different branch name (`topic:main`) so the object lands in the bare repo for real,
leaving the workspace's own `refs/remotes/origin/main` stale — the actual scenario being tested.

## Open findings

resolved_findings:
- docs/issue-1179/reports/implementation/2026-08-13-hunt-automatic-lifecycle-cleanup.md (before-landing
  hunt, stance 4): `docs/specs/reconciled-index.md` was touched but absent from the proposal's frozen
  write set. Resolution: `spec-index-preflight.sh` mechanically requires regenerating this file
  (`python3 gates/spec_index.py --update`) whenever a tracked spec/handbook file's content changes —
  `docs/handbooks/setup.md` is one such tracked file, so the regeneration was a mandatory, gate-enforced
  mechanical side effect of the write-set change, not an independent scope expansion. No further action.

## Doc-placement ladder (completed)

- [x] Env vars (`MUSTER_CLEAN_AUTO`, `MUSTER_CLEAN_MAX_AGE_DAYS`, `MUSTER_CLEAN_MAX_BYTES`) documented
  in `docs/handbooks/setup.md` (Korean and English sections), same turn as the code that reads them.
- [x] Design decision (shared-checkout dedup, requirement 4) recorded in
  `docs/issue-1179/decisions/shared-checkout-dedup.md`.

## Test run

acceptance: python3 gates/test_clean_reconcile_safety.py — result:
```
$ python3 gates/test_clean_reconcile_safety.py
....[auto-sweep] 지움 1
...[auto-sweep] 지움 1
.....
----------------------------------------------------------------------
Ran 8 tests in 0.327s

OK
```
4 pre-existing #1124 regression tests (unchanged behavior after the `roster_clean()` extraction) plus 4
new `AutoSweepTest` cases (age bound, size bound oldest-first, live-session exemption, dirty-workspace
exemption).

## Live measurement (issue's second acceptance check)

acceptance: python3 -c "... spawn._workspace_clean_state() over every ~/.tokenmaxxxer/work entry ..." —
result:
```
safe-to-delete: 24 dirs, 0.75 GB
kept (live/dirty): 294 dirs
```

acceptance: du -sh ~/.tokenmaxxxer/work; python3 -c "... spawn.auto_sweep(...) at default bounds ..."; du -sh ~/.tokenmaxxxer/work — result:
```
before: 11G  /home/jwjung/.tokenmaxxxer/work
auto_sweep() result: {'removed': 0, 'failed': 0}
after:  11G  /home/jwjung/.tokenmaxxxer/work
```

acceptance: the two fenced results directly above — result: at default bounds, nothing was reclaimed on
this run because none of the safe-to-delete workspaces are older than 14 days and their combined size is
under the 5GiB bound, so neither bound fired yet. This is the actual outcome measured this turn, not the
issue text's assumed one.

Reading the two fenced results together, the residue split on this specific machine leans toward
workspaces #1124 keeps because they carry uncommitted or unpushed work, not workspaces that are safe to
delete. The bound policy this change adds only ever touches the safe subset — it must not reach the
protected subset, by #1124's own guarantee. Left as an open note for whoever looks at residue growth
next: most of this machine's accumulated directories fall into the protected, dirty/abandoned category,
which sits outside this issue's automatic-sweep scope.

## Reopen continuation (2026-08-13): fixing the dirty-classification false positive

canonical: spawn.py `auto_sweep()` (reads `wb.glob("*")` directly, no index/roster read in its
candidate loop) — the reopen comment's literal claim (sweep only sees indexed workspaces) does not
match the code as it stood before this continuation. The actual cause of `removed:0` against measured
11GB/2374 entries is different: `_workspace_clean_state()`'s dirty check was a false positive on nearly
every legacy workspace, so the safe-to-delete set it computed was almost empty.

derived: iterate every `~/.tokenmaxxxer/work/*` dir with a `.git`, running the pre-fix
`_workspace_clean_state()`:
```
total 320 live 0 dirty 293 safe 27
```

Two causes, both checked directly against this machine's actual workspaces:

canonical: `git branch -vv`, run directly in the accessibility-rulebook issue-19 workspace, output
`issue-19/implementation ... [origin/main: 2개 앞]`, before fetch.
Cause 1, stale remote-tracking refs: a legacy workspace is never `fetch`ed again after creation, so
once its branch lands upstream (merge/squash), `git log --branches --not --remotes` reports it "ahead"
forever; the local ref never learns the branch landed.
derived: `git log --branches --not --remotes --oneline` in that same workspace returned 2 commits
before `git fetch -q origin main`, 0 commits after.

canonical: `file fundamentals.db`, run directly in a project-rich workspace, output `SQLite 3.x
database`; `ls web_out_snapshot` in the same workspace, output `app.js`, `index.html`.
Cause 2, untracked operational/build artifacts counted as "unpreserved work": `git status --porcelain`
flags any untracked file, including files the harness's own hooks write into the workspace
(`self-update.sh` writes `.pull-check` and `.shallow-check`; `directive.sh` writes
`.orchestrate-greeted`; warrant-hunt dispatch writes `.warrant-hunt.count`/`.warrant-hunt.lock`),
Python's own bytecode cache (`__pycache__`), and one target repo's (project-rich) untracked test/build
output (`fundamentals.db` plus its `-shm`/`-wal` sidecars, and `web_out_snapshot`/`web_out`) — none of
these are user-authored source, none were ever committed to lose.
derived: `git status --porcelain` in `project-rich-issue-151-implementation` returned only
`?? fundamentals.db` and `?? web_out_snapshot/`.

Fix (spawn.py `_workspace_clean_state()`, new `_HARNESS_NOISE_BASENAMES`): before deciding "dirty", (a)
drop untracked (`??`) status lines whose basename is in a fixed, narrowly-scoped allowlist —
staged/tracked changes (`M`/`D`/`A`, anything not `??`) are never filtered, so a real
committed-then-modified or committed-then-deleted file still counts as dirty; (b) when the only
remaining reason to keep a workspace is "ahead" and the working tree is otherwise clean, run one
`git fetch -q --all` (30s timeout, failures swallowed) and re-check — fetch only reads, it can never
destroy local state.

derived: same iteration as above, after the fix:
```
safe 254 8.938824099488556 GiB
dirty 66 0.8356152474880219 GiB
```
canonical: `git status --porcelain`, run directly in two still-dirty workspaces after the fix —
project-rich issue-178's workspace showed an untracked real report file; project-rich issue-181's
workspace showed a staged tracked-file modification. Both correctly still kept.

## Live reclaim (second acceptance check, re-run 2026-08-13 after the fix)

derived: `du -sh ~/.tokenmaxxxer/work` before, then `spawn.auto_sweep(wb, spawn._clean_max_age_days(),
spawn._clean_max_bytes())` at default bounds (14d / 5GiB), then `du -sh ~/.tokenmaxxxer/work` after:
```
before: 11G   /home/jwjung/.tokenmaxxxer/work
auto_sweep() result: {'removed': 61, 'failed': 0}
after:  6.8G  /home/jwjung/.tokenmaxxxer/work
```
canonical: the fenced before/after `du` output directly above — 11G to 6.8G is the terminal majority of
what the fix newly made visible as safe (8.94GiB of the classified-safe 9.77GiB workspace-dir total,
reclaimed down to the 5GiB bound). This session's own live workspace
(`on-the-record-issue-1179-implementation`, uncommitted at sweep time) was correctly kept, confirming
the live/dirty exemptions still hold under the new classification.

## Regression tests

`gates/test_clean_reconcile_safety.py` gained three cases: a harness-marker-only workspace is swept, a
real untracked file alongside a marker still exempts the workspace, and a workspace with a stale
remote-tracking ref (branch pushed to `main` under a different local branch name, simulating a
squash-merge the workspace never fetched) is swept after the fetch-and-recheck.

acceptance: `python3 -m unittest gates.test_clean_reconcile_safety` — result:
```
Ran 11 tests in 0.417s

OK
```
8 pre-existing cases (4 #1124 regression + 4 original `AutoSweepTest`) unchanged, 3 new.

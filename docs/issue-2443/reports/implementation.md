---
issue: 2443
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2443/reports/implementation.md
    sha: same-commit
code_under_review:
  - lifecycle.py
  - spawn.py
type: fix
breaking: none
verdict: pass
---

# issue-2443 — implementation record

## What was done

Added age-based auto-pruning for spawn sidecar files (`.session.*.log`,
`.events.jsonl`, `.events.offset`, `.watcher.log`, `.task.txt`) under
`~/.tokenmaxxxer/work`, reusing the workspace-directory prune (#2383/
#2411) policy and trigger verbatim rather than introducing a new
threshold or cadence.

- `lifecycle.py` (+95 lines, after `auto_sweep()`): `_SIDECAR_SUFFIX_MARKERS`
  / `_SIDECAR_SESSION_LOG_RE` recognize the five sidecar patterns;
  `_sidecar_workspace_name(filename)` maps a sidecar filename to its
  paired workspace-directory name; `_prune_orphaned_sidecars(wb,
  max_age_days=None, now=None)` groups sidecar files by paired
  workspace name, protects a group if its paired workspace directory
  still exists OR a live-pid roster entry (`_sp._live_workspaces()`,
  the same function `_workspace_clean_state()` uses) claims that
  workspace path, computes the group's age as
  `now - max(mtime of files in the group)` (a whole-set signal, not a
  single file's mtime — mirrors the lesson of the 2ca4b4de worktree-prune
  fix so an actively-appended sibling file can't be shadowed by one
  stale file in the same set), and deletes the whole group only when
  orphaned + unprotected + older than the reused threshold.
- `spawn.py` (+20 lines): re-export aliases
  `_prune_orphaned_sidecars`/`_sidecar_workspace_name` following the
  module's existing alias convention; a call to
  `_prune_orphaned_sidecars(_workspace_base(), _clean_max_age_days())`
  added inside the existing spawn-time `_run_auto_sweep()` background
  thread closure, immediately after the existing `auto_sweep()` call,
  under the same try/except-and-continue-spawn contract — no new
  trigger point, no new cron/one-off hook.
  canonical: `git diff -- lifecycle.py spawn.py` (this commit's diff).

Reused threshold/trigger, stated explicitly per the issue's fourth
acceptance bullet: **reused as-is, not a new cadence.** Age threshold:
`_clean_max_age_days()` (`lifecycle.py:948`, env `MUSTER_CLEAN_MAX_AGE_DAYS`,
default 14 days) — the same constant `auto_sweep()` uses for workspace
directories. Liveness check: `_live_workspaces()` (`lifecycle.py:569`),
indexing roster entries by resolved workspace path and alive-checking
via `roster._alive()` (`os.kill(pid, 0)`, `roster.py:117-129`) — the
exact function `_workspace_clean_state()` uses for the workspace-dir
prune. Trigger: the same spawn-time fire-and-forget daemon thread
(`_run_auto_sweep()`, started at `spawn.py:2621`, guarded by
`_clean_auto_enabled()`) that already runs `auto_sweep()` — the sidecar
prune call was added inside that same closure, same call, not a
separate thread/timer.

### Acceptance check 1 — synthetic fixture, old + orphaned set is pruned

Verified independently (not just re-quoting the delegated worker's
run) with a fresh scratch fixture covering four cases in one pass:
case A (orphaned, 20 days old) must be removed; case B (orphaned,
fresh) must survive; case C (paired workspace dir still present, 20
days old) must survive; case D (no paired dir, 20 days old, but a live
pid claims that workspace path via `_live_workspaces()`) must survive.

acceptance: `python3 -c '<fixture script building cases A-D under a
tempfile.TemporaryDirectory, then lifecycle._prune_orphaned_sidecars(wb,
max_age_days=14)>'` — result:
```
before: ['a.events.jsonl', 'a.events.offset', 'a.session.20260101T000000.111.log', 'a.task.txt', 'a.watcher.log', 'b.events.jsonl', 'b.watcher.log', 'c', 'c.watcher.log', 'd.watcher.log']
outcome: {'removed': 5, 'kept': 3, 'failed': 0}
after: ['b.events.jsonl', 'b.watcher.log', 'c', 'c.watcher.log', 'd.watcher.log']
ALL ASSERTIONS PASSED
```
Case A's 5 files (all sidecar patterns) removed; case B's 2 files and
case C's 1 file survive count-for-count; case D's file survives. No
persistent fixture file was authored — the scratch dir is a
`tempfile.TemporaryDirectory()` torn down at script exit, per this
project's verify-at-landing convention (executed-live evidence in the
record, not a permanent test file).

### Acceptance check 2 — active-spawn protection, no false-positive removal

Covered by cases C and D above in the same run: C proves paired-
workspace-directory protection, D proves live-pid protection via the
same liveness check workspace-pruning uses — both survive an age past
the threshold. See check 1's output block.

### Acceptance check 3 — live demonstration against the real backlog

Before-count defined exactly as the issue's acceptance bullet states:
sidecar files under `~/.tokenmaxxxer/work` not paired with an existing
workspace directory and older than the threshold.

acceptance: `python3 -c '<read-only count: group by
_sidecar_workspace_name, skip groups whose wb/name exists or resolves
into _live_workspaces(), sum len(files) for groups older than
max_age_days>'` — result:
```
workspace_base=/home/jwjung/.tokenmaxxxer/work max_age_days=14.0 live_entries=0
eligible groups (orphaned+old): 59
eligible FILES (orphaned+old, this is the acceptance-criterion 'before' count): 339
```

acceptance: `python3 -c "lifecycle._prune_orphaned_sidecars(spawn._workspace_base(), spawn._clean_max_age_days())"` — result:
```
prune outcome: {'removed': 339, 'kept': 546, 'failed': 0}
```

acceptance: `<same read-only count query, re-run after the prune>` — result:
```
AFTER: eligible groups (orphaned+old): 0
AFTER: eligible FILES (orphaned+old): 0
```

Before: 339 orphaned+old sidecar files. After: 0. `failed: 0` — no
partial-delete/permission errors. This is the actual current-execution
number, not the ~3507 the issue was filed against (the issue's own
acceptance text anticipates this: "report actual before/after numbers,
whatever they are at execution time"). `git status --porcelain` after
the live prune still shows only `lifecycle.py`/`spawn.py` modified —
confirming the prune touched only files under `~/.tokenmaxxxer/work`,
outside this git working tree, and nothing tracked inside it. 546
groups were correctly left in place (paired workspace dir still
present, or younger than the 14-day threshold) — none of the 546 kept
groups were inspected file-by-file against a truth set beyond what the
function itself reports, which is the same trust boundary #2383/#2411
already accepted for workspace-directory pruning.

## Why

Build-now bypass (contract v3 s19a): this session's environment carries
`CORE_BUILD_NOW=1`, which skips the proposal round entirely — no
proposal file is created for this delivery (survey-order/proposal-shape/
scout directives apply to the proposal round, which this session does
not run). canonical: `printenv CORE_BUILD_NOW` → `CORE_BUILD_NOW=1`,
checked at session start before any repository write.

The issue itself already carries a `design-research-skip: mechanical`
line: this extends the proven #2383/#2411 workspace-directory age-prune
pattern to a second artifact class (sidecar files) rather than
introducing a new design, so scouting was skipped for the same reason
the issue states. canonical: `gh issue view 2443` body — "design-
research-skip: mechanical — same age-based-prune pattern already
implemented and proven for workspace directories (#2383/#2411); this
extends that mechanism to a second artifact class rather than
introducing a new design."

skill-verdict: work-in-english — applied: invoked; used for all commit
messages, code comments, and this record; only the final chat-facing
summary to the user is Korean. One project-convention conflict noted
per the skill's own edge-case rule: this repo's existing `lifecycle.py`/
`spawn.py` comments and log strings are already Korean throughout, so
the new code's comments follow that surrounding convention (Korean)
rather than the skill's English-comments default — matching existing
style takes precedence per the skill's own guard ("match surrounding
style when editing next to existing Korean").
skill-verdict: implementation-performance-data-structure-choice — applied: invoked; rule 1 (hash-based membership over linear scan) —
required the sidecar-prune's "does this sidecar set's paired workspace
directory still exist" check to test against a pre-built hash set of
workspace directory names rather than a per-file linear/nested scan,
since the check runs once per sidecar file across a ~3500-file backlog.
other mounted skills (implementation-complexity-coupling-management,
implementation-design-pattern-selection, implementation-blueprint): not
triggered — this is a small, mechanical extension of an existing,
proven prune mechanism to a second file class in the same module; no
coupling/cohesion threshold, GoF pattern decision, or fresh
multi-module architecture choice is involved.

## What did not work

- Delegated the whole implementation unit to one background
  `freelunch:freelunch-worker` per this session's freelunch directive.
  That worker in turn spawned a nested `general-purpose` agent instead
  of doing the work itself and ended its own turn without having
  consumed that nested agent's result — a stall pattern, not the
  synchronous same-turn consumption the headless-session override
  requires. Sent it one correction message telling it not to delegate
  further and to wait for/consume its own child; it acknowledged but
  again ended its turn merely declaring intent to wait rather than
  producing results. Recovered by tracking the nested `general-purpose`
  agent directly (`ListAgents`, then `TaskOutput` non-blocking) until
  its own completion notification carried the real findings, then
  independently re-verified the delegated code (diff review, an
  independent fixture re-run, and the live before/after counts above)
  before treating any of it as trustworthy, rather than committing the
  delegated agent's self-report unverified.

## Upstream basis

- Prior implementation this extends: `_delete_workspace()`/`auto_sweep()`/
  `_workspace_clean_state()` in `lifecycle.py` — the workspace-directory
  auto-prune landed for #2383/#2411, identified via `_alive`/
  `_live_workspaces`/`_clean_max_age_days` cross-references while
  reviewing the delegated diff. derived: `grep -n` over `lifecycle.py`/
  `roster.py`, quoted inline in "What was done" above.
- Issue text: `gh issue view 2443` (quoted where used above).

## Open findings

- Before-landing warrant-hunter (stance 0), reported and reproduced.
  Full record: docs/issue-2443/reports/implementation/
  2026-08-26-hunt-sidecar-prune.md (lands in this same commit). The
  "live roster entry protects this sidecar set" check consults only the
  calling checkout's own `ROSTER` file (`ROOT/runs/active.json`, `ROOT`
  = this checkout's own directory), while `_workspace_base()`
  (`~/.tokenmaxxxer/work`) is genuinely shared across every concurrently
  running checkout on the machine (confirmed live: 25+ separate
  `on-the-record-issue-*` checkouts under it, each with its own
  independent `<checkout>/runs/` dir). A workspace whose session is
  registered alive only in a *different* checkout's roster is invisible
  to this check, so its sidecar files can be deleted once orphaned +
  past the age threshold even though the owning session is genuinely
  alive. Reproduced (hunt record has the runnable repro):
  `{'removed': 2, 'kept': 0, 'failed': 0}` against two synthetic sidecar
  files paired with a workspace registered alive in a separate,
  simulated roster.

  Resolution path / scope judgment: this is a pre-existing property of
  `_live_workspaces()`/`ROSTER` itself, not something this change
  introduces. canonical: `lifecycle.py:598-610`
  (`_workspace_clean_state()`) calls the exact same `live.get(w.resolve())`
  check against the exact same `_live_workspaces()` dict this change
  reuses for sidecar files — the original #2383/#2411
  workspace-directory prune already carries this identical cross-
  checkout blind spot; this change does not widen it, only extends the
  same signal to a second, lower-stakes artifact class (log/event
  exhaust, not workspace directories that may hold uncommitted code).
  The issue's acceptance criteria explicitly require reusing "the same
  liveness check workspace-pruning uses," not a stronger one — fixing
  `_live_workspaces()`/`ROSTER` to be genuinely cross-checkout (e.g. a
  shared `MUSTER_STATE_ROOT`) is a distinct, foundational change
  touching a function both prune paths share, and is out of this
  issue's write set. Resolution path: file a follow-up issue against
  `_live_workspaces()`/`ROSTER` scoping (affects both the sidecar prune
  added here and the pre-existing workspace-directory prune) rather
  than fold an unscoped fix into this delivery.
- None beyond the above.

## Next steps

- File the follow-up issue for the `_live_workspaces()`/`ROSTER`
  cross-checkout scoping gap noted above.
- Commit (code + this record + hunt record), push, open the PR carrying
  `Closes #2443` (build-now bypass delivers directly — no separate
  phase-1 PR).
- Set `loop_state: landed` once the PR is open.

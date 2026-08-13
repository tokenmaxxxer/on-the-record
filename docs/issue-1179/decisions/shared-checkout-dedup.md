---
name: shared-checkout-dedup
description: issue-1179 requirement 4 — accept/reject decision on shared read-only checkout dedup for spawn.py workspaces
metadata:
  type: decision
---

# Shared-checkout dedup — issue-1179 requirement 4

## Decision

Accept a design direction, defer the build. `git clone --reference <persistent-local-mirror>` for the
target-repo clone in `issue_workspace()` is the recommended dedup mechanism. It is not implemented in
this change — requirement 4 asks for an evaluated decision at phase-1 scope, and the write set for
phase 2 of issue-1179 (this session) is the automatic-sweep lifecycle work (requirements 1-3), not the
dedup build. A follow-up issue should carry the `--reference` mirror implementation.

## What was actually measured, vs. what the issue assumed

The issue's framing was "rulebook/core clones dominate the ~150MB/workspace". Reading the code
(spawn.py:262-307 `rulebook_checkout()`, spawn.py:4183-4207 `core_plugin_dirs()`/`core_root()`) shows
rulebook and core are already single shared clones under `ROOT/runs/rulebooks/<mkt>` and `ROOT`
respectively, `git pull`-refreshed and reused across every workspace — they are not duplicated per
workspace today. The actual per-workspace cost is the target-repo clone itself
(`issue_workspace()`, spawn.py:5332-5342), a full-history clone of the repo `spawn.py` lives in, made
fresh for every `(issue, role)` pair.

## Rejected alternative: git worktree

`git worktree` shares one `.git` object store across worktrees, but all worktrees of one repo share the
same `.git` directory and remotes — a worktree cannot carry its own independent `origin`. This directly
conflicts with why `issue_workspace()` clones instead of reusing a shared tree in the first place: its
own docstring (spawn.py:5332-5340) states that concurrent spawns must not share one `.git/index` or
current branch, citing a measured collision between concurrently-spawned issue-45 and issue-59
sessions. Worktree reintroduces exactly that shared-state hazard for the sake of disk savings that
`--reference` achieves without it.

## Why `--reference` fits

A `--reference`/alternates clone is a fully independent repository — its own `.git`, own refs, own
remote, safe to push from concurrently with any other clone — while its object database is populated
from a shared local mirror via `objects/info/alternates`. That preserves every isolation property
`issue_workspace()` currently relies on and removes only the redundant object storage, which is exactly
the axis the issue's disk measurement is about.

## What the follow-up build would need

- A persistent bare mirror clone of the target repo (e.g. under `ROOT/runs/repo-mirror/<repo>.git`),
  fetched on the same lazy/TTL cadence `rulebook_checkout()` already uses for its own shared clone
  (`_pull_is_fresh()`/`_mark_pulled()`, spawn.py:106-146).
  reason: reuse rather than adding a second freshness mechanism.
- `issue_workspace()`'s clone step passing `--reference <mirror> --dissociate=false` (or letting the
  alternates file persist) so packs stay shared even after a `git gc` on the workspace.
  reason: `--dissociate` would silently copy objects back into the workspace, erasing the dedup.
- A decision on mirror lifecycle when the mirror itself needs to be cleaned or re-created (corruption,
  disk pressure on the mirror path itself) — out of scope for this note, belongs in that follow-up
  issue's own proposal.

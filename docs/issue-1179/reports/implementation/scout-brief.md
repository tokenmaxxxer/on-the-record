---
name: scout-brief
description: issue-1179 shared-checkout dedup scout — worktree/alternates comparison for spawn.py's per-workspace clones
---

# Scout brief — issue-1179 (shared-checkout dedup, requirement 4)

Non-product infra decision. One deepening round only — the dedup mechanisms this search surfaced form
a small set (worktree, `--reference`/alternates, custom content-addressed layering), so a second round
was judged unlikely to change the pick.

## Field survey (git dedup mechanisms for many ephemeral checkouts)

- **git worktree** (Git 2.5+): worktrees share one `.git` object store; each worktree still needs its
  own checked-out branch. Constraint: all worktrees share the *same* `.git` directory/refs — a worktree
  cannot have its own `origin` remote independent of the parent repo.
- **`git clone --reference`/`--shared` (alternates)**: a clone gets its own full `.git` (own refs, own
  remotes, independently push/fetchable) but reads objects from a pointed-at reference repo via
  `objects/info/alternates`. Each clone is a fully independent repo; only the object database is shared.
- **Content-addressed / "git fork"-style pattern**: custom tooling layering a shared object cache under
  many independent working copies — same sharing idea as alternates, packaged with extra machinery not
  in stock git.

## Fit against this codebase's actual write surface

canonical: spawn.py:5332-5340 (`issue_workspace()` docstring and body)
`issue_workspace()` clones the target repo (the repo `spawn.py` itself lives in) fresh per
`(issue, role)` — its own docstring states why: concurrent spawns must not share one `.git/index` or
current branch (it cites a measured collision between issue-45 and issue-59 sessions).

canonical: spawn.py:262-307 (`rulebook_checkout()`), spawn.py:4183-4207 (`core_plugin_dirs()`/`core_root()`)
`rulebook_checkout()` and `core_root()` already use one shared clone (`ROOT/runs/rulebooks/<mkt>` and
`ROOT` respectively), reused and `git pull`-refreshed across all workspaces — rulebook/core are not
duplicated per workspace today. The per-workspace disk cost is dominated by the target-repo clone
itself (full history, once per issue+role), not by rulebook/core duplication as the issue's framing
assumed.

## Adopt / skip

- **Adopt (recorded here, not built this round — requirement 4 asks for a decision, phase-1 scoped)**:
  `git clone --reference <persistent-local-mirror>` for the target-repo clone in `issue_workspace()` —
  keeps each workspace a fully independent repo (own refs, own remote, safe for concurrent push/PR —
  the isolation `issue_workspace()` was built for) while objects come from one shared, periodically
  fetched bare mirror. Full write-up: docs/issue-1179/decisions/shared-checkout-dedup.md (written in
  this same change).
- **Skip**: `git worktree` for the target-repo clone — worktrees force one shared `.git`/remote across
  concurrent sessions, which reopens the index/branch contention `issue_workspace()` was written to
  avoid. Wrong fit for this write surface regardless of its disk-saving numbers in the single-developer
  case worktree guides describe.

## Segment fit

on-the-record's workspaces are short-lived, per-issue, concurrently-spawned, independently-pushed
clones — closer to "many independent CI checkouts of one repo" than to "one developer's several local
branches" (worktree's home case).

## Gap line

Current state already meets the "shared rulebook/core" must-be (one cache, reused). It is missing the
"shared object store for the target-repo clone" must-be — that gap is what the adopted `--reference`
mirror closes.

Sources:
- [Git Worktree vs Clone - Which Is Better?](https://www.gitworktree.org/compare/worktree-vs-clone)
- [Git Worktree for Large Repos & Git LFS](https://www.gitworktree.org/guides/large-repos)
- Git Fork Pattern, Eugene Petrenko (jonnyzzz.com blog) — full-checkout-without-bloat pattern using a shared object cache

Stages used: sweep (one search query) plus one deepening round reading spawn.py directly. Mode: direct
search plus code read, well inside the five-stage / three-minute budget.

# issue-711 current-state survey — spawn bootstrap path

Subject: issue-711. Scope: `spawn.py`'s per-spawn bootstrap path (rulebook
fetch, core plugin fetch, plugin-dir assembly, workspace setup), timing
instrumentation, and reduction candidates.

**Correction note:** an earlier pass of this survey read the wrong file (an
older `spawn.py` copy found via a repo-wide `find`, ~2960 lines, that turned
out to belong to a different work directory). This revision reads the actual
`spawn.py` in *this* branch's workspace (4833 lines) — line numbers and
findings below are against that file. A dispatched warrant-hunter's finding
against the stale draft (`_resolve_gh_token` caching) turned out to already
exist in the real file, which is what surfaced the mistake.

Scout skip: this step is diagnose-then-instrument on an internal tool with no
external competitive surface (spawn.py is on-the-record's own orchestration
script, not a product). The spec names the concrete reduction techniques to
weigh (cache-and-verify, warm pool, skip-unchanged), so a genuine design
choice exists for whatever residual gap the survey finds — but scouting a
"category of product" has no referent here; the applicable reference class
(how package managers/CI runners bound local-cache staleness) is general
engineering knowledge, not a field with best-in-class *products*. No scout
brief precedent exists in this repo for spawn-latency work.

## Bootstrap call chain (`_spawn_one`, spawn.py:4308)

For an issue-scoped spawn (`--issue N`), in the order they execute:

1. **`issue_workspace(cwd, issue, role)`** (spawn.py:3975) — resolve/create
   the isolated work clone under `MUSTER_WORK_DIR`. Reused workspace: one
   `_fetch_or_halt` network `git fetch`. New workspace: `git clone` (local
   `cwd`→`work`, not necessarily network) + `remote set-url` + credential
   helper + `_fetch_or_halt(..., after=remote set-head)`.
2. **`checkout_issue_branch(cwd, issue, role)`** (spawn.py:4088) — another
   `_fetch_or_halt` call on the *same* `work_dir`. **Already deduplicated**:
   `_fetch_or_halt` (spawn.py:3942) keeps a process-local `_FETCHED_THIS_SPAWN`
   dict (spawn.py:3939) keyed by resolved path — the second call in the same
   spawn process is a no-op, no second network fetch (issue #285 P3).
3. **`plugin_dirs(role, spec)`** (spawn.py:248) → **`rulebook_checkout`**
   (spawn.py:185): **already has a TTL-gated skip** (issue #285 P4). A
   `runs/ttl-markers/<hash>` mtime marker (`_ttl_marker`, spawn.py:69) records
   the last successful pull; `_pull_is_fresh` (spawn.py:77) compares its age
   against `MUSTER_RULEBOOK_TTL` (default 15 min, spawn.py:59-66; `TTL=0`
   forces "never fresh," i.e. today's always-pull behavior). Inside the TTL
   window, `git pull` is skipped entirely — this **is** the "cache-and-verify
   /skip-unchanged" reduction the issue's proposal section asks step 1 to
   consider; it has already landed for the rulebook clone. Also
   process-memoized via `_RULEBOOK_CACHE` (spawn.py:205) so a single spawn
   process never re-derives the checkout dir twice.
4. **`core_plugin_dirs()`** → **`core_root()`** (spawn.py:3181): the same TTL
   gate (spawn.py:3200-3204, same `_pull_is_fresh`/`_ttl_marker` helpers) —
   the core clone gets the identical skip-unchanged treatment.
5. **`role_settings(role, cwd)`** (spawn.py:398) — in-memory JSON merge, two
   file reads. No network. Negligible cost, not worth a phase timer on its own.
6. **`spawn_cmd(...)`** (spawn.py:3424) — resolves `GH_TOKEN` via
   **`_resolve_gh_token()`** (spawn.py:3888), which is **already cached
   process-wide** (`_GH_TOKEN_CACHE`, spawn.py:3885) — its docstring states
   this exists specifically because `issue_workspace`/`checkout_issue_branch`
   already call the same resolver (via `_git_env()`, spawn.py:3914, used by
   `_fetch_or_halt`) earlier in the same spawn. **Consequence for
   instrumentation** (see Proposal §Rationale): by the time `spawn_cmd` asks
   for the token, the cache already has it from the workspace/branch phase —
   a naive per-call timer wrapping *only* `spawn_cmd`'s use would read ~0 and
   silently misattribute the real `gh auth token` cost to whichever earlier
   phase happened to trigger the cache fill.
7. Workspace setup: `.muster-cache` env-var wiring + `go_proxy_layer` — pure
   string/path computation, no I/O beyond an `os.path.isdir` check.

## What is NOT measured today

No phase-level timing exists anywhere in this chain. `_spawn_one` does start
one `t0 = time.monotonic()` (spawn.py:4405), but that measures **only the
child `claude` session's own runtime** (used later for `duration_s` in the
result event, spawn.py:4771) — exactly the "session lifetime... counted
separately from the child session's own runtime" split the issue asks for on
the *other* side of that split. It confirms session-runtime timing already
exists; **bootstrap-phase** timing (before that `t0`) does not exist at all.
The one status line printed before `spawn_cmd` (spawn.py:4380-4382) carries no
timestamps.

## What issue #285 already delivered (do not re-propose)

Git history/docstrings (spawn.py:48, 78, 3957) show issue #285 already added:
TTL-gated skip for both rulebook and core pulls (P4), process-local fetch
dedup for the two `_fetch_or_halt` calls in one spawn (P3), and
timeout-bounded network calls via `_run_net` (P5, prevents an indefinite hang
from masquerading as bootstrap latency). This means two of the issue's three
named reduction candidates — **cache-and-verify** and **skip-unchanged** —
are already implemented for the rulebook/core fetch phases, which the survey
above identifies as the two `git pull` calls. The **warm pool** candidate
(pre-starting a ready `claude` process or pre-warming clones outside the
critical path) is not implemented anywhere in this file.

## Concurrency / write-set check (per prompt instruction)

`git log --oneline -5` on this branch shows only unrelated merges (#710/#705,
#709/#659) — nothing touching `spawn.py`. No sibling `on-the-record-issue-*`
work directory has uncommitted `spawn.py` changes. issue-659 phase 2's
declared write set is `gates/`/`hooks/` only, consistent with the prompt's
note. This step's write set (below) touches `spawn.py`'s bootstrap functions
only — no overlap.

## Reference: staleness bound already established in this codebase

`checkout_version`/`rulebook_version`/`core_version` and the TTL mechanism
itself already set the precedent this issue's "bounded staleness" requirement
must match: `_pull_is_fresh` bounds staleness to a configurable, explicit
window (default 15 min) rather than an implicit "trust the cache forever,"
and `MUSTER_RULEBOOK_TTL=0` gives an explicit escape hatch back to
always-fresh. Any further reduction (e.g. extending the same TTL mechanism to
the workspace/branch `git fetch` calls, which currently have no TTL — only
within-process dedup) must preserve that same "never silently report or run
something staler than the stated bound" property.

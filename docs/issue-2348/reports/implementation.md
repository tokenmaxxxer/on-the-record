---
issue: 2348
role: implementation
author: implementation
loop_state: done
upstream:
  - path: docs/issue-2333/reports/implementation.md (Deviations section — the deferred design sketches this issue completes)
    sha: 983ad6e4cabbaa2c41fa3aa33d9ff9bfc7afa51c
code_under_review:
  - hook_fires.py
  - deviation_log.py
  - on-the-record/hooks/hook-fires.sh
  - on-the-record/hooks/directive.sh
  - on-the-record/hooks/stop-gate.sh
  - on-the-record/hooks/stop-poll-rearm.sh
  - on-the-record/hooks/deviation-log-guard.sh
  - on-the-record/hooks/role-deviation-directive.sh
  - on-the-record/hooks/skill-verdict-guard.sh
  - on-the-record/directive/delegation-loops.md
  - docs/handbooks/deviation-loop.md
  - docs/specs/generated-paths.md
  - docs/specs/enforcement-boundary.md
  - spawn.py
  - on-the-record/hooks/test_hook_fire_counter.py
  - on-the-record/hooks/test_deviation_log_guard.py
  - on-the-record/hooks/test_stop_poll_rearm_deadman.py
  - tests/test_spawn_consult_panel.py
type: feat
breaking: "no — `_hook_fires_path()`/`_deviation_log_path()` are new internal helpers; `.orchestrate-hook-fires.log` and `docs/issue-<n>/reports/deviation-log.md` (or the role-scoped equivalent many sessions already used) stop being appended to going forward but are left in place as historical artifacts — same precedent as `consult-log.md`'s own flat-file retirement in #2333. The only shipped CLI contract changes are additive (`spawn.py hook-fires`, `spawn.py deviation-log`, `spawn.py deviation-log-path`)."
verdict: pass
---

# issue-2348 — implementation record

amendments-reconciled: issuecomment-5407297407 — operator-frozen
constraint (2026-08-25: fix must hold systemically for every installing
session/target repo, and land with no added per-spawn overhead/
steady-state load, no new conflict surfaces, no stall/deadlock, no
consumer-tree pollution). Addressed: (1) systemic — `hook_fires.py`/
`deviation_log.py` both resolve their root via `Path(cwd).resolve()`
(the target repo `-C`/cwd passed in), never this checkout's own path;
`hook-fires.sh`/`deviation-log-guard.sh` both operate on `$(pwd -P)` of
whatever workspace the hook fires in, same as every other on-the-record
hook. (2) no added per-spawn overhead — `hook-fires.sh`'s
`hook_fires_record()` is deliberately pure bash+coreutils
(`sha256sum`/`shasum`/`openssl`, never python3) specifically because these
three hooks fire on every UserPromptSubmit/Stop event fleet-wide; a
python3 interpreter start on that path would have been a real new
steady-state cost the old plain `printf >>` never paid (see the
hook-fires.sh section below for the exact fallback chain). `deviation_log.py`'s
per-append cost is one `glob()` over a handful of small shard files inside
an already-running `spawn.py` process — no new process, matching
`consult-log.md`'s own #2333 precedent exactly. (3) no new conflict
surfaces — sharding is the mechanism that *removes* the shared-path
conflict surface both artifacts had; no new shared path is introduced (the
`hook-fires.sh` source file itself is edited only by developers, never
appended to at runtime). (4) no stall/deadlock — the one behavior change
with stall potential, `stop-poll-rearm.sh` now reading its own stdin via
`cat` for the first time, matches `directive.sh`'s/`stop-gate.sh`'s
already-existing `cat`-on-stdin pattern; the harness always pipes and
closes the hook payload for these event types, so `cat` returns on EOF
the same way it already does for the other two hooks — verified live via
the deadman-check test suite passing with the `input=""` case
(`test_stop_poll_rearm_deadman.py`, see Executed evidence). (5) no
consumer-tree pollution — the sharded paths replace the flat files inside
the exact same tracked-workspace-relative convention the flat files
already used; no new top-level path category is introduced.

## What was done

Implements the append-log conflict elimination #2333 deferred, per its
Deviations section's design sketches, for both remaining artifacts —
canonical: commit `927079c9c77c26a428bd56ebe2ff3d57aaccb08a` (`git show
--stat 927079c9`), the delivery commit this record documents.

**Hook-fires** (`.orchestrate-hook-fires.log`, issue #2028's fire counter):
- New `hook_fires.py`: `_hook_fires_dir()`/`_hook_fires_shard_id()`
  (`sha256(session_id)[:24]`, the same hash formula `directive.sh`'s
  pre-existing monitor-notice marker already used — warrant-hunt findings
  under docs/issue-947, hash never a substitution sanitizer)/
  `_hook_fires_path()`/`_hook_fires_aggregate()` — the reader, sorting
  merged lines (each already timestamp-prefixed and one-line, so line-sort
  reproduces chronological order exactly, unlike the file-level sort
  `_consult_log_aggregate()` uses).
- New `on-the-record/hooks/hook-fires.sh`, a shared library (mirrors the
  existing `poll-rearm.sh` precedent for cross-hook logic) exposing
  `hook_fires_record <label> <payload-json>`. Deliberately pure
  bash+coreutils (`grep`/`sed` to pull `session_id` out of the JSON
  payload; `sha256sum`, falling back to `shasum -a 256` then `openssl
  dgst -sha256`, for the hash) rather than shelling out to python3 for
  every firing — see the amendment reconciliation below.
- `directive.sh`/`stop-gate.sh`/`stop-poll-rearm.sh`: each now captures
  its own stdin exactly once, before any kill-switch/role short-circuit
  (preserving the existing "count every real trip" invariant), and calls
  `hook_fires_record`. `directive.sh`'s later monitor-notice block and
  `stop-gate.sh`'s later Python check now reuse that one captured payload
  instead of re-reading stdin (stdin can only be consumed once).
  `stop-poll-rearm.sh` previously never read its own stdin at all; it now
  captures it solely to carry `session_id` into `_deadman_check()`'s
  (already-conditional) counter write, an existing asymmetry versus the
  other two hooks' unconditional placement left unchanged.
- `spawn.py hook-fires [-C <repo>]`: reader/CLI subcommand, same shape as
  `consult-log`.

**Deviation log** (`docs/issue-<n>/reports/deviation-log.md`, issue #803's
deviation loop): two differences from hook-fires/consult-log drove a
different scheme —
1. The writer is the session itself (a manual Edit/Write, not a
   subprocess or a stdin-JSON hook), so there is no process to cache a
   shard id in and no per-firing JSON payload to hash. `$CLAUDE_CODE_SESSION_ID`
   (present in every tool call's env) is the one stable per-session
   identity available; `deviation_log._deviation_log_shard_id()` hashes
   it but *also* prefixes a microsecond-precision timestamp — reusing an
   existing shard matched by its hash suffix so repeat appends in one
   session land in the same file, minting a fresh timestamp+hash on first
   use — so shard filenames stay lexically-sortable-is-chronological, the
   same property `consult-log.md`'s ts-pid shard ids have.
2. Entries can wrap several physical lines (real example:
   docs/issue-2207/reports/conformance-review/deviation-log.md). Sharding
   by whole file, not by line, matters more here than for the one-line
   hook-fires/consult-log entries — `_deviation_log_aggregate()`
   concatenates whole shard files in filename order, never individual
   lines, so a multi-line entry never gets spliced with another session's.
- New `deviation_log.py`: `_deviation_log_dir()` (role-scoped when
  `$CLAUDE_ROLE`/an explicit `role=` is given, else the pre-#2348
  role-less bucket — see the reconciliation below)/
  `_deviation_log_shard_id()`/`_deviation_log_path()`/
  `_deviation_log_aggregate()`.
- `spawn.py deviation-log-path --issue <n>` / `spawn.py deviation-log
  --issue <n>`: a session never computes its own shard path or reads the
  aggregate by hand — both CLI subcommands resolve role from this
  session's own `$CLAUDE_ROLE`.
- Reconciles a pre-existing, previously unenforced convention found while
  implementing this: many role sessions already write
  `docs/issue-<n>/reports/<role>/deviation-log.md` (e.g. this record's own
  `upstream:` sibling, `docs/issue-2333/reports/implementation/deviation-log.md`)
  rather than the flat, role-less path `deviation-log-guard.sh` actually
  checked. Left unreconciled, sharding the flat role-less path would have
  made it a worse conflict surface than before: every role working the
  same issue (implementation, conformance-review, execution-observation,
  ...) would now shard into the same directory, still colliding on
  session identity across roles. `deviation-log-guard.sh`'s branch-regex
  already captured a role group from `issue-<n>/<role>` but discarded it
  (pre-#2348 `rel = os.path.join(..., "deviation-log.md")` never
  referenced `branch_m.group(2)`); role now comes from `$CLAUDE_ROLE` (the
  same signal board-gate's R4 already treats as authoritative for a role
  session's own subtree — not the branch group, since a role session is
  defined by `$CLAUDE_ROLE` being set, and the branch is already required
  to equal `issue-<n>/<CLAUDE_ROLE>` rather than being an independent
  source for it).
- Fixes a detection gap sharding would otherwise open:
  `deviation-log-guard.sh` verified a matching append via `git diff`/
  `git log -p` only. Under the old single-flat-file layout that was fine
  because after the very first deviation ever logged for an issue+role,
  the file was already tracked, so every later append was a plain
  working-tree diff. Sharding makes "this session's first deviation for
  this issue+role" the common case, not a one-time-ever event — every
  session mints its own brand-new, initially-untracked shard file, and
  `git diff`/`git log -p` never report untracked paths at all. Added a
  `git status --porcelain` fallback (reports untracked/staged/unstaged
  alike); `on-the-record/hooks/test_deviation_log_guard.py`'s new
  `t_untracked_new_shard_passes` covers it directly — see the Executed
  evidence section below.
- Updated `on-the-record/hooks/role-deviation-directive.sh`,
  `on-the-record/hooks/skill-verdict-guard.sh`'s advisory text,
  `on-the-record/directive/delegation-loops.md`, and
  `docs/handbooks/deviation-loop.md` to point at `spawn.py
  deviation-log-path`/`deviation-log` instead of the old flat path.

**Shared across both**: `docs/specs/generated-paths.md` gained a row for
the new `hook-fires.sh` (n/a — its write is append-mode, which this
gate's `open\([^)]*['"]w` pattern doesn't match, same blind spot the raw
bash `>>` it replaces always had) and an updated `deviation-log-guard.sh`
row; `docs/specs/enforcement-boundary.md` gained a `hook-fires.sh` row
("not a hook itself", same shape as `poll-rearm.sh`) and an updated
`deviation-log-guard.sh` row; `docs/specs/reconciled-index.md`
regenerated via `python3 gates/spec_index.py --update`.

Tests: rewrote `on-the-record/hooks/test_hook_fire_counter.py` and
`on-the-record/hooks/test_deviation_log_guard.py` (+ the new
untracked-shard test) for the sharded/role-scoped layout, fixed
`test_stop_poll_rearm_deadman.py`'s path assertions, and added
`HookFiresSharding`/`DeviationLogSharding` test classes to the named
acceptance gate (`tests/test_spawn_consult_panel.py`) — same shape as
#2333's `ConsultLogSharding`: distinct shards, aggregate reconstruction,
empty state, and a real `git init`/branch/merge exercise per artifact.

## Why

Append-only file + concurrent writers + one shared path is what makes the
git merge conflict predictable, per #2333's own reasoning, which #2348
asked to finish applying. Sharding removes the shared path rather than
resolving individual conflicts as they occur. The two artifacts needed two
different shard-id schemes (hash-of-session-id for hook-fires vs.
timestamp+hash for deviation-log) because their writers are structurally
different — a stateless bash hook re-invoked every event vs. an
interactive session appending by hand across a whole session — not
because the underlying conflict-elimination shape differs; both still
reduce to "one path per session instead of one shared path," and both
still reconstruct the pre-sharding single-file view through an aggregator
CLI verb, matching `consult-log.md`'s own contract exactly.

Used `implementation-blueprint` before writing code to decide two open
structure questions: whether the hook-fires reader/aggregator belongs in
a new standalone module vs. inline in `spawn.py` (already ~3000 lines),
and whether the three hooks' duplicated shard-id-and-append logic should
factor into one sourced bash library vs. stay duplicated per script. The
`data-centric` archetype's stated principles (module hides exactly one
nameable design decision; monolith-file named as an anti-pattern) argued
for a new module (mirroring `consult.py`'s own shape) and for the
existing `poll-rearm.sh`-style shared-library precedent on the bash side
— this delivery followed both for `hook_fires.py`/`hook-fires.sh` and
`deviation_log.py`.

## What did not work

PR #2388 drifted into `mergeable: CONFLICTING` against `main` (ordinary
unrebased drift — two independent observer-record commits landed on
`main` for this same issue while this branch sat open, and one of them
appended to `.orchestrate-hook-fires.log`, the exact append-only file
this delivery is retiring). Fixed by rebasing
`issue-2348/implementation` onto `origin/main`
(`git rebase origin/main`); the only conflict was that log file itself —
resolved by a plain chronological union of both sides' lines (both were
independent hook-fire timestamp appends, no semantic conflict), then
`git rebase --continue`. Force-pushed with `--force-with-lease`.

acceptance: `python3 -m pytest tests/test_spawn_consult_panel.py -q` (re-run
after the rebase, on `e9ad25f3`) — result:

```
.............................................................x.......... [ 98%]
.                                                                        [100%]
72 passed, 1 xfailed in 1.17s
```

acceptance: `gh pr view 2388 --json mergeable,mergeStateStatus` (after the
force-push) — result:

```
{"mergeStateStatus":"UNKNOWN","mergeable":"MERGEABLE"}
```

## Upstream basis

`docs/issue-2333/reports/implementation.md`'s Deviations section
(commit `983ad6e4cabbaa2c41fa3aa33d9ff9bfc7afa51c`) — the concrete design
sketches for both hook-fires and deviation-log sharding this delivery
implements; see that record's Deviations/Open findings sections for the
sketch text.

## Open findings

None — no resolution path needed.

## Next steps

None — this record's own frontmatter `loop_state` is the terminal value.

## Executed evidence

acceptance: `python3 -m pytest tests/test_spawn_consult_panel.py -q` (the
named gate, includes the new `HookFiresSharding`/`DeviationLogSharding`
classes) — result:

```
..........................................................x............. [ 98%]
.                                                                        [100%]
72 passed, 1 xfailed in 1.08s
```

acceptance: `python3 -m pytest on-the-record/hooks/test_hook_fire_counter.py
on-the-record/hooks/test_deviation_log_guard.py
on-the-record/hooks/test_stop_poll_rearm_deadman.py
on-the-record/hooks/test_directive_diet.py
on-the-record/hooks/test_role_deviation_directive.py
on-the-record/hooks/test_skill_verdict_guard.py -q` — result:

```
................................F.........                               [100%]
1 failed, 41 passed in 2.58s
```

The one failure, `test_directive_diet.py::test_always_on_injection_within_size_budget`
(2978 bytes vs. a `SIZE_BUDGET` of 2688), reproduces identically with this
delivery's changes stashed out via `git stash` — pre-existing on this
branch, unrelated to hook-fires/deviation-log (this delivery touched none
of `directive.sh`'s always-on injected index text, only the fire-counter
section above it).

acceptance: `python3 -m pytest gates/test_generated_paths.py
gates/test_boundary.py -q` (the golden-reference tables both new hook
scripts and the changed `deviation-log-guard.sh` must stay consistent
with) — result:

```
...........xx.                                                           [100%]
12 passed, 2 xfailed
```

acceptance: `python3 -m pytest tests/test_consult_trace_root.py
gates/test_consult_siblings.py gates/test_consult_verdict_parsing.py
gates/test_consult_json_parse.py test/test_spawn_cross_family_skill_selection.py
test/test_spawn_skill_judge_haiku_timeout_overlap.py -q` (adjacent
consult-path tests, checking the new `import deviation_log`/`import
hook_fires` wiring in `spawn.py` didn't disturb anything already there) —
result:

```
..............x..................x.............x..........               [100%]
55 passed, 3 xfailed
```

**Provenance — two real sessions per artifact, executed live** (acceptance
requirement: "the same two-branch concurrent proof PR #2345 ran for
consult-log, repeated for hook-fires and a deviation log"): a scratch git
repo per artifact (`mktemp -d`, discarded after the run — not a path in
this repository), two branches each firing the real hook / calling the
real `spawn.py deviation-log-path` CLI, real `git commit`, real merge.

Hook-fires — session A on `issue-2348/session-a`, `directive.sh` fired
with `session_id=session-a-real`, under the scratch repo's own root:

```
.orchestrate-hook-fires/b06ba9d6df69129b76b66f04.log
```

session B on `issue-2348/session-b` (checked out from `main`, session-a's
branch untouched), `session_id=session-b-real`:

```
.orchestrate-hook-fires/47d456f89ee8d050764e0360.log
```

acceptance: `git checkout main && git merge -q --no-edit
issue-2348/session-a && git merge --no-edit issue-2348/session-b` —
result:

```
Merge made by the 'ort' strategy.
 .orchestrate-hook-fires/47d456f89ee8d050764e0360.log | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 .orchestrate-hook-fires/47d456f89ee8d050764e0360.log
merge rc=0
```

No conflict — the two sessions never wrote the same path.

acceptance: `python3 spawn.py hook-fires -C "$REPO"` (run against `main`
after both merges) — result:

```
2026-08-25T08:18:06Z UserPromptSubmit directive.sh
2026-08-25T08:18:06Z UserPromptSubmit directive.sh
```

Both entries present after both merges, from two branches that never
touched the same file.

Deviation log — session A on `issue-2348/session-a`,
`CLAUDE_ROLE=implementation CLAUDE_CODE_SESSION_ID=session-a-real`,
`spawn.py deviation-log-path --issue 2348 -C "$REPO"` printed the
scratch-repo-relative path
`docs/issue-2348/reports/implementation/deviation-log/20260825T081814-b06ba9d6df69129b.md`
(untracked at the scratch repo, since deleted with it — not a path in
this repository); session B (checked out from `main`),
`CLAUDE_CODE_SESSION_ID=session-b-real`, printed the sibling shard ending
`...-47d456f89ee8d050.md`, written a real multi-line entry.

acceptance: `git checkout main && git merge -q --no-edit
issue-2348/session-a && git merge --no-edit issue-2348/session-b` —
result:

```
Merge made by the 'ort' strategy.
 .../implementation/deviation-log/20260825T081814-47d456f89ee8d050.md | 2 ++
 1 file changed, 2 insertions(+)
 create mode 100644 docs/issue-2348/reports/implementation/deviation-log/20260825T081814-47d456f89ee8d050.md
merge rc=0
```

No conflict.

acceptance: `python3 spawn.py deviation-log --issue 2348 -C "$REPO"` (run
against `main` after both merges) — result:

```
- 2026-08-25T08:05:00Z | filed | session B real deviation, multi-line
  continuation text here.
- 2026-08-25T08:00:00Z | inline | session A real fix.
```

Both entries present, session B's multi-line entry intact (not
line-scrambled with session A's), from two branches that never touched
the same file. (Both sessions started in the same UTC second, so the
timestamp-prefix ordering ties and falls back to hash order for these
two — the same coarse-tie-goes-to-hash property `consult-log.md`'s own
ts-pid scheme has at microsecond granularity; the aggregate above still
carries both entries in full regardless of which one sorts first.)

**Empty state** (single-session issue, no concurrency provoked):
`HookFiresSharding.test_empty_state_no_prior_firing_is_empty_string` and
`DeviationLogSharding.test_empty_state_no_prior_deviation_is_empty_string`
(covered by the `tests/test_spawn_consult_panel.py` run above).

## skill-verdict

skill-verdict: implementation-blueprint — applied: invoked; used before
writing any code to decide (a) hook_fires.py/deviation_log.py as new
standalone modules vs. inline in spawn.py, and (b) hook-fires.sh as a
shared sourced bash library vs. duplicated per hook script — see the Why
section above for how the `data-centric` archetype's principles resolved
both.
other mounted skills: not triggered.

skill-verdict: work-in-english — applied: invoked; loaded during the
mergeability-fix follow-up (see "What did not work") to keep the commit
message and this addendum in English with the turn's final summary in
Korean. canonical: 799365de (this commit's own message and diff).

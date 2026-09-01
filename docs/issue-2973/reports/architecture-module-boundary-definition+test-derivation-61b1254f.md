---
issue: 2973
role: architecture-module-boundary-definition+test-derivation-61b1254f
author: architecture-module-boundary-definition+test-derivation-61b1254f
skills: architecture-module-boundary-definition (skill-repository(c05de12)), test-derivation (skill-repository(c05de12))
verifies_subject: false
code_under_review:
  - lifecycle.py
  - spawn.py
  - tests/test_temp_root_reclaim.py
type: feature
breaking: false
verdict: pass
loop_state: landed
upstream:
  - path: lifecycle.py
    sha: 3fe539f08c09632e6d34a5b048f07baf98363fc6
  - path: spawn.py
    sha: 3fe539f08c09632e6d34a5b048f07baf98363fc6
  - path: tests/test_temp_root_reclaim.py
    sha: 3fe539f08c09632e6d34a5b048f07baf98363fc6
---

# issue-2973 — architecture-module-boundary-definition+test-derivation-61b1254f record

Build-now delivery (CORE_BUILD_NOW=1, set by the spawner) — no phase-1 proposal round.

## What was done

Gave sessions a plugin-managed location for the temp repo copies / build
trees they otherwise picked freely (issue's observed case: `/tmp/tas-*-repos`
via a session-chosen `TAS_REPOS_ROOT`, invisible to every existing
reclamation mechanism), and an age-based sweep of that location that runs
independently of any cleanup the session itself performs.

- `lifecycle.py`:
  - `_temp_repos_base()` — resolves the plugin-managed base
    (`~/.tokenmaxxxer/tmp-repos`, `MUSTER_TEMP_REPOS_ROOT` override for
    ops/tests, same convention as `_workspace_base()`'s `MUSTER_WORK_DIR`)
    — deliberately a different location than `_workspace_base()`, so
    sweeping it never touches `~/.tokenmaxxxer/work` (issue #2960's scope).
  - `session_temp_root(roster_key)` — `<base>/<roster_key, "/" -> "-">`,
    created on demand. This is the path a session should use instead of
    picking its own `/tmp/...` root.
  - `sweep_temp_repos(base=None, max_age_days=None, now=None)` — age-based
    reclamation. Only ever walks the immediate children of `base` (never
    a `/tmp`-wide name-pattern scan). Compares each live (pid-alive)
    roster key, sanitized with the same `"/" -> "-"` rule
    `session_temp_root()` uses, against directory names, and skips any
    match regardless of age. Everything else is reaped once
    `now - <max mtime across the entry's tree>` exceeds `max_age_days`
    (tree-wide mtime, not the top directory's own mtime — same rationale
    already documented at `_worktree_last_activity()`: a build writing
    only nested files never touches the top directory's mtime). Returns
    `{"removed", "kept", "failed"}`; an empty/missing `base` returns all
    zeros.
- `spawn.py`:
  - re-exports the three names above (`_temp_repos_base`,
    `session_temp_root`, `sweep_temp_repos` = `lifecycle.<name>`), same
    pattern as every other `lifecycle`-extracted name.
  - `_spawn_one()`: right after `roster_key` is computed (before it's
    used for anything else), injects
    `extra_env["MUSTER_TEMP_ROOT"] = str(session_temp_root(roster_key))`
    — the spawned session gets a ready-made, plugin-managed temp root
    instead of having to invent one.
  - the existing spawn-time background auto-sweep thread (the one that
    already runs `auto_sweep()` + `_prune_orphaned_sidecars()` on every
    spawn, issue #1179/#2443) now also calls `sweep_temp_repos()` in the
    same thread, same per-call exception absorption (`실패(스폰은 계속)`),
    so reclamation rides the existing spawn-time cadence rather than
    needing a new trigger point.
- `tests/test_temp_root_reclaim.py` (new): the two acceptance-named test
  classes plus supporting cases for the issue's `must not:` lines (never
  sweeps `/tmp` by name pattern, never deletes a live session's temp
  root, dead roster entries don't block reclamation, empty state sweeps
  zero).

## Why

architecture-module-boundary-definition: the issue's own consult already
rejected the two tempting alternatives (sweep `/tmp` by name pattern —
ungeneralizable and unsafe on a directory shared with other
processes/sessions; rely on session self-cleanup — doesn't survive a
turn-limit kill or a crash before cleanup code runs). That leaves exactly
one placement decision: where does the module boundary between "a
session's own scratch space" and "the plugin's reclamation machinery" sit?
Putting `_temp_repos_base()` as a sibling of `_workspace_base()` rather
than inside it keeps the two reclamation policies (workspace git-state
safety checks vs. temp-repo pure age+liveness checks) from having to share
one code path that would need to special-case one or the other — and, more
concretely, keeps this change from touching `~/.tokenmaxxxer/work` sweep
logic at all, satisfying the issue's explicit `must not: do not widen this
to touch ~/.tokenmaxxxer/work reclamation (issue #2960's scope)`.

test-derivation: the two acceptance checks are equivalence-partition
boundaries on the sweep's decision table (candidate is under a
plugin-managed base — yes/no; candidate's roster key is pid-alive —
yes/no; candidate age vs. `max_age_days` — under/over), so
`tests/test_temp_root_reclaim.py` derives one test per partition
(managed-vs-bare-tmp placement; dead+old reclaimed; dead+young kept;
live+old kept regardless of age; dead-roster-entry doesn't block reclaim;
empty-base is the boundary/empty-state case named directly in the issue's
acceptance; and a `/tmp` canary directory that must survive the sweep
untouched, covering the `must not: sweep /tmp by name pattern` line
directly rather than only by absence of a `/tmp` glob in the source).

Liveness check reuses the sanitize-and-compare approach (compare
`roster_key.replace("/", "-")` against the directory name) instead of
reversing the directory name back to a roster key, because that reversal
would be lossy (roster keys can themselves contain "-"), while comparing
in one direction only is unambiguous and needs no new state.

## Upstream basis

No proposal precedes this delivery — build-now bypass. The only upstream
input is the issue itself:

canonical: `gh issue view 2973` (read this session) — body, Acceptance
section, and the consult's rejection of the two "obvious" fixes (sweep
`/tmp` by pattern; rely on session self-cleanup), which the design above
is derived directly from.

## Open findings

None.

## Next steps

None — loop_state: landed. Acceptance requirement met — checked:
`python3 -m pytest tests/ -k temp_root_is_managed -q` — result: 4 passed
in 0.86s.
Acceptance requirement met — checked:
`python3 -m pytest tests/ -k temp_root_swept_without_session_cooperation -q`
— result: 6 passed in 0.92s.
derived: `git stash && python3 -m pytest test/test_spawn_artifact_skill_pairing.py test/test_local_dependency_env.py test/test_spawn_cross_family_skill_selection.py -q && git stash pop` — result: same 9 pre-existing failures / 33 passed both with and without this change (baseline noise unrelated to this issue, also flagged by the session's own lint-test-on-edit hook before any edit was made) — confirms no regression from the `_spawn_one()` env-injection edit.
derived: `python3 -m py_compile spawn.py lifecycle.py pipeline.py` — result: compiles clean.

## What did not work

None.

skill-verdict: architecture-module-boundary-definition — applied: invoked; used to place `_temp_repos_base()` as a sibling of, not inside, `_workspace_base()` so the new sweep never shares a code path with (or scope-creeps into) the `~/.tokenmaxxxer/work` reclamation that issue #2960 owns
skill-verdict: test-derivation — applied: invoked; used to derive `tests/test_temp_root_reclaim.py`'s cases from the sweep's decision table (managed-location partition, liveness partition, age partition, plus the issue's explicit `must not:` lines) rather than writing only the two literally-named acceptance tests
other mounted skills: not triggered

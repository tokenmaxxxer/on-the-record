---
subject: issue-1803
kind: survey
---

# Current-state survey — watch/roster explicit role field

## Scope

Issue #1803 executes migration-order entry 2 (frozen at
`docs/issue-1792/reports/implementation.md:104-109`, committed at a prior
merge to main): watch/roster stops deriving `role` by splitting the
roster/workspace-index string key and instead reads an explicit `role`
field, dual-written alongside the unchanged key.

## The two stores

`spawn.py` keeps two separate on-disk stores that both hold per-session
entries keyed by an `issue-N/role` (or `repo/issue-N/role`) string:

1. **ROSTER** (`runs/active.json`, loaded via `_roster_load`/saved via
   `_roster_save`/written via `roster_register`, `spawn.py:2298-2301`).
   Entries here already carry a `role` field today — `_build_expected`
   (`spawn.py:2160-2169`) reads `entry.get("role")` directly, and the
   docstring at `spawn.py:2163-2164` states `roster_register()` 가 이미
   쓰는 필드(`role`, `expects_pr`).
   canonical: read spawn.py:2160-2169, spawn.py:2298-2301, spawn.py:8289-8390 this session.
   This store is already migrated per that same read: the
   `roster_register` call sites at `spawn.py:8310` and `spawn.py:8388`
   both construct entry dicts that include `"role": role`, so no
   dual-write is needed for ROSTER — only the workspace index (below)
   needs it.

2. **workspace index** (`WORKSPACE_INDEX`, loaded via
   `_workspace_index_load` and written via `_workspace_index_put`,
   `spawn.py:4515-4589`). This is the store the issue's three cited line
   numbers (`spawn.py:4700`, `:4750`, `:4798` per the #1792 survey/proposal)
   actually target — those absolute line numbers have drifted with
   intervening commits, but the same three call sites are still present
   in the current tree.
   canonical: read spawn.py:4515-4589, spawn.py:4695-4813 this session.
   Now at:
   - `_live_roster_matches` (`spawn.py:4695-4706`): `role =
     k.rsplit("/", 1)[1]` — splits the workspace-index key `k` to recover
     `role`, then looks the entry up in ROSTER by
     `f"issue-{issue}/{role}"`.
   - `_roster_fallback_entry` (`spawn.py:4726-4756`): the no-`role`-given
     branch does `m = re.match(rf"^issue-{issue}/([^/]+)$", k)` over
     ROSTER keys (not workspace-index keys) to recover `found_role` —
     this one splits a ROSTER key, but ROSTER keys have the identical
     `issue-N/role` shape, so it is included as a split site.
   - `_lookup_workspace_entry` (`spawn.py:4780-4811`): two split sites —
     the `repo is None` + `role given` branch matches
     `k.endswith(f"/issue-{issue}/{role}")` (membership test, not an
     extraction, so no role recovery happens there) and the
     `_ambiguous_watch_exit` helper (`spawn.py:4705-4713`) does
     `roles = [k.rsplit("/", 1)[1] for k, _ in matches]` to build its
     error message's candidate list — a fourth split site, cosmetic
     (error text only), not behavior-critical.

   The workspace-index write site is `_workspace_index_put`
   (`spawn.py:4553-4589`); its entry dict today is `{"work": work, "log":
   log}` plus optional `watcher_pid`/`watcher_armed_at` — no `role` field
   currently, even though the function already receives `role` as a
   parameter and uses it only to build the key
   (`f"{_repo_identity(work)}/issue-{issue}/{role}"`, `spawn.py:4556`).
   canonical: read spawn.py:4553-4589 this session.

## Read-site count vs. the issue text

The issue text says "the three key-split read sites the #1792 survey
identified (spawn.py:4700, :4750, :4798 region)". Reading the current
tree in that region (canonical: read spawn.py:4695-4813 this session,
same read as above) turns up three functions with key-split logic
(`_live_roster_matches`, `_roster_fallback_entry`,
`_lookup_workspace_entry`'s no-role branches, counting
`_ambiguous_watch_exit`'s cosmetic split as part of the third region) —
consistent with "three read sites" if counted by function rather than by
individual `rsplit`/`re.match` call. This survey treats all of
`_live_roster_matches`, `_roster_fallback_entry`, and
`_lookup_workspace_entry` (which also anchors `_ambiguous_watch_exit`'s
candidate list, called from within it) as the three read sites in scope,
matching the issue's three-region framing.

## Existing golden-case coverage

`test/test_convention_equivalence.py`'s `WatchRosterEquivalenceTest`
(`test/test_convention_equivalence.py:205-246`) already has three golden
cases against today's split-based behavior:
- `test_live_roster_matches_key_split` — exercises `_live_roster_matches`.
- `test_roster_fallback_entry_key_shape` — exercises
  `_roster_fallback_entry`.
- `test_lookup_workspace_entry_suffix_match` — exercises
  `_lookup_workspace_entry`.
canonical: read test/test_convention_equivalence.py:203-246 this session.

These three cases construct roster/workspace-index entries with no
`role` field (legacy shape) per that same read, so they double as
regression coverage for the legacy-fallback path once the field-read
path is added — but new golden cases are still needed for the
field-present path per requirement 3's "new cases may be added for the
field-read path."

## Dependency check against the frozen order

Per `docs/issue-1792/reports/implementation.md:104-106`, watch/roster
"depends only on the branch/roster key shape... never touches APPROVE
grammar or approval-gate... independent of consumer 3 (branch names)."
canonical: read spawn.py:4695-4813 this session (same read cited above
for the three read sites) — none of `_live_roster_matches`,
`_roster_fallback_entry`, or `_lookup_workspace_entry` reads branch names
or the APPROVE needle, matching that dependency claim; this issue's
write set does not need to touch `approval-gate.sh`, `pr-preflight.sh`,
`contract-guard.sh`, or `gates/flows.py`.

## Assumptions-skip

`assumptions-skip: mechanical` per the issue body — no design-research
scout run for this survey; the replacement mechanism (dual-write field +
legacy fallback) is fully specified by the frozen #1792 migration-order
proposal (`docs/issue-1792/reports/implementation.md:104-109`) and by
requirement 1-2 of issue #1803's own body, leaving no open design
decision for this sub-issue to make.

---
proposal: docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md
---

# Hunt record — decision-queue-session-scope

## after-proposal — stance 1: the frozen write set (gates/flows.py, spawn.py, tests/test_flows.py) cannot carry the work it commits to

Verdict: FINDING — the write set omits docs/specs/flows-schema.md, the versioned, externally-mirrored contract doc for `decision_queue`, whose §2.1 will silently misdescribe the field once landed
Kind: design-error
Seed: docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md
cap_seconds: 60
tier: default
diff_stat_lines: 0 (proposal only, no diff yet)
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:03:00Z

### Reproduce
```
grep -n "decision_queue" docs/specs/flows-schema.md | sed -n '1,10p'
grep -n "repo-status-board.*스키마 문서의.*사본" tests/test_spawn.py
```

### Observed
`docs/specs/flows-schema.md` §2.1 documents `decision_queue[]` as "One
entry per open PR awaiting phase 1 or phase 2 approval" with a fixed
field table (`issue`, `pr`, `phase`, `role`, `opened_at`, `age_hours`,
`awaiting`) and no mention of any caller/session filtering. The
repository's own issue-566 planning notes (embedded in
`tests/test_spawn.py`) state explicitly that this same schema doc is
mirrored by the separate `repo-status-board` repo and any change
requires "동기화 필요" (sync required) with that copy. The proposal's
"What will be done" section changes `decision_queue`'s *default*
contents (foreign-session items silently dropped unless `--all`) but
never touches `docs/specs/flows-schema.md`, and explicitly excludes any
doc change from its Out of scope / write set. Landing the 3-file set as
frozen leaves the schema doc (and the external repo-status-board copy
it says must stay synced) describing `decision_queue` as an unscoped,
repo-wide list — which becomes false the moment `flows_payload()` ships
the ownership filter, and no gate in this repo (checked
`gates/test_capability_gates.py`'s `schema_field_orphans`) catches
content drift, only field-name reachability.

### Expected
A write set that scopes `decision_queue`'s semantics should also list
`docs/specs/flows-schema.md` (or explicitly justify, inside the
proposal, why the versioning-policy doc can stay unchanged despite
altering what the field returns by default for every consumer that
doesn't set `ORCHESTRATOR_SESSION_ID_ENV`/pass `--all` — including the
external repo-status-board consumer the doc itself says holds a
separate copy needing sync).

## before-landing — stance 3: assume the write set cannot carry this work — find the path the build will need that the proposal does not list.

Verdict: NO FINDING
Seed: diff ~120 lines across gates/flows.py, spawn.py, tests/test_flows.py, docs/specs/flows-schema.md (docs/issue-1035/proposals/2026-08-12-decision-queue-session-scope.md)
cap_seconds: 120
tier: default
diff_stat_lines: ~120
started_at: 2026-08-12T00:00:00Z
ended_at: 2026-08-12T00:02:00Z

Checked for a build-required path missing from the proposal's write set:
- `--all` is registered once on the shared top-level `argparse.ArgumentParser` in `spawn.py` (not per-subcommand), so `a.all` is available to the `flows` role dispatch without any new `add_argument` call — confirmed by grepping other `--all` consumers (`watch --all`, `watchdog`) sharing the same flag.
- `on-the-record/hooks/decision-queue-stopgate.sh` calls `python3 spawn.py flows --json -C "$REPO"` (no `--all`) and only consumes the returned JSON — no code change needed there since it doesn't touch `flows_payload()`'s signature, matching the proposal's explicit "Out of scope" note.
- `gates/flows.py`'s new `_own_item()` builds `key = f"{subject}/{role}"` where `subject` is the `"issue-<n>"` string parsed from the PR branch regex — this matches `spawn.py`'s own `roster_key = f"issue-{issue}/{role}"` format exactly (verified both sites), so no roster-key mismatch.
- `gates/test_capability_gates.py` (a third file that references `decision_queue` and is not in the write set) uses only synthetic fixtures with a literal `decision_queue` string, not the actual `docs/specs/flows-schema.md` table row text, so it is not sensitive to the schema-doc wording change.
- Ran `python3 -m pytest -q tests/test_flows.py gates/test_capability_gates.py`: 25 passed, no failures.

No reproducible missing-file/path defect found within the cap.

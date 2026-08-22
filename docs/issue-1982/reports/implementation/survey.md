---
name: survey
subject: issue-1982
kind: implementation-survey
---

# Current-state survey: state-aware respawn continuation preamble

## Write surface

canonical: read spawn.py:1618-1662

`_reconcile_pr_expected_missing()` computes `policy_verdict`
(`RESPAWN_IDENTICAL` / `RESPAWN_WITH_HANDOFF` / `ESCALATE`) from
`recovery_policy.classify_from_state()`, keyed on `has_commit`. The
divergence dict it returns carries a `"handoff"` bool.

canonical: read spawn.py:3376-3377

`roster_watchdog()` only prints that divergence dict's fields
(`div['kind']`, `div['detail']`, `div['next_action']`) — no downstream
reader in this file reads the `"handoff"` field to alter respawn
behavior. `reconcile()`'s divergence list is observational only at this
call site; it does not itself invoke `_spawn_one()`.

canonical: read spawn.py:3984-4066

```
4050	    task_path = Path(str(work) + ".task.txt")
4051	    if not task_path.exists():
...
4055	    task = task_path.read_text(encoding="utf-8")
...
4066	    _spawn_one(work, role, task, unattended=True, issue=issue, bounded=True)
```

`_respawn_or_cap()` is the only function in `spawn.py` that reads
`.task.txt` and forwards it to `_spawn_one()`. No branch between these two
lines inspects the workspace's current git state before the forward.

canonical: read spawn.py:4069-4104,4107,4110-4135

`_respawn_or_cap()` has exactly two callers: `_auto_respawn_check()`
(watchdog-observed `crashed`) and `_self_trigger_respawn()`, which fires
when `outcome in _ABANDONED_WORK_OUTCOMES = ("uncommitted-work",
"failed-no-commit", "silent-failure")`. The self-trigger path is the one
that fires on a dirty workspace.

canonical: read spawn.py:8442-8454

Right after a session ends, `_spawn_one()` computes `uncommitted` via
`git -C cwd status --porcelain`, logs the uncommitted paths when
non-empty, and that feeds (through `classify()`/`fail_closed_downgrade()`,
not re-read here) the `outcome` that `_self_trigger_respawn` checks.

canonical: read spawn.py:3973-3981,4033-4036

`_respawn_fingerprint()` computes `{"head": _git_head(work), "board":
<hash of board_snapshot(work)>}` at every respawn call, for no-progress-
streak comparison only. It runs at the same moment a completed-work
heuristic would need to run, but only inspects HEAD sha and
`board_snapshot()` fields — not uncommitted diff content.

canonical: read spawn.py:8446-8448

`git status --porcelain` is the repo's existing idiom for detecting
uncommitted work; a completed-work heuristic can reuse this call rather
than invent a new git-state probe.

## Related work / prior reproductions

canonical: read docs/issue-1959/reports/test-authoring/survey.md

#1959's survey documents stranding needing 3 respawn rounds in the
test-authoring role — same root cause class (identical task text replayed
into a workspace already holding prior-round output), different call
path.

canonical: read docs/issue-1978/reports/implementation/survey.md and docs/issue-1978/proposals/spawn-directive-single-phase-and-skill-trigger-lines.md

#1978's survey/proposal is the RESPAWN_IDENTICAL observed-failure case
this issue's Request paragraph cites directly ("#1978 respawned
identically").

canonical: read docs/issue-1981/proposals/checkpoint-commit-directive-line.md

#1981 added a static "checkpoint-commit" directive line to the task-text
template itself — a build-time constant applied to every session, not a
respawn-time, workspace-state-conditional preamble. It does not touch
`_respawn_or_cap()`; this issue's mechanism is complementary, not
overlapping.

canonical: read spawn.py:1633,1644-1649

`RESPAWN_IDENTICAL` currently means only "no prior commit was observed
per `has_commit=False`" — it carries no signal about whether the current
dirty workspace holds finished-but-uncommitted work versus broken/partial
work-in-progress.

## Gap this issue targets

derived: grep -rn "finished.work|is_finished|workspace_classif" spawn.py gates/
```
(no output — no such heuristic exists in either location)
```

No existing code path distinguishes, at the moment `_respawn_or_cap()`
reuses `task`, between a dirty workspace holding finished-but-uncommitted
work (candidate for a continuation preamble: verify, commit/push/PR,
don't redo) and one holding partial/broken work-in-progress (where a
premature "commit this" nudge risks pushing something unready). That
gap — a finished/unfinished classifier gated on dirty-workspace state at
respawn time — is this issue's phase-1 deliverable.

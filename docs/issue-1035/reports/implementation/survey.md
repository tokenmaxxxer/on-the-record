Subject: issue-1035

# Current-state survey

## Write set (expected)
- `gates/flows.py` — `flows_payload()`/`flows()` build `decision_queue`
  from `gh pr list` (all open PRs, repo-wide) with no ownership filter.
- `spawn.py` — CLI dispatch for the `flows` role invokes
  `gates/flows.py`, carrying flags along.
- `tests/test_flows.py` — acceptance cases.

## What's there now
derived: `grep -n "decision_queue = \[\]" -A 25 gates/flows.py`
```
    decision_queue = []
    unapproved_open_prs = []
    flows_out = []
    for (subject, role), pr in sorted(pr_by_branch.items()):
        issue_n = int(subject.split("-", 1)[1])
        loop_state = (b.get(subject, {}).get(role, {}) or {}).get("loop_state")
        comments = comments_for(subject, pr["number"])
        approved = _pr_approved(pr, comments, approvers, subject, role)
        phase = 1 if loop_state in (None, "scope-proposed") else 2
        if not approved:
            decision_queue.append({
                "issue": issue_n, "pr": pr["number"], "phase": phase,
                "role": role, "opened_at": pr.get("createdAt"),
                "age_hours": _age_hours(pr.get("createdAt")),
                "awaiting": "approve-scope" if phase == 1 else "approve-full",
            })
```
`flows_payload(root)` builds `decision_queue` by iterating
`pr_by_branch` — every open PR matching `issue-<n>/<role>`, from
`_pr_list_all()` (repo-wide, no scoping) — and appends every unapproved
one, unconditionally. No session attribution exists on these items
today — `age_hours`, `issue`, `pr`, `role`, `phase`, `awaiting` only.

`spawn.py` already carries the exact ownership convention this issue
asks to reuse:
derived: `grep -n "def _roster_own" -A 20 spawn.py`
```
def _roster_own(d: dict, all_scope: bool) -> dict:
    if all_scope:
        return d
    own = os.environ.get(ORCHESTRATOR_SESSION_ID_ENV) or None
    out = {}
    for key, e in d.items():
        sid = e.get("session_id")
        if sid == own or sid is None:
            out[key] = e
    return out
```
`_roster_own(d, all_scope)` filters a roster dict (keyed
`issue-<n>/<role>`, e.g. `roster_key = f"issue-{issue}/{role}"` at
spawn.py) to entries whose `session_id` equals
`os.environ[ORCHESTRATOR_SESSION_ID_ENV]` or is `None` on either side
(empty-state parity; an orphaned entry with no `session_id` stays
observable — the "observation-loss" invariant named in its own
docstring). `all_scope=True`, driven by the pre-existing `--all` CLI
flag already shared by `watch`/`watchdog`, returns the dict unfiltered.

Critically: the roster key shape (`issue-<n>/<role>`) is identical to
`decision_queue`'s own `(issue, role)` pair — a `decision_queue` item
can be joined to a roster entry by that same string key, so the exact
`_roster_own` predicate (not a re-derivation) is directly reusable
per-item.

`flows()` (the CLI wrapper) and the `spawn.py` dispatch for the `flows`
role have no scope plumbing today; `--all` is parsed by the single
top-level `ArgumentParser` shared by every subcommand, so it is already
available as `a.all` at the `flows` dispatch site — no new flag has to
be added, only threaded through.

## Prior decisions
- #1013 (PR #1023/#1028): introduced `_roster_own` and scoped
  roster/watchdog/PR-gate/auto-respawn paths to it. Issue #1035's body
  states #1013 left `flows.py`'s `decision_queue` global/unscoped.
- #1021 (PR #1025): bounded the re-block loop in
  `decision-queue-stopgate.sh` but did not change what feeds the queue
  itself — a foreign item still triggers the one-time block/advisory
  in the current code.

## Skip-condition note
This proposal names one rejected alternative (see proposal's
Rationale) but the design space is narrow: the issue body already
prescribes reusing #1013's convention and keeping a global escape, and
`_roster_own` is the only convention in this codebase for this exact
problem shape — an external scout sweep for "how other tools scope a
shared queue to a session" would not surface anything more applicable
than the sibling function already imported into this same file
(`spawn.py`). Scope is judged narrow enough that a full external scout
sweep is skipped; this internal precedent is treated as the survey's
finding instead.

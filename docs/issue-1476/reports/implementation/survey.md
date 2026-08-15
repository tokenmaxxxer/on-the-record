# Current-state survey — issue-1476

Skip condition: pure bugfix (scout-directive skip condition 1). This is a
defect fix inside existing infra (`gates/spawn_on_pr.py`, `spawn.py`), not a
product-facing surface — no category/exemplar to scout.

## Write set

- `gates/spawn_on_pr.py` — respawn gate; add park/re-arm logic keyed off a
  structured signal (not prose). New test file `test_spawn_on_pr_park.py`
  will live under `tests/` alongside it (not yet created).
- `spawn.py` — the watchdog print site that calls
  `spawn_on_pr.spawn_missing_for_pr` needs one more line reporting parked
  entries so watch-coverage stays intact (Requirement 3).

## What already exists

canonical: gates/ci.py:181-201 (read this turn)
```python
def _approved_roles_on_issue(repo: Path, issue: int) -> set[str]:
    approvers = spawn._approvers(repo)
    comments, _ok = spawn._issue_comments(repo, issue)
    prefix = f"APPROVE issue-{issue}/"
    roles = set()
    for c in comments:
        body = (c.get("body") or "").strip()
        if body.startswith(prefix) and c.get("login") in approvers:
            role_token = body[len(prefix):]
            if role_token:
                roles.add(role_token)
    return roles
```

This scans issue-level comments for the exact-string `APPROVE
issue-<n>/<role>` pattern (approver allowlist, string equality, never
prose) — the existing structured signal for "has a human approved this
role," reused here as the basis for the awaiting-human-APPROVE blocker
instead of inventing a second comment-matching path.

canonical: gates/spawn_on_pr.py:42-90 (read this turn)
```python
def applicable_roles(subject_board: dict, roles: tuple[str, ...] = PR_TRIGGERED_ROLES) -> list[str]:
    return [r for r in roles if r not in subject_board]


def missing_verification(root: Path, issue_states: dict[int, str] | None = None
                          ) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    ...
    for subject, subject_board in b.items():
        missing = applicable_roles(subject_board)
        if not missing:
            continue
        pr_number = spawn._pr_open_or_merged_for_branch(root, f"{subject}/implementation")
        if pr_number is None:
            continue
        issue = int(subject.split("-", 1)[1])
        if not _issue_is_open(issue, issue_states):
            continue
        out[subject] = missing
    return out
```

The quoted `missing_verification()` body above (`role not in subject_board`,
issue-OPEN check, PR-exists check) is the full spawn-candidate predicate;
`spawn_missing_for_pr()` in the same file spawns every resulting pair up to
`SPAWN_CAP`, every tick, with no persisted memory of a prior tick's
outcome.

derived: `gh issue view 1163 --comments` (read this turn) shows
`docs/issue-1163/reports/conformance-review/deviation-log.md` accumulated
17 "re-check" entries, one per spawn, each re-confirming in prose that the
same `APPROVE issue-1163/implementation` comment (not the required
`APPROVE issue-1163/conformance-review`) is the only approval present —
the sequence issue #1476 targets.

## Gap

Nothing currently distinguishes "this role has never been given a chance to
try" from "this role tried, hit the human-approve blocker, and nothing about
that blocker has changed since." The fix needs a small persisted park-state
(per subject/role: last-seen blocker + branch head sha) so a second tick
with the same unresolved blocker can be told apart from a first attempt or a
real state change (new APPROVE comment, new commit).

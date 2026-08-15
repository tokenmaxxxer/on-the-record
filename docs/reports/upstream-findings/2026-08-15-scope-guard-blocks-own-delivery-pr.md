# upstream-defect-scope-guard.sh: in_scope() blocks a role's own delivery PR against its own origin

Local fallback record: `gh issue create` was refused for this role session
by `gh-guard.sh` ("issues are the user's requirement backlog, user-authored
only (contract v3 s9) — no role touches them"), and `gh pr create` was
separately refused by this role's own `upstream-defect-scope-guard.sh`. No
live upstream filing happened; this file is the fallback write per this
role's `write_scope` (`docs/reports/upstream-findings/`).

## Plugin version

`git -C on-the-record rev-parse HEAD` of the installed plugin at
observation time (this session, issue #1199).

## Reproduction

From an `upstream-defect-report`-role session, run `gh pr create` targeting
the session's own `origin` remote (`tokenmaxxxer/on-the-record` — i.e.
`target_repo == ORIGIN_REPO`). Expected: allowed, since the guard's own
header comment states it should exempt "a role session's own delivery PR
against origin." Actual: denied with:

```
upstream-defect-scope-guard: `gh pr create` (including a GH_REPO/GH_HOST-env-var-prefixed invocation) is denied — the upstream defect channel files issues only, never PRs (issue #1131 req#4).
```

## Observation context

`on-the-record/hooks/upstream-defect-scope-guard.sh` lines 18-26 (header
comment): "Scoped (issue #1171): deny only within the upstream-defect
channel's own flow, never a role session's own delivery PR against
origin."

Same file, lines 117-126 (`in_scope()`, quoted verbatim):

```
def in_scope(target_repo):
    """PR-creation call is in-scope for denial iff the channel's own role
    is active, or a target repo was extracted and it isn't this session's
    origin repo. `target_repo=None` (no extractable target, or origin
    unresolvable) relies on the role signal alone."""
    if channel_role_active:
        return True
    if target_repo is not None and ORIGIN_REPO is not None:
        return target_repo.lower() != ORIGIN_REPO
    return False
```

`channel_role_active` is checked and returns `True` unconditionally before
`target_repo == ORIGIN_REPO` is ever compared — the origin-exemption the
header comment describes is never reached when the acting role is
`upstream-defect-report`, which is exactly the role this guard's own
docstring says should still be allowed a delivery PR against origin.

## Suggested fix

Check the origin-exemption before the role check:

```python
def in_scope(target_repo):
    if target_repo is not None and ORIGIN_REPO is not None and target_repo.lower() == ORIGIN_REPO:
        return False
    if channel_role_active:
        return True
    if target_repo is not None and ORIGIN_REPO is not None:
        return target_repo.lower() != ORIGIN_REPO
    return False
```

## Outcome

Not filed upstream live this session (both `gh issue create` and
`gh pr create` were mechanically refused for this role). This fallback
file, plus the same diagnosis in
`docs/issue-1199/reports/upstream-defect-report.md`, is the record until
a human or a differently-scoped session files it upstream.

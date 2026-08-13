# Survey — issue #1283

Skip condition: pure bugfix (survey-order-directive skip condition 1). The
issue itself frames the open question as a judgment call ("which side is
correct"), but the judgment is resolvable mechanically from git history —
no product/design decision remains once the history is read. Scout
(product-field sweep) is skipped for the same reason: this is an internal
bugfix to a reconcile helper, not a product-shaped surface.

## Write set (expected)

- `spawn.py` — `_roster_reconcile_unreported()` (spawn.py:2888-2939)
- `tests/test_spawn.py` — `RosterReconcileUnreported` test class
  (tests/test_spawn.py:6446-6511)

## Current state

canonical: spawn.py:2911-2916 (read this session)
```
        if not Path(work).exists():
            # 이슈 #1124: reconcile 은 `clean` 이 이미 지운 workspace 를
            # 회복하려고 존재한다 — 바로 그 상태에서 죽으면 안 된다.
            print(f"[reconcile --unreported] {key}: workspace 없음(clean 됨?) "
                  f"— 건너뜀 [{work}]")
            continue
```

`_roster_reconcile_unreported()` skips a workspace-index entry outright
when `Path(work).exists()` is false, printing "workspace 없음(clean 됨?)
— 건너뜀" and `continue`-ing before ever computing `session_end_verdict()`
or checking the `[watch]` comment marker.

derived: `git log -S "def _roster_reconcile_unreported" --oneline -- spawn.py`
```
c4bb24b0 feat(issue-534): durable session-end/PR-open comments + reconcile --unreported sweep
```

derived: `git log -S "clean 됨?" --oneline -- spawn.py`
```
b62e57dc issue-1124: clean/reconcile safety — archive non-landed logs, tolerate missing workspace
```

canonical: tests/test_spawn.py:6446-6511 (read this session)

Commit `c4bb24b0` (issue #534) introduced both the function and the
`RosterReconcileUnreported` test class in the same commit — the tests
stub `work` paths that were never created on disk, and assert the entries
are still listed. Commit `b62e57dc` (issue #1124), landed later, added
the `Path(work).exists()` skip quoted above. That skip's own comment
states its purpose as making reconcile tolerant of an already-`clean`ed
workspace, not making it silently drop the entry — the `continue`
implementation contradicts the comment directly above it, and its
addition is what makes the pre-existing tests fail (verified this session
via `python3 -m pytest tests/test_spawn.py::RosterReconcileUnreported -q`,
pasted in the proposal's Rationale).

canonical: spawn.py:1738,1756-1757 (read this session)
```
def session_end_verdict(work: str, log_path: Path | None, now: float | None = None,
...
    if not events_path.exists():
        return "normal"
```

`session_end_verdict()` already tolerates a non-existent `work` path: it
only calls `_events_path(work).exists()` and falls back to `"normal"`
when the events file is absent.

`_issue_comments()` calls `_repo_slug(root)`; when `root` does not exist
as a git checkout, `_repo_slug` returns falsy and `_issue_comments`
returns `([], False)`.

canonical: spawn.py:1287-1289,2931-2932 (read this session)
```
    slug = _repo_slug(root)
    if not slug:
        return [], False
...
        comments, ok = _issue_comments(Path(work), issue_n)
        if ok and any(marker in c.get("body", "") for c in comments):
            continue
```

canonical: spawn.py:2929-2930 (read this session)

The existing "확인 못 함은 통과가 아니다" (#287) comment at that line
already states the same fail-closed direction the issue's
no-silent-observation-loss standard asks for.

No existing test in `RosterReconcileUnreported` covers an empty
workspace-index (`{}`) — the issue's "empty state" acceptance item is not
yet covered.

derived: `grep -n "workspace_index_load = lambda: {}" tests/test_spawn.py`
```
(no output)
```

## Judgment

Observation-loss regression, not a test defect: `b62e57dc` added the skip
after the tests quoted above already existed, and after
`session_end_verdict`/`_issue_comments` were already written to tolerate a
missing workspace — the skip's own adjacent comment states the opposite
intent of what the code does. Resolution: drop the existence check in
`spawn.py`, keep the pre-existing tests unmodified, add a regression test
named for the cleaned-before-report case, and add the missing empty-index
case.

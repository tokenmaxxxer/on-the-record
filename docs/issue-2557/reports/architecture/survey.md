# issue-2557 — architecture survey (phase 1)

Current-state inventory of the write_scope persistence mechanism, ahead
of amending `docs/issue-2548/reports/architecture.md`'s Step D. Every
citation below was read directly this session; the executed check
(Question 2 of the amendment) is not repeated here — it lives in the
amendment record itself, `docs/issue-2557/reports/architecture.md`.

## The roster: liveness dict, popped at session end

canonical: `roster.py:159-173` (read this session):

```python
def roster_register(key: str, entry: dict) -> None:
    with _sp._roster_locked():
        d = _sp._roster_load()
        d[key] = entry
        _sp._roster_save(d)


def roster_remove(key: str) -> None:
    with _sp._roster_locked():
        d = _sp._roster_load()
        entry = d.pop(key, None)
        if entry is not None:
            _sp._roster_save(d)
```

`d[key] = entry` is an unconditional overwrite (no merge, no append);
`d.pop(key, None)` deletes the whole entry, with no awareness of which
fields inside it matter past session end. canonical: `roster.py:129-140`
(read this session) — the key itself is `lease_key(issue,
disambiguator)`, shape `issue-{issue}/{disambiguator}`, the same shape
Step C wires into the branch name.

## Step A: write_scope bootstrapped into that same dict, at spawn time

canonical: `spawn.py:77-99` (`_bootstrap_write_scope()`, read this
session) resolves `write_scope` from `spawn_roles.json`/`role_data()` at
spawn time and returns `{"write_scope": [...]}` or `{}`. canonical:
`spawn.py:3499` and `spawn.py:3636` (grep this session) both call it
inside the same dict literal that builds the roster entry `roster_
register()` receives — so `write_scope` lives inside the exact dict
`roster_remove()` deletes above. Nothing in `spawn.py` or `roster.py`
persists that value anywhere else.

## Step B: the only reader, and its existing fail-closed behavior

canonical: `gates/gates.py:931-964` (`_roster_write_scope()`, read this
session):

```python
    key = spawn.lease_key(issue, role)
    entry = spawn._roster_load().get(key)
    if entry is None:
        return None
    expires_at = entry.get("lease_expires_at")
    if expires_at is not None and time.time() > expires_at:
        return None
    if "write_scope" not in entry:
        return None
    return list(entry["write_scope"])
```

canonical: `gates/gates.py:992-1000` (`role_scope()`, read this session)
— on a `None` return above, falls back to `spawn_roles.json[role].
write_scope` via `_role_cfg(role)`, and fails closed with `"{role!r} 에
write_scope 선언이 없다 (fail closed)"` if that role has no
`write_scope` key either. Both branches are already fail-closed by
construction — no default-allow path exists in this function today.

## The only consumer: a PR gate, run after the session ends

canonical: `gates/ci.py:618-623` (read this session):

```python
    if pr is not None:
        branch = _pr_head_ref(repo, pr)
        if branch is None:
            bad.append(f"PR #{pr} 의 head 브랜치를 읽을 수 없다 (fail closed)")
        else:
            bad += gates.role_scope(repo, branch)
```

This runs against a pushed PR — by construction, after the spawning
session's process has exited and already called `roster_remove()`.

derived: `python3 -c "import sys; sys.path.insert(0,'.'); import spawn as _sp; d = _sp._roster_load(); print(len(d), d)"`
— result: `0 {}` (this session, no session running in this checkout).

## Adjacent durable-storage pattern already in the codebase

canonical: `plumbing.py:327-334` (`ledger_write()`, read this session):

```python
def ledger_write(entry: dict) -> Path:
    """runs/ledger.jsonl 에 한 줄. runs/ 는 gitignore 되어 있다 — 측정 데이터는
    소스가 아니다."""
    d = _sp.ROOT / "runs"
    d.mkdir(exist_ok=True)
    p = d / "ledger.jsonl"
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return p
```

This file is append-only and is never touched by `roster_remove()`
(verified by the full-function quote above — its only statements act on
`_sp.ROSTER`, not on `runs/ledger.jsonl`). It is the closest existing
precedent for a store that outlives a session, and the amendment's
proposed `runs/write_scope_ledger.jsonl` follows the same shape.

## No process/OS isolation between spawner and role session

derived: `grep -n "chown\|chmod\|setuid\|seteuid\|os.geteuid\|container\|sandbox\|docker\|namespace\|jail\|cgroup" spawn.py roster.py plumbing.py`
— result: no matches in any of the three files (this session).
canonical: `docs/decisions/2026-08-11-remove-role-session-sandbox.md:38-41`
(read this session; tracked file, `git log --follow` returns commits) —
`role_settings()` forces `sandbox.enabled = False` centrally for every
spawned session. Role sessions run same-uid, same-filesystem as the
orchestrator process that spawns them, with no code-level or OS-level
boundary found in the three files greped above.

## Binding data already captured at spawn time, unused for CI-side identity today

canonical: `spawn.py:3418` (read this session):

```python
before_head = _git_head(cwd) if issue is not None else None
```

canonical: `events.py:55` (`_git_head`, read this session) and
`spawn.py:968` (`_is_new_commit(work, entry.get("before_head"),
after_head)`, read this session) — `before_head` is already captured in
the spawner's own process before the child starts, and is already
trusted for one ancestor-style comparison (watchdog signal 4). Nothing
today uses it to bind a persisted declaration to a specific PR.

## Conclusion driving the amendment

Every piece the amendment's ledger design needs already exists in the
codebase in some other consumer: an append-only durable store shape
(`ledger_write()`), a spawner-captured immutable git ancestor field
(`before_head`), and an existing per-spawn key (`lease_key()`). No
external prior art is needed — see `scout-brief.md` in this same
directory for that disposition.

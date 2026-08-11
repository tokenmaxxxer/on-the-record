---
kind: current-state-survey
loop_state: handed-off
---

# Current-state survey — issue #857 (spawn.py roster/watch namespace collision)

## Scope

Reproduce and pin exactly where `spawn.py`'s roster/state namespace is
shared between the observing session and a fixture session it launches,
such that the fixture's `spawn.py watch --issue 776` resolved to the
observer's own roster entry for issue 776 on a different repository
(PR #855, finding 5). No fix — that is issue #857 step 2
(implementation), gated on this record.

canonical: `gh issue view 857`, read this session — quotes finding 5's
`ps aux` evidence:
```
jwjung 3238031 python3 spawn.py execution-observation issue #776 re-measure #2 ... --issue 776 -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer
jwjung 3238257 python3 spawn.py watch --issue 776 --role execution-observation --follow -C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer
```

code_under_review:
- spawn.py
- harness/driver.py

## Finding 1 — `ROSTER` is a single global file, keyed bare `issue-<n>/<role>` with no repo scoping and no collision guard

canonical: spawn.py:1757, read this session, verbatim:
```
ROSTER = ROOT / "runs" / "active.json"
```
`ROOT` (spawn.py:37) is `Path(__file__).resolve().parent` — the
directory holding the running `spawn.py` file itself, i.e. the single
shared plugin installation
(`~/.claude/plugins/marketplaces/tokenmaxxxer` in the #855 `ps aux`
evidence above), not anything derived from `-C`/the invoking repo. Every
`spawn.py` invocation against that one installation — the observer's own
session and any role/fixture session it spawns from that same
installation — reads and writes the identical file
`~/.claude/plugins/marketplaces/tokenmaxxxer/runs/active.json`.

canonical: spawn.py:4894, read this session, verbatim:
```
roster_key = f"issue-{issue}/{role}" if issue is not None else f"adhoc/{role}/{os.getpid()}"
```
The key written into that single global file carries no repo
identifier at all — only issue number and role name.

canonical: spawn.py:1824-1828, read this session, verbatim:
```
def roster_register(key: str, entry: dict) -> None:
    with _roster_locked():
        d = _roster_load()
        d[key] = entry
        _roster_save(d)
```
`d[key] = entry` blind-overwrites on a repeat key with no check that the
existing entry belongs to a different repo/work dir. This is the exact
opposite of `_workspace_index_put()`'s guard (Finding 2 below), which
raises rather than silently overwriting. Two independent `spawn.py`
invocations against the same plugin installation, both running role
`execution-observation` for issue 776 — the observer's own real session
and a fixture-under-test session — write to the same `ROSTER` key
`issue-776/execution-observation`, and whichever registers second wins
the entry the first one's watchers/lookups then read.

## Finding 2 — the repo-scoped layer (`WORKSPACE_INDEX`) exists but is entirely dependent on a correctly-threaded `-C`, which the #855 evidence shows was not given the fixture's own directory

canonical: spawn.py:2487, read this session:
```
WORKSPACE_INDEX = ROOT / "runs" / "workspaces.json"
```
Also `ROOT`-rooted (same shared-installation file as `ROSTER`), but its
keys are repo-scoped: `_workspace_index_put()` (spawn.py:3060-3088)
builds `key = f"{_repo_identity(work)}/issue-{issue}/{role}"`
(spawn.py:3075) and raises `RuntimeError` (spawn.py:3078-3081) rather
than silently overwriting when an existing entry's `work` dir differs —
issue #533's fix for exactly this shape of repo collision.

`_repo_identity(cwd)` (spawn.py:3018-3031) resolves the scoping
identifier from `git -C <cwd> remote get-url origin`, falling back to
`Path(cwd).resolve().name` when there is no such remote. Its `cwd` input
is the `work` dir string passed by the caller — for the CLI's own
`watch` command, that's `_repo_identity(a.cwd)` (spawn.py:4113), where
`a.cwd` comes straight from argparse:
```
ap.add_argument("-C", "--cwd", default=".", help="작업 디렉터리")
```
(spawn.py:3987) — default `.`, the OS process's own current working
directory at invocation, with nothing in `spawn.py` verifying that value
against the caller's actual intended target directory.

canonical: `gh issue view 857`'s finding-5 `ps aux` quote (Scope section
above) — the fixture session's own `spawn.py watch --issue 776 --role
execution-observation --follow` process ran with
`-C /home/jwjung/.claude/plugins/marketplaces/tokenmaxxxer` — the real
on-the-record checkout's own path, not the isolated fixture directory
(`.../ftarget-steady-20260811b`, quoted in the issue body as where the
fixture session "armed" its watch). With that `-C` value,
`_repo_identity()` resolves to the real checkout's own repo identity, so
`_lookup_roster_entry()` (spawn.py:3226-3269) builds the exact same
`WORKSPACE_INDEX` key the observer's own session registered under
(`<repo-identity>/issue-776/execution-observation`,
spawn.py:3236-3239) and returns the observer's entry — matching the
issue body's quote of the fixture session's own reasoning: "There is
already a running execution-observation session on issue-776 in this
repo's ledger."

`WORKSPACE_INDEX`'s repo-scoping (Finding 2) therefore only isolates a
fixture correctly when the fixture's own `spawn.py` invocations are
launched with `-C`/cwd pointed at the fixture's own working copy; the
#855 evidence shows a real run where that precondition did not hold, so
the isolation this layer nominally provides collapsed to the same
collision `ROSTER` (Finding 1) has unconditionally, by construction, in
every case.

## Finding 3 — even where `WORKSPACE_INDEX` correctly disambiguates by repo, the bare-keyed `ROSTER` lookup inside `_watch()` is unconditionally repo-unscoped

canonical: spawn.py:3385-3390, read this session, verbatim (comment plus
code):
```
        # 이슈 #533: `key` 는 workspace 인덱스 키(레포 접두사 포함)지만
        # ROSTER 는 별도 메커니즘으로 `issue-<n>/<role>` 그대로 키를 쓴다
        # (이번 변경의 out-of-scope) — 여기서 조회할 때는 접두사를 떼어
        # bare 형태로 되돌린다.
        m = re.search(r"issue-\d+/[^/]+$", key) if key else None
        roster_entry = _roster_load().get(m.group(0)) if m else None
```
The comment states, as prior art from issue #533, that `ROSTER` staying
repo-unscoped relative to `WORKSPACE_INDEX` was known and explicitly
marked out of scope at that time. The same pattern repeats at
spawn.py:3303-3305 (`_watch()`'s `session_idx`/`live_pid` lookup) and
spawn.py:1849-1868 (`roster_ps()` joining `ROSTER` to
`WORKSPACE_INDEX`). Any code path that strips the repo prefix back to
the bare `issue-<n>/<role>` form and reads `ROSTER` with it inherits
Finding 1's collision even when the `WORKSPACE_INDEX` half of the same
lookup was correctly repo-scoped.

## Conclusion

1. The shared-namespace root cause is `ROSTER` (spawn.py:1757,
   `ROOT / "runs" / "active.json"`): a single file per `spawn.py`
   plugin installation, keyed bare `issue-<n>/<role>`
   (spawn.py:4894) with a blind-overwrite register
   (spawn.py:1824-1828, no guard) — reproduced from the #855 `ps aux`
   evidence, Findings 1 and 3.
2. A partial, repo-scoped mitigation (`WORKSPACE_INDEX`,
   spawn.py:2487, issue #533) exists alongside it, but it depends
   entirely on the caller threading a correct `-C`/cwd
   (spawn.py:3987 default `.`) into `_repo_identity()`
   (spawn.py:3018-3031); the #855 run's fixture session invoked
   `spawn.py watch` with `-C` pointed at the observer's own checkout
   path rather than the fixture's directory, so this layer's
   disambiguation collapsed to the same collision — Finding 2.
3. Even a `WORKSPACE_INDEX` lookup that did resolve to the correct,
   fixture-scoped key still falls through to the repo-unscoped
   `ROSTER` for pid/offset data (Finding 3), a gap `spawn.py`'s own
   comments (spawn.py:3385-3388) record as knowingly left out of
   scope by issue #533.

## Finding 4 — `WORKSPACE_INDEX` (the repo-scoped layer in Finding 2) also has no lock, so its own collision guard is not race-safe

canonical: `docs/issue-857/reports/defect-verification/hunt-defect-verification.md`,
this session's dispatched warrant-hunter, read this session —
`_workspace_index_put()` (spawn.py:3060) does load-mutate-save with no
locking, unlike `ROSTER`, which is wrapped in `_roster_locked()`
(`fcntl` flock, spawn.py:1760-1770). The hunter's reproduction spawned
20 concurrent `_workspace_index_put()` calls against distinct keys and
observed only 1 surviving entry afterward — a classic unlocked
read-modify-write race, independent of Findings 1-3's repo-scoping
question. `_workspace_index_put()`'s same-key collision guard
(spawn.py:3077-3081) only catches a collision visible within one
process's own load; it does nothing for two processes (an observer and
a fixture it spawns) racing to load, mutate distinct keys, and save —
whichever saves last silently discards the other's key. This means even
a step-2 fix that correctly threads `-C`/repo scoping through
`WORKSPACE_INDEX` (closing Finding 2) would still be exposed to this
independent concurrent-write data-loss path unless that fix also adds
locking equivalent to `ROSTER`'s.

## Open findings

Finding 4 above is a defect independently reproduced by this session's
dispatched warrant-hunter, additional to and independent of the #855
finding-5 collision this survey was scoped to pin (Findings 1-3). Route
to issue #857 step 2 (implementation) alongside Findings 1-3, or to a
new backlog item, per spec §6. Formal severity assignment
(`verify:severity-classification`) is later work, gated on approval.

## What did not work

None.

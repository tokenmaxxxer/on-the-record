---
issue: 2557
role: architecture
author: architecture
code_under_review: docs/issue-2548/reports/architecture.md
loop_state: landed
type: design-amendment
breaking: false
upstream:
  - path: docs/issue-2548/reports/architecture.md
    sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019
  - path: docs/decisions/2026-08-11-remove-role-session-sandbox.md
    sha: 51599adabaa31e14549a468ea4eaf91ed993d73c
decision_id: issue-2557-write-scope-declaration-ledger
context: >
  #2548's Step D (drop the spawn_roles.json fallback so write_scope
  always comes from the roster) cannot land: the roster is a liveness
  registry popped at session end (roster.py:166), and its only consumer
  (gates/ci.py:623) runs after the session that would have populated it
  is gone. This amendment answers the issue's five questions and
  restates Step D against a persisted-declaration design that survives
  session end without landing the declaration in the PR artifact itself.
considered_options:
  - keep-write_scope-inside-the-roster-entry-and-stop-popping-it (rejected — conflates two different lifetimes, see Question 4)
  - persist-in-PR-artifact-branch-frontmatter-trailer (ruled out by the issue's own constraint — self-attestation inside the material under review)
  - reintroduce-spawn_roles.json-role-keyed-table (ruled out — issue non-goal, also reintroduces alt-B rejected in #2548)
  - new-append-only-write_scope-declaration-ledger-plus-before_head-ancestor-binding (chosen)
outcome: accepted
---

# issue-2557 — architecture record

skill-verdict: work-in-english — applied: invoked; this record and all
repo-bound content (branch, commits, this document) written in English per
the skill, since the spawning task communicated substantially in Korean.
skill-verdict: technical-feasibility-spike-report — not-applicable: this is
an architecture design-amendment record, not a feasibility role's `probing`
state awaiting a timeboxed spike verdict.

## What was done

canonical: `gh issue view 2557` (read this session, full text in the
Ask/gap/constraint/questions this record answers below).
Read the landed design under review (`docs/issue-2548/reports/
architecture.md`, sha `c0c180e0`) and re-verified every file:line
citation it makes for the write_scope mechanism against today's code
(`roster.py`, `spawn.py`, `gates/gates.py`, `gates/ci.py`, `plumbing.py`,
`events.py`, all read this session), then executed the one check the
issue requires be run rather than read (Question 2). No code changed —
`docs/issue-2548/reports/architecture.md` itself is untouched; this is a
standalone amendment record, per the issue's "deliverable is an
amendment to that design document, not code."

### Question 1 — where does the declaration persist so it is readable at `gates/ci.py:623` time, after the session has ended?

canonical: `roster.py:166-173` (read this session):

```python
def roster_remove(key: str) -> None:
    with _sp._roster_locked():
        d = _sp._roster_load()
        entry = d.pop(key, None)
        if entry is not None:
            _sp._roster_save(d)
    # 이슈 #2215: 세션 종료 시 체크포인트 ref 정리 — push/PR 에 새지 않게
```

Today `write_scope` does not persist past session end at all — that is
the gap. Step A (#2551, landed) put `write_scope` inside the same roster
dict entry `roster_remove()` deletes wholesale above: `d.pop(key, None)`
has no field-level awareness of `write_scope`, it deletes the whole
entry. canonical: `gates/ci.py:618-623` (read this session, quoted in
full under Question 5) — that check runs against a pushed PR, after the
spawned session process has already exited and already called
`roster_remove()`, so whatever Step A wrote is already gone by the time
this check runs.

canonical: `plumbing.py:327-334` (read this session):

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

Proposed persistence location: a new append-only file,
`runs/write_scope_ledger.jsonl`, sibling to the existing
`runs/ledger.jsonl` shown above — same file family, same "gitignored,
measurement data, not source" character. canonical: `spawn.py:3499` and
`spawn.py:3636` (grep this session: both lines read
`**_bootstrap_write_scope(role)` / call it, inside the same dict-literal
block that also calls `roster_register`) — the ledger write would sit at
those same two call sites, as an addition alongside the existing
roster-entry write, not a replacement of it: the roster keeps its
in-flight copy for any live-session consumer (Step E), the ledger is the
copy Step D's reader would trust. Proposed entry shape: `{key, issue,
role, write_scope, before_head, ts}` — `key` is the same
`lease_key(issue, role)` string Step B already uses to look the roster
up (`roster.py:129-140`, read this session); `before_head` is the field
`spawn.py` already captures — see Question 3.

canonical: `spawn.py:44` (read this session):

```python
ROOT = Path(__file__).resolve().parent
```

derived: `python3 -c "import sys; sys.path.insert(0,'.'); import spawn as _sp; print(_sp.STATE_ROOT); print(_sp.ROSTER)"`
— result: `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2557-architecture/runs`
then `/home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2557-architecture/runs/active.json`,
i.e. `STATE_ROOT`/`ROSTER` resolve relative to `spawn.py`'s own file
location (`ROOT`, quoted above), not to any `work`/`repo` argument a
caller supplies. canonical: `gates/gates.py:899-919`'s
`_import_spawn_for_roster()` (read this session) imports `spawn` via
`Path(__file__).resolve().parent.parent` — relative to `gates.py`'s own
checkout, i.e. the orchestrator's own on-the-record checkout, never the
reviewed repo's `work` path. This is why `gates/ci.py:623`'s call can
see the same `runs/` a role session spawned from that same checkout
wrote to: both resolve the identical `ROOT`. A new reader (successor to
`_roster_write_scope()`, `gates/gates.py:931-964`, read this session)
would read `runs/write_scope_ledger.jsonl` from that same `ROOT` at CI
time, after the session that wrote it has exited — the file, unlike the
roster dict, is never popped by `roster_remove()` (verified by reading
`roster.py:166-173` above in full: its only statements touch `_sp.ROSTER`).

### Question 2 — is that location writable by a role session? (executed check)

Executed, not read. From this very session — a session-shaped context,
analogous to a role session spawned from this same checkout, not the
orchestrator — I called the exact function the spawner itself calls to
persist a roster entry, with an arbitrary, self-declared, maximally wide
`write_scope`:

canonical: command run this session, literal output reproduced verbatim below.

```
$ python3 -c "
import sys; sys.path.insert(0,'.')
import spawn as _sp
import roster
key = 'fake-role-session-2557'
entry = {'pid': 999999, 'role': 'implementation', 'issue': 2557,
         'write_scope': ['**/*'], 'ts': 0}
roster.roster_register(key, entry)
print('WRITE SUCCEEDED. roster path=', _sp.ROSTER)
print('contents now:', _sp.ROSTER.read_text())
"
WRITE SUCCEEDED. roster path= /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2557-architecture/runs/active.json
contents now: {
  "fake-role-session-2557": {
    "pid": 999999,
    "role": "implementation",
    "issue": 2557,
    "write_scope": [
      "**/*"
    ],
    "ts": 0
  }
}
```

The write succeeded, no credential, no permission check, no error.
canonical: `roster.py:159-163` (read this session) — `roster_register()`
takes only `key` and `entry`; any process that can `import roster` (a
plain repo-relative module, not a privileged API — every role session
can) may call it directly, exactly as the spawner does at `spawn.py:3499`
/`spawn.py:3636`. There is no code-level distinction between "the
spawner wrote this" and "the session wrote this" — they are the same
function call, confirmed by the transcript quoted above.

derived: `grep -n "chown\|chmod\|setuid\|seteuid\|os.geteuid\|container\|sandbox\|docker\|namespace\|jail\|cgroup" spawn.py roster.py plumbing.py`
— result: no matches in any of the three files (this session's actual
grep, not an assumption that sandboxing prevents the write above).

canonical: `docs/decisions/2026-08-11-remove-role-session-sandbox.md:38-41`
(read this session; `git log --follow` on this path returns commits, so
it is a tracked, real file):

```
## Decision

`role_settings()` (`pipeline.py`) now forces `sandbox.enabled = False`
centrally, regardless of what any individual `roles/*.json` says.
```

canonical: `docs/issue-2548/reports/architecture.md:414-419` (read this
session) independently cites the same decision record for the same
conclusion — role sessions run unsandboxed by deliberate, already-landed
choice, not by gap or oversight. Role sessions therefore run as the same
OS user, in the same filesystem, with the same Python module access as
the orchestrator process that spawns them; there is no OS-level or
process-level boundary anywhere in `spawn.py`, `roster.py`, or
`plumbing.py` (all three greped above) that would stop a role session
from writing directly to `runs/active.json` — demonstrated above — and
because the Question 1 ledger would be written through the same kind of
plain, uncredentialed function (`ledger_write()`, `plumbing.py:327-334`,
quoted under Question 1), nothing stops a role session from writing
directly to `runs/write_scope_ledger.jsonl` either. Relocating the
declaration from the roster entry to a separate ledger file fixes the
Question 1 and Question 4 lifetime gap; it does not fix writability.
That gap is real and this amendment does not close it — see Open
finding 1.

### Question 3 — how does CI know the persisted declaration belongs to this PR?

canonical: `gates/gates.py:988` (read this session) — `role_scope()`
already parses `(issue, role)` out of the branch via
`BRANCH_ROLE.match(branch)` and looks up `lease_key(issue, role)`
(`roster.py:129-140`); that part of the binding is unavoidable (CI has
nothing but the branch/PR to start from) and already landed in Step B.
The weakness the issue flags: a session that can push commits to (or
open a PR from) a branch matching that key pattern can present any
commits under a declaration it did not originally earn, including a
stale, wider one left behind by an earlier spawn on the same `(issue,
role)` pair. canonical: `roster.py:159-163` (quoted under Question 2) —
`roster_register()` does `d[key] = entry`, an unconditional overwrite,
so re-spawning the same role on the same issue (an ordinary remediation
retry) already silently replaces one ledger candidate with another under
the identical key.

The proposed binding adds a second, spawner-authored, immutable
condition beyond the key match: the ledger entry's `before_head` — the
git HEAD the spawner captured before the child process was forked — must
be an ancestor of the PR's actual head commit.

canonical: `spawn.py:3418` (read this session):

```python
before_head = _git_head(cwd) if issue is not None else None
```

canonical: `events.py:55` (read this session) defines `_git_head`. This
line runs in the spawner's own process, before `Popen()` hands control
to the session — canonical: `spawn.py:3480-3499` (read this session)
contains the same in-file comment the landed design already relies on
for the roster-registration ordering: "이슈 #908: fork-child 설정...과
Popen() 은 첫 roster_register/session-start... 이전에 실행된다." A
session cannot retroactively change the SHA its own branch forked from
without rewriting its own branch's history out from under the PR it
opened — a separately visible red flag, out of this amendment's scope.
canonical: `spawn.py:968` (read this session) — `before_head` is already
trusted for an analogous ancestor-style check today
(`_is_new_commit(work, entry.get("before_head"), after_head)`, watchdog
signal 4), so this proposal reuses an established mechanism rather than
inventing new session-writable material.

At CI time: for a given `(issue, role)` key, the reader would select,
among ledger entries whose `before_head` is an ancestor of the PR's
current head (`git merge-base --is-ancestor <before_head> <head>`), the
one with the latest `ts`. derived: reasoning, not yet implemented code —
no ledger or reader exists in the checkout today; `git log --follow`
on `runs/write_scope_ledger.jsonl` returns nothing because the path does
not exist (this session, `runs/` is gitignored per `.gitignore:1`, read
this session). No qualifying entry (the ordinary case for a branch whose
declaration was never durably persisted for this exact history) is not
a special case — it falls into Step B's existing "no write_scope
declared" fail-closed path, unchanged (`gates/gates.py:1000`, quoted
under Question 5). This binding does not touch the branch name, PR
frontmatter, or a commit trailer — the key is still the same `(issue,
role)` string Step B already derives from the branch, and the added
condition is spawner-written data the session cannot retroactively edit,
satisfying the issue's constraint against self-attestation inside the
material under review.

### Question 4 — does `roster_remove()` keep deleting liveness state while the declaration survives, and what distinguishes the two lifetimes in code?

Today: nothing distinguishes them, because there is only one entry and
one deletion path, quoted in full under Question 1
(`roster.py:166-173`). canonical: `gates/gates.py:936-939` (read this
session) — `_roster_write_scope()`'s expiry check (`if expires_at is not
None and time.time() > expires_at: return None`) already treats an
expired-but-still-present lease as "no live declaration" and falls back
correctly; that is the case the landed design covered. Deletion is a
different case: a *deleted* entry reads back as a plain dict miss,
indistinguishable in code from a role that never declared anything —
`_roster_write_scope()` has no way to tell "this key was popped at
session end" from "this key never existed."

Proposed distinction going forward: `roster_remove()`
(`roster.py:166-173`, quoted under Question 1) keeps its current
behavior verbatim — it continues to pop only the liveness dict
(`_sp.ROSTER`, i.e. `active.json`) that Step E's board/heartbeat/
watchdog consumers already read, and gains no new code path into
`runs/write_scope_ledger.jsonl`; the function's only three statements
(`_roster_load()`/`d.pop()`/`_roster_save()`, all against `_sp.ROSTER`)
are exhaustively quoted above. The declaration in the proposed ledger is
append-only and outlives the session by construction — it is never
written into the structure `roster_remove()` deletes — not by carving a
new exemption into `roster_remove()` itself. The two lifetimes become:
liveness (roster dict, mutable, popped at session end, unchanged from
today) and declaration (ledger, append-only, never popped — GC is a
separate, explicitly deferred concern, see Open finding 2).

### Question 5 — restate Step D with its failure mode

**Step D (restated) — `gates.py:role_scope()` stops falling back to
`spawn_roles.json[role].write_scope`; the only source is the persisted
declaration: the roster entry for a live session, or the ledger lookup
bound by `(issue, role)` key plus `before_head` ancestry (Question 3)
for the case that matters here — a PR checked after the session ended.**

canonical: `gates/ci.py:618-623` (read this session):

```python
    if pr is not None:
        branch = _pr_head_ref(repo, pr)
        if branch is None:
            bad.append(f"PR #{pr} 의 head 브랜치를 읽을 수 없다 (fail closed)")
        else:
            bad += gates.role_scope(repo, branch)
```

What breaks if Step D lands alone — before the ledger from Questions 1
and 3 exists and is wired as `_roster_write_scope()`'s fallback of last
resort — is exactly the failure the issue measured and this amendment
starts from: every check above runs after the session has exited, so the
roster dict `_roster_write_scope()` reads is already empty.

derived: `python3 -c "import sys; sys.path.insert(0,'.'); import spawn as _sp; d = _sp._roster_load(); print('roster entries:', len(d), 'contents:', d)"`
— result: `roster entries: 0 contents: {}` (this session, no session
running).

With the `spawn_roles.json` fallback removed and no ledger wired in,
`_roster_write_scope()` returns `None` for every branch — canonical:
`gates/gates.py:955-964` (read this session): `entry =
spawn._roster_load().get(key)` finds nothing against the empty dict
measured above, `if entry is None: return None` — and `role_scope()` has
nothing left to fall back to:

```python
# gates/gates.py:992-1000 (read this session)
    allowed = _roster_write_scope(branch, role)
    if allowed is None:
        try:
            role_cfg = _role_cfg(role)
        except (OSError, json.JSONDecodeError, KeyError) as e:
            return [f"역할 정의를 읽을 수 없어 write_scope 를 검사할 수 없다: "
                    f"{_ROLE_DATA_PATH} 의 {role!r} (on-the-record 체크아웃: {ON_THE_RECORD_ROOT}) ({e})"]
        if "write_scope" not in role_cfg:
            return [f"{_ROLE_DATA_PATH} 의 {role!r} 에 write_scope 선언이 없다 (fail closed)"]
```

derived: reasoning from `gates/gates.py:992-1000` and `gates/ci.py:
618-623`, both quoted directly above (read this session, no code
executed for this specific projection since Step D is not landed in
this checkout to run against) — removing the fallback means this branch
either reads a now-pruned `spawn_roles.json` role entry or is changed to
reach the fail-closed message directly; either way, called from
`gates/ci.py:623`'s `bad += gates.role_scope(repo, branch)` inside `if
pr is not None:`, the message `"{role!r} 에 write_scope 선언이 없다
(fail closed)"` (`gates/gates.py:1000`, quoted above) fires for every
branch on every PR unconditionally, because the roster measured 0
entries above and, with Step D landed alone, there is no other source
left. `bad` is non-empty for every PR; the required status check
(`gates/ci.py:623`'s caller) fails closed on all of them — a repo-wide
write freeze, not the single-role, loud-refusal-on-a-genuinely-stale-
branch scenario the original Step D restatement described.

canonical: `docs/issue-2548/reports/architecture.md:497-502` (read this
session):

```
What breaks if Step D lands before every live spawn path already writes
the roster field (i.e. before Step C is fully rolled out): a session on
an old code path has no roster `write_scope` and no fallback, hitting
the same fail-closed message quoted under Authorization on its first
commit — loud, not silent, and the deliberate final tightening the
fail-closed correction asks for.
```

That restatement's precondition — every live spawn path already writes
the roster field — is necessary but no longer sufficient: Step A/C are
landed per this checkout's own commit log (`git log` shows `issue-2555`,
`issue-2553`, `issue-2551` merged, recent-commits list at session start),
so every live spawn path already writes the roster field today, and Step
D would still fail closed on everything, because the field it writes
does not survive to CI time (Questions 1 and 4). This amendment's
precondition for Step D is stricter: the ledger (Questions 1 and 3)
exists, is populated at the same call sites Step A already populates,
and the fallback order in `_roster_write_scope()`'s successor is
roster-entry-if-live, then ledger-entry-bound-by-`before_head`, then
nothing. Only then does removing the `spawn_roles.json` fallback produce
the loud, single-branch refusal the fail-closed correction asks for,
instead of the repo-wide one demonstrated above.

## Why

canonical: `spawn.py:3499`/`spawn.py:3636` (quoted under Question 1) and
`gates/ci.py:618-623` (quoted under Question 5), both unchanged by this
amendment. The gap is a scope-persistence bug, not an authorization-
design bug: the landed design chose the right owner (the spawner, not
the session — already settled per this issue's own framing) and the
right check (`gates/ci.py:623`), but picked a storage location (inside
the same dict `roster_remove()` deletes wholesale) whose lifetime is
shorter than the consumer's read time. The fix keeps the owner and the
check exactly as landed and only changes where the already-correct
declaration is written down — from inside the liveness dict to a durable
ledger the liveness dict's deletion never touches — plus one added
binding condition (`before_head` ancestry) so the persisted copy cannot
be attributed to a PR it was not minted for.

I chose the ledger-plus-`before_head` design over the other
`considered_options` because: keeping `write_scope` in the roster and
simply not popping it would conflate liveness and declaration lifetime
forever, the exact confusion Question 4 asks to resolve, not preserve;
the three PR-artifact locations (branch, frontmatter, commit trailer)
are the issue's own explicit exclusion, because a session that can edit
its own declared scope inside the material under review can widen it;
and a role-keyed table (`spawn_roles.json`-shaped) is the issue's own
non-goal and is the same alt-B the original design already rejected.

### Checked against #2548's own prior corrections

Two corrections the landed design already made must not be reintroduced.

**1. `write_scope` must be fail-closed (absence/ambiguity to deny, never
allow).** canonical: `gates/gates.py:1000` (quoted under Question 5) —
every new path this amendment adds terminates in the existing
fail-closed message unchanged: no ledger match falls through to Step B's
current message exactly as a roster miss does today (Question 3's
"before_head ancestry fails to find an entry" case is treated
identically to no entry at all); nothing in this amendment adds a new
default-allow branch anywhere in `role_scope()`.

**2. No role-to-skill mapping table.** This amendment does not add one.
canonical: `roster.py:129-140` (quoted under Question 1) — the proposed
ledger is keyed by the same per-spawn `lease_key(issue, role)` string
Step B already uses, and canonical: `spawn.py:77-99` (`_bootstrap_write_
scope()`, read this session) — it is populated, per spawn event, from
the same already-resolved `write_scope` value that function already
computes from `spawn_roles.json`/`role_data()` today. It relocates where
that already-resolved value is durably written; it does not add a second
static role-or-skill-keyed table.

```
canonical: docs/issue-2548/reports/architecture.md:582-587 (read this session)
- **alt-B, a role-to-skill mapping table** — rejected per the issue's
  own correction and the Consumers-item-c measurement above:
  role-to-skill cardinality is many-to-one in the roles-to-skills
  direction (most roles map to more than one skill), so any table keyed
  by role-or-slug on one side and skill on the other reintroduces a
  closed axis this design retires.
```

## Upstream basis

canonical: `docs/issue-2548/reports/architecture.md` (sha `c0c180e0`,
this amendment's `code_under_review`, read this session) — Steps A-C
landed and stay unchanged; this amendment only restates Step D and adds
the persistence mechanism Step D would depend on. canonical:
`docs/decisions/2026-08-11-remove-role-session-sandbox.md` (sha
`51599ada`, read this session) — the decision record confirming role
sessions run unsandboxed, load-bearing for Question 2's answer.
canonical: `gh issue view 2557` (read this session) — the direct spec
for what this record must answer; its Ask/gap/constraint/five-questions
text is reproduced piecewise across the sections above.

## Open findings

1. **Writability (Question 2) is not closed by this amendment.**
   canonical: Question 2's executed write transcript above (this
   session) — relocating the declaration to a ledger fixes the lifetime
   gap (Questions 1 and 4) but not the authorization gap: nothing in
   `spawn.py`/`roster.py`/`plumbing.py` today stops a role session from
   calling `ledger_write()`-shaped functions itself, since role sessions
   run unsandboxed and same-uid as the orchestrator. Closing this fully
   requires an OS/process-level boundary (a distinct uid for role-session
   processes, filesystem permissions on `runs/write_scope_ledger.jsonl`
   that only the orchestrator's own uid can write, or a mediating write
   API rather than direct file access) that does not exist anywhere in
   this codebase today (derived: the same three-file grep under Question
   2 found none) and is out of this amendment's scope — design amendment,
   not implementation. Resolution path: a follow-up issue scoped to
   process/privilege separation for spawned sessions, a prerequisite to
   treating Step D as fully closing the authorization boundary the
   original issue #2557 describes ("somewhere the session cannot
   write"). Until that lands, this amendment's ledger is only as
   trustworthy against forgery as the roster is today — better lifetime,
   same writability exposure.
2. **Ledger growth/GC.** An append-only `runs/write_scope_ledger.jsonl`
   grows without bound unless pruned. canonical: `roster.py:` reconcile-
   ledger TTL machinery (`plumbing.py:300-312`, read this session) shows
   an existing TTL-dedup pattern in this codebase this proposal could
   reuse, but this amendment does not design the concrete GC policy for
   the new file — flagged as a follow-up, not a Step D blocker, since an
   unbounded-but-still-correct ledger fails safe (more candidates to
   ancestor-check under Question 3, not fewer), not fail-open.
3. **Multiple qualifying ledger entries under one `(issue, role)` key.**
   The "latest `ts` among `before_head`-ancestor-qualifying entries" rule
   (Question 3) is this amendment's proposed tie-break; it has not been
   tested against every remediation-retry shape in the live system (for
   example a rejected-then-resubmitted PR that reuses the same branch
   without a fresh `before_head`). Flagged for the implementation role to
   verify against `docs/issue-2548/reports/architecture.md`'s own
   remediation-cycle assumptions before Step D lands.

## What did not work

None.

## Next steps

canonical: Open findings 1-3 above (this session's own analysis) —
implementation role should land a ledger-writing step parallel to Step
A's existing `_bootstrap_write_scope()` call sites (`spawn.py:3499`/
`3636`, quoted under Question 1), then extend `_roster_write_scope()`/
`role_scope()` (`gates/gates.py:931-1006`) with the ledger plus
`before_head`-ancestry fallback described under Question 3, before Step
D removes the `spawn_roles.json` fallback, per Question 5's restated
precondition. Open finding 1 (writability) should be raised as its own
follow-up issue rather than assumed solved by this amendment.
`loop_state` for this record is terminal (`landed`): the five questions
are answered with the citations and executed check above, and no further
drafting is expected on this specific record; the design work it hands
off (ledger, binding, Step D sequencing, and the writability follow-up)
is future work tracked under Open findings, outside this record's own
loop.

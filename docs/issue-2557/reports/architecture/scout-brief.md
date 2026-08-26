# issue-2557 — architecture scout brief (phase 1)

Scope: this issue amends one lifetime detail of an already-landed,
already-scouted internal design (`docs/issue-2548/reports/
architecture.md`, sha `c0c180e0`, read this session) — where a value
persists and how it is bound to a PR. It is not a new external category
that needs field survey against outside prior art.

## Internal analogues canvassed this session

Three internal patterns already exist in this codebase and cover the
shape this amendment needs, all read directly this session (also
inventoried in this issue's phase-1 survey note, written alongside this
brief):

- **Append-only durable store**: `plumbing.py:327-334`'s `ledger_write()`
  — a `runs/*.jsonl` file that is never touched by `roster_remove()`
  (`roster.py:166-173`, read this session — its only statements act on
  `_sp.ROSTER`). The amendment's proposed `runs/write_scope_ledger.jsonl`
  reuses this shape rather than inventing a new storage primitive.
- **Spawner-captured immutable ancestor field**: `spawn.py:3418`'s
  `before_head = _git_head(cwd) if issue is not None else None`, already
  read by `spawn.py:968`'s `_is_new_commit()` for an analogous
  ancestor-style comparison (watchdog signal 4). The amendment reuses
  this field for PR-binding rather than minting a new identity
  mechanism.
- **Per-spawn key shape**: `roster.py:129-140`'s `lease_key(issue,
  disambiguator)`, already the join key `gates/gates.py:931-964`'s
  `_roster_write_scope()` uses today. The amendment keeps this key
  unchanged.

## Why no external scouting round

The three items above are internal, already-in-production code in this
same repository, not an unfamiliar category (unlike, for example, a new
third-party auth provider or a new external protocol) — there is no
external design space to survey. `docs/issue-609/proposals/
architecture.md` (read this session; a prior architecture record tracked
in this repository) sets the precedent for this disposition on a
comparably narrow, internally-scoped issue: "the spec... already fixes
every design-relevant choice this role would otherwise scout for...
leaving architecture with a placement/wiring decision inside an
already-scouted, already-merged internal pattern... not a new external
category needing a fresh field survey." The same reasoning applies here:
`docs/issue-2548/reports/architecture.md` (sha `c0c180e0`, read this
session) already scouted and decided the write_scope
ownership/authorization shape; this amendment only relocates where one
already-decided value is stored and adds one already-existing field
(`before_head`) as a binding key.

## Disposition

Scouting skipped for this phase. Reason: no design decision open outside
the placement/wiring choice covered by the internal analogues above —
same disposition as `docs/issue-609/proposals/architecture.md`'s
precedent, cited above.

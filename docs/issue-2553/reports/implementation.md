---
issue: 2553
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2548/reports/architecture.md
    sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019
  - path: docs/issue-2551/reports/implementation.md
    sha: ea6a064640d4c4a7297b7c5b0236e7fa951ca516
code_under_review:
  - gates/gates.py
  - on-the-record/gates/gates.py
type: feat
breaking: none — additive read path only; the JSON-fallback branch and its
  refusal text are byte-identical before/after for every roster-miss/roster-
  absent case (acceptance criteria 2 and 5 below), so no branch that used
  spawn_roles.json alone before this change behaves differently now
verdict: pass
---

# issue-2553 — implementation record

skill-verdict: work-in-english — applied: invoked; all code, comments, commit
messages, PR title/body, and record content written in English
skill-verdict: defect-verification-independence-from-upstream-verdicts —
not-applicable: this is fresh implementation work, not re-verification of a
prior Present/closed_checks verdict

## What was done

Step B of the eight-step role-axis removal
(`docs/issue-2548/reports/architecture.md`, section `### Order`, Step B
paragraph): `gates/gates.py:role_scope()` now reads `write_scope` from the
roster entry first, via `spawn.lease_key(issue, role)`, falling back to
`spawn_roles.json` only when the roster lookup can't supply a value (miss,
expired lease, or entry present without a `write_scope` key).

```
derived: git diff --stat gates/gates.py on-the-record/gates/gates.py
 gates/gates.py               | 112 +++++++++++++++++++++++++++++++++++++------
 on-the-record/gates/gates.py | 112 +++++++++++++++++++++++++++++++++++++------
 2 files changed, 196 insertions(+), 28 deletions(-)
```

Concretely, in `gates/gates.py` (byte-identical change mirrored into the
packaged copy `on-the-record/gates/gates.py`, matching the existing
sync-both-copies convention this repo already uses for this file — canonical:
`gates/gates.py`/`on-the-record/gates/gates.py`, `diff -q` confirms the two
files are byte-identical this session):

- `gates/gates.py:874` adds `_BRANCH_ISSUE = re.compile(r"^issue-(\d+)/")` —
  a second, narrower regex used only to pull the integer issue number back
  out of the branch for the roster lookup (`spawn.lease_key(issue, role)`
  needs an `int`). `BRANCH_ROLE` (`gates/gates.py:868`) itself is untouched,
  same pattern, same single capture group, per the issue's explicit "branch
  shape stays unchanged" boundary.
- `gates/gates.py:902-929` adds `_import_spawn_for_roster()`, a lazy,
  memoized import of `spawn.py` (the re-export point for `roster.py`'s
  `_roster_load`/`lease_key`) — the same sys.path-then-import-spawn idiom
  `gates/ci.py`, `gates/flows.py`, `gates/merge_gate.py` and five other
  `gates/*.py` siblings already use (`grep -n "^import spawn" gates/*.py`
  shows the existing pattern this session), but performed inside a function
  instead of at module level, and returning `None` on `ImportError` instead
  of raising. This is the new `roster.py` coupling the architecture
  record's Authorization section named as "a deliberate new coupling,
  introduced in Step B" — made lazy for the reason logged under "What did
  not work" below.
- `gates/gates.py:931-964` adds `_roster_write_scope(branch, role) ->
  list[str] | None`: looks up `spawn._roster_load()[spawn.lease_key(issue,
  role)]`, returns `None` (→ caller falls back to `spawn_roles.json`) on any
  of: `spawn.py` unreachable from this `gates.py` copy's location, no
  parseable issue number, roster miss, an expired lease
  (`lease_expires_at is not None and time.time() > lease_expires_at`, the
  same guarded comparison `roster.py:402-406`'s `lease_reconcile_sweep()`
  already uses for the identical field), or a present entry with no
  `write_scope` key. Otherwise returns `list(entry["write_scope"])` as-is —
  including an empty list, checked via `"write_scope" not in entry`, never
  by truthiness, so a declared-empty roster scope is never confused with
  "not declared."
- `gates/gates.py:967-1008` (`role_scope()`) calls `_roster_write_scope()`
  first; only when it returns `None` does the function run the original
  `_role_cfg()` / `_write_scope_overrides()` / `spawn_roles.json` lookup,
  byte-identical to the pre-change code in that branch. `_always_writable()`
  is still appended unconditionally after either source, unchanged, so the
  issue-149 "record duty always survives" invariant holds for both sources.

## Why

The design (`docs/issue-2548/reports/architecture.md`, Step B paragraph)
requires the roster to be the first-checked source and `spawn_roles.json` to
be reached only "on a roster miss," with an expired lease "treated as 'no
`write_scope` declared.'" This is safe to land now — and only now — because
Step A (issue #2551, PR #2552) already populates the roster's `write_scope`
field on every spawn; landing this reader before Step A would have made
every roster lookup miss and, since `write_scope` is fail-closed
(`gates/gates.py:915-916`'s message, unchanged by this diff), frozen every
commit on every branch. That ordering constraint, and Step A's own
"absent-key vs empty-list" distinction, are cited verbatim as this step's
starting state.

The one judgment call the issue calls out — collapsing "absent key" and
"empty list" into one code path — is avoided by checking key presence
(`"write_scope" not in entry`) rather than truthiness anywhere in
`_roster_write_scope()`; an empty list survives the `None`-vs-list branch
in `role_scope()` and is used as-is, so it refuses every file the diff
touches outside `_always_writable()`'s paths. Acceptance criterion 3 below
is the executed proof this distinction actually holds in the shipped code,
not just in the reasoning above.

The override file `docs/specs/write_scope.md` (untracked in this repo,
same as the architecture record found — derived: `git ls-files | grep -i
write_scope.md` returns nothing) is read by `_write_scope_overrides()`
(`gates/gates.py` — retired in Step D per the architecture record's note
under Authorization) and is left applying only inside the
`spawn_roles.json` fallback branch, unchanged in shape and untouched by
this diff — the issue's scope boundary explicitly excludes touching that
mechanism, and this design doesn't extend it to the new roster-sourced
branch either, since doing so would be new behavior the issue didn't ask
for.

## What did not work

One deviation from the original plan, caught and fixed within this session
before landing: the first version of this change put `import spawn` at
`gates/gates.py`'s module top level (`sys.path.insert(0,
str(Path(__file__).resolve().parent.parent)); import spawn`), matching the
pattern `gates/ci.py`/`gates/flows.py` use. That broke a consumer this
step's own scope review had not traced: `on-the-record/hooks/record-claim-
guard.sh` (a PreToolUse write-time hook, executed in-process by
`on-the-record/hooks/pretooluse_dispatcher.py`) loads `on-the-record/gates/
record_lint.py`, which does its own sibling-load of `on-the-record/gates/
gates.py` at import time — a *second*, packaged copy of `gates.py` whose
location is two directories below the real repo root that holds `spawn.py`,
not one. The eager top-level `import spawn` computed
`Path(__file__).resolve().parent.parent` from *that* location, which has no
`spawn.py`, and raised `ModuleNotFoundError` the moment `record_lint` (and
therefore `gates.py`) was imported — even though nothing in that call path
ever invokes `role_scope()`. Reproduced directly this session, derived: an
actual `Write` attempt to this record file with the eager-import version of
`gates/gates.py` still live in the working tree:

```
PreToolUse:Write hook error: [.../on-the-record/hooks/pretooluse-dispatcher.sh]:
record-claim-guard: gates module could not be imported
```

Fix: moved the `spawn.py` import into a new lazy, memoized helper,
`_import_spawn_for_roster()` (`gates/gates.py:902-929`), called only from
inside `_roster_write_scope()` — so it only ever runs when `role_scope()`
itself is actually invoked, and returns `None` (→ JSON fallback) instead of
raising if `spawn.py` isn't reachable from wherever this `gates.py` copy was
loaded. Re-verified against the actual failure mode this session (loading
`on-the-record/gates/record_lint.py` from a `sys.path` state that excludes
the repo root, matching how the in-process hook dispatcher invokes it),
derived: `python3 /tmp/repro_rcg.py` (chdir to `/tmp` first, only
`on-the-record/gates/` on `sys.path`):

```
record_lint imported OK, gates module: <module '_on_the_record_gates_sibling_impl' from '.../on-the-record/gates/gates.py'>
role_scope callable: <function role_scope at 0x75b0e72cb910>
```

Also re-ran the full acceptance script against the fixed code, derived:
`python3 /tmp/verify_2553.py` — output unchanged, full text quoted under
"Acceptance evidence" below.

## Acceptance evidence

All five checks below were run via one script,
`derived: python3 /tmp/verify_2553.py` (throwaway, not committed — no
existing test file covers `role_scope()` today, confirmed this session:
`derived: grep -rln "role_scope" test/ tests/ 2>/dev/null` → no output).
The script builds a fresh throwaway git repo per scenario (`git init`, an
initial commit, `refs/remotes/origin/main` pointed at it so
`changed_files()`'s `origin/main...HEAD` diff resolves, then the scenario's
branch checked out with one commit touching the file under test), points
`spawn.ROSTER` (via the module `gates._import_spawn_for_roster()` returns)
at a throwaway roster file seeded with the scenario's roster entry (or an
empty/missing one), and calls the real `gates.role_scope(work, branch)`
loaded fresh from the actual `gates/gates.py` in this checkout each time
(`importlib.util.spec_from_file_location`, no mocking of `role_scope()`'s
internals). The full run (executed this session, exit 0, all in-script
`assert` statements raised nothing, final printed line "ALL ASSERTIONS
PASSED" — derived: `python3 /tmp/verify_2553.py`):

```
###### Criterion 1: roster is the real source, proven by disagreement ######
=== 1a roster-allows / JSON-would-refuse (docs/onlyme/** vs src/**) ===
  branch='issue-3001/implementation' touched='docs/onlyme/x.txt'
  roster={'issue-3001/implementation': {'write_scope': ['docs/onlyme/**']}}
  result=[]
=== 1b roster-refuses / JSON-would-allow (docs/onlyme/** vs src/**) ===
  branch='issue-3002/implementation' touched='src/x.py'
  roster={'issue-3002/implementation': {'write_scope': ['docs/onlyme/**']}}
  result=['write_scope 이탈: src/x.py (역할 implementation, 허용: docs/onlyme/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']

###### Criterion 2: out-of-scope diff still refused, before vs after ######
=== 2 AFTER (current code, roster miss -> JSON fallback) ===
  branch='issue-3003/implementation' touched='docs-out-of-scope.txt'
  roster={}
  result=['write_scope 이탈: docs-out-of-scope.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']

=== 2 BEFORE (pre-change gates.py, git-stashed) ===
  branch='issue-3003/implementation' touched='docs-out-of-scope.txt'
  result=['write_scope 이탈: docs-out-of-scope.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']

###### Criterion 3: absent key vs empty list -> different outcomes ######
=== 3a absent write_scope key in roster entry (falls back to JSON, src/** allowed) ===
  branch='issue-3004/implementation' touched='src/x.py'
  roster={'issue-3004/implementation': {'pid': 1, 'role': 'implementation'}}
  result=[]

=== 3b write_scope: [] present in roster entry (declared empty -> refuse everything) ===
  branch='issue-3005/implementation' touched='src/x.py'
  roster={'issue-3005/implementation': {'pid': 1, 'role': 'implementation', 'write_scope': []}}
  result=['write_scope 이탈: src/x.py (역할 implementation, 허용: docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']

###### Criterion 4: expired lease treated as 'no write_scope declared' ######
=== 4 expired lease, write_scope present in roster (docs/onlyme/**) but lease expired ===
  branch='issue-3006/implementation' touched='docs/onlyme/x.txt'
  roster={'issue-3006/implementation': {'write_scope': ['docs/onlyme/**'], 'lease_expires_at': 1787748000.5955155}}
  result=['write_scope 이탈: docs/onlyme/x.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']

###### Criterion 5: roster miss falls back to spawn_roles.json, matches today ######
=== 5 AFTER (current code, roster miss, in-scope src/** file) ===
  branch='issue-3007/implementation' touched='src/x.py'
  roster={}
  result=[]

=== 5 BEFORE (pre-change gates.py, git-stashed) ===
  branch='issue-3007/implementation' touched='src/x.py'
  result=[]

ALL ASSERTIONS PASSED
```

### 1. Roster is the real source, proven by disagreement

acceptance: `python3 /tmp/verify_2553.py` — result:
scenario 1a seeds the roster entry for `issue-3001/implementation` with
`write_scope: ["docs/onlyme/**"]` — a value
`spawn_roles.json["implementation"]["write_scope"]` (`["src/**", "test/**",
"tests/**"]`) would refuse — and touches the fixture path 'docs/onlyme/x.txt'
(inside the script's own throwaway git repo, not a path in this repo); the
gate returns `[]` (permitted), which only the roster value explains.
Scenario 1b, same roster declaration, touches 'src/x.py' instead (again a
throwaway-fixture path) — a path the JSON value would permit — and the gate
refuses it (`write_scope 이탈: src/x.py ... 허용: docs/onlyme/**, ...`),
which only the roster value explains, since the refusal text's own "허용"
(allowed) list names `docs/onlyme/**`, not `src/**`. The two scopes disagree
by construction, and the enforced outcome tracks the roster value both
times, in both directions.

### 2. Out-of-scope diff is still refused, quoted before and after

acceptance: `python3 /tmp/verify_2553.py` — result:
same branch (`issue-3003/implementation`), same out-of-scope fixture path
('docs-out-of-scope.txt'), no roster entry (roster miss → JSON fallback in
both the current and the pre-change code, since the pre-change code never
reads a roster at all). AFTER (current code): `['write_scope 이탈:
docs-out-of-scope.txt (역할 implementation, 허용: src/**, test/**, tests/**,
docs/issue-*/reports/implementation.md,
docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**,
docs/issue-*/decisions/**)']`. BEFORE (`git stash push -- gates/gates.py
on-the-record/gates/gates.py`, re-run, then `git stash pop` — this session's
script does this automatically, derived: `git status --short` immediately
after the run showed the same two modified files and nothing else, i.e. the
stash left no residue): byte-identical list to AFTER. The two lists were
compared for exact equality inside the script itself (derived: `python3
/tmp/verify_2553.py`, the pair of `result=[...]` lines printed for "2 AFTER"
and "2 BEFORE" above are identical strings).

### 3. Absent key vs. empty list produce different outcomes

acceptance: `python3 /tmp/verify_2553.py` — result:
3a's roster entry (`issue-3004/implementation`) has no `write_scope` key at
all (`{"pid": 1, "role": "implementation"}`) — falls back to JSON, the
fixture path 'src/x.py' is allowed, result `[]`. 3b's roster entry
(`issue-3005/implementation`) has `write_scope: []` present — the gate
refuses 'src/x.py' (`write_scope 이탈: src/x.py (역할 implementation, 허용:
docs/issue-*/reports/implementation.md,
docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**,
docs/issue-*/decisions/**)` — note `src/**` is absent from the "허용" list
here, unlike 3a's JSON-sourced fallback). The two results above (`result=[]`
for 3a, `result=['write_scope 이탈: ...]` for 3b) are, by direct comparison,
not the same value — derived: `python3 /tmp/verify_2553.py`, the two
`result=` lines quoted above for 3a/3b.

### 4. Expired lease is treated as "no write_scope declared"

acceptance: `python3 /tmp/verify_2553.py` — result:
the roster entry for `issue-3006/implementation` declares `write_scope:
["docs/onlyme/**"]` (which would permit the touched fixture path
'docs/onlyme/x.txt' if used) together with `lease_expires_at` set to
`time.time() - 3600` (one hour in the past) — the same field and the same
`now > lease_expires_at` comparison `roster.py:402-406`'s
`lease_reconcile_sweep()` already uses to detect expiry (guarded by
`expires_at is not None`, reused identically in `_roster_write_scope()`,
`gates/gates.py:951-952`). The gate refuses the file (`write_scope 이탈:
docs/onlyme/x.txt (역할 implementation, 허용: src/**, test/**, tests/**,
...)`) — the "허용" list names `src/**`, the JSON fallback's value, not
`docs/onlyme/**`, proving the expired roster value was never consulted; the
gate fell through exactly as it does for "no `write_scope` declared."

### 5. Roster miss falls back to `spawn_roles.json`, matching today's exact behavior

acceptance: `python3 /tmp/verify_2553.py` — result:
`issue-3007/implementation` has no roster entry at all, diff touches the
fixture path 'src/x.py' (in scope per `spawn_roles.json`). AFTER (current
code): `[]`. BEFORE (pre-change code, `git stash`d as in criterion 2): `[]`
— the two `result=[]` lines quoted above for "5 AFTER" and "5 BEFORE" are
identical, derived: `python3 /tmp/verify_2553.py`. This is also the issue's
named empty-state case: a fresh issue with no roster entries yet.

## Upstream basis

`docs/issue-2548/reports/architecture.md` (issue #2548, PR #2550,
`sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019`), section `### Order`, the
Step B paragraph — the concrete spec this record implements against,
including the roster-first/JSON-fallback-on-miss ordering, the
expired-lease-as-no-declaration rule, and the "branch shape unchanged"
boundary.

`docs/issue-2551/reports/implementation.md` (issue #2551, PR #2552,
`sha: ea6a064640d4c4a7297b7c5b0236e7fa951ca516`) — Step A, the writer this
step depends on. canonical: `docs/issue-2551/reports/implementation.md`,
"Acceptance evidence" §4 (read this session) — quotes
`_bootstrap_write_scope()` (cited there as `spawn.py:56-78`) omitting the
`write_scope` key entirely (`{}`) for an undeclared role rather than writing
`{"write_scope": []}`: "role missing entirely: {}" / "role present, no
write_scope key: {}" — which is the exact absent-vs-empty distinction this
step's `_roster_write_scope()` reads back out via `"write_scope" not in
entry"`.

## Open findings

None — every acceptance check the issue lists ran clean this session, and
the scope boundaries (no `spawn_roles.json` fallback-internals changes, no
`docs/specs/write_scope.md` (untracked in this repo) override changes, no
slug/branch-shape changes) were kept: `_role_cfg()`,
`_write_scope_overrides()`, and `BRANCH_ROLE`
itself are unmodified in this diff (derived: `git diff gates/gates.py` shows
no hunk touching those three definitions' bodies, only `role_scope()`'s
control flow above them and two new, additive helpers/regex).

## Next steps

Step C (wire the slug into spawn/branch/settings/admission/CLI dispatch,
per `docs/issue-2548/reports/architecture.md` Step C) and Step D (remove the
`spawn_roles.json` fallback and the `docs/specs/write_scope.md` (untracked
in this repo) override entirely, making the roster the only source) are
both out of scope here and left for separate issues/PRs, per the
architecture record's own step ordering and this issue's explicit scope
boundary.

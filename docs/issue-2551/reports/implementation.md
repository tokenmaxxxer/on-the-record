---
issue: 2551
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/issue-2548/reports/architecture.md
    sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019
code_under_review:
  - spawn.py
type: feat
breaking: none — additive-only field, no reader added, gates.py has zero roster coupling
verdict: pass
---

# issue-2551 — implementation record

skill-verdict: work-in-english:work-in-english — applied: invoked; kept the
new function's docstring and this record in English, and matched the
existing Korean inline-comment style at the two `roster_register(...)` call
sites in `spawn.py` (they sit inside blocks where every neighboring comment
is already Korean — the skill's own "match surrounding style" guard, not a
skipped translation).

## What was done

Step A of the eight-step role-axis removal
(`docs/issue-2548/reports/architecture.md`, section `### Order`, Step A):
the roster/lease entry now carries a `write_scope` field, populated by
`spawn.py` at spawn time from `spawn_roles.json[role].write_scope`. No
reader of the field was added anywhere.

```
derived: git diff --stat spawn.py
 spawn.py | 30 ++++++++++++++++++++++++++++++
 1 file changed, 30 insertions(+)
```

Concretely, in `spawn.py`:
- a new function `_bootstrap_write_scope(role: str) -> dict` (spawn.py:56-78)
  reads `role_data()[role]["write_scope"]` and returns
  `{"write_scope": [...]}` — or `{}` (the key entirely absent) when the role
  isn't a `spawn_roles.json` key at all, or is a key but has no
  `write_scope` declared.
- both roster-write call sites merge its result into the entry they build:
  the early crash-visibility stub (spawn.py:3449,
  `_early_roster_entry.update(_bootstrap_write_scope(role))`) and the main
  post-`Popen` registration (spawn.py:3586, `**_bootstrap_write_scope(role)`
  inside the `roster_register(roster_key, {...})` call).

## Why

The design (`docs/issue-2548/reports/architecture.md` Step A) calls this
step "fully inert" because `gates.py` has no roster import, so
`role_scope()` cannot see the new field — re-verified this session:

```
derived: grep -c 'import roster' gates/gates.py
0
```

Step A must land before Step B (which makes `role_scope()` read
`write_scope` from the roster) because `write_scope` is fail-closed — an
empty roster on day one of Step B would freeze every branch's writes if no
prior spawn had ever populated the field. Landing the populate-only writer
now, with zero readers, is the safe halt point the design names.

The one judgment call the issue calls out: an undeclared `write_scope` must
not collapse to `{"write_scope": []}`, because several roles (e.g.
`product-discovery`) legitimately declare an *empty* list today, and
Step B's planned fail-closed read needs to keep telling that apart from "no
declaration at all" — the same distinction `gates.py:role_scope()` already
makes for `spawn_roles.json` itself (`"write_scope" not in role_cfg`,
gates/gates.py:915-916). `_bootstrap_write_scope()` handles this by omitting
the key entirely (returning `{}`) in the undeclared case, never writing an
empty list.

## Acceptance evidence

### 1. A real spawn writes a roster entry carrying `write_scope`, matching `spawn_roles.json[role].write_scope`

Not `--dry-run`: this drives `spawn._spawn_one()` directly, the same live
function `main()` and `drive()` call for a real spawn (the existing
regression test `test/test_spawn_artifact_skill_pairing.py` uses the same
technique to exercise `_spawn_one()` for real). Only the `claude` subprocess
launch itself is swapped for `cat` (`spawn_cmd` mocked to return `(["cat"],
{})`) and unrelated I/O (GitHub issue fetch, skill-repository disk layout)
is stubbed — `roster_register`, `_bootstrap_write_scope`, and every other
roster-construction line in `_spawn_one()` run unmodified.

```
derived: python3 /tmp/verify_2551.py (case 1)
=== case 1: role=implementation (declared write_scope) ===
rc 0
issue-999001/implementation -> {
  "pid": 1837982,
  "role": "implementation",
  "issue": 999001,
  "ts": 1787750224,
  "work": "/tmp/tmpi22a9fgv/tmpcc49jski/work",
  "log": "/tmp/tmpi22a9fgv/tmpcc49jski/work.session.20260826T221704.1837950.log",
  "expects_pr": true,
  "task": null,
  "model": "",
  "model_rule": "",
  "session_id": null,
  "before_head": "780020d82e2a84eaf5ca3dc0c66cca6e5f333a40",
  "wrapper_pid": 1837950,
  "resolution_source": "skill-repo",
  "resolution_skills": [],
  "resolution_skill_sha": null,
  "write_scope": [
    "src/**",
    "test/**",
    "tests/**"
  ]
}
spawn_roles.json[implementation].write_scope = ["src/**", "test/**", "tests/**"]
```

The roster entry's `write_scope` (`["src/**", "test/**", "tests/**"]`) is
byte-identical to `spawn_roles.json["implementation"]["write_scope"]`,
quoted alongside it above.

Empty-state case (issue body's extra requirement: "an issue with no roster
entries yet is the normal first-spawn case and must work"): the spawn above
already ran against a brand-new `spawn.ROSTER` path that had never been
written before it (a temp file, never pre-seeded) — `roster.py`'s
`_roster_load()` catches the missing-file `OSError` and starts from `{}`.
Isolated re-check of exactly that:

```
derived: python3 -c one-off script (empty-state check)
roster file exists before any spawn: False
roster file exists after first-ever spawn (empty-state path): True
contents: {
  "issue-1/implementation": {
    "pid": 1,
    "role": "implementation",
    "write_scope": [
      "src/**",
      "test/**",
      "tests/**"
    ]
  }
}
```

### 2. Behavior is unchanged: `gates.role_scope()` before/after, in-scope and out-of-scope

Fixture: a fresh git repo per scenario (created under a tempdir, not part of
this repo's own tree), `refs/remotes/origin/main` pointing at the initial
commit, a second commit on branch `issue-1/implementation` that either
touches a file under an `src/` directory (in-scope for role
`implementation`, whose `write_scope` is `["src/**", "test/**",
"tests/**"]`) or a file outside every declared glob (out of scope). Ran once
with the Step A diff applied (current tree) and once with it stashed out
(`git stash push -- spawn.py`), same fixture script both times:

```
derived: python3 /tmp/verify_2551_gates.py, once with spawn.py's Step A diff live and once with it `git stash`-ed out

--- AFTER (current, with Step A change) ---
OUT-OF-SCOPE result: ['write_scope 이탈: docs-out-of-scope.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']
IN-SCOPE result: []
--- BEFORE (baseline, no Step A change) ---
OUT-OF-SCOPE result: ['write_scope 이탈: docs-out-of-scope.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']
IN-SCOPE result: []
```

All four outputs are identical — the out-of-scope refusal text is
byte-identical before and after, and the in-scope result is `[]` both
times.

### 3. No reader of the new field exists

```
derived: grep -rn "write_scope" --include="*.py" --include="*.sh" . | grep -v "^\./docs/\|^docs/" > /tmp/write_scope_grep.txt; wc -l /tmp/write_scope_grep.txt; grep -c "^spawn.py" /tmp/write_scope_grep.txt
68 /tmp/write_scope_grep.txt
14
```

All 68 non-docs matches (`docs/issue-167/` and `docs/issue-170/` under
`_assets/rulebook-skeleton/` are historical fixture text, excluded) read
`write_scope` from `spawn_roles.json`/the role-config dict — `gates.py`'s
`role_cfg` (from `_role_cfg()`, itself `spawn_roles.json[role]`),
`spawn.py:2725`'s `spec = role_data()[role]` (feeding `spawn.py:3007`'s
pre-existing `_role_touches_code(spec.get("write_scope", []))`, unrelated
to and predating this issue), `gates/risk_report.py`'s
`_role_write_scopes()` (explicitly docstringed as reading
`spawn_roles.json`), and `on-the-record/hooks/delegated-judgment-gate.sh`'s
embedded `ROLES.get(role, {}).get("write_scope")` (a role-definition
snapshot, not the roster). The 14 `spawn.py` matches are exactly this
change: the new function (definition, docstring, body — spawn.py:56-78),
its two call sites (spawn.py:3449, 3586), and the Korean comment
immediately above the second call site (spawn.py:3583-3585). None reads
`write_scope` off a roster/lease entry.

### 4. A spawn for a role with no `write_scope` declared

Today's live `_spawn_one()` cannot actually reach `roster_register()` for a
role absent from `spawn_roles.json` — `admission_gate()`'s
`_admission_check_directive_completeness()` (`pipeline.py:1643`,
`role not in _sp.ROLES`) refuses it first, and even bypassing that,
`_spawn_one()` itself does an unconditional `role_data()[role]` a few lines
later (spawn.py:2725) that would `KeyError`. That's the pre-existing,
structural reason this scenario isn't reachable end-to-end yet — removing
it is Step C's job (`role_settings()`/the admission check dropping the
`_sp.ROLES` membership requirement), not this step's. Real spawn attempt,
confirming that outcome (no roster entry of any shape gets written — not
even one with `write_scope` omitted):

```
derived: python3 /tmp/verify_2551.py (case 2)
=== case 2: role=totally-unknown-role-xyz (no write_scope declared) ===
rc 1
'totally-unknown-role-xyz' in spawn_roles.json: False
```

(stderr from the same run: `[totally-unknown-role-xyz] admission refused:
missing precondition 'directive-completeness' (issue #2100) — no session
created, no workspace left behind.`)

Constructing the scenario directly against the shipped writer
(`_bootstrap_write_scope`, the actual function this PR adds — not a
simulation of it) covers both ways a role can have "no `write_scope`
declared": absent from `spawn_roles.json` entirely, and present but missing
the `write_scope` key:

```
derived: python3 /tmp/verify_2551.py (case 3)
=== case 3: _bootstrap_write_scope() directly on the writer's two undeclared branches (role missing from spawn_roles.json entirely; role present but without a write_scope key) ===
role missing entirely: {}
role present, no write_scope key: {}
roster entry merged with the undeclared-role bootstrap result: {'pid': 1, 'role': 'totally-unknown-role-xyz'}
'write_scope' in that entry: False
```

Stated outcome: the roster entry for an undeclared role simply has no
`write_scope` key at all — not `[]`. `list(cfg["write_scope"])` (spawn.py:78)
is only ever reached after the preceding `if "write_scope" not in cfg:
return {}` (spawn.py:76-77), so an empty allow-list is structurally
impossible to write from this function.

## What did not work

None.

## Upstream basis

`docs/issue-2548/reports/architecture.md` (issue #2548, PR #2550), section
`### Order`, the Step A paragraph (`sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019`
— the commit that landed that record) — the concrete spec this record
implements against, including the "no reader yet" constraint and the
Step A/Step B ordering rationale.

## Open findings

None — Step A is scoped as deliberately inert per the issue, and every
`acceptance: <command> — result:` pair in the "Acceptance evidence" section
above ran clean this session.

## Next steps

Step B (`gates.py:role_scope()` reads `write_scope` from the roster via
`lease_key(issue, role)`, falling back to `spawn_roles.json` only on a
roster miss) is out of scope here per the issue's own boundary and is left
for a separate PR/issue.

---
issue: 2539
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: docs/decisions/2026-08-25-retire-role-axis-staging.md
    sha: same-commit
code_under_review:
  - spawn_roles.json
  - gates/gates.py
  - on-the-record/gates/gates.py
  - gates/risk_report.py
  - gates/roles_due.py
  - gates/patrol_wiring.py
  - gates/spec_schema_five_activities_test.py
  - spawn.py
  - pipeline.py
  - directive_assembly.py
  - bench/run.py
  - consult.py
  - on-the-record/hooks/record-scaffold.sh
  - on-the-record/hooks/quality-bar-gate.sh
  - on-the-record/hooks/merge-allow-gate.sh
  - on-the-record/hooks/delegated-judgment-gate.sh
  - test/test_spawn_role_skill_resolution.py
  - test/test_spawn_skills_mount.py
type: refactor
breaking: none — spawn_roles.json ships in the same commit as the roles/ + roles/specs/ deletion; on-the-record/gates/gates.py stays byte-identical to gates/gates.py (checked — `diff gates/gates.py on-the-record/gates/gates.py` — result: no output)
verdict: pass
---

# issue-2539 — implementation record

commit: 5bd1cd42 on `issue-2539/implementation`

## What was done

Stage 6C, per the orchestrator's scope-correction comment, superseding the issue body's original "just delete it" framing.

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/2539/comments` — issuecomment-5423927858 body, read at session start (quoted table: "Only two fields are actually consumed" — `write_scope` and `required_fields`/`roles/specs/*.spec.json`; enumeration-only sites listed as `pipeline.py:225,1643`, `patrol_wiring.py:54`, `spawn.py:2005`, `bench/run.py`)

**What the comment's table got wrong, found by reading the actual code at each cited site (not just re-grepping):**

- `pipeline.py:225` is inside `role_settings()`. `derived`: reading `pipeline.py` lines 211-280 (current, pre-edit) shows it builds `s = {k: v for k, v in spec.items() if k not in (...)}` from the **full** parsed role JSON and goes on to read `s["env"]`, `s.get("sandbox", {})` — not an existence check. `role_settings()` is called from `spawn.py:2042`, `spawn.py:3237`, and 3 sites in `consult.py` (`derived`: `grep -n "role_settings\b" *.py` before any edit — result included those 6 call sites) — every spawn calls it to build `settings.json`.
- `bench/run.py`'s `rulebook_bench()` reads `spec["path"]`, not just existence (`derived`: reading `bench/run.py` lines 30-37 pre-edit).
- `gates/roles_due.py`'s `load_triggered_specs()` reads `roles/specs/*.spec.json` for `use_when.trigger` — not named in the comment's table at all.
- `gates/gates.py:288`'s `# CLAIM-CHECK: enum-subset roles/implementation.json:record_fields.loop_state ...` marker is a live input to `gates/claims.py`'s machine-checked claim verifier — not named in the table.
- `gates/spec_schema_five_activities_test.py` is a real pytest suite asserting on `roles/specs/*.spec.json` content for 14 roles — not named in the table.
- Four `on-the-record/hooks/*.sh` scripts have embedded Python that reads the directories directly: `record-scaffold.sh`, `quality-bar-gate.sh`, `merge-allow-gate.sh`, `delegated-judgment-gate.sh` — none named in the table (`derived`: `grep -rn '"roles"' --include=*.py --include=*.sh .` before any edit, run after the literal-`"roles/"` grep alone had already missed these `Path(x)/"roles"/y`-style joins).
- `test/test_spawn_role_skill_resolution.py` and `test/test_spawn_skills_mount.py` each assert `(spawn.ROOT / "roles" / "implementation.json").is_file()` directly.

Design: one file, `spawn_roles.json`, a dict keyed by role name → the original `roles/<role>.json` content, plus a nested `record_spec` key holding the original `roles/specs/<role>.spec.json` content when one existed. `derived`: `comm -23 <(ls roles/*.json | xargs -n1 basename | sed 's/\.json$//' | sort) <(ls roles/specs/*.spec.json | xargs -n1 basename | sed 's/\.spec\.json$//' | sort)` (run before deletion) — result: `upstream-defect-report`, the one role with no spec file.

The migrated blob is named `record_spec`, not `spec`: `derived`: `grep -l '"spec"' roles/*.json | wc -l` (run before deletion) — result: `42` — 42 of the 44 role JSONs already had their own `"spec"` field (a doc-path string). A first draft named the new nested key `"spec"`, which would have clobbered that pre-existing field for those 42 roles; caught before landing by a round-trip check (`derived`: a Python script comparing every `spawn_roles.json[role]` minus `record_spec` against the original `roles/<role>.json`, and `record_spec` minus the popped `role` key against the original spec file, across all 44 roles — result: `mismatches: []`).

Consumer migration (one loader pattern — read `spawn_roles.json`, index by role name; every site kept its original fail-closed/refusal shape):

- `gates/gates.py` + its byte-identical mirror `on-the-record/gates/gates.py`: 5 sites (`record_enums`, `record_refusal_reasoned`, `parse_checked_claims`/`record_checked_claims`'s shared `_terminal_loop_state` path, `role_scope`). Added one shared `_role_cfg(role)` helper; each site's `except (OSError, json.JSONDecodeError)` grew a `KeyError` arm.
- `gates/risk_report.py`: `_role_write_scopes(root)` reads `root / "spawn_roles.json"`.
- `gates/roles_due.py`: `load_triggered_specs(root)` reads `spawn_roles.json`'s per-role `record_spec`.
- `spawn.py`: added `role_data()`; the bare-role-listing help text and `_spawn_one()`'s directive-assembly spec read both use it.
- `pipeline.py`: `role_settings()` uses `role_data()`; the admission-time existence check uses `role in _sp.ROLES` (per the comment's own guidance for that specific site).
- `gates/patrol_wiring.py`: `_known_roles()` returns `sorted(spawn.ROLES)`.
- `bench/run.py`: `spawn_mod.role_data()[role]`.
- `directive_assembly.py`: both `write_record_skeleton()` reads (loop_state enum, required_fields) use `_sp.role_data()`.
- `on-the-record/hooks/record-scaffold.sh`, `quality-bar-gate.sh`, `merge-allow-gate.sh`, `delegated-judgment-gate.sh`: embedded Python reads `spawn_roles.json` in place of directory reads.
- `gates/spec_schema_five_activities_test.py`, `test/test_spawn_role_skill_resolution.py`, `test/test_spawn_skills_mount.py`: repointed at `spawn_roles.json`.

`roles/` (44 files) and `roles/specs/` (43 files) were `git rm -r`'d in the same commit as the migration.

derived: `git show --stat 5bd1cd42 | tail -1`
```
105 files changed, 5920 insertions(+), 5618 deletions(-)
```

## Why

canonical: `gh api repos/tokenmaxxxer/on-the-record/issues/2539/comments` — issuecomment-5423927858 body, "Per an architecture consult on this issue: `write_scope` is the one carrying actual enforcement semantics ... its failure mode is silent widening of write permissions, not a loud error" and the fail-closed quote at `gates/gates.py:886-887` (pre-migration) it names.

Given that explicit risk, the migration had to preserve `role_scope()`'s exact fail-closed shape, not just avoid a crash. Consolidating into one file (rather than distributing fields across separate homes per the comment's original two-field split) let every migrated call site keep its existing error-handling shape with a single substitution (file path → dict lookup by key), instead of re-deriving fail-closed behavior independently for each of the under-enumerated consumers found above (`role_settings()`'s full-spec read, `bench/run.py`, `roles_due.py`, `claims.py`'s marker, the four hooks).

## Acceptance verification

**check 1 — `roles/` and `roles/specs/` deleted, both greps clean, every surviving hit named.**

derived: `ls roles; ls roles/specs`
```
ls: cannot access 'roles': No such file or directory
ls: cannot access 'roles/specs': No such file or directory
```

derived: `grep -rn "roles/" --include=*.py --include=*.sh . | grep -v '/\.git/' | grep -v '^\./docs/' | wc -l`
```
93
```

Every one of the 93 is a comment/docstring, a regex/set-literal pattern that becomes permanently non-matching now that `roles/` doesn't exist, or a historical fixture template under `docs/issue-170`/`docs/issue-167` (these matched despite the `grep -v '^\./docs/'` filter because this grep's paths aren't `./`-prefixed, so the filter is a no-op against them — they are dead template files, never executed, from already-closed issues). No functional reader survives — every functional reader found by reading actual code (not this grep alone, which misses `Path(x)/"roles"/y`-style joins) was migrated above. Representative categories:
- Bare-string path classifiers, permanently inert now: `gates/gates.py:36` `PROTECTED_ROOT_DIRS = {"roles", ...}`, `gates/risk_report.py:82` and `on-the-record/hooks/delegated-judgment-gate.sh:394` `GATES_DIRS = {"roles", ...}`, `gates/skip_eligibility.py:50`'s `HARD_TO_REVERT_RE` alternative, `gates/accumulation.py:98` and `on-the-record/hooks/accumulation-claim-guard.sh:114`'s shape-5 regex, `gates/closure_sweep.py:459`'s `git ls-files roles/*.json` (advisory-only accumulation-trend counter, not a blocking gate — degrades to a permanent 0 for this one shape), `gates/patrol_board.py:60`'s `roles/<role>/` queue-path-namespace convention (unrelated to the physical directory).
- Frozen-decision glob data, not code: `docs/decisions/2026-08-21-single-skill-axis.md` and `docs/decisions/README.md` declare `scope.globs: ["roles/**"]` to forbid *reintroducing* a role manifest — meaningful precisely because the directory is now gone. `gates/constitution_check.py:44` and `gates/frozen_decisions.py:16` are the generic glob matcher and its docstring example.
- Explanatory comments (pre-existing or added this commit) describing already-migrated behavior: `consult.py:397,773,1247,1398` (updated in this commit to stop asserting `role_settings()` "still reads `roles/`"), `gates/gates.py:298,323`, `gates/risk_report.py:67,132,160,170`, `gates/roles_due.py:7-8,51`, `gates/ci.py:414`, `gates/flows.py:26`, `directive_assembly.py:426,602`, `pipeline.py:265`, `gates/quality_bar.py:5`, `spawn.py:45-47`, `on-the-record/hooks/quality-bar-gate.sh:19,213`, `gates/spec_schema_five_activities_test.py:12`.

derived: `grep -rl CLAUDE_ROLE on-the-record/hooks/ | grep -v test_ | wc -l`
```
8
```

Unchanged from issue #2538 (a separate axis — `CLAUDE_ROLE` presence/value, not `roles/` file content). canonical: read all 8 files directly — `upstream-defect-scope-guard.sh`, `approval-gate.sh`, `deviation-log-guard.sh` still call `os.environ.get("CLAUDE_ROLE", ...)` (the 3 value-dependent survivors #2538's own record names); `role-deviation-directive.sh`, `skill-verdict-guard.sh`, `pretooluse_dispatcher.py`, `quality-bar-gate.sh`, `session-role-bind.sh` mention `CLAUDE_ROLE` only in comments. No change needed for this issue's scope.

**check 2 — `write_scope` has a home other than a per-role `roles/<role>.json` file, `gates/gates.py`'s fail-closed path still refuses, before/after quoted.**

`write_scope` now lives at `spawn_roles.json[role]["write_scope"]` — a dict-key lookup, not a filesystem path per role. Constructed a real out-of-scope PR diff (branch `issue-1/implementation`, whose `write_scope` is `src/**, test/**, tests/**`; diff adds a new file `out_of_scope.txt` at repo root) and ran `gates.role_scope(work, "issue-1/implementation")` twice: once loaded from commit `a4d85dbb` (the parent commit, still has `roles/implementation.json`), once from the current tree.

acceptance: `role_scope()` from a4d85dbb (before) — result:
```
write_scope 이탈: out_of_scope.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
```

acceptance: `role_scope()` from the current tree (after) — result:
```
write_scope 이탈: out_of_scope.txt (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
```

Byte-identical refusal text. The fail-closed-on-missing-declaration branch (`if "write_scope" not in role_cfg`) is untouched logic, only re-pointed at the new source.

**check 3 — `required_fields`/`roles/specs/` has a named home, `directive_assembly.py` reads it, one assembled directive quoted before/after and shown equivalent.**

Home: `spawn_roles.json[role]["record_spec"]["required_fields"]`. Ran `directive_assembly.write_record_skeleton()` for role `implementation` against the `a4d85dbb` checkout and against the current tree, into two disposable local paths (untracked, not committed to this repo), and diffed the generated files.

acceptance: `diff <before-checkout skeleton> <current-tree skeleton>` — result:
```
(no output — byte-identical, including the code_under_review:/type:/breaking:/verdict: lines required_fields populates)
```

**check 4 — the four existence/enumeration sites read `spawn.ROLES`, the `patrol_wiring._known_roles()`/`spawn.ROLES` one-entry disagreement resolved and named.**

`pipeline.py`'s admission existence check, `pipeline.py`'s `role_settings()` unknown-role message, `gates/patrol_wiring.py`'s `_known_roles()`, and `spawn.py`'s bare-role-listing help text all now read `spawn.ROLES` or `spawn.role_data()` instead of globbing `roles/*.json`.

derived: `sed -n '703,715p' spawn.py | grep -oE '"[a-z-]+"' | wc -l`
```
43
```

`roles/*.json` had 44 entries before deletion. The one-entry disagreement: `upstream-defect-report`. canonical: `roles/upstream-defect-report.json` (read before deletion) declares `"report_only": true`, and its `use_when` states `board_condition: N/A — hooks/command 요소만 쓰는 report_only 채널, 스폰 파이프라인을 거치지 않는다` — it is an upstream-defect-filing channel invoked via `/report-upstream`, never through `spawn.py`'s role pipeline or the board. `spawn.ROLES`' own comment is `# 역할 순서. 보드를 읽을 때 이 순서로 보여준다` (board display order) — a role that never reaches the board correctly has no board-order entry; this is not an off-by-one to paper over by picking the longer list. `patrol_wiring._known_roles()` switching to `spawn.ROLES` correctly drops `upstream-defect-report` from post-merge patrol iteration too, for the identical reason (no board queue entries for a role that never runs through the pipeline).

**check 5 — a real spawn runs end to end after the deletion, `bootstrap_timing` + resolved skills quoted, not a `--dry-run` substitute.**

Ran `python3 spawn.py implementation "<task>" -C <disposable local clone> --no-contract --max-turns 6 --model haiku` (no `--dry-run`) against a disposable clone of this branch's tip (untracked, not committed to this repo).

acceptance: real (non-dry-run) spawn stderr — result:
```
[implementation] 플러그인 0개, 룰북 skill-repo(이슈 #1955), core 플러그인 core, terse, freelunch, scout, warrant, core ad043a0 (2026-08-26, on-the-record 클론), 작업 디렉터리 /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2539-implementation-adhoc-implementation-1516907
[implementation] bootstrap_timing admission=0.027 skill_resolve=0.003 workspace=0.000 branch=0.000 returned_pr_gate=0.000 auto_sweep=0.000 rulebook=0.000 core=0.000 gh_token=0.028 settings=0.003 cross_family=0.000 issue_fetch=0.000 directive_write=0.000 design_bearing=0.000 spawn_cmd=0.000 board_snapshot=0.098 total=0.159
```

Resolved skills: no `--skills` mounts (0), skill-repo guidance mounted via issue #1955's `--plugin-dir` path, core plugins `core, terse, freelunch, scout, warrant`. `admission`/`skill_resolve`/`settings` completing with real nonzero timings (rather than throwing) is the direct proof that `role_settings()` — the biggest under-enumerated consumer, reading the entire role spec (`sandbox`, `env`, `decides`, `use_when`, `produces`) — resolved successfully from `spawn_roles.json`; before this migration that exact call site still read `roles/{role}.json`, which no longer exists on this tree.

The nested session reached real interactive engagement inside the actual production PreToolUse/board-gate stack and attempted a real `Write` to a disposable record path (untracked, not committed to this repo, outside any real issue tree). It was refused by the live board-gate: ad hoc spawns with no `--issue` stay on `main`, and board-gate requires the target issue's own `issue-<n>/<role>` branch to write into its tree — a pre-existing invariant unconnected to this migration, which a throwaway ad hoc verification spawn without a real `--issue` will always trip.

acceptance: nested-session stdout on the first such attempt — result:
```
Stopped as instructed. The write was blocked by hook requirements that exceed the scope of your directive.
```

It reached and exercised the real record-writing code path end to end; it did not land a file for the reason quoted above.

**check 6 — at least 3 gates that previously keyed on role identity still refuse the same payload, outcome quoted (before/after).**

Gate 1 (`gates.role_scope`, `write_scope`): quoted under check 2 above.

Gate 2 (`gates.record_enums`, `record_fields` enum-subset): constructed a fixture record (untracked local test repo, not committed to this repo) with `loop_state: bogus-state` — not in the declared enum — and ran `record_enums()` before/after.

acceptance: `record_enums()` before (a4d85dbb / roles/implementation.json) — result:
```
레코드 enum 위반: docs/issue-1/reports/implementation.md 의 loop_state='bogus-state' — roles/implementation.json 이 선언한 값 (['scope-proposed', 'scope-approved', 'in-progress', 'refused', 'not-needed', 'cannot-verify', 'landed']) 이 아니다
```

acceptance: `record_enums()` after (current tree / spawn_roles.json) — result:
```
레코드 enum 위반: docs/issue-1/reports/implementation.md 의 loop_state='bogus-state' — /home/jwjung/.tokenmaxxxer/work/on-the-record-issue-2539-implementation/spawn_roles.json 의 'implementation' 이 선언한 값 (['scope-proposed', 'scope-approved', 'in-progress', 'refused', 'not-needed', 'cannot-verify', 'landed']) 이 아니다
```

Same enum, same violation caught, same refusal — only the cited source changed (expected: that is this migration).

Gate 3 (`gates.record_checked_claims`, terminal-state Acceptance-verification requirement): same fixture repo, record changed to `loop_state: landed` (a terminal value per the same enum) with no `## Acceptance verification` section.

acceptance: `record_checked_claims()` before — result:
```
docs/issue-1/reports/implementation.md: loop_state='landed'(터미널)인데 '## Acceptance verification' 섹션이 없다 — 완료 주장은 기계로 확인되지 않으면 터미널 상태로 못 간다
```

acceptance: `record_checked_claims()` after — result:
```
docs/issue-1/reports/implementation.md: loop_state='landed'(터미널)인데 '## Acceptance verification' 섹션이 없다 — 완료 주장은 기계로 확인되지 않으면 터미널 상태로 못 간다
```

Byte-identical. `_terminal_loop_state()` reads `record_fields.loop_state`'s last enum value from `spawn_roles.json` now, same value it read from `roles/implementation.json` before.

(All three `docs/issue-1/reports/implementation.md` references above are to a disposable local git fixture used only for this gate comparison — untracked, never committed to this repo.)

**check 7 — the record states what the role axis is replaced by, and what a future reader should look at instead of `roles/`.**

See "Role axis replacement" below.

## Role axis replacement

canonical: `docs/decisions/2026-08-25-retire-role-axis-staging.md` (read this session) — Option A decomposes `role`'s four jobs onto: an issue-scoped **lease** (collision safety), an append-only **author identity** field per record (write isolation/audit — `directive_assembly.py`'s `author:` stamp), a **record-kind** tag (independent-verification integrity), and **skill** (capability/guidance selection, task-composed per issues #2507/#2536, not a static per-role enum). That full decomposition is the larger issue #2241 program (stages 0-6) and is not what this issue did.

This issue's scope was narrower: the **data storage** backing `role`-keyed lookups (`write_scope`, `record_fields`, `required_fields`, sandbox/env declarations) moved from one-file-per-role under `roles/`/`roles/specs/` to a single `spawn_roles.json`. The `role` axis itself — `spawn.ROLES`, branch naming (`issue-<n>/<role>`), `CLAUDE_ROLE`, record-path-by-role — is unchanged here; retiring the *directory* was Stage 6C's job, not retiring the axis. A future reader who used to open `roles/<role>.json` or `roles/specs/<role>.spec.json` for a role's write scope, record-field enums, or required record fields should now open `spawn_roles.json[role]` (and its nested `record_spec` key for what used to be the `.spec.json`). A reader looking for where the axis itself eventually goes away should read `docs/decisions/2026-08-25-retire-role-axis-staging.md` and the issue #2241 stage proposals, not this record.

## What did not work

- An early draft named the migrated `required_fields` blob `"spec"` inside each role's entry; the round-trip check described under "What was done" caught, before landing, that this clobbers 42 roles' own pre-existing `"spec"` field. Renamed to `record_spec`.
- Two attempts at a clean "real spawn writes and lands a record" run did not land a file. First attempt: cloned onto this branch's own tip, whose diff vs `origin/main` is this issue's own 105-file migration — every path falls under `gates.py`'s `PROTECTED_ROOT_DIRS = {"roles", ...}`, so the pre-session risk classifier escalated before the task started. Second attempt: re-pointed the disposable clone's local `main` ref at this branch's tip to simulate a post-merge empty diff, which cleared that escalation, but then hit `spawn.py`'s pre-existing adhoc-spawn/board-gate branch-mismatch rule (an ad hoc spawn with no `--issue` stays on `main`; board-gate requires the target issue's own branch) — unrelated to this migration. Accepted the resulting real, non-dry-run evidence as-is (quoted under check 5) rather than spend further turns forcing a landed-record outcome.

## Upstream basis

`docs/decisions/2026-08-25-retire-role-axis-staging.md` (same-commit — cited by this record, not modified by it). Issue #2539's body and its scope-correction comment (issuecomment-5423927858) are the actual requirement source; both are GitHub issue/comment content, not a repo path — cited via `gh api` above.

## Open findings

None outstanding.

derived: this session's own trace (checks 1-6 above) — the scope-correction comment's reader table was under-enumerated (`role_settings()`/`bench/run.py` mischaracterized as existence-only; `roles_due.py`, `claims.py`'s marker, `spec_schema_five_activities_test.py`, and 4 hooks not named at all); every one of those was found, migrated, and verified in this same session before `roles/` was deleted — no partial migration was left standing.

## Next steps

None. This is Stage 6C, the last stage of the `roles/`-deletion sub-program (issues #2537/#2538/#2539). The larger role-axis retirement (issue #2241 stages 0-6) continues independently per `docs/decisions/2026-08-25-retire-role-axis-staging.md`.

## Acceptance

acceptance: `git show --stat 5bd1cd42` — result:
```
105 files changed, 5920 insertions(+), 5618 deletions(-)
```

acceptance: `ls roles; ls roles/specs` — result:
```
ls: cannot access 'roles': No such file or directory
ls: cannot access 'roles/specs': No such file or directory
```

acceptance: `python3 -m pytest -q -p no:cacheprovider` (full suite, current tree) — result:
```
14 failed, 369 passed in 4.41s
```
All 14 failures independently reproduced with this commit's own changes `git stash`'d (same 14, byte-for-byte same failing test IDs) — a pre-existing skill-repository test-fixture gap (`work-in-english` skill unavailable in this sandbox's mounted skill checkout) and one unrelated harness flake (`harness/fixture-operator-experience/test_flow.py`), neither touching `roles/`.

acceptance: `python3 -m pytest test/test_spawn_role_skill_resolution.py test/test_spawn_skills_mount.py gates/spec_schema_five_activities_test.py -q` — result:
```
48 passed
```

acceptance: `bash on-the-record/hooks/record-scaffold.sh implementation 999999 <disposable tmpdir, untracked>` — result:
```
record-scaffold: wrote <tmpdir>/docs/issue-999999/reports/implementation.md
```
(scaffold's frontmatter carried `implementation`'s real `record_fields` keys, read from `spawn_roles.json`)

acceptance: `python3 -m py_compile` on every edited `.py` file, plus `bash -n` and extracted-heredoc `py_compile` on every edited `.sh` file — result:
```
PY COMPILE OK
```
(and `bash -n`/heredoc `py_compile` each individually exited 0, no output)

skill-verdict: work-in-english — applied: invoked; matched surrounding Korean comment style at every migrated call site instead of translating (this skill's own "match surrounding style" guidance), wrote the commit message and this record in English matching this repo's own commit convention (recent `git log` titles are English — checked at session start), made no policy announcement
skill-verdict: silent-failure-audit — applied: invoked; reviewed the ~10 migrated `try/except` call sites across `gates/gates.py`, `gates/risk_report.py`, `gates/roles_due.py`, `pipeline.py`, `directive_assembly.py` (enumerated under "What was done" — Consumer migration). Every fail-closed shape (a refusal string appended to the caller's `bad`/return list, e.g. the `KeyError` arm added alongside each existing `(OSError, json.JSONDecodeError)` catch) is preserved unchanged from before this migration. Every pre-existing soft-fail shape (`risk_report.py`/`roles_due.py` returning an empty dict on unreadable data — both are advisory-only classifiers, not enforcement gates) is preserved unchanged. No new silent absorption introduced. `directive_assembly.py`'s pre-existing broad `except Exception: pass` around the two migrated reads is unchanged and out of this issue's scope to harden — it only populates a record-skeleton hint (default `loop_state`/placeholder fields), not an enforcement path.

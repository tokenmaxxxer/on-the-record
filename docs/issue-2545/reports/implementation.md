---
issue: 2545
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: github.com/tokenmaxxxer/on-the-record/issues/2545
    sha: cdf80483a583faf29ee343db8ca17a112c61c158
code_under_review:
  - pipeline.py:1131
  - spawn.py:524
  - directive_assembly.py:579
  - spawn.py:2924
  - spawn.py:2999
  - spawn.py:3061
  - gates/gates.py:873
  - gates/landing_readiness.py:61
  - gates/landing_readiness.py:79
  - gates/ci.py:409
  - gates/ci.py:438
  - board.py:849
  - on-the-record/hooks/record-scaffold.sh:10
  - on-the-record/gates/gates.py:873
type: fix
breaking: no
verdict: pass
---

# issue-2545 — implementation record

Removed the role axis from the record-filename resolution path: new
records now write at issue-<n>/reports/<role>-<lease-disambiguator>.md
(the same `<skill>-<lease-disambiguator>` naming `pipeline.checkout_issue_branch_for_skill`
already used for branch names) instead of issue-<n>/reports/<role>.md,
and every reader of that filename that the issue named was updated to
resolve the new shape alongside the old one. The git branch itself keeps
the old role-axis name (`issue-<n>/<role>`) — that axis was deliberately
left untouched (see "Rationale for deviations" below).

## What was done

`pipeline.py:1131` (`checkout_issue_branch_for_skill`) already minted the
`<skill>-<lease-disambiguator>` naming convention for branch names (issue
#2432) but had no caller. Rather than duplicating that string-formatting
logic at a second call site (the issue's own must-not), the naming was
extracted into a new pure function, `pipeline.skill_lease_name(skill,
disambiguator=None)` (`pipeline.py:1131`), which `checkout_issue_branch_for_skill`
now delegates to internally — both the branch-naming caller and the new
record-naming caller go through the one function.

`directive_assembly.write_record_skeleton()` (`directive_assembly.py:579`)
takes a new required `disambiguator` argument and writes to
`docs/issue-<n>/reports/<name>.md` where `<name>` is
`_sp.skill_lease_name(role, disambiguator)`, instead of `reports/{role}.md`.
Its caller, `spawn._spawn_one()` (`spawn.py:2999`), mints the
disambiguator once per workspace and persists it alongside the existing
`.task.txt` idempotency sidecar (`spawn.py:2924`, new
`.record-disambiguator.txt` file) so a respawn into the same workspace
resolves the same record path instead of forking a second skeleton. The
scaffold preamble line sent to the spawned session (`spawn.py:3061`) now
names the actual path written, not a reconstructed one — it echoes
`skill_lease_name(role, disambiguator)` directly.

`on-the-record/hooks/record-scaffold.sh` (the on-demand, hand-invoked CLI
scaffolder) takes an optional 4th `disambiguator` argument, minting one
with `secrets.token_hex(4)` (matching `roster.new_lease_disambiguator()`'s
8-hex-char shape) when omitted, and writes to the same
`<role>-<disambiguator>.md` filename.

The three "must not silently permit" reader sites the issue flagged:

- `gates/gates.py:873` (`_always_writable`, the write-scope allow-list
  `gates.role_scope()` unions into a role's declared `write_scope` before
  checking a PR diff) now globs `docs/issue-*/reports/{role}-*.md` in
  addition to the existing `docs/issue-*/reports/{role}.md` — see
  "Acceptance verification" #3 below for a live before/after refusal
  demonstration.
- `gates/landing_readiness.py:61` (`reexecution_blocking_cause`) and
  `gates/landing_readiness.py:79` (`obligation_blocking_cause`) each
  scope their blocking cause to a `frozenset` of two path prefixes now —
  the old exact `reports/{role}.md` path, plus a `reports/{role}-`
  prefix — matched with `startswith` per the module's own scope-matching
  convention (canonical: `gates/landing_readiness.py:41-43` docstring,
  read directly).
- `gates/ci.py:438` (`_phase2_record_evidence`, the CI closing-intent
  evidence check) can no longer recover the disambiguator from the PR's
  branch name, because the branch axis was deliberately left on the old
  scheme (see deviation note below) — it now falls back to a new
  `gates/ci.py:409` (`_fetch_ref_dir_names`) directory listing of the PR
  branch's `docs/issue-<n>/reports/` via the same `gh api .../contents/<path>`
  call `_fetch_ref_file` already uses (GitHub's contents API returns an
  array when `path` is a directory), and picks the first `{role}-*.md`
  entry that resolves.

The one post-hoc, non-blocking site:

- `board.py:849` (`ownership_report`) now also accepts a
  `{role}-`-prefixed report filename as "this session's own record" in
  addition to the exact `{role}.md` match it already had.

`board.py`'s live board-discovery walk itself (`_skill_axis_report_names`,
not one of the issue's 7 cited sites) needed no change — it already
discovers any `reports/*.md` file outside the fixed role-name enum that
carries a `loop_state` frontmatter key, generically, since issue #2432
stage 4's dual-scheme coexistence work (canonical: `board.py:693-717`,
read directly); that is why board discovery is not itself in the 7-site
list.

`on-the-record/gates/gates.py`, the packaged plugin-cache copy of
`gates/gates.py` (issue #2295's drift class), was re-synced with `cp
gates/gates.py on-the-record/gates/gates.py` after the `gates/gates.py`
edit — see "Acceptance verification" #5.

## Why

`pipeline.checkout_issue_branch_for_skill()` already existed with the
right naming and the right reason for that naming (a skill name is not
unique per session; the lease-disambiguator is the actual collision-proof
key — `pipeline.py:1144`'s docstring, `docs/decisions/2026-08-25-retire-role-axis-staging.md`)
before this issue. Reimplementing an equivalent `f"{role}-{token}"`
string at each of the record-side call sites, instead of factoring the
one existing naming rule out into something both the branch caller and
the record caller share, would have been exactly the "second naming
scheme" the issue's acceptance criteria rule out.

## What did not work

None.

## Rationale for deviations

The git branch name was deliberately NOT switched to
`checkout_issue_branch_for_skill` (i.e. `spawn.py:2919`'s
`checkout_issue_branch(cwd, issue, role)` call was left unchanged), even
though acceptance check #1 talks about "the existing
`checkout_issue_branch_for_skill` naming" and the issue's own text calls
the function "never wired to any caller." This is a deviation from what
a literal reading of that sentence could suggest, so it is recorded here
per the record-shape directive.

Reason (canonical: `gates/ci.py:623` and `gates/gates.py:866-928`, read
directly): `gates/ci.py:623` calls `gates.role_scope(repo, branch)` as
part of `ci.check()` — the CI gate this repository runs on every PR,
including this one. `role_scope()` (`gates/gates.py:903`) resolves the
acting role by regex-matching the PR's head branch against `BRANCH_ROLE
= re.compile(r"^issue-[^/]+/([^/]+)$")` and looking the captured group
up directly in `spawn_roles.json` via `_role_cfg(role)`. If the branch
name became `issue-<n>/<role>-<disambiguator>`, that captured group
would be the whole `<role>-<disambiguator>` string, which is not a key
in `spawn_roles.json` — `_role_cfg()` would raise `KeyError`, and
`role_scope()` would then return "역할 정의를 읽을 수 없어 write_scope
를 검사할 수 없다" for every future PR from a real spawn, breaking
`write_scope` enforcement for legitimate work going forward.
`gates/ci.py:90-97` (`_issue_and_role_from_branch`) has the identical
assumption via `_ISSUE_ROLE_BRANCH = re.compile(r"^issue-(\d+)/([^/]+)$")`.

The issue's own list of 7 sites does not include `gates/gates.py:903`
(`role_scope`), `gates/gates.py:866` (`BRANCH_ROLE`), or `gates/ci.py:90`
(`_issue_and_role_from_branch`/`_ISSUE_ROLE_BRANCH`) — all three would
need to change together with the branch-naming switch to keep
`write_scope` enforcement alive, and none of them are named. Read
together with the explicit non-goal "do not touch core's configs here,"
and with the issue calling out `gates/gates.py:852` (now line 873,
`_always_writable`) specifically as "the sharpest risk" rather than
`role_scope()` more broadly, the interpretation taken here is that "the
record filename is the root" scopes this issue to the filename the
record is written under, not to the branch string — the branch axis
(the staging decision doc's "job d") stays on its existing naming,
unaffected, and only `pipeline.skill_lease_name()` (the naming rule
itself, not the git-checkout side effect) is reused for the record's
filename stem.

## Acceptance verification

- Acceptance 1 (real spawn produces a record at the skill+lease path,
  with its `bootstrap_timing` line) — checked: real-spawn-demo — result:
  pass

  `spawn._spawn_one()` was run for real (unmocked `checkout_issue_branch`,
  unmocked `write_record_skeleton`, unmocked disambiguator minting; only
  the actual `claude` binary launch was swapped for `cat`, following this
  repo's own established pattern in
  `test/test_spawn_cross_family_skill_selection.py`'s
  `SpawnOneCrossFamilyAcceptanceTest._run()`, which mocks `spawn_cmd` the
  same way) against a real local git repo with a bare `origin` remote.
  derived: python3 /tmp/verify_2545_real_spawn.py (script not committed —
  ad hoc verification per the "verify-at-landing" contract clause, not a
  persistent test file)

  ```
  === rc ===
  0
  === reports/ listing ===
  docs/issue-999999/reports/implementation-e975f7e7.md
  === disambiguator sidecar ===
  /tmp/tmpo6n0zs_p/work.record-disambiguator.txt exists= True
  content: e975f7e7
  === bootstrap_timing stderr line ===
  [implementation] bootstrap_timing admission=0.030 skill_resolve=0.003 workspace=0.000 branch=0.050 returned_pr_gate=0.000 auto_sweep=0.000 rulebook=0.000 core=0.000 gh_token=0.026 settings=0.002 cross_family=11.193 issue_fetch=0.379 directive_write=0.010 design_bearing=0.001 spawn_cmd=0.000 board_snapshot=0.000 total=11.695
  ```

  The preamble text piped to the spawned session's stdin (captured from
  the real session log the fork-child wrote, since the `claude` argv was
  replaced by `cat`) carries the new path:

  ```
  레코드 스켈레톤: docs/issue-999999/reports/implementation-e975f7e7.md 가 미리 쓰여 있다 — 구조를 새로 만들지 말고 스켈레톤의 섹션을 채워라(이슈 #2135, #2545).
  ```

  The checked-out branch stayed on the old scheme, confirming the
  deviation note above:

  ```
  $ git -C /tmp/tmpo6n0zs_p/work branch --show-current
  issue-999999/implementation
  ```

- Acceptance 2 (every one of the 7 sites migrated or justified, each with
  a file:line citation) — checked: seven-site-sweep — result: pass

  All 7 sites the issue cited are addressed above under "What was done,"
  each with its current file:line. None were left unmigrated; the one
  additional site touched beyond the 7 (`on-the-record/hooks/record-scaffold.sh`)
  is the CLI scaffolder the issue's own preamble table lists as a sibling
  concern to `directive_assembly.py`'s writer, and `board.py`'s generic
  `_skill_axis_report_names()` discovery walk is explicitly justified
  above as not needing migration.

- Acceptance 3 (`write_scope` still refuses an out-of-scope diff under
  the new naming, before and after, quoted) — checked:
  write-scope-before-after-demo — result: pass

  Two real git repos (bare `origin`, real commits, real push) were built
  on branch `issue-88801/implementation`. Case A commits only the
  session's own new-scheme record, "issue-88801/reports/implementation-a1b2c3d4.md";
  case B commits that same record plus an edit to `README.md`, a file
  genuinely outside `implementation`'s declared `write_scope` (`src/**`,
  `test/**`, `tests/**`). `gates.role_scope(work, branch)` was called
  directly — the same function `gates/ci.py:623` calls in the real CI
  gate.

  derived: python3 /tmp/verify_2545_write_scope_before.py (BEFORE —
  `gates/gates.py` loaded via `git show HEAD:gates/gates.py`, i.e. the
  version on disk before this change) and python3
  /tmp/verify_2545_write_scope.py (AFTER — the working tree's current
  `gates/gates.py`); scripts not committed, ad hoc verification.

  BEFORE (own new-scheme record wrongly refused, and the genuinely
  out-of-scope file also refused):

  ```
  ### [BEFORE FIX] CASE A: only the session's own new-scheme record changes
  violations: ['write_scope 이탈: docs/issue-88801/reports/implementation-a1b2c3d4.md (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']

  ### [BEFORE FIX] CASE B: record change + out-of-scope README.md edit
  violations: ['write_scope 이탈: README.md (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)', 'write_scope 이탈: docs/issue-88801/reports/implementation-a1b2c3d4.md (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']
  ```

  AFTER (own new-scheme record now correctly permitted; the genuinely
  out-of-scope file is still refused, unchanged):

  ```
  ### CASE A: only the session's own new-scheme record changes (should be ALLOWED)
  branch: issue-88801/implementation
  violations: []

  ### CASE B: record change + a genuinely out-of-scope file (README.md) (should be REFUSED)
  branch: issue-88801/implementation
  violations: ['write_scope 이탈: README.md (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation-*.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)']
  ```

- Acceptance 4 (`git status` shows no modification or rename under
  `docs/issue-*/reports/` for any pre-existing record) — checked:
  git-status-reports-scope — result: pass

  derived: git status --short -- 'docs/issue-*/reports/'

  ```
  (no output)
  ```

  The only docs-tree change in the full `git status --short` output is
  this issue's own new, untracked issue-2545 docs tree (this record) —
  not a modification or rename of any other issue's existing record.

- Acceptance 5 (`on-the-record/gates/gates.py` byte-identical to
  `gates/gates.py`) — checked: packaged-copy-diff — result: pass

  derived: diff gates/gates.py on-the-record/gates/gates.py; echo "exit
  code: $?"

  ```
  exit code: 0
  ```

## Regression check

derived: python3 -m pytest test/ -q (run twice: once against this
change, once with the change `git stash`-ed out, to separate pre-existing
failures from anything this change touched)

```
13 failed, 255 passed in 3.53s
```

The same 13 failures occurred, byte-for-byte identical failure list, with
this change's 9 modified files stashed out — a pre-existing environment
fixture issue (canonical: `test/test_spawn_skill_judge_haiku_timeout_overlap.py`
failure traceback, read directly — `resolved_skill_dirs()` expects a
skill named `work` in this environment's skill-repository checkout, but
`_admission_check_directive_completeness()` resolves the real
`MUSTER_SKILLS=work-in-english` env value against it), unrelated to this
change. `test/test_branch_naming_dual_scheme.py` (issue #2432's own
dual-scheme regression suite) and `gates/test_tier_contract.py` +
`on-the-record/monitors/test_poll_heartbeat.py` were also run directly:

```
9 passed in 0.91s
30 passed in 6.80s
```

## Open findings

None.

## Next steps

None — loop_state is terminal (`landed`).

## Skill verdicts

skill-verdict: work-in-english — applied: invoked; code comments in
touched files match each file's own pre-existing Korean-comment
convention (per the skill's own "follow the project" / "match
surrounding style" guard), while this record, commit messages, and the
PR are written in English.
other mounted skills: not triggered

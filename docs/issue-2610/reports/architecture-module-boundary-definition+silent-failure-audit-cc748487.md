---
issue: 2610
role: architecture-module-boundary-definition+silent-failure-audit-cc748487
author: architecture-module-boundary-definition+silent-failure-audit-cc748487
skills: architecture-module-boundary-definition (skill-repository(297e350)), silent-failure-audit (skill-repository(297e350))
loop_state: landed
upstream:
  - path: docs/issue-2548/reports/architecture.md
    sha: c0c180e01a22f7ab4d571e00b8677d70bce0b019
---

# issue-2610 — architecture-module-boundary-definition+silent-failure-audit-cc748487 record

## What was done

Retired `spawn_roles.json` (the 44-entry closed identity table) and split
its content back into `roles/<role>.json` — one file per role — then
repointed every real consumer at that directory instead of the single
file, and removed the two discovery surfaces that presented the table as a
browsable catalog.

derived: `python3 -c "import json,pathlib; [pathlib.Path('roles', f'{r}.json').write_text(json.dumps(c, ensure_ascii=False, indent=2, sort_keys=True)+chr(10), encoding='utf-8') for r,c in json.load(open('spawn_roles.json', encoding='utf-8')).items()]"` — result: 44 files written under `roles/`, byte-for-byte the same per-role config `spawn_roles.json` held (verified by re-globbing `roles/*.json` back into a dict and diffing against the original parse before deletion — no field dropped).

Consumers repointed (real readers, not just comment mentions), derived:
`grep -rln 'spawn_roles' --include=*.py --include=*.sh --include=*.md .` on
`HEAD` before this session's edits, cross-checked against each hit's
actual code (not just its comment) this session: `spawn.py`
(`role_data()` now globs `roles/*.json`), `gates/gates.py` + its packaged
mirror `on-the-record/gates/gates.py` (`_role_cfg()`), `gates/roles_due.py`
(`load_triggered_specs()`), `gates/spec_schema_five_activities_test.py`
(`_role_data()`), `on-the-record/hooks/record-scaffold.sh`,
`on-the-record/hooks/delegated-judgment-gate.sh`,
`on-the-record/hooks/merge-allow-gate.sh`,
`on-the-record/hooks/quality-bar-gate.sh`. `pipeline.py`, `consult.py`,
`gates/patrol_wiring.py` already called through `spawn.role_data()`, so
only their comments needed updating (no functional change — the seam
absorbed the storage-shape change without a call-site change, see Why).
Comment-only fixes: `gates/closure_sweep.py`, `gates/scope_adherence.py`,
`gates/spawn_on_pr.py`, `test/test_spawn_role_skill_resolution.py`,
`test/test_spawn_skills_mount.py`.

canonical: `python3 spawn.py | grep -c '역할:'` — result: `0`.
canonical: `ls spawn_roles.json; grep -rln 'spawn_roles' --include=*.py --include=*.sh --include=*.md . | grep -v '^./docs'` — result: `ls` reports the file absent; the grep (adjusted for this environment's GNU grep not prefixing `./` on an explicit `.` path — verified with a throwaway fixture that plain `grep -v '^docs'` is the equivalent filter here) returns zero non-docs hits. Full raw hit list before the docs-only filter is quoted in Open findings for inspection.

`spawn.py`'s bare-invocation output (previously the `역할:` catalog) now
prints the skill-repository checkout's own directory listing instead —
derived: `python3 spawn.py 2>&1 | tail -3` — result: `스킬 소스:
/home/jwjung/skill-registry/skills (273개) — --skills 가 받는 이름은 이
디렉터리 목록이다(고정 역할 카탈로그는 이슈 #2610 으로 은퇴했다): ...`
(273 real skill names, the same list `--skills`'s own fail-closed unknown-name
error already validates against — not a new invented catalog).
`on-the-record/commands/consult.md:30`'s pointer was rewritten to describe
`<역할>` as free text and to send a reader to that same bare-`spawn.py`
output for the real skill-source listing, rather than deleting the pointer.

## Why

canonical: `gh issue view 2610` (read this session) — the issue's two
`must not` clauses shaped the design: (1) don't replace the catalog with
another curated list of names, (2) don't delete `consult.md:30`'s pointer
without replacing it.

Splitting into `roles/<role>.json` is not a second catalog in the sense
the issue prohibits: nothing in the discovery path (`spawn.py`'s
bare-invocation output, `consult.md`) enumerates or points a session at
`roles/` — a session picking a name to spawn against was never the
problem `roles/` solves; it is config storage addressed by callers that
already hold a role string, the same category as `docs/specs/*.md`. This
also matches the codebase's own already-documented shape:
`docs/specs/role-spec-template.schema.json` (not modified this session)
still describes `roles/<role>.json` / `roles/specs/<role>.spec.json` as
the canonical per-role layout, and `gates/gates.py`'s
`PROTECTED_ROOT_DIRS` (not modified this session) already listed `"roles"`
— canonical: `gates/gates.py:36` (read this session) — both predate this
change and were never updated when #2539 consolidated the directory away,
so reviving the directory is not an invented shape.

Applying the mounted architecture-module-boundary-definition skill (rule
1, hide a likely-to-change decision behind a stable interface) after most
of the investigation confirmed rather than changed the approach already
under way: nearly every real consumer already called through
`spawn.role_data()` or `gates._role_cfg(role)` rather than touching
`spawn_roles.json` directly, so swapping the storage shape behind those
two functions (one-file -> one-file-per-role) required zero call-site
changes in `pipeline.py`, `consult.py`, or `gates/patrol_wiring.py` — the
storage decision was already hidden behind those seams before this
session started; this session only had to change what sat behind them.
Rule 3 (organize by domain concept) and rule 5 (bounded contexts as the
seam, not a database-schema-style single blob) both support role-as-file
as the boundary, since no role's config is read together with another
role's in the steady state (patrol/poll-heartbeat/five-activities are the
only enumerate-all-roles callers, and a directory glob serves that
identically to a dict's `.keys()`).

Rejected alternative: keep one consolidated JSON file but rename it (e.g.
`role_registry.json`). Rejected because the acceptance's own grep checks
for the literal string `spawn_roles`, not for "a single consolidated
file" — a rename would pass that mechanical check while reproducing the
exact defect the issue names (one file enumerating 44 identities), which
a reviewer or the warrant-hunter would flag as gaming the letter of the
check. It would also not explain why `docs/specs/role-spec-template.schema.json`
already documents a per-file shape.

Rejected alternative: retire `record_fields`/`record_spec` entirely and
replace with a universal, role-agnostic vocabulary (the way
`verifies_subject`, per issue #2623, and `PR_TRIGGERED_RECORD_KINDS`'s
removal per #2615, made those two axes role-agnostic). Rejected after
checking `gates/spec_schema_five_activities_test.py`'s five-activity,
`quality_bar`, and `degree_level_knowledge` assertions (read this
session) — these encode real, role-specific substance (e.g.
`ux-engineering`'s quality bar differs from `secure-coding`'s) that a
single shared vocabulary cannot represent without losing content; no
generic replacement (`implementation.spec.json` or similar) exists in the
repo today — derived: `find . -iname "*.spec.json" -not -path "./.git/*"`
(read this session) — returns nothing, so inventing one would be new,
uncited architecture, not a follow of an existing pattern.

## What did not work

- First edit to `gates/gates.py` renamed the module constant from
  `_ROLE_DATA_PATH` to `_ROLE_DATA_DIR` and updated `_role_cfg()`, but
  missed four downstream error-message f-strings that still referenced
  the deleted name `_ROLE_DATA_PATH` — derived: `grep -n
  "_ROLE_DATA_PATH" gates/gates.py` (run against the mid-session,
  post-rename-pre-fix state) — result: 4 hits, all inside
  `record_enums`/`record_refusal_reasoned`/`record_checked_claims`'s
  except-branch error strings. Would have raised `NameError` on the
  fail-closed path the first time one of those functions hit an
  unreadable role. Caught by re-reading the full file for remaining
  `_ROLE_DATA_PATH` references before running tests, not by a failing
  test — no test in the current suite exercises that specific
  except-branch with a real bad-role record. Fixed by replacing each with
  `_ROLE_DATA_DIR / f'{role}.json'`, re-synced to the
  `on-the-record/gates/gates.py` mirror, and re-verified — derived:
  `python3 -c "import sys; sys.path.insert(0,'gates'); import gates;
  gates._role_cfg('nonexistent-role-xyz')"` — result:
  `FileNotFoundError(2, 'No such file or directory')`, not `NameError`.

## Upstream basis

canonical: `docs/issue-2548/reports/architecture.md` "Step H" section
(read this session, not modified) — named this exact retirement
("retire `spawn_roles.json`'s closed table itself ... or narrow it to
only the fields `consult.py`'s advisory paths still read") as the last
step of the #2548 identity-model redesign, and its "what breaks if Step H
lands before Step C/D" paragraph is why this session checked (and found
already-landed) that `role_settings()` no longer hard-exits on an
unrecognized role — canonical: `pipeline.py:225-231` (read this session)
— `spec = data.get(role, {})`, a graceful fallback, not a `sys.exit`.

canonical: `gh issue view 2539` / `gh pr view 2542 --repo
tokenmaxxxer/on-the-record` (read this session) — the prior consolidation
this session partially reverses: #2539 merged `roles/*.json` (44 files) +
`roles/specs/*.spec.json` (43 files) into `spawn_roles.json` as an
intermediate simplification step inside the larger #2548 identity-model
migration, not as a permanent architectural preference — its own issue
text frames it as stage "6C of three," with #2548's Step H (this issue)
as the eventual full retirement.

canonical: `gh pr view 2624 --repo tokenmaxxxer/on-the-record --json
number,state,url,headRefName` (read this session) — result: number=2624,
state=OPEN, headRefName=issue-2610/prose-modes-18b36a06 — the third
acceptance bullet's "spawn a session end-to-end and show it reaching PR"
check, executed live this session: `python3 spawn.py --skills
prose-modes "<verification-scoped task>" --issue 2610 --two-phase
--unattended` bootstrapped a real workspace/branch, resolved skills,
composed the directive (all three steps route through the
`roles/`-backed `role_data()`/`role_settings()` changed this session),
ran to completion, and opened PR #2624
(`https://github.com/tokenmaxxxer/on-the-record/pull/2624`) — a real,
verification-scoped record commit, not a dry run.

canonical: `bash on-the-record/hooks/record-scaffold.sh implementation
999999 /tmp/rs-test` (read this session) — result:
`record-scaffold: wrote /tmp/rs-test/docs/issue-999999/reports/implementation.md`,
exit 0, frontmatter correctly carrying `loop_state:` (the one
`record_fields` key `roles/implementation.json` declares) as a
`PLACEHOLDER` token — the second half of the third acceptance bullet.

derived: `python3 -m pytest -q` — result: `485 passed, 16 failed` both
before this session's changes (`git stash`) and after (`git stash pop`) —
byte-identical failure name set both times (network/git-remote failures
in a sandboxed test environment, e.g. `fatal: 'origin' does not appear to
be a git repository`), confirmed by diffing the two `FAILED` line lists.
Zero new failures, zero newly-passing tests attributable to this change.

## Open findings

- A dispatched before-landing warrant-hunter (stance 1: silent-on-malformed-input) found that `on-the-record/hooks/delegated-judgment-gate.sh`'s `load_roles()` originally skip-and-continued past a corrupt `roles/<role>.json`, silently dropping one role from the panel while the pre-split single-file version zeroed all 44 roles on any corruption and forced `escalate(...)` on every decision. Fixed in this same session. derived: `grep -n "return {}" on-the-record/hooks/delegated-judgment-gate.sh` — result: two `return {}` sites (directory-missing case, and now the per-file parse-failure case too) — `load_roles()` fails the whole catalog closed the moment any one file fails to parse, reproducing the old blast radius. Not re-verified with a second hunter pass (turn budget) — the fix is a one-line narrowing (`continue` -> `return {}`) directly matching the hunter's own "Expected" section.
- Applying the architecture-module-boundary-definition skill (invoked
  this session) surfaced a pre-existing rule-4 gap (public-interface,
  no-direct-reach-through) this session did not fix: several consumers
  — `on-the-record/hooks/record-scaffold.sh`,
  `on-the-record/hooks/delegated-judgment-gate.sh`,
  `on-the-record/hooks/merge-allow-gate.sh`,
  `on-the-record/hooks/quality-bar-gate.sh`, `gates/roles_due.py`,
  `gates/spec_schema_five_activities_test.py` — each open and parse
  `roles/<role>.json` (or glob `roles/*.json`) themselves instead of
  going through one shared reader, the same duplication that existed
  against `spawn_roles.json` before this session. derived: `grep -ln
  '\.json"' gates/roles_due.py gates/spec_schema_five_activities_test.py
  on-the-record/hooks/record-scaffold.sh
  on-the-record/hooks/delegated-judgment-gate.sh
  on-the-record/hooks/merge-allow-gate.sh
  on-the-record/hooks/quality-bar-gate.sh` — result: all 6 files. Resolution
  path: consolidating these into one shared accessor (importable from both
  plain-Python gates and the bash-invoked heredoc scripts) is a real
  follow-up but is new abstraction beyond this issue's ask (retire the
  table, keep consumers working) — left as a candidate future issue, not
  fixed here.
- The raw (pre-docs-filter) hit list for `grep -rln 'spawn_roles'
  --include=*.py --include=*.sh --include=*.md .` is entirely
  `docs/issue-*/reports/**` and `docs/handbooks/observer-verification.md`
  — historical records of past sessions' own work, out of scope per the
  issue's own "must not: do not touch records under `docs/`." No
  resolution path needed; these are expected permanent mentions of a
  retired filename in past records.
- canonical: `gh pr view 2624 --repo tokenmaxxxer/on-the-record --json
  number,state,url` (read this session) — result: number=2624,
  state=OPEN. PR #2624 (the live spawn-verification PR opened this
  session) is left open rather than merged or closed — it carries a
  real, self-scoped verification record and no code change; merging or
  closing it is a call for the human approver, not this session
  (contract v3: never approve or merge yourself). Resolution path: none
  needed from this role; noted here so the reviewer of this PR knows
  #2624 exists and why.

## Next steps

None — `loop_state: landed`, all four acceptance checks executed live
and quoted above.

skill-verdict: architecture-module-boundary-definition — applied: invoked; mid-session, after the roles-directory design was already underway from direct investigation of the consumer list, to cross-check the boundary decision — canonical: this skill's own `references/rules.md` (read this session) rule 1 (hide a likely-to-change decision behind a stable interface) matched how `role_data()`/`_role_cfg()` already shielded every real consumer from the storage-shape change; rules 3/5 (domain-concept/bounded-context seams) supported role-as-file; the check surfaced the rule-4 gap logged under Open findings.
skill-verdict: silent-failure-audit — not-applicable: this issue's work is a data-storage migration (splitting one JSON file into many) and call-site repointing, not new AI-authored error-handling logic — the `try/except (OSError, ValueError)` blocks touched are unchanged in shape from what already existed (fail-closed to `{}`/refusal, same as before), not newly introduced error-swallowing.

---
code_under_review: HEAD
loop_state: scope-undeclared
type: partial-delivery
breaking: false
verdict: cannot-verify
---

# issue-2289 — role retirement stage 6 (final): partial delivery, scope-exceeded stop

## What was done

canonical: this session's own file reads of gates/gates.py, pipeline.py,
skills.py, consult.py, board.py, spawn.py (this turn, via Read/Bash/Agent
tool calls in this conversation).

Surveyed the stage-6 proposal (`docs/issue-2241/proposals/2026-08-25-stage-6-role-deletion.md`)
against the live tree. Found the `roles/*.json` consumer set is larger than
the proposal's write set: `gates/gates.py` (`record_enums`, `role_scope`,
`record_refusal_reasoned`), `pipeline.py` (`role_settings()`), `skills.py`
(`resolve_role_source()`/`_ROLE_SKILLS`), `consult.py` (5 sites), `board.py`
(`_sp.ROLES`), `spawn.py` (`ROLES` tuple) all read it, on top of the four
named in the issue.

Landed only the confirmed-dead subset (no live caller found by direct read,
canonical as above), in this commit:
- git rm: gates/role_spec_shape.py (removed, no successor),
  on-the-record/gates/role_spec_shape.py (removed, packaged copy),
  gates/need_detector.py (removed), gates/test_need_detector.py (removed),
  and derived: `git rm` output this turn — the 12 gates/test_role_spec_shape*
  batch test files plus gates/test_role_spec_shape_open_decision.py (removed,
  all covered `role_spec_shape.py` which is removed).
- spawn.py: removed the `needs-due` CLI block that imported the now-removed
  `need_detector.py` (its only live caller, canonical: this session's Read of
  spawn.py before edit).
- on-the-record/hooks/test_hook_cache_layout.py: dropped `role_spec_shape.py`
  from `_SYNCED_GATE_FILES` and repointed the drift-check test and broken-
  cache fixture at `gates.py` instead (edited in place, still present).

`roles/` and `roles/specs/` directories were not touched this session.

## What did not work

- First `git rm` batch call failed on a stale `.git/index.lock` held by an
  unrelated concurrent `git status` in a sibling workspace (canonical: ps aux
  output this turn showed `git -C .../on-the-record-issue-2451-implementation
  status --porcelain`, a different repo checkout). Retried after the lock
  cleared; second attempt succeeded.
- CHANGES round on PR #2495: `gh pr edit` to remove the "Closes #2289"
  trailer per reviewer request was blocked by `pr-preflight.sh`, which
  requires a Closes/Fixes/Resolves match unconditionally whenever
  `CORE_BUILD_NOW=1` forces `phase2 = True` (canonical: this session's `gh
  pr edit` attempt this turn, hook output quoted in the deviation-log entry
  below), with no partial-delivery exception found in the file. Kept the
  trailer and rewrote the surrounding body instead — see Rationale below and
  `docs/issue-2289/reports/implementation/deviation-log/20260826T030211879705-d80f87825dd04f0d.md`.

## Rationale for deviations

Scope exceeded per warrant protocol: the proposal's write set and the issue's
"four consumers" framing undercounted the real `roles/*.json` surface (see
above). Editing `gates/gates.py`/`pipeline.py`/`skills.py`/`consult.py`/
`board.py`/`spawn.py`'s `ROLES` tuple together is required to safely delete
`roles/`, and a partial edit there risks breaking every future session spawn
(several are fail-closed). A turn-budget convergence warning arrived mid-
build; rather than rush the fail-closed paths, this session stopped at the
confirmed-dead subset and defers the rest.

Separately, the CHANGES round on PR #2495 asked to remove the "Closes #2289"
trailer from the PR body since this delivery is explicitly partial. That
edit is blocked by `pr-preflight.sh`'s phase2 model (see "What did not
work" above) — a gate outside this session's write set; fixing the gate's
lack of a partial-delivery exception is a separate change from issue-2289's
own scope and is not attempted here. The trailer stays in the PR body, with
prose making the partial status and the gate conflict explicit, so a human
merging the PR can decide whether to let the auto-close fire.

## Open findings

- canonical: this session's own `ls roles/ roles/specs/` this turn showed
  files still present — `roles/` and `roles/specs/` remain on disk, full
  stage-6 deletion is outstanding. Resolution path: a follow-up session
  should migrate, in one coordinated commit: `spawn.py` `ROLES` tuple,
  `board.py`'s `_sp.ROLES` iteration, `gates/gates.py`'s `record_enums`/
  `role_scope`/`record_refusal_reasoned` (also drop their callers in
  `gates/record_lint.py` and `gates/ci.py`), `pipeline.py`'s
  `role_settings()` — canonical: this session's Read of its body this turn
  showed `sandbox.enabled` force-set `False` and `permissions.allow` largely
  inert under `bypassPermissions`, suggesting it may already be near
  role-agnostic, but that needs a real diff across all `roles/*.json` to
  confirm before collapsing it — `skills.py`'s `resolve_role_source()`
  (recommended: delete it, migrate its 6 call sites in `spawn.py`,
  `pipeline.py`, `consult.py` onto `resolve_skill_source()`), and
  `consult.py`'s 5 existence-check sites, then delete `gates/roles_due.py`
  (same dead-once-`roles/specs/`-is-gone shape as the two modules removed
  this session) and finally `roles/`/`roles/specs/` themselves, then run the
  full suite.
- No test run was executed before landing (turn-budget cutoff). Resolution
  path: the follow-up session must run the full suite before its own
  landing, and also before extending this session's change further.
- canonical: this session's `grep -n "roles/" on-the-record/hooks/record-scaffold.sh
  on-the-record/hooks/quality-bar-gate.sh on-the-record/hooks/accumulation-claim-guard.sh`
  this turn — three hooks reference `roles/*.json`-shaped paths on top of the
  six code consumers above: `record-scaffold.sh` opens `roles/<role>.json`
  to seed a new record's fields (`role_file = plugin_root / "roles" / f"{role}.json"`,
  line 38 at review time); `quality-bar-gate.sh` opens
  `roles/specs/<role>.spec.json` for the 7 bar-scoped roles
  (`spec_path = os.path.join(CHECKOUT, "roles", "specs", role + ".spec.json")`,
  line 214); `accumulation-claim-guard.sh` regex-classifies a changed path
  as `^roles/[^/]+\.json$` to detect repeated one-line-edit claims (line
  114) — it does not open the file, only pattern-matches the path, but its
  behavior is still contingent on `roles/` existing in its current shape.
  All three break if `roles/` is deleted without a coordinated edit.
- canonical: this session's `grep -rl CLAUDE_ROLE on-the-record/hooks/` this
  turn returned 51 files (149 total occurrences via `grep -ro`); 25 of the
  51 are non-test `.sh`/`.py` hook sources, the rest are that hook's own
  `test_*.py`. This session did not classify which of the 25 are
  role-file-dependent (read `roles/*.json` to resolve the value) vs.
  merely role-name-dependent (compare `CLAUDE_ROLE` against a literal) —
  that classification is unstarted.

## Deferred remainder (follow-up issue candidate list)

canonical: same evidence cited in "What was done" and "Open findings" above
(this session's Read of gates.py/pipeline.py/skills.py/consult.py/board.py/
spawn.py, and this session's grep of on-the-record/hooks/ this turn) —
compiled here into one list for a follow-up issue to scope its write set
from, rather than re-deriving it from scratch:

1. `roles/` and `roles/specs/` directories themselves (deletion target).
2. `spawn.py`'s `ROLES` tuple.
3. `skills.py`'s `_ROLE_SKILLS` mapping and `resolve_role_source()` (6 call
   sites across `spawn.py`, `pipeline.py`, `consult.py`).
4. `consult.py` (5 existence-check sites), `pipeline.py`'s `role_settings()`,
   `board.py`'s `_sp.ROLES` iteration.
5. `gates/gates.py`'s `record_enums`/`role_scope`/`record_refusal_reasoned`,
   plus their callers in `gates/record_lint.py` and `gates/ci.py`.
6. `gates/roles_due.py` and `spawn.py`'s `roles-due` CLI block.
7. Three hooks that reference `roles/*.json`-shaped paths, per Open findings
   above: `on-the-record/hooks/record-scaffold.sh`,
   `on-the-record/hooks/quality-bar-gate.sh`,
   `on-the-record/hooks/accumulation-claim-guard.sh`.
8. The `CLAUDE_ROLE` env var's disposition across the 25 non-test hook
   sources that reference it, per Open findings above — a follow-up
   session's own scope, not started here beyond the file count.

## Next steps

1. Coordinated edit of the six fail-closed code consumers listed above, in
   one commit, per the resolution paths given.
2. Delete `gates/roles_due.py` + `spawn.py`'s `roles-due` CLI block.
3. Migrate or retire the three `roles/*.json`-referencing hooks and classify
   the `CLAUDE_ROLE` references, per the deferred-remainder list above.
4. Delete `roles/` and `roles/specs/`, run the full suite, fix fallout.
5. Update `docs/handbooks/architecture-methodology.md` per the stage-6
   proposal's "What will be done".

## Doc-placement ladder

- [x] this implementation record, in this stage's reports directory

skill-verdict: implementation-blueprint — not-applicable: task was deletion/migration of existing modules, not new multi-module structure to design.
skill-verdict: work-in-english — applied: invoked; all commits, PR, and this record written in English per the skill.
other mounted skills: not triggered

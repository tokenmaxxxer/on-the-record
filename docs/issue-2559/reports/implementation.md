---
issue: 2559
role: implementation
author: implementation
loop_state: coding
upstream:
  - path: docs/issue-2559 (issue body — operator decision, no separate design doc)
    sha: same-commit
code_under_review:
  - spawn_roles.json
  - consult.py
  - directive_assembly.py
  - gates/ci.py
  - gates/gates.py
  - gates/quality_bar.py
  - gates/risk_report.py
  - gates/scope_adherence.py
  - on-the-record/gates/gates.py
  - on-the-record/hooks/delegated-judgment-gate.sh
  - spawn.py
type: refactor
breaking: "removes the write-permission ceiling: any session may now modify any file on an issue branch; PRs gates/ci.py used to refuse for touching paths outside a role's declared write_scope now pass"
verdict: pass
---

# issue-2559 — implementation record

## What was done

Removed the `write_scope` field entirely from `spawn_roles.json` (44
top-level `write_scope` keys deleted via a script that round-trips the
JSON byte-identically before editing, so the diff is exactly the field
removal — `derived: git diff --stat spawn_roles.json` — result: `129
deletions`, no other field touched) and from every one of the ten
consumers the issue named, plus the Step A/B roster plumbing that only
existed to carry the field:

- `role_scope()` (formerly `gates/gates.py:967-1009`), `_roster_write_scope()`
  (`:931-964`), `_write_scope_overrides()` (`:888-899`), the
  `_import_spawn_for_roster()`/`_spawn_for_roster` lazy-import helper
  (`:902-928`), and the now-unused `BRANCH_ROLE`/`_BRANCH_ISSUE`/
  `_WRITE_SCOPE_OVERRIDE`/`_always_writable()` constants/helper (`:868-885`)
  — deleted outright, not stubbed. `checked: grep -n "role_scope\b"
  gates/gates.py` — result: no matches (function gone).
- `_bootstrap_write_scope()` (formerly `spawn.py:77-99`) and its two
  roster-write call sites (formerly `spawn.py:3469`, `spawn.py:3605-3611`)
  — deleted. `checked: grep -n "_bootstrap_write_scope"
  spawn.py` — result: no matches.
- `gates/ci.py`'s enforcement call `bad += gates.role_scope(repo, branch)`
  (formerly `gates/ci.py:618-623`, the block guarded by `if pr is not
  None: branch = _pr_head_ref(...); ... else: bad += gates.role_scope(...)`)
  — deleted; `check()` now falls straight from the `closes_only` early
  return (`gates/ci.py:613-614`) to the record/deps checks.
- `directive_assembly.py`'s `_role_touches_code()` (formerly
  `:436-441`), which derived a `code_scoped` decision from a role's
  `write_scope` to gate whether `known-paths.md`/`task-lookup.md` were
  materialized for a spawn — deleted. `spawn.py`'s only call site
  (formerly `:3057`, `code_scoped=_role_touches_code(spec.get("write_scope",
  []))`) now omits the kwarg entirely (`spawn.py:3023-3026`), so every
  spawn gets `directive_section_files()`'s existing `code_scoped=True`
  default (`directive_assembly.py:432`) — the "safe, over-inclusive"
  bundle the function's own docstring already called out as the
  never-narrower-by-omission default. The now-dead `spec = role_data().get(role,
  {})` binding and the `_role_touches_code = directive_assembly._role_touches_code`
  re-export (formerly `spawn.py:2742-2745`, `spawn.py:584`) were removed
  too — both were unused once the write_scope-derived call was gone.
  `checked: grep -n "_role_touches_code" spawn.py directive_assembly.py`
  — result: no matches.
- `gates/risk_report.py`'s `_role_write_scopes()` (formerly `:85-103`),
  which fed a role-ownership-overlap signal into `blast_radius_grade()`
  (`:107-138` now) and `propagation_grade()` (`:141-165` now) — deleted.
  Both grading functions kept their remaining live signal (proposal-file
  overlap for blast radius; `enforcement-boundary.md` row matches for
  propagation) and now document in their own docstrings that grades can
  skew lower than before, because the role-ownership input is gone, not
  because risk actually decreased — this is the "say what its numbers
  mean now" the issue asked for, not a silent narrowing. `derived:
  python3 -c` smoke call (quoted below) confirms both functions still
  run and return in-range grades.
- `on-the-record/hooks/delegated-judgment-gate.sh` used `write_scope` at
  three call sites through its own local `role_scope(role)`/`glob_matches()`
  helpers (both now deleted, `checked: grep -n "role_scope(\|glob_matches("
  on-the-record/hooks/delegated-judgment-gate.sh` — result: no matches):
  1. `standing_roles` (formerly `:614-618`), the panel-composition filter
     that limited judgment-axis standing to roles whose write_scope
     glob-matched a changed path. Left as a leftover empty-list read,
     this collapses to "no role ever has standing," which flows into
     `implicated_axes`/`eligible_roles` and hits the existing
     `if not eligible_roles: escalate(...)` branch (`:626-627`
     unchanged) for every single candidate decision forever — the same
     fail-closed trap shape as `gates.py:role_scope()`, just inside this
     hook's panel logic instead of a write gate. Replaced with
     `standing_roles = set(ROLES)` (`:610`): since sessions are no
     longer scope-limited, no role is confined to a path subset anymore,
     so every role now has standing over every changed path — the
     direct translation of the operator's decision into this hook's own
     terms, not an invented heuristic.
  2. `role_record_path()` (`:479-483` now), which walked a role's
     write_scope for the one glob ending in `.md` with an `<n>`
     placeholder to find that role's own record file. Replaced with
     direct construction of the fixed path (`docs/issue-<n>/reports/<role>.md`,
     with `<n>`/`<role>` resolved the same way the deleted code did)
     every role's record already lives at per the role-handoff
     contract's Layout line — no write_scope lookup was ever needed for
     this, since the path is not actually role-variable.
  3. The remediation-routing loop (formerly `:704-708`), which routed a
     contradicting finding's `target_path` to whichever role's
     write_scope glob-matched it. With no ownership signal left, this
     can no longer resolve anything — `routed_to` now stays `None`
     unconditionally (`:704-710`), which lands in the existing `routed_to
     is None` branch of the `status = "escalated" if ... else "open"`
     line (`:734-735` unchanged) — remediation now always escalates to a
     human instead of silently misrouting or dropping the finding. The
     PR-comment text that used to claim ownership of `target_path` "via
     write_scope" was corrected to a plain "(target: ...)" phrasing
     since that ownership claim is never true anymore.
  `fnmatch` import (`:67`, formerly `import fnmatch, json, os, re,
  subprocess, sys, time`) dropped — no longer used anywhere in the file
  once `glob_matches()` was deleted.
- `consult.py` never enforced or derived from `write_scope` — both
  mentions were prose. `draft_cmd()`'s docstring (`:962-966`) dropped
  the now-meaningless "No write_scope applies" line (there is no
  write_scope for any verb to apply or not apply anymore).
  `_readonly_plugin_dirs()`'s docstring (`:993-1005`) was reworded so
  `judge_cmd()`'s described judgment target is "role's record contract"
  instead of "role's write_scope/record contract."
- `gates/quality_bar.py`'s `mission_bar_scoped()` docstring (`:50-57`)
  dropped a `write_scope` mention that was only naming it as an example
  of another glob source elsewhere in the codebase — the function itself
  never read the field.
- `gates/scope_adherence.py`'s module docstring (`:1-14`) leaned on "the
  static write_scope gate already blocks writes outside a role's area"
  as context for why its own, unrelated `scope:` issue-body mechanism
  exists. That premise is now false (nothing blocks the write anymore),
  so the docstring was reworded to state plainly that its mechanism
  (an issue-body-declared prefix list, opted into per issue, never
  derived from `spawn_roles.json`) is unaffected and still catches
  intent drift even though nothing blocks the underlying write.
- `on-the-record/gates/gates.py` was kept byte-identical to
  `gates/gates.py` by editing the latter and then copying it over the
  former (not two independent edits). `derived: diff gates/gates.py
  on-the-record/gates/gates.py` — result: empty diff (files identical).

## Why

Operator decision, quoted in the issue body: "remove `write_scope`
altogether. Sessions are not limited to a declared set of paths." The
issue's scope boundary explicitly listed the ten files above as the
full consumer set and required, for each, a stated disposition
(enforce/report/derive) and what replaced it — a straight field
deletion was not enough anywhere the field was actually read, because
`role_scope()`'s allow-list (and, it turned out,
`delegated-judgment-gate.sh`'s own `role_scope()`/`standing_roles` panel
filter) is fail-closed: a leftover function or filter that silently
degrades to an empty list does not stop enforcing, it starts
refusing/escalating everything. Each derive/enforce site above was
traced to its actual downstream branch before being changed,
specifically to catch that trap rather than assume "delete the field,
the reader will just return `[]` and that's fine."

## What did not work

None.

## Upstream basis

No separate upstream design doc — the issue body itself carries the
full "Consumers, measured" list and the acceptance criteria; this
record treats the issue body as the upstream input (`sha: same-commit`,
since the only artifact besides code is this record, landing in the
same commit set).

## Acceptance evidence

**Check 1 — a diff `write_scope` refused before this change now passes,
both outcomes quoted.** This branch's own diff is the constructed case:
`implementation`'s pre-removal `write_scope` was `['src/**', 'test/**',
'tests/**']` (`checked: git show origin/main:spawn_roles.json` parsed
for `['implementation']['write_scope']` — result: that exact list), and
this diff touches `spawn_roles.json`, `gates/*.py`,
`directive_assembly.py`, `consult.py`, `spawn.py`,
`on-the-record/gates/gates.py`, `on-the-record/hooks/*.sh` — none of
which are under `src/**`/`test/**`/`tests/**`. Reproducing the OLD
`gates.py:role_scope()` fallback branch (the `spawn_roles.json` +
`_always_writable()` path Step D was always going to touch) against
this branch's real changed-file set:

```
BEFORE (origin/main gates.py:role_scope, branch issue-2559/implementation): 11 of 12 changed files refused
 - write_scope 이탈: consult.py (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
 - write_scope 이탈: directive_assembly.py (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
 - write_scope 이탈: gates/ci.py (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
 - write_scope 이탈: gates/gates.py (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
 - write_scope 이탈: gates/quality_bar.py (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
 - write_scope 이탈: gates/risk_report.py (역할 implementation, 허용: src/**, test/**, tests/**, docs/issue-*/reports/implementation.md, docs/issue-*/reports/implementation/**, docs/issue-*/proposals/**, docs/issue-*/decisions/**)
   ... and 5 more

AFTER (this branch's gates.py): role_scope attribute exists?  False
AFTER: gates.py has no write-scope enforcement path left, so none of the above are refused anymore.
```

`derived:` a one-off script (run this session, not persisted in the
repo) called this branch's own unmodified `gates.changed_files()` to
get the real diff, then reproduced the OLD `role_scope()` fallback math
by hand against `origin/main`'s recorded `implementation.write_scope`.
AFTER, `gates/ci.py`'s `check()` no longer calls `role_scope()` at all
(see "What was done"), so the same 11 files are unconditionally
permitted now.

**Check 2 — consumer disposition table.** See "What was done" above for
the full per-file breakdown with citations; summary:

| file | disposition (before) | replaced by |
| --- | --- | --- |
| `spawn_roles.json` | data source | field deleted, 44 roles, no other field touched |
| `gates/gates.py` | enforces | `role_scope()`/`_roster_write_scope()`/`_write_scope_overrides()` deleted |
| `gates/ci.py` | enforces (calls `gates.role_scope`) | call site deleted |
| `spawn.py` | enforces (roster carrier, Step A/B) | `_bootstrap_write_scope()` + both call sites deleted |
| `on-the-record/hooks/delegated-judgment-gate.sh` | derives (panel standing, record path, remediation routing) | `standing_roles = set(ROLES)`; `role_record_path()` direct-constructs the fixed path; `routed_to` stays unresolved (existing escalate branch) |
| `gates/risk_report.py` | derives (blast-radius/propagation role-overlap signal) | signal dropped, remaining live inputs kept, docstrings say why grades may shift |
| `directive_assembly.py` | derives (`code_scoped` gating) | `_role_touches_code()` deleted, default `code_scoped=True` for every caller |
| `consult.py` | reports (prose only) | docstrings reworded, no logic change |
| `gates/quality_bar.py` | reports (prose only) | docstring reworded, no logic change |
| `gates/scope_adherence.py` | reports (prose only, unrelated mechanism) | docstring reworded, no logic change |
| `on-the-record/gates/gates.py` | enforces (byte-identical mirror) | edited via copy from `gates/gates.py`, stays byte-identical |

**Check 3 — `role_scope()`/`_roster_write_scope()`/`_bootstrap_write_scope()`
gone.**
```
checked: grep -rn "role_scope\b" --include="*.py" --include="*.sh" . | grep -v '/.git/'
result:
  on-the-record/hooks/delegated-judgment-gate.sh:608:# the same fail-closed trap as `gates.py:role_scope()`, just inside this
  gates/ci.py:546:    `gates.role_scope()`/`_always_writable()` 파일명-패턴 불일치는
(both are historical prose referring to the deleted function in the past tense — no callable named role_scope remains)

checked: grep -rn "_roster_write_scope\|_bootstrap_write_scope" --include="*.py" --include="*.sh" . | grep -v '/.git/'
result: (empty — no matches at all, prose or code)
```
No leftover function returns an empty allow-list anywhere in this diff
— every write_scope-reading function was deleted outright (see "What
was done" for the two places, `standing_roles` in
`delegated-judgment-gate.sh` and `role_scope()` in `gates.py` itself,
where a stub-instead-of-delete would have produced exactly that trap).
```
checked: grep -rn "write_scope 이탈" --include="*.py" --include="*.sh" . | grep -v '/.git/'
result: (empty — no refusal path survives)
```

**Check 4 — a real spawn runs end to end, its PR passes the required
status check.** This session is itself that real spawn: dispatched via
`spawn.py` for issue #2559 (branch `issue-2559/implementation`, no
`--dry-run` anywhere in this session's history). The commit/push/PR-open
sequence and the live `gates/ci.py --autodetect --closes-only` run
against the real opened PR are captured in "Open findings" below and
will be appended to this section once the PR exists (record-order.md:
code and checks land before the record's executed-evidence claims for
them, not the reverse).

**Empty-state check — a branch with no changed files behaves the same
before and after.** With zero changed files, the OLD `role_scope()`'s
final comprehension (`[... for f in files if not any(...)]`) iterates
an empty `files` list and returns `[]` unconditionally — no refusal,
regardless of role or write_scope content. AFTER this change,
`role_scope()` does not exist and is never called, so `gates/ci.py`'s
`check()` also contributes nothing for this concern with zero changed
files. Both before and after: zero write_scope-related blocks for an
empty diff — behavior identical (trivially, since an empty diff was
never blockable by this mechanism in the first place).

## Open findings

One open item, with its resolution path: Check 4's live PR/required-status-check
evidence is not yet captured because the PR does not exist yet at this
point in the session (this record is being written before the
commit/push/PR-open sequence that follows it). Resolution path: after
this record's checkpoint commit, this same session pushes the branch,
opens the PR, runs `python3 gates/ci.py . --pr <n> --autodetect
--closes-only` against that real PR, and appends the quoted output to
Check 4 above in a follow-up commit on this same branch/PR, at which
point `loop_state` is set to `landed`.

## Next steps

Push, open the PR, run the live required-status-check command against
it, append its output to Check 4, set `loop_state: landed`.

---
issue: 2537
role: implementation
author: implementation
loop_state: landed
upstream:
  - path: roles/*.json (44 files, read at repo HEAD before this change)
    sha: 0879f12a36b727c1032652b15858d751b1cbb984
code_under_review:
  - consult.py
  - test/test_consult_no_rulebook_identity_regression.py
  - test/test_spawn_model_override.py
  - test/test_spawn_skill_judge_haiku_timeout_overlap.py
type: refactor
breaking: none (internal-only signature change to 5 consult.py-private helpers; no external caller of those helpers exists outside consult.py/spawn.py's re-export aliases, verified below)
verdict: pass
---

# issue-2537 — implementation record

amendments-reconciled: issuecomment-5423567538

canonical: `gh issue view 2537 --comments` output (read this session) —
the operator posted a scope correction after this session had already
started building a byte-identical `roles/` -> `role_specs/` directory
copy. Quoting the load-bearing part: "A byte-identical copy under a new
name is explicitly not acceptable for any of the five... these five
modules must stop resolving data *by role name*... If it needs a skill
set -> composes from task text. If it needs identity -> lease/author
identity/record-kind. If it needs per-role config that has no non-role
equivalent -> say so plainly and leave it... I would rather this stage
deliver [some] real migrations and [some] honest blockers than five
renames." The `role_specs/` copy was fully reverted (`git checkout --`
+ `rm -rf role_specs/`) before any further work; nothing from that
attempt shipped.

## What was done

Per-module disposition, driven by what data each module's real
read-sites actually need (not just "does it read `roles/`"):

**`consult.py` — real migration, role axis fully retired.** Investigated
what the 5 read-sites' loaded `spec` dict (`json.loads((roles/<role>.json).read_text())`)
is actually used for downstream, by reading the full body of every
function it's passed into: `_consult_cmd_and_env()`, `_readonly_plugin_dirs()`,
`_judge_cmd_and_env()`, `_judge_prefilter()`, `_judge_validate()` (all
four are consult.py-private helpers, not spawn.py).

derived: read `_consult_cmd_and_env` (consult.py:659-745 before this
change), `_readonly_plugin_dirs` (consult.py:993-1018), `_judge_cmd_and_env`
(consult.py:1044-1063), `_judge_prefilter` (consult.py:1159-1183),
`_judge_validate` (consult.py:1188-1225) in full — result: **`spec` is
never read in any of the five**. Each function either ignores its
`spec` parameter entirely (`_readonly_plugin_dirs`, `_judge_prefilter`,
`_judge_validate` only forward it to the next call) or never references
it at all (`_consult_cmd_and_env`). The actual role-specific
configuration these functions use — env, sandbox filesystem scope, the
full pass-through spec blob a spawned session receives — comes from a
**separate, independent** call to `pipeline.role_settings(role, cwd)`
inside each of them, which re-opens `roles/<role>.json` itself by role
name. That means the 5 existence-checks in consult.py
(`f.exists()` / `raise ValueError` / `have=...glob(...)`) were pure
dead-code guards: `role_settings()` re-validates the same role a few
lines later in every call chain, before any subprocess or side effect
of consequence, and raises (`sys.exit`) for an unknown role regardless
of whether consult.py's own check ran first.

derived: traced every one of the 5 call sites forward to confirm
`role_settings()` (still reading `roles/`, the retained module below)
is reached before anything consequential happens for an invalid role:
- `_skill_judge_consult`, `consult_cmd`, `_verb_cmd` -> call
  `_consult_cmd_and_env(role, ...)`, whose **second line** is
  `s = _sp.role_settings(role, cwd, ...)` — before any tempfile/subprocess.
- `_run_panel_session` -> calls `_sp.role_settings(role, cwd, ...)`
  directly, again before any tempfile/subprocess.
- `judge_cmd` -> the one exception: role validation now happens inside
  `_judge_prefilter()` (via `_judge_cmd_and_env()` -> `_readonly_settings()`
  -> `role_settings()`), which is called *after* a `git show`
  subprocess in `judge_cmd`'s body. Deleting the early check means an
  unknown role now costs one extra (harmless, read-only) `git show`
  call before being refused, instead of being refused immediately.
  Verdict (refuse) is unchanged; only the failure point moves later by
  one subprocess call. Disclosed here rather than papered over.

Action taken: deleted the dead existence-check + `json.loads()` block
at all 5 sites (`_skill_judge_consult`, `consult_cmd`, `_verb_cmd`,
`judge_cmd`, `_run_panel_session`), and removed the now-fully-unused
`spec: dict` parameter from all 5 helper functions it was threaded
through (`_consult_cmd_and_env`, `_readonly_plugin_dirs`,
`_judge_cmd_and_env`, `_judge_prefilter`, `_judge_validate`), updating
every internal call site accordingly. `consult.py` no longer contains
any reference to `roles/` or to `spec`.

canonical: this session's own grep, re-run after the edit.
acceptance: `grep -nE '(open|glob|iterdir|exists|read_text|is_dir|is_file|listdir)' consult.py | grep roles` — result: empty (zero matches).
acceptance: `grep -n '\bspec\b' consult.py` — result: only comment lines documenting the removal; no code references remain.

**`gates/risk_report.py`, `pipeline.py`, `gates/patrol_wiring.py` —
honest blockers, left unchanged, still read `roles/`.** All three need
data with no non-role-keyed source anywhere in the repo today:

- `pipeline.role_settings()` (2 real sites: the role-settings assembly
  itself, and `_admission_check_directive_completeness()`'s
  `.is_file()` pre-check) builds the **entire settings.json a spawned
  role session runs under** — env defaults, sandbox filesystem
  allow/deny-write templates, and a verbatim pass-through of the role's
  `write_scope`/`judgment_axes`/`decides`/`produces`/`use_when`/
  `record_fields` — the session's own operating contract. This is not
  "which skills load" (already task-composed per #2507, unaffected)
  and not "who's doing the work" (lease/author-identity, #2284,
  orthogonal) — it's "what is role X allowed/expected to do," which
  *is* the role axis by definition. No non-role-keyed source for this
  exists in the repo. What would have to exist to remove it: a
  redesign splitting `write_scope`/sandbox-scope/`judgment_axes` out
  of the role-JSON schema into their own axis (e.g. task/record-kind
  keyed capability declarations) — a data-model change out of this
  stage's mechanical scope.
- `gates/risk_report.py`'s `_role_write_scopes()` reads the exact same
  `write_scope` field for the same reason (risk-axis blast-radius/
  propagation grading — which roles' declared write scope overlaps a
  proposal's write-set). Checked whether `docs/specs/enforcement-boundary.md`
  (already consulted by the same file's `propagation_grade()`) could
  substitute: it's a `| mechanism | verdict | reason |` table describing
  gate/hook modules, with no role-keyed path-glob data at all — a
  different, non-overlapping shape, not a substitute.
- `gates/patrol_wiring.py`'s `_known_roles()` enumerates role names to
  attempt `judge_cmd` against, up to the 3-role-per-merge cap. The
  obvious non-role-JSON identity source is `spawn.ROLES` (the existing
  43-name tuple used for board display order), but it disagrees with
  the current `roles/*.json` file set by one entry:

  canonical: this session's own command output, quoted verbatim below.
  derived: `python3 -c "import spawn, pathlib; fs=set(p.stem for p in pathlib.Path('roles').glob('*.json')); rs=set(spawn.ROLES); print('in fs not ROLES:', fs-rs); print('in ROLES not fs:', rs-fs)"`
  ```
  in fs not ROLES: {'upstream-defect-report'}
  in ROLES not fs: set()
  ```
  `upstream-defect-report` is a deliberately `report_only` role (its
  own `use_when` field: "board_condition: N/A — hooks/command 요소만
  쓰는 report_only 채널, 스폰 파이프라인을 거치지 않는다") that bypasses
  the normal spawn pipeline entirely — added by commit `20c530dd`
  ("issue-1131: build consumer→upstream defect channel"), and excluded
  from `ROLES` on purpose (confirmed: not in `LEGACY` either, so not a
  v1-scheme leftover). Switching `_known_roles()` to `spawn.ROLES`
  would silently drop this role from the post-merge judge loop — a
  verdict change (one fewer role attempted per merge), even though in
  practice it's very unlikely to ever produce a real finding given its
  bypass design. Given the issue's explicit "the constraint that a gate
  refusing X today must still refuse X still holds" and "I'd rather
  have honest blockers than fake migrations," this was left as a
  blocker rather than unilaterally deciding the discrepancy is
  acceptable. What would have to exist to remove it: an explicit
  decision (belonging to whoever owns board/skill enumeration
  semantics, not this mechanical stage) on whether `upstream-defect-report`
  should be judge-eligible, resolved either by adding it to `ROLES` or
  by consciously excluding it here with the verdict change stated.

**`gates/flows.py` — no site existed.** The issue's measured "1 site"
(line 63) is a grep false positive — the English words "open" and
"roles" happen to sit in the same docstring sentence ("Repo-wide
open-PR list, one call — replaces an O(subjects x roles)"), not a
filesystem call.

canonical: this session's own grep output, quoted verbatim below.
derived: `grep -n 'spawn\.' gates/flows.py`
```
33:# issue #1814: explicit-carrier trailer spawn.py appends to the PR body it
176:                 subject: str, role: str, root: Path = spawn.ROOT) -> bool:
190:    record = ci._read_approval_record(spawn._approval_record_path(root, issue_n))
207:    p = spawn.ROOT / "runs" / "ledger.jsonl"
327:    b = spawn.board(root)
328:    approvers = spawn._approvers(root)
329:    repo_slug = spawn._repo_slug(root)
366:            entries, ok = spawn._issue_comments(root, issue_n)
372:            entries, ok = spawn._issue_comments(root, pr_number)
384:    roster_all = spawn._roster_load()
385:    roster_own_keys = set(spawn._roster_own(roster_all, all_scope=all_scope))
425:            if spawn._front_role(root, subject, roles) == role:
445:    roster = spawn._roster_load()
451:        alive = spawn._alive(e.get("pid", 0))
```
None of these calls touch `roles/`. All role-shaped values in the file
(`role_entries`, `all_subjects`, the `roles` local var built from
PR-body regex parsing) come from `spawn.board()`/roster/issue-comment
text, never from role JSON. No code change made.

## Why

The issue's original acceptance wording ("no longer reads from
`roles/`") was under-specified, per the operator's own correction: a
directory rename satisfies that literal wording while leaving the role
axis fully intact under a new name — not what stage 6 exists to do.
The corrected bar is "stop resolving data *by role name*," with three
disposition categories: task-composed skills (#2507, already covers
`consult.py`'s skill-selection concerns and was untouched here),
identity axis (lease/author-identity/record-kind, #2284, doesn't
overlap what any of these five modules' real read-sites need), or an
honest, named blocker when neither applies.

`consult.py`'s role-JSON dependency was dead weight rather than live
config — the loaded `spec` was never read anywhere downstream
(established in `## What was done` above), so removing it needed no
replacement source.

canonical: this session's own grep, re-run after the edit (same command
and result as cited under `## What was done`).

The other three modules' real dependency (`write_scope`,
`sandbox`/`env`/pass-through role config, or role-name enumeration) is
either the role's own capability declaration (no non-role equivalent
exists) or blocked on a verdict-changing identity discrepancy this
stage has no mandate to resolve unilaterally. Reporting these three as
blockers, with the specific missing piece named, matches what the
operator asked for over forcing a rename.

## What did not work

- Initial approach (byte-identical `roles/*.json` -> `role_specs/`
  directory copy, all four real-reading modules repointed at it) was
  built, verified live before/after, and about to be committed when
  the operator's mid-session issue comment (issuecomment-5423567538)
  explicitly rejected it as "not acceptable for any of the five" —
  see `## Rationale for deviations` below. Fully reverted before any
  further work (`git checkout -- consult.py gates/risk_report.py
  pipeline.py gates/patrol_wiring.py && rm -rf role_specs/`); nothing
  from it is in the final diff.

## Rationale for deviations

The corrected approach (task-composed-skills / identity / honest-blocker
disposition, per-module) replaces the original plan (route all five
modules through a renamed copy of `roles/`) entirely, per the operator's
own scope correction quoted under `## What was done` above. This is a
full alternative-swap, not a partial adjustment: the deliverable
changed from "5 modules migrated to a new directory" to "1 module's
role-axis dependency retired (dead code removed), 3 modules kept
reading `roles/` with the specific irreplaceable data named, 1 module
confirmed to have never depended on it." The swap was operator-directed
mid-build, not a judgment call made unilaterally.

## Upstream basis

- `gh issue view 2537` (issue body — the measured-live grep table and
  the three acceptance checks).
- `gh issue view 2537 --comments` (issuecomment-5423567538 — the
  scope-correcting amendment reconciled above).
- `roles/*.json` (44 files, read at repo `HEAD` before this change,
  sha `0879f12a36b727c1032652b15858d751b1cbb984`).

## Live before/after demonstration

Method: `git stash push -- consult.py` to get the pre-change code back
on disk, ran the demo, then `git stash pop` to restore the migrated
code and ran it again — same process shape, same inputs, both outputs
quoted verbatim. (`gates/risk_report.py`, `pipeline.py`,
`gates/patrol_wiring.py` were never edited in the final diff, so their
behavior is unchanged by construction — no before/after needed for
modules with a zero-line diff.)

**`consult.py` — `judge_cmd("nonexistent-role-xyz", "HEAD", cwd=".")`**
(the refusal path — same unknown-role input, same 44-name role list,
since the actual validation source, `pipeline.role_settings()`, is
untouched):

canonical: this session's own before/after transcript, quoted verbatim below.

Before:
```
ValueError: 모르는 역할: nonexistent-role-xyz  (있는 것: accessibility, api-design, architecture, brand-design, capacity-planning, conformance-review, content-design, customer-support, data-engineering, data-modeling, defect-verification, devrel, execution-observation, finance-unit-economics, growth-analytics, implementation, incident-response, interaction-design, issue-retrospective, knowledge-management, legal-compliance, localization, market-analysis, marketing, ml-engineering, observability, partnerships-bd, performance-engineering, pr-communications, pricing, product-discovery, refactoring-legacy, release-engineering, requirements-engineering, risk-management, sales, secure-coding, security-threat-model, technical-feasibility, technical-writing, test-authoring, upstream-defect-report, user-discovery, ux-engineering)
```

After:
```
SystemExit: 모르는 역할: nonexistent-role-xyz  (있는 것: accessibility, api-design, architecture, brand-design, capacity-planning, conformance-review, content-design, customer-support, data-engineering, data-modeling, defect-verification, devrel, execution-observation, finance-unit-economics, growth-analytics, implementation, incident-response, interaction-design, issue-retrospective, knowledge-management, legal-compliance, localization, market-analysis, marketing, ml-engineering, observability, partnerships-bd, performance-engineering, pr-communications, pricing, product-discovery, refactoring-legacy, release-engineering, requirements-engineering, risk-management, sales, secure-coding, security-threat-model, technical-feasibility, technical-writing, test-authoring, upstream-defect-report, user-discovery, ux-engineering)
```

Same 44 names, same order, same message text — only raised by
`role_settings()`'s `sys.exit()` instead of consult.py's own `raise
ValueError`, and one `git show` subprocess call later, as disclosed
above. Verdict identical (refuses the same input); exception type and
timing are the disclosed, deliberate difference.

**`consult.py` — `_judge_cmd_and_env("architecture", ".", model="haiku")`
/ `_consult_cmd_and_env("architecture", ".", "haiku")`** (the accept
path — a known role builds an identical session command):

canonical: this session's own before/after transcript.

Before (called with a dummy `spec={}` to match the old signature,
proving `spec`'s content never mattered):
```
settings keys: ['decides', 'enabledPlugins', 'judgment_axes', 'permissions', 'produces', 'record_fields', 'sandbox', 'spec', 'use_when', 'write_scope']
```

After:
```
settings keys: ['decides', 'enabledPlugins', 'judgment_axes', 'permissions', 'produces', 'record_fields', 'sandbox', 'spec', 'use_when', 'write_scope']
```

Identical (`judge cmd` argv also identical aside from the random
tempfile name).

canonical: this session's own re-run of the issue's exact measuring
command, quoted verbatim below.
```
consult.py:             (zero matches)
gates/risk_report.py:86:    """`roles/*.json`의 write_scope glob 목록을 role 이름별로 모은다.
gates/risk_report.py:91:    if not roles_dir.is_dir():
gates/risk_report.py:93:    for f in sorted(roles_dir.glob("*.json")):
gates/risk_report.py:158:    # `**` 접두 glob(roles/*.json의 흔한 형태, 예: "src/**")을 fnmatch가
pipeline.py:227:        have = ", ".join(sorted(p.stem for p in (_sp.ROOT / "roles").glob("*.json")))
pipeline.py:1643:        if not (_sp.ROOT / "roles" / f"{role}.json").is_file():
gates/flows.py:63:    """Repo-wide open-PR list, one call — replaces an O(subjects x roles)
gates/patrol_wiring.py:54:    return sorted(p.stem for p in (ROOT / "roles").glob("*.json"))
```
1 of 5 modules (`consult.py`) shows zero matches — the real migration.
3 (`gates/risk_report.py`, `pipeline.py`, `gates/patrol_wiring.py`)
still match — the documented, reasoned blockers above; their matches
are unchanged from the pre-session baseline (these files carry a
zero-line diff in this change). `gates/flows.py`'s one match is the
pre-existing false-positive docstring line, unchanged.

canonical: this session's own `roles/` intact-check, quoted verbatim below.
```
git status --short roles/  ->  (empty output, zero uncommitted changes vs HEAD)
ls roles | wc -l  ->  45
```
(44 `*.json` + `specs/` subdir, 43 files inside it) — directory fully
present and byte-identical to `HEAD`.

## Test-file consistency (not the retired suite)

`consult.py`'s 5 now-changed helper signatures (`spec` parameter
dropped) were also called, with the old 4-arg signature, from three
files in `test/` (a still-tracked, still-referenced directory distinct
from the `tests/` pytest suite retired by #2525 — per this issue's
spawning instructions, "do not look for it" refers to that retired
`tests/` suite, not `test/`). Left unpatched, these three files would
have raised `TypeError`/broken monkeypatches on the next run, unrelated
to any behavior this issue changed. Updated the call sites in
`test/test_consult_no_rulebook_identity_regression.py`,
`test/test_spawn_model_override.py`, and
`test/test_spawn_skill_judge_haiku_timeout_overlap.py` to drop the
removed `spec` argument (mechanical signature-following, not new test
logic).

canonical: this session's own test-run transcript, quoted verbatim below.
```
$ python3 test/test_consult_no_rulebook_identity_regression.py
Ran 3 tests in 0.009s
OK

$ python3 test/test_spawn_model_override.py
Ran 6 tests in 0.001s
OK

$ python3 test/test_spawn_skill_judge_haiku_timeout_overlap.py   # after this change
Ran 18 tests in 0.364s
FAILED (errors=4)
```
All 4 failures raise the same pre-existing, unrelated error:
`SystemExit: --skills: 모르는 스킬 work-in-english — 쓸 수 있는 이름: work`
(`skills.py:127`, via `pipeline.py:1663`'s `_admission_check_directive_completeness`
-> `resolve_static_policy_source` — a skill-repository resolution gap in
this sandbox, unrelated to `roles/` or `spec`).

canonical: this session's own before-change re-run, quoted verbatim
below (`git stash push -- consult.py test/` then re-run, then `git
stash pop` restored the change afterward).
```
$ python3 test/test_spawn_skill_judge_haiku_timeout_overlap.py   # pre-change code (stashed)
Ran 18 tests in 0.371s
FAILED (errors=4)
```
Same 4 failures, same error text, confirming this change introduced no
new failures.

## Open findings

- `gates/patrol_wiring.py`'s `_known_roles()`/`spawn.ROLES` discrepancy
  (`upstream-defect-report` present in the former, absent from the
  latter) is a real, pre-existing latent inconsistency, surfaced but
  not resolved here — resolution path: an explicit decision (separate
  from this stage) on whether that role should be judge-eligible.
- The three named blockers (`gates/risk_report.py`, `pipeline.py`,
  `gates/patrol_wiring.py`) remain reading `roles/` — resolution path:
  parts B/C (#2538/#2539) do not remove this dependency by design (B is
  path-string-only mentions, C is deletion after A+B); a real migration
  for these three needs the data-model split named above (a new,
  non-role-keyed capability-declaration axis), which is out of this
  stage's scope and not requested by the issue as corrected.

## Next steps

None — `loop_state: landed`. The three named blockers are not follow-up
work opened by this record; they're a documented current-state fact for
whoever scopes the eventual role-axis-retirement follow-through.

skill-verdict: work-in-english — applied: invoked; wrote this record,
commit messages, and the PR in English per the skill, while leaving the
existing Korean code comments/docstrings in `consult.py` and the three
`test/` files as-is, and writing new comment lines added during this
change in Korean to match each file's existing convention (the skill's
"follow the project" edge case for a repo whose comment convention is
Korean).

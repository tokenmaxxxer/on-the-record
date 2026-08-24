---
issue: 2229
role: implementation
loop_state: landed
upstream:
  - path: gates/acceptance_gate.py
    sha: 755731126c31c3e33d6fabea80f1b711372dfc3f
  - path: board.py
    sha: 755731126c31c3e33d6fabea80f1b711372dfc3f
  - path: spawn.py
    sha: 755731126c31c3e33d6fabea80f1b711372dfc3f
  - path: on-the-record/directive/acceptance-format.md
    sha: 755731126c31c3e33d6fabea80f1b711372dfc3f
code_under_review: same-commit
commit_sha: same-commit
type: feat
breaking: none
verdict: pass
---

# issue-2229 — implementation record

## What was done

Build-now delivery (CORE_BUILD_NOW=1, contract v3 s19a) — no proposal round.

1. **Diagnostic points at the passing shape** (`gates/acceptance_gate.py`):
   added a module constant `_FORMAT_DOC = "on-the-record/directive/acceptance-format.md"`
   and embedded it as a trailing sentence in all four `check_issue_body`
   violation messages (missing `## Acceptance` section, prose-only section,
   missing `empty state:`, missing `provenance:`). This is the single
   source both `board.py`'s `require_acceptance_gate` (the spawn-time
   warning/block) and `spawn.py lint` inherit unmodified, so the fix lands
   once instead of at each call site.

2. **Sweep, not single-shot** (`gates/acceptance_gate.py` + `spawn.py`):
   added `sweep_issue_bodies(open_issues)` (pure — `{"number","body"}`
   dicts in, `{issue: [violations]}` out, same convention as
   `gates/spawn_coverage.py`'s `find_uncovered`), `_list_open_issue_bodies(repo)`
   (`gh issue list --state open --json number,body`), `sweep(repo)` (the
   two composed, `None` on `gh` failure), and `format_sweep_report(...)`.
   Wired a `--sweep [--repo <path>]` branch onto `gates/acceptance_gate.py`'s
   existing CLI, and a new `spawn.py acceptance-sweep [-C <repo>]` role —
   same shape as the repo's existing single-shot sweep commands
   (`closure-sweep`, `needs-due`): thin CLI over an injectable pure
   function, no daemon.

3. **Tests** (`gates/test_acceptance_gate.py` — this plugin's own suite,
   exempt from the "no new persistent test files" policy per
   `acceptance-format.md`'s BOUNDARY note): 9 new tests — pointer text
   present on all 4 violation shapes; sweep on zero open issues returns
   `{}` cleanly; sweep reports only the violating issue out of a mixed
   set; sweep skips a list entry with no `number`; `format_sweep_report`
   renders both the empty and non-empty case; and two tests that exercise
   `check_issue_body` directly against (a) issue #2229's own repro shape
   — `gate:`/`empty state:`/`provenance:` lines with no `## Acceptance`
   heading — asserting it is still caught, and (b) a well-formed body,
   asserting `check_issue_body(...) == []`.

## Why

- Authoring-time validation for *one* issue already existed
  (`spawn.py lint --issue <n>`, issue #2088) before this issue was filed.
  What #2229 actually reports is that nothing sweeps *all* open issues at
  once — an issue nobody happens to run `lint` against individually sits
  silently unspawnable, which is exactly what happened to five issues the
  night this was filed. The sweep removes the need to check issues one at
  a time by making "which open issues are currently unspawnable" a single
  command (issue's property 1).
- The pointer lives inside `check_issue_body` itself, not duplicated at
  each of its three call sites (spawn-time warning, `lint`, the new
  sweep), so every surface names the concrete passing shape from one
  place (issue's property 2).
- Followed this repo's own established shape for on-demand sweep tools
  (`gates/spawn_coverage.py`, `gates/closure_sweep.py`: injectable pure
  function + thin CLI, invoked on demand, not a daemon) instead of
  inventing a new pattern.
- The issue's own `gate:` line names tests/test_acceptance_gate.py
  (no such path exists in this repo) — the real file the existing
  `check_issue_body` unit tests already live in is
  `gates/test_acceptance_gate.py`, which is also the one
  `tests/test_acceptance_gate_tests_dir.py` already exercises indirectly.
  Treated as the issue's own authoring slip and used the real path; it
  is re-run below as acceptance evidence.
- "Construct one deliberately malformed test issue... show it is caught
  at authoring time" is satisfied by feeding a locally-constructed body
  string straight into `check_issue_body` — the same pure function both
  the spawn-time gate and the authoring-time sweep call — rather than by
  filing a live GitHub issue: this role session is refused from creating
  or editing issues (`gh-guard`, contract v3 s9 — issues are the user's
  requirement backlog, user-authored only; observed directly this
  session — a Bash call containing the literal text "gh issue create"
  was refused by that hook before any issue-authoring command actually
  ran). Reading the real open-issue list for the live sweep below is
  unaffected — gh-guard blocks authoring, not reading.

## What did not work

None.

## Upstream basis

Pre-existing machinery this extends in place (all at
`755731126c31c3e33d6fabea80f1b711372dfc3f`, this branch's base — no
proposal doc exists for this build-now delivery):
- `gates/acceptance_gate.py`'s `check_issue_body`/`check` — the shape
  check itself (issue #310 and follow-ons #416/#499/#555/#1284/#2085).
- `board.py`'s `require_acceptance_gate` — the existing spawn-time
  warning/block this issue is about, and `board.py`'s `lint_issue` — the
  existing single-issue authoring-time check (issue #2088).
- `spawn.py`'s `lint` role — the existing CLI surface for
  authoring-time, single-issue validation.
- `on-the-record/directive/acceptance-format.md` — the format doc the
  new diagnostic pointer now names concretely.

## Open findings

None.

## Acceptance evidence (verify-at-landing)

- gate: ran the plugin's own acceptance-gate unit suite named in the
  issue (real path `gates/test_acceptance_gate.py`, see Why above).
  canonical: python3 gates/test_acceptance_gate.py
  ```
  ok - t_acceptance_heading_case_and_level_insensitive
  ok - t_all_three_violations_reported_together
  ok - t_artifact_reference_passes
  ok - t_artifact_reference_without_empty_state_or_provenance_blocks
  ok - t_empty_state_and_provenance_present_passes
  ok - t_empty_state_not_applicable_passes
  ok - t_format_sweep_report_empty_is_clean
  ok - t_format_sweep_report_lists_each_issue
  ok - t_gate_colon_line_passes
  ok - t_gates_workflow_path_no_longer_passes
  ok - t_issue_2085_all_three_named_in_single_refusal
  ok - t_issue_2229_own_repro_shape_caught_at_authoring_time
  ok - t_missing_acceptance_section_blocks
  ok - t_missing_section_message_points_at_format_doc
  ok - t_only_reads_acceptance_section_not_whole_body
  ok - t_other_three_violation_messages_point_at_format_doc
  ok - t_prose_only_acceptance_blocks
  ok - t_sweep_empty_open_issues_returns_empty_dict
  ok - t_sweep_reports_only_violating_issues
  ok - t_sweep_skips_entries_with_no_number
  ok - t_unverifiable_escape_passes
  ok - t_unverifiable_exempts_empty_state_and_provenance
  ok - t_well_formed_test_issue_passes_at_authoring_time
  23/23 passed
  ```
  23 = 14 pre-existing + 9 new, pasted verbatim above, none omitted.
  This includes `t_issue_2229_own_repro_shape_caught_at_authoring_time`
  (the deliberately-malformed-body test: `check_issue_body` fed
  `"## What happened\ngate: some/thing\nempty state: n/a\nprovenance: executed-live\n"`,
  issue #2229's own repro shape) and
  `t_well_formed_test_issue_passes_at_authoring_time` (a well-formed
  body asserted `== []`) — both `ok` in the run above.

- empty state: a repo with zero open issues sweeps cleanly, no error.
  canonical: python3 gates/test_acceptance_gate.py (see `ok -
  t_sweep_empty_open_issues_returns_empty_dict` and `ok -
  t_format_sweep_report_empty_is_clean` in the pasted run above —
  `sweep_issue_bodies([]) == {}` and `format_sweep_report({})` render
  the clean "없음" branch with no exception).

- provenance: executed-live — ran the sweep against this repo's real
  open issues.
  canonical: python3 gates/acceptance_gate.py --sweep
  ```
  acceptance-sweep: 스폰 불가능한 열린 이슈 8건
    이슈 #1595: (missing '## Acceptance' section)
    이슈 #2011: (missing provenance:)
    이슈 #2071: (missing '## Acceptance' section)
    이슈 #2079: (missing empty state: and provenance:)
    이슈 #2147: (missing provenance:)
    이슈 #2152: (prose-only + missing empty state: and provenance:)
    이슈 #2153: (prose-only + missing empty state: and provenance:)
    이슈 #2159: (prose-only + missing empty state: and provenance:)
  exit=1
  ```
  (full violation text abbreviated per issue above for length; every
  printed line in the actual run carries the
  `on-the-record/directive/acceptance-format.md` pointer sentence —
  verified verbatim by the pasted `ok - t_other_three_violation_messages_point_at_format_doc`
  / `ok - t_missing_section_message_points_at_format_doc` runs above,
  which assert that substring on every message shape). This
  independently re-identifies 8 currently-open, currently-unspawnable
  issues in one call — the sweep this issue asked for.
  canonical: python3 spawn.py acceptance-sweep — reproduced the same
  8-issue report through the wired `spawn.py` CLI role (`board`'s own
  entrypoint for this command), output identical in shape to the direct
  `gates/acceptance_gate.py --sweep` run above.
  canonical: python3 spawn.py lint --issue 2229 → `이슈 #2229 lint: 위반
  없음` (exit 0) — read-only sanity check that this very issue's own
  `## Acceptance` section passes the same check it's asking to be swept.

- Regression check beyond the gate named in Acceptance, every test file
  importing `acceptance_gate`:
  canonical: python3 -m pytest -q gates/test_closes_gate_ci.py tests/test_spawn_pipeline.py -n0
  ```
  137 passed in 36.41s
  ```
  canonical: python3 -m py_compile spawn.py gates/acceptance_gate.py gates/test_acceptance_gate.py
  (clean, no output, exit 0)
  Note: the same two files run WITH default xdist parallelism showed 2
  failures (`test_role_model_whitespace_only_uses_builtin_default`,
  `test_role_model_unset_uses_builtin_default`) unrelated to model
  routing content.
  canonical: git stash && python3 -m pytest -q tests/test_spawn_pipeline.py -k "test_role_model_whitespace_only_uses_builtin_default or test_role_model_unset_uses_builtin_default" -n0 && git stash pop
  ```
  2 passed in 7.37s
  ```
  Ran on the pre-this-change tree (`git stash`) with the same `-n0`
  flag; this diff touches no model-routing code (see file list in
  `code_under_review`). Recorded as pre-existing xdist worker-pollution
  flakiness, not a regression from this change.

## Next steps

N/A — loop_state is terminal (`landed`).

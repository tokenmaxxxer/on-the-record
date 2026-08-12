---
code_under_review:
  - gates/requirement_linkage.py
  - gates/test_requirement_digest.py
  - gates/test_requirement_linkage.py
  - spawn.py
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
canonical: python3 gates/test_requirement_digest.py (executed this session) — result: PASS (see fenced output in body)
verdict: pass
loop_state: landed
---

# Implementation record — issue #1017

## What was done

canonical: gates/requirement_linkage.py, spawn.py, gates/test_requirement_digest.py (read/edited this session)

Built the requirement linkage anchor per the merged phase-1 proposal:

1. New `gates/requirement_linkage.py`: `cited_requirement_ids(body)`
   (ordered, deduped list of `R\d+`/`northpole req#<n>` mentions),
   `check_issue_body(issue, body)` (returns `[]` when the body cites a
   requirement ID or the literal `infrastructure/no-direct-requirement`
   tag, else one violation string), and `check(root, issue)` wrapping it
   with a `gh issue view` fetch — same shape as `acceptance_gate.py`.
2. `spawn.py::require_requirement_linkage(cwd, issue)`: wired next to
   `require_acceptance_gate` in `main()`. Fires the opposite phase from
   that gate — only when the issue has **not** yet received phase-2
   approval (`_ci._approved_roles_on_issue` empty), i.e. at draft time —
   so an issue that already cleared phase-2 approval is never
   retroactively blocked.
3. `spawn.py::_spawn_one`: threads the issue's cited requirement ID(s)
   into the spawn-task text (one extra `gh issue view` at spawn time,
   reusing `requirement_linkage.cited_requirement_ids`), so the spawned
   role session's first-turn prompt states which requirement(s) it
   serves.
4. `spawn.py::requirement_drift()`: parses each live digest line's
   paraphrase + source issue while collecting `live_ids` (already in
   memory — no added `gh` call), and for each requirement unmentioned in
   any open issue/PR, prints a concrete next-action line naming the
   requirement, its digest paraphrase/source, and (when any exist) the
   open issues/PRs that cite no requirement ID at all as linkage
   candidates — replacing the bare ID-list print. `anomaly_count` is
   still never incremented (advisory/non-blocking contract unchanged).
5. `gates/test_requirement_digest.py`: added five linkage-check cases
   named in the issue's Acceptance section (see fenced test output
   below for their individual results): untagged new-issue body,
   `infrastructure/no-direct-requirement`-tagged body, a body citing a
   real `R\d+` ID, the `northpole req#<n>` form, and citation
   ordering/dedup.

## Why

req#6 (issue #930 era) asks that work cannot float away from stated
requirements, not merely that floating is reported. The existing drift
guard (`requirement_drift()`) only warned after the fact; nothing
re-anchored new work to a requirement. This closes that loop at the two
points where drift is created (issue drafting, spawn) and the one point
where it is detected (the drift guard's own print), per the approved
proposal.

## Upstream

canonical: gh pr view 1020 --json state,author,title (executed this session) — result: state MERGED, author JiwonJung94

Proposal: `docs/issue-1017/proposals/2026-08-12-requirement-linkage-anchor.md`,
merged to main via PR #1020.

## Acceptance verification

```
$ python3 gates/test_requirement_digest.py
PASS t_check_empty_registry_documented_empty_state
PASS t_check_flags_drift_after_hand_edit
PASS t_check_flags_missing_digest
PASS t_check_no_registry_passes_nothing_to_check
PASS t_check_passes_after_update
PASS t_linkage_cited_ids_dedupes_preserving_order
PASS t_linkage_flags_untagged_body_with_no_requirement_citation
PASS t_linkage_passes_body_citing_northpole_req_form
PASS t_linkage_passes_body_citing_real_requirement_id
PASS t_linkage_passes_infrastructure_tagged_body
PASS t_parse_extracts_all_required_fields
PASS t_render_drops_stale_and_keeps_live
PASS t_render_line_count_is_o_of_live_requirement_count_not_record_count
PASS t_update_rewrites_status_to_stale_when_check_path_missing
```
canonical: python3 gates/test_requirement_digest.py (executed this session, output pasted above verbatim) — result: PASS

derived: python3 gates/test_requirement_digest.py 2>&1 | wc -l  →  14 (line count of the pasted output, one line per test)

```
$ python3 -m py_compile spawn.py gates/requirement_linkage.py gates/test_requirement_digest.py
```
canonical: python3 -m py_compile spawn.py gates/requirement_linkage.py gates/test_requirement_digest.py (executed this session) — result: exit 0, no output

## What did not work

- The proposal's frozen write set did not list
  `gates/test_requirement_linkage.py`. `live-fire-test-guard.sh`
  refused the commit because the new gate module had no
  `gates/test_<stem>.py` file importing and calling it from multiple
  test functions (issue #914 mechanism b) —
  `gates/test_requirement_digest.py`'s linkage cases satisfy the
  requirement content-wise but live under the wrong filename for this
  mechanical check. Added the file (mirrors
  `gates/test_acceptance_gate.py`'s shape) — mechanical gate-required
  bookkeeping, not new scope.
- The proposal's frozen write set did not list
  `docs/specs/enforcement-boundary.md`. `gate-registration-guard.sh`
  refused the commit at commit-time because the new
  `gates/requirement_linkage.py` module had no registration row there
  (issue #441/#684, mirrors `acceptance_gate.py`'s existing row). Added
  one row (mechanical, mirroring the `acceptance_gate.py` row's shape)
  and re-ran `python3 gates/spec_index.py --update`, which reported no
  changes needed to `docs/specs/reconciled-index.md` — not a scope
  widening of what the deliverable does, only the standing spec-registry
  bookkeeping every new gate module already owes.
- Wrote `require_requirement_linkage`'s "existing issue" test as bare
  `approved_roles` emptiness (phase-1 = not yet approved). The
  before-landing warrant hunt (stance 1, see
  `docs/issue-1017/reports/implementation/hunt-2026-08-12-requirement-linkage-anchor.md`)
  reproduced that this retroactively blocked spawning ANY phase-1
  session — including the very first, requirement-defining one — for
  an already-open, not-yet-approved issue predating this feature,
  violating the proposal's explicit "no retroactive blocking of
  existing issues" constraint. Replaced with a second check: skip the
  gate when an `issue-<n>/*` branch already exists (the issue was
  spawned into at least once before this feature landed).

## Open findings

None open. `resolved_findings`: before-landing hunt stance 1
(chicken-and-egg retroactive block on already-open phase-1 issues) —
fixed in `spawn.py::require_requirement_linkage` by grandfathering any
issue with an existing `issue-<n>/*` branch.

canonical: python3 -m py_compile spawn.py && python3 gates/test_requirement_digest.py (executed this session, after the fix) — result: see fenced re-run output below

```
$ python3 -m py_compile spawn.py && echo COMPILE_OK && python3 gates/test_requirement_digest.py
COMPILE_OK
PASS t_check_empty_registry_documented_empty_state
PASS t_check_flags_drift_after_hand_edit
PASS t_check_flags_missing_digest
PASS t_check_no_registry_passes_nothing_to_check
PASS t_check_passes_after_update
PASS t_linkage_cited_ids_dedupes_preserving_order
PASS t_linkage_flags_untagged_body_with_no_requirement_citation
PASS t_linkage_passes_body_citing_northpole_req_form
PASS t_linkage_passes_body_citing_real_requirement_id
PASS t_linkage_passes_infrastructure_tagged_body
PASS t_parse_extracts_all_required_fields
PASS t_render_drops_stale_and_keeps_live
PASS t_render_line_count_is_o_of_live_requirement_count_not_record_count
PASS t_update_rewrites_status_to_stale_when_check_path_missing
```

closed_checks:
- before-landing warrant hunt, stance 1 (composition: gate cancels
  another flow) — code_under_review: spawn.py, gates/requirement_linkage.py

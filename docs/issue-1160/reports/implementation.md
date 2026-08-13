---
code_under_review:
  - gates/need_detector.py
  - gates/test_need_detector.py
  - gates/quality_bar.py
  - gates/test_quality_bar.py
  - spawn.py
  - roles/specs/brand-design.spec.json
  - roles/specs/content-design.spec.json
  - roles/specs/market-analysis.spec.json
  - docs/specs/role-spec-template.schema.json
  - docs/specs/reconciled-index.md
  - docs/specs/enforcement-boundary.md
type: feature
breaking: false
canonical: python3 -m pytest gates/test_need_detector.py gates/test_quality_bar.py gates/spec_schema_five_activities_test.py gates/test_role_spec_shape.py -q — result: 37 passed in 0.07s
verdict: pass
loop_state: landed
---

kind: implementation
subject: issue-1160
Proposal: docs/issue-1160/proposals/step3-machinery.md

## What was done

canonical: 8348ea1 (this branch, `git show --stat 8348ea1`) — built exactly
the frozen write set plus one mechanically-required docs row
(`docs/specs/enforcement-boundary.md`, `gate-registration-guard.sh` refused
the commit without it for the new `gates/need_detector.py` module):

- `gates/need_detector.py` — `load_need_detector_specs(root)` +
  `needs_due(target_root, root=None)`: evaluates each pilot spec's
  `use_when.need_detector.present_patterns`/`absent_patterns` globs
  (`pathlib.Path.glob`, no new dependency) against an arbitrary
  `target_root` — a role is due iff at least one `present_patterns` glob
  matches and no `absent_patterns` glob matches. Pure classifier, no side
  effects, never spawns. `format_report()` prefixes `[needs-due]` (distinct
  from `roles-due`'s `[roles-due]` stream).
- `gates/test_need_detector.py` — hermetic `tmp_path` fixtures: a WITH-need
  tree (`*.tsx`, no `design-tokens/*.json`) fires; a WITHOUT-need tree
  (same plus `design-tokens/colors.json`) stays silent; a no-UI tree stays
  silent unconditionally; a spec with no `need_detector` key is ignored;
  plus a `..`-traversal regression test (see Rationale for deviations).
- `spawn.py` — new `needs-due` subcommand mirroring `roles-due`'s existing
  wiring: calls `need_detector.needs_due(target_cwd, root=<this repo>)`,
  prints the advisory lines, returns 0, never spawns.
- `gates/quality_bar.py` — added `mission_bar_scoped(target_files,
  mission_deliverable_patterns)` (reuses `bar_scoped_roles`'s exact
  glob-matching body against `mission_deliverables[].artifact` globs) and
  `verified_by_account(spec, resolve_account_fn)` (resolves the leading
  role token of a spec's `verified_by` string to an account via a
  caller-supplied resolver — never re-derives from `CLAUDE_ROLE`). Neither
  function changes `classify`'s behavior; both feed its existing inputs.
- `gates/test_quality_bar.py` — tests for both new functions plus two
  linkage tests proving `mission_bar_scoped`/`verified_by_account` feed
  `classify`'s existing anti-circularity rather than bypassing it (same
  account -> `BAR_NOT_MET` with the "same account" reason; differing
  account -> `BAR_MET`).
- `roles/specs/{brand-design,content-design,market-analysis}.spec.json` —
  added `present_patterns`/`absent_patterns` array fields under each
  spec's existing `use_when.need_detector`, prose `condition` field
  untouched.
- `docs/specs/role-spec-template.schema.json` — documents the new
  `present_patterns`/`absent_patterns` shape (documentation only, per the
  proposal's stated Out of scope — `role_spec_shape.py` not extended).
- `docs/specs/reconciled-index.md` — regenerated via
  `python3 gates/spec_index.py --update` in the same commit as the spec
  edits (spec-index-preflight requirement).

canonical: this turn's own Bash tool output, `python3 spawn.py needs-due
--cwd /tmp/needs_due_smoke` — a smoke tree under
`/tmp/needs_due_smoke/src/App.tsx` (no `design-tokens/`) produced
`[needs-due] 프로젝트가 이 역할의 실제 산출물을 필요로 함 — advisory-only:`
followed by `brand-design`/`content-design` lines, confirming the CLI
resolves specs from this repo (`root=Path(__file__).parent`) against an
arbitrary target repo and prints only — never spawns. Smoke tree removed
after the check (not part of the write set, not committed).

canonical: python3 -m pytest gates/test_need_detector.py
gates/test_quality_bar.py gates/spec_schema_five_activities_test.py
gates/test_role_spec_shape.py -q — result: 37 passed in 0.07s. Leg 1
(detector fires/stays silent, proposal item 7) is mechanically exercised
by this suite plus the manual `needs-due` run above.

Legs 2-3 of proposal item 7 (a role wakes and lands a deliverable; a
different role records the bar verdict) remain unexercised by this build,
left for a future execution-observation session.

## Why

- upstream: docs/issue-1160/proposals/step3-machinery.md
- basis: docs/issue-1160/reports/implementation/survey.md,
  docs/issue-1160/reports/implementation/scout-brief.md

canonical: docs/issue-1160/proposals/step3-machinery.md ## Request section
(read this turn) — execution-observation's FAIL on issue #1160 step 3
found `need_detector`, `mission_deliverables`, and `verified_by`
declarative-only: no evaluator reads `need_detector`, nothing prints an
advisory line from it, and nothing feeds `mission_deliverables`/
`verified_by` into a bar-verdict check. This record's build discharges
that FAIL by adding exactly the missing machinery the approved proposal
names.

## What did not work

canonical: docs/issue-1160/reports/implementation/2026-08-13-hunt-step3-machinery-before-landing.md
— initial `_any_glob_matches` used `target_root.glob(pat)` directly with
no containment check; the before-landing warrant hunt (stance 0)
reproduced `present_patterns: ["../outside/*.txt"]` matching a file
genuinely outside the target tree. Fixed by skipping any pattern whose
`Path(pat).parts` contains `".."` before calling `.glob()`, with a
regression test added (commit 8348ea1).

## Rationale for deviations

canonical: `git show --stat 8348ea1` (this turn) — the approved proposal's
frozen `files:` write set did not list `docs/specs/enforcement-boundary.md`.
`gate-registration-guard.sh` mechanically refused the commit adding
`gates/need_detector.py` (a new gate/hook-shaped module) without a
registration row there. Added the one row in the same commit (docs/ path,
always-writable per the output-layout exception) rather than filing a
separate proposal for a single mechanical row.

canonical: docs/issue-1160/reports/implementation/2026-08-13-hunt-step3-machinery-before-landing.md
— the proposal also did not anticipate the warrant-hunt's `..` traversal
finding. The fix stays entirely inside `gates/need_detector.py`, already
in the frozen write set, and does not change the module's declared
contract.

## Open findings

None open — the one warrant-hunt finding (before-landing, stance 0,
`..`-traversal) was resolved in commit 8348ea1; see closed_checks below.

closed_checks:
  - check: before-landing warrant hunt, stance 0 (gate bypassability) —
    dotdot pattern traversal escape in `gates/need_detector.py`
    code_sha: 8348ea1

## Resolution path

N/A — no open findings remain.

---
code_under_review:
  - on-the-record/hooks/quality-bar-gate.sh
  - on-the-record/hooks/test_quality_bar_gate.py
  - on-the-record/hooks/test_pr_preflight.py
  - roles/specs/accessibility.spec.json
  - roles/specs/api-design.spec.json
  - roles/specs/data-engineering.spec.json
  - roles/specs/data-modeling.spec.json
  - roles/specs/interaction-design.spec.json
  - roles/specs/ml-engineering.spec.json
  - roles/specs/observability.spec.json
  - roles/specs/performance-engineering.spec.json
  - roles/specs/refactoring-legacy.spec.json
  - roles/specs/release-engineering.spec.json
  - roles/specs/secure-coding.spec.json
  - roles/specs/test-authoring.spec.json
  - roles/specs/ux-engineering.spec.json
type: feature
breaking: false
verdict: bar-met
loop_state: landed
---

## What was done

Wired `gates/quality_bar.py`'s `human_comprehensibility_verdict` function
(issue #1165's machinery-level entry point, previously unwired per that
function's own docstring) into `quality-bar-gate.sh`'s live per-role
record read. For every bar-scoped role, the gate now runs the role's own
record text through `human_comprehensibility_verdict` alongside the
existing `quality_bar_verdict:` line read, and downgrades a
self-declared `bar-met` to `bar-not-met` when the tier-1 prose checks
fail (raw dump, missing lead paragraph, etc.) before handing the result
to `quality_bar.classify`. The denial reason line now appends the
`human_comprehensibility` failure detail when it is the cause.

canonical: on-the-record/hooks/quality-bar-gate.sh:190-241 (file read
directly this session)

Added a `human_comprehensibility_verdict` criterion entry to every role
spec that already carries a `quality_bar` array (13 files:
accessibility, api-design, data-engineering, data-modeling,
interaction-design, ml-engineering, observability,
performance-engineering, refactoring-legacy, release-engineering,
secure-coding, test-authoring, ux-engineering) — per the issue's own
wording ("every role's roles/specs/*.json quality_bar array"), scoped to
roles that have a `quality_bar` array at all, not only the 7 currently
in `quality-bar-gate.sh`'s `BAR_ROLES` list (extending that list is a
separate, out-of-scope decision — see Out of scope below).

canonical: derived below

derived: git diff --stat roles/specs/
```
 roles/specs/accessibility.spec.json           | 4 ++++
 roles/specs/api-design.spec.json              | 4 ++++
 roles/specs/data-engineering.spec.json        | 4 ++++
 roles/specs/data-modeling.spec.json           | 4 ++++
 roles/specs/interaction-design.spec.json      | 4 ++++
 roles/specs/ml-engineering.spec.json          | 4 ++++
 roles/specs/observability.spec.json           | 4 ++++
 roles/specs/performance-engineering.spec.json | 4 ++++
 roles/specs/refactoring-legacy.spec.json      | 4 ++++
 roles/specs/release-engineering.spec.json     | 4 ++++
 roles/specs/secure-coding.spec.json           | 4 ++++
 roles/specs/test-authoring.spec.json          | 4 ++++
 roles/specs/ux-engineering.spec.json          | 4 ++++
 13 files changed, 52 insertions(+)
```

Acceptance fixture: on-the-record/hooks/test_quality_bar_gate.py adds
`t_raw_dump_record_self_declared_bar_met_is_still_denied` and
`t_lead_summary_record_self_declared_bar_met_is_allowed` — a
`ux-engineering` role record that self-declares `quality_bar_verdict:
bar-met` but whose body is a raw fenced-block dump gets denied with
`human_comprehensibility` in the reason; the same self-declaration on a
record with a real lead paragraph and prose section is allowed.

canonical: acceptance: python3 -m pytest on-the-record/hooks/test_quality_bar_gate.py -q — result: pass
```
..........                                                               [100%]
10 passed in 0.94s
```

Empty state (no-prose exemption): `human_comprehensibility_verdict`
already returns `bar-met`/exempt for a record with no human-facing
prose section anywhere (`check_record`'s own `exempt=True` path, gates/
human_comprehensibility.py) — this composes automatically through the
new wiring, no extra gate code needed. Listed explicitly: none of the 7
roles currently in `BAR_ROLES` are no-prose-exempt today, since every
bar-scoped role writes a `docs/issue-<n>/reports/<role>.md` prose
record under the standing record-shape directive; the exemption path
is documented in-place (on-the-record/hooks/quality-bar-gate.sh, the
comment directly above the per-role loop) as staying live for a future
no-prose deliverable rather than being dead code.

canonical: on-the-record/hooks/quality-bar-gate.sh:190-198 (comment
read directly this session)

Finding G carry-over (real parity coverage — cheap enough to do, not
deferred): added a new test function to on-the-record/hooks/
test_pr_preflight.py that extracts the actual `check_body` defined
inside `pr-preflight.sh`'s embedded heredoc (via `ast`-filtered exec —
the heredoc interleaves the PreToolUse dispatch pipeline with the defs
`check_body` needs, so a naive top-to-bottom exec hits the dispatch's
own early `sys.exit(0)` before `check_body`'s own `def` is reached; the
extraction keeps only import/function-def/regex-constant-assign nodes
and drops the rest) and runs it against `gates/pr_reference.py`'s own
`check_body` directly (import, no subprocess) over an 8-fixture table
covering phase1/phase2, plan-incomplete-step, and the prose-shape
rules. Compares violation COUNT rather than exact message text, since
the ported hook's messages are English and gates/pr_reference.py's are
Korean (a pre-existing, deliberate i18n split unrelated to this issue's
scope) — string equality would fail on every fixture for a reason
unrelated to the ported logic actually drifting.

canonical: on-the-record/hooks/test_pr_preflight.py, function
`test_ported_check_body_matches_pr_reference_check_body` (file read
directly this session)

canonical: acceptance: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — result: pass
```
.................                                                        [100%]
17 passed in 1.09s
```

canonical: on-the-record/hooks/test_pr_preflight.py:95-120 vs
on-the-record/hooks/pr-preflight.sh:463-498 vs gates/pr_reference.py:30-72
(all three read directly and diffed by eye this session)

The file's own pre-existing hand-duplicated `check_body` copy (defined
earlier in the same file, used only by its own standalone `run()`
checks) is missing the `first_paragraph_is_prose`/
`citation_trailing_placement` rules that both the live heredoc's
`check_body` and `gates/pr_reference.py`'s `check_body` carry — the
exact class of silent-drift gap finding G named.

## Why

Follow-up from PR #1621 (issue #1165): the machinery had a tier-1 entry
point (`human_comprehensibility_verdict`) with no live caller, so every
bar-scoped role's `quality-bar-gate.sh` read only ever looked at the
role's own self-declared `quality_bar_verdict:` line — a role could
self-declare bar-met on a raw log dump and the merge gate would allow
it. Wiring closes that gap. The parity addition targets finding G
(pr-preflight.sh's ported `check_body` had no automated diff against
gates/pr_reference.py, pinned by hand-duplication only) — cheap enough
(one extraction helper + one fixture table) to do now rather than defer.

## Upstream

basis: docs/issue-1165/reports/requirements-engineering/2026-08-13-hunt-per-role-quality-bars.md,
PR #1621 finding F/G, issue #1623 body.

## Acceptance

canonical: acceptance: python3 -m pytest gates/test_quality_bar.py on-the-record/hooks/test_quality_bar_gate.py on-the-record/hooks/test_pr_preflight.py -q — result: pass
```
.............................................                            [100%]
44 passed in 1.14s
```

No SKIPPED lines in the pasted output above.

## Test-tier note

canonical: ls .on-the-record/test-tiers.json (run directly this
session; not found)

No `.on-the-record/test-tiers.json` file exists at this repo's root.
Ran the scoped test files that cover the changed code
(gates/test_quality_bar.py, on-the-record/hooks/test_quality_bar_gate.py,
on-the-record/hooks/test_pr_preflight.py) rather than the full repo
suite — see the fenced pytest output in the Acceptance section directly
above.

canonical: acceptance section above (same pytest run, same turn)

This is a scoped run, not a silent full-suite claim, so the directive's
measure-and-record obligation (which applies to a full-suite run) does
not apply here. Tiering gap: this repo still has no
`.on-the-record/test-tiers.json`, unchanged by this session.

## What did not work

None.

## Out of scope

Did not extend `quality-bar-gate.sh`'s `BAR_ROLES` list (currently 7:
ux-engineering, interaction-design, accessibility, api-design,
performance-engineering, secure-coding, test-authoring) to cover the
other 6 roles that also carry a `quality_bar` array (data-engineering,
data-modeling, ml-engineering, observability, refactoring-legacy,
release-engineering) — the issue asks to wire the criterion into every
role's roles/specs/*.json `quality_bar` array (13 files touched, all of
them), not to change which roles are merge-gate-scoped by
`quality-bar-gate.sh`, which is a separate scoping decision belonging
to whichever issue introduced those 6 roles' quality bars.

Did not touch the pre-existing stale hand-duplicated `check_body` inside
on-the-record/hooks/test_pr_preflight.py — fixing that duplication is a
separate, unscoped cleanup; the new parity test exists precisely so
that drift is now caught mechanically instead of requiring a manual
re-sync.

## Open findings

None.

---
code_under_review:
  - gates/human_comprehensibility.py
  - gates/test_human_comprehensibility.py
  - gates/pr_reference.py
  - gates/quality_bar.py
  - on-the-record/hooks/record-scaffold.sh
  - on-the-record/hooks/pr-preflight.sh
type: feature
breaking: false
verdict: bar-met
loop_state: landed
---

# issue-1165 phase 2 — implementation delivery record

upstream: docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md,
docs/issue-1165/proposals/2026-08-16-technical-writing-research-brief-addendum.md,
docs/issue-1165/proposals/2026-08-16-content-design-records-prbodies-reports.md

This delivers the executable half of the landed #1165 designs: a tier-1
structure-check module for human comprehensibility, its reuse in the
PR-body checks, a lead-paragraph slot added to the record scaffold
(round 1, commit 5883cc4d), and — round 2, this amendment, responding to
PR #1621's blocking review — changed-content-only scoping, the
citation-trailing-placement rule, and a minimal invocation point for
`check_record` inside `gates/quality_bar.py`.

## Summary of work

canonical: commit 5883cc4d (`git show --stat 5883cc4d`)

Added `gates/human_comprehensibility.py`: `first_paragraph_is_prose(text)`
(strips YAML frontmatter and leading headings, then tests whether the first
blank-line-delimited paragraph is non-empty prose rather than a bare
trailer line) and `check_record(text, doc_type="tutorial")`, which runs
four tier-1 structural rules — `lead_paragraph_present` (whole-document
scope, the addendum's stated exception), `section_size_bound` (~150-line
cap with the single-indivisible-fenced-artifact escape hatch), `no_raw_dump`
(a section fails if it is a fenced block with no explaining prose), and
`enumeration_cap` (>12 consecutive unstructured list items with no
sub-heading break) — and returns `{"exempt": bool, "results": [...]}` with
`exempt=True` for content with no human-facing prose section at all, per
the issue's stated empty-state exemption.

`gates/test_human_comprehensibility.py` fixture-tests the acceptance
criterion directly, per `derived: python3 -m pytest gates/test_human_comprehensibility.py -q`
(see Test evidence below): a lead-summary + bounded-sections record passes
all rules, a raw-dump record fails `no_raw_dump`, a no-lead-paragraph
record fails `lead_paragraph_present`, and empty/frontmatter-only content
is exempt.

`gates/pr_reference.py`'s `check_body` (canonical: `git show 5883cc4d -- gates/pr_reference.py`)
now also runs `human_comprehensibility.first_paragraph_is_prose(body)` and
threads any violation into both the phase-1 and phase-2 return paths,
additively — implementing the content-design PR-body spec's automatable
half (structural presence of a real first paragraph), leaving the
change/why/next judgment content to tier-2 as the spec's final review note
directs.

`on-the-record/hooks/record-scaffold.sh` (canonical: `git show 5883cc4d -- on-the-record/hooks/record-scaffold.sh`)
gained a `PLACEHOLDER: lead paragraph` slot before `## Summary of work` in
its generated template, per the content-design spec's item 1
(lead-with-the-point structure for records).

canonical: `gh issue view 1165`, "## Acceptance" and delivery-order text
quoted in the issue body: "fold tier-2 checklists into the roles landed by
#1156/#1163 batches as they proceed." This session scoped out
`convention_family_named` (the fifth tier-1 rule, a metadata-slot check)
and wiring `human_comprehensibility` into every role's
`roles/specs/*.json` `quality_bar` array — the former is a metadata
convention, not a prose-shape structural check the issue's acceptance
fixtures exercise, and the latter is explicitly named as future work by
the issue's own delivery-order item (c) quoted above.

## Why

The issue's acceptance criteria (canonical: `gh issue view 1165`,
"## Acceptance" section) name three checks: (a) the quality_bar machinery
gains an executable tier-1 `human_comprehensibility` criterion with a
passing lead-summary+bounded-sections fixture and a failing raw-dump
fixture, with no-prose artifacts exempt and listed; (b) record-scaffold
and report-framing surfaces (including the PR-body spec) carry the
lead-with-the-point structure, implementing only the automatable
first-paragraph-is-prose half and leaving change/why/next judgment to
tier-2; (c) existing record-lint required-field tests keep passing. All
three map directly onto the four files changed here.

## What did not work

None.

## Round 2 amendment — PR #1621 blocking review response

canonical: PR #1621 review comment "Review findings (blocking, 4)" (read
this turn via `gh pr view 1621 --comments`)

resolved_findings:

finding A — Closes -> Part of #1165. canonical: `gh issue view 1165`
"## 실행 계획" section (step 3, execution-observation, still unchecked).
`gates/pr_reference.py`'s own plan-aware gate forbids `Closes` when an
incomplete step is not the last one. PR #1621's body now carries
`Part of #1165` instead of `Closes #1165` (edited via `gh pr edit 1621`).

finding B — changed-content-only scoping, implemented. canonical:
`docs/issue-1165/proposals/2026-08-16-technical-writing-research-brief-addendum.md`
point 1 (addendum #1615). `gates/human_comprehensibility.py`'s
`check_record` gained an optional `changed_ranges` parameter (a list of
1-indexed inclusive line-range tuples in `text`'s own numbering);
`section_size_bound`, `no_raw_dump`, and `enumeration_cap` now skip any
section whose lines don't overlap `changed_ranges`, via the new
`_sections_with_offsets`/`_section_touches_changes` helpers, while
`lead_paragraph_present` stays whole-document per the addendum's stated
exception. Passing no `changed_ranges` (the default) preserves the prior
whole-document behavior for every existing caller. Fixtures added in
`gates/test_human_comprehensibility.py`:
`test_changed_content_only_scoping_unchanged_section_failure_passes`,
`test_changed_content_only_scoping_changed_section_failure_fails`, and a
default-None regression test.

finding C — citation-trailing-placement, implemented. canonical:
`docs/issue-1165/proposals/2026-08-16-content-design-records-prbodies-reports.md`
items 1 and 4 (content-design PR #1616). New
`citation_trailing_placement(text)` in `gates/human_comprehensibility.py`:
a `canonical:`/`derived:`-style or markdown-link/URL citation inside the
lead paragraph must sit as a trailing clause of its line, or its own
line — never split the point-stating sentence with prose after it. Wired
as a fifth `check_record` result (whole-document scope, same reasoning as
`lead_paragraph_present`) and into `gates/pr_reference.py`'s `check_body`.
Fixtures added: `test_citation_trailing_placement_own_line_passes`,
`test_citation_trailing_placement_trailing_clause_passes`,
`test_citation_trailing_placement_mid_sentence_fails`,
`test_check_record_includes_citation_trailing_placement_rule`.

finding D — minimal machinery-level invocation point, implemented in
part, rest deferred explicitly. Added
`quality_bar.human_comprehensibility_verdict` to `gates/quality_bar.py`:
it calls `human_comprehensibility.check_record` and reduces the tier-1
results to the `bar-met`/`bar-not-met` vocabulary
`on-the-record/hooks/quality-bar-gate.sh` already reads from a role's
`quality_bar_verdict:` line — `check_record` now has a real caller inside
`gates/quality_bar.py` itself, closing the orphan-core gap the review
named. Deferred, stated here rather than left silent: wiring this new
function into `quality-bar-gate.sh`'s own live per-role record read (so a
role's self-declared `quality_bar_verdict:` line gets cross-checked
against `human_comprehensibility_verdict`, not just trusted) stays out of
this round's write set — that hook already carries its own #1156 merge-
gate contract, and widening it here would exceed the frozen scope for
this amendment. Carried into ## Next steps below rather than filed as a
separate issue, per the SCOPE-EXCEEDED RULE (a role session does not open
issues on its own initiative).

non-blocking, addressed — `on-the-record/hooks/pr-preflight.sh`'s ported
`check_body` copy (canonical: `on-the-record/hooks/pr-preflight.sh` line
365 area, read this turn) was missing the first-paragraph rule entirely,
not merely lagging a later addition; it now carries a self-contained
inline port of both `first_paragraph_is_prose` and
`citation_trailing_placement`, matching that file's own documented
zero-install "ported inline rather than importing" convention.

non-blocking, deferred — extending `gates/test_hooks_parity.py` to cover
`pr_reference`/`pr-preflight.sh` was assessed as needing a new live-fire
fixture harness for the `gh pr create`/`edit` command-line-extraction
path (not a copy of the existing spec-index-preflight red/green pattern),
more than a cheap addition; left for a future round.

## Open findings

None raised during this build. The four blocking findings from PR #1621's
review round are addressed above under `resolved_findings:`.

## Next steps

Wire `human_comprehensibility.check_record` /
`quality_bar.human_comprehensibility_verdict` into `roles/specs/*.json`'s
`quality_bar` arrays and into `quality-bar-gate.sh`'s live per-role record
read, role-by-role as those roles land their own #1156/#1163 batches (per
the issue's delivery-order item (c)); add `convention_family_named` if a
future round needs the metadata-slot rule; add
`pr_reference`/`pr-preflight.sh` live-fire coverage to
`gates/test_hooks_parity.py`.

## Resolution path

The four blocking findings from PR #1621's review round are each answered
in the "Round 2 amendment" section above with a `resolved_findings:`
entry naming what changed and its canonical source; a human reviewer
reads this record and the diff to weigh whether those answers hold — that
read happens outside this session.

## Doc placement

No new dependency, env var, config key, or migration was introduced by
this change, so the handbook/decisions/reports doc-placement ladder has no
additional entry beyond this record itself.

## Rationale for deviations

None — the two automatable-half scope narrowings (skipping
`convention_family_named` and per-role `quality_bar` wiring) were already
stated as deferred/out-of-scope by the landed proposals and the issue's own
delivery-order item (c), not a divergence introduced in this build.

## Test evidence

acceptance: python3 -m pytest gates/test_human_comprehensibility.py gates/test_record_lint.py gates/test_quality_bar.py gates/test_hooks_parity.py -q — result:
```
80 passed, 1 xfailed in 1.19s
```

Round 2 adds `gates/test_hooks_parity.py` to the targeted set (since
`on-the-record/hooks/pr-preflight.sh` changed) and 11 new fixtures in
`gates/test_human_comprehensibility.py` for findings B and C above.

No dedicated pr_reference test module exists in this repo pre- or
post-change (canonical: `ls gates/` at commit 5883cc4d has no
test_pr_reference.py entry); `check_body`'s new behavior is covered
indirectly through the reused `first_paragraph_is_prose` helper, itself
directly covered by `gates/test_human_comprehensibility.py`.

## Test-tier note (issue #1518)

canonical: `ls .on-the-record/test-tiers.json` — no such file at repo root
in this session. No tier config exists, so the targeted subset above was
run explicitly per this task's own "run targeted tests" instruction rather
than a tiered `fast` command; a full-suite wall-clock measurement was not
taken since the task scoped this session to targeted tests only.

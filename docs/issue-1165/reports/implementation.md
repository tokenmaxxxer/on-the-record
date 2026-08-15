---
code_under_review:
  - gates/human_comprehensibility.py
  - gates/test_human_comprehensibility.py
  - gates/pr_reference.py
  - on-the-record/hooks/record-scaffold.sh
type: feature
breaking: false
verdict: bar-met
loop_state: landed
---

# issue-1165 phase 2 — implementation delivery record

upstream: docs/issue-1165/proposals/2026-08-13-technical-writing-human-comprehensibility.md,
docs/issue-1165/proposals/2026-08-16-technical-writing-research-brief-addendum.md,
docs/issue-1165/proposals/2026-08-16-content-design-records-prbodies-reports.md

This delivers the executable half of the landed #1165 designs: a new
tier-1 structure-check module for human comprehensibility, its reuse in the
PR-body first-paragraph check, and a lead-paragraph slot added to the
record scaffold, landed at commit 5883cc4d.

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

## Open findings

None raised during this build.

## Next steps

Wire `human_comprehensibility.check_record` into `roles/specs/*.json`'s
`quality_bar` arrays role-by-role as those roles land their own #1156/#1163
batches (per the issue's delivery-order item (c)); add
`convention_family_named` if a future round needs the metadata-slot rule;
consider adding a dedicated pr_reference test module if `pr_reference.py`
gains further checks (no such test module existed before this change).

## Resolution path

No open findings; nothing to resolve.

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

acceptance: python3 -m pytest gates/test_human_comprehensibility.py gates/test_record_lint.py gates/test_quality_bar.py -q — result:
```
69 passed, 1 xfailed in 1.11s
```

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

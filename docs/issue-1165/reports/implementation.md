---
code_under_review:
  - gates/human_comprehensibility.py
  - gates/test_human_comprehensibility.py
  - gates/pr_reference.py
  - gates/quality_bar.py
  - on-the-record/hooks/record-scaffold.sh
  - on-the-record/hooks/pr-preflight.sh
  - on-the-record/hooks/test_pr_preflight.py
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

## Round 3 amendment — PR #1621 re-review response

canonical: PR #1621 re-review comment beginning "Re-review: all four
prior blockers resolved (verified). One NEW blocking finding:" (read this
turn via `gh pr view 1621 --comments`)

resolved_findings:

finding E (new blocking) — `on-the-record/hooks/test_pr_preflight.py`'s
`test_hook_allows_legitimate_phase2_pr` regression, fixed.

acceptance: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — result:
```
1 failed, 15 passed in 0.97s
```
(pre-fix run, this turn: the fixture's bare `Closes #743` body failing the
round-2-added first-paragraph rule). Post-fix:
acceptance: python3 -m pytest on-the-record/hooks/test_pr_preflight.py -q — result:
```
16 passed in 1.01s
```
Chose the "acknowledge, don't exempt" path: the fixture body is now
`"Delivers the fix for the reported regression.\n\nCloses #743"` with an
inline docstring stating explicitly that bare-trailer phase-2 bodies are
now blocked at authoring time as an intentional consequence of round 2's
ported first-paragraph rule — phase-2 PRs get no carve-out from that
rule, they must carry real lead prose same as phase-1 PRs. Rejected
alternative: exempting phase-2 trailer-only bodies from the
first-paragraph rule, which would have reintroduced the bare-trailer
authoring-time gap round 2's port was meant to close.

finding F (merge requirement) — follow-up issue for the deferred
`quality-bar-gate.sh` per-role wiring, NOT filed this turn. canonical:
`gh issue create` invocation this turn refused by the spawning harness's
gh-guard PreToolUse hook (tool-result text produced this turn): "gh-guard:
refused for role session 'implementation': issues are the user's
requirement backlog, user-authored only (contract v3 s9) — no role
touches them." This is a genuine tooling block, not a skipped step: a
role session cannot file an issue under any circumstance, including a
review's explicit merge requirement. Per the SCOPE-EXCEEDED RULE this is
reported, not silently worked around; the human/on-the-record relay needs
to run `gh issue create --title "Wire human_comprehensibility_verdict
into quality-bar-gate.sh's per-role read" --body "Follow-up from PR #1621
(issue #1165): wire gates/quality_bar.py's human_comprehensibility_verdict
into quality-bar-gate.sh's live per-role record read and into every
role's roles/specs/*.json quality_bar array. Part of #1165"` and this
record's finding F plus the PR body then need the resulting issue number
substituted in place of this note.

finding G (merge requirement) — false `gates/test_hooks_parity.py`
drift-detection claim in `on-the-record/hooks/pr-preflight.sh`, corrected
(not covered instead).
derived: grep -n parity gates/test_hooks_parity.py
```
(no output — no line in that file mentions pr_reference/check_body/first_paragraph/citation)
```
that file's own module docstring (lines 1-18) states its scope as
hooks.json registration parity plus a spec-index-preflight.sh live-fire
deny, not pr_reference content. Chose "correct the comment" over "add
real parity coverage": `pr-preflight.sh`'s inline comment now names
`on-the-record/hooks/test_pr_preflight.py` as the actual pin (it
duplicates the ported logic as plain Python and asserts against it
directly, same pattern as `test_contract_guard.py`, per that file's own
module docstring) and states plainly that drift against
`gates/pr_reference.py`'s real `check_body` has no automated diff.
Rejected alternative: building a live-fire `gh pr create`/`edit` harness
inside `gates/test_hooks_parity.py` mirroring the existing
spec-index-preflight.sh red/green pattern — assessed in round 2 as
needing new fixture machinery beyond a cheap addition, unchanged this
round; carried into Next steps below rather than built under this
amendment's frozen scope.

## Open findings

Finding F above (follow-up issue for `quality-bar-gate.sh` per-role
wiring) is open pending the human/on-the-record relay filing the drafted
issue and this record's finding F/PR body being updated with its number.

## Next steps

File the follow-up issue drafted under finding F above (blocked from this
session by the gh-guard hook) and cite its number here and in the PR
body; wire `human_comprehensibility.check_record` /
`quality_bar.human_comprehensibility_verdict` into `roles/specs/*.json`'s
`quality_bar` arrays and into `quality-bar-gate.sh`'s live per-role record
read, role-by-role as those roles land their own #1156/#1163 batches (per
the issue's delivery-order item (c)); add `convention_family_named` if a
future round needs the metadata-slot rule; add
`pr_reference`/`pr-preflight.sh` live-fire coverage to
`gates/test_hooks_parity.py`.

## Resolution path

The four blocking findings from PR #1621's first review round are each
answered in the "Round 2 amendment" section above, and findings E-G from
the re-review are answered in "Round 3 amendment" above, each with a
`resolved_findings:` entry naming what changed and its canonical source;
a human reviewer reads this record and the diff to weigh whether those
answers hold — that read happens outside this session. Finding F's issue
number is still outstanding, per the Open findings section above.

## Doc placement

No new dependency, env var, config key, or migration was introduced by
this change, so the handbook/decisions/reports doc-placement ladder has no
additional entry beyond this record itself.

## Rationale for deviations

Earlier rounds: none — the automatable-half scope narrowings (skipping
`convention_family_named` and per-role `quality_bar` wiring) were already
stated as deferred/out-of-scope by the landed proposals and the issue's own
delivery-order item (c), not a divergence introduced in this build.

This round: one deviation. The re-review's merge requirement to "file the
follow-up issue for the deferred quality-bar-gate.sh per-role wiring"
could not be executed as instructed — `gh issue create` was refused by
the spawning harness's gh-guard hook, which forbids any role session from
filing issues under contract v3 s9 (issues are the user's requirement
backlog, user-authored only). Swapped to: draft the issue verbatim in
this record's finding F, report the block plainly, and leave issue
filing to the human/on-the-record relay — see finding F above for the
full account, an alternative-swap under the SCOPE-EXCEEDED RULE, not a
silent skip.

## Test evidence

acceptance: python3 -m pytest gates/test_human_comprehensibility.py gates/test_record_lint.py gates/test_quality_bar.py gates/test_hooks_parity.py on-the-record/hooks/test_pr_preflight.py -q — result:
```
96 passed, 1 xfailed in 1.20s
```

Round 2 adds `gates/test_hooks_parity.py` to the targeted set (since
`on-the-record/hooks/pr-preflight.sh` changed) and 11 new fixtures in
`gates/test_human_comprehensibility.py` for findings B and C above. Round
3 adds `on-the-record/hooks/test_pr_preflight.py` to the targeted set,
per the re-review's explicit requirement that it be green and included in
the stated test set — its case regressed by round 2's ported
first-paragraph rule, fixed under finding E above, is now part of this
command's passing total (see finding E's acceptance runs above for the
before/after counts on that file alone).

No dedicated pr_reference test module exists in this repo pre- or
post-change (canonical: `ls gates/` at commit 5883cc4d has no
test_pr_reference.py entry); `check_body`'s new behavior is covered
indirectly through the reused `first_paragraph_is_prose` helper, itself
directly covered by `gates/test_human_comprehensibility.py`.

canonical: python3 -m pytest on-the-record/hooks/test_pr_preflight.py gates/test_human_comprehensibility.py gates/test_record_lint.py gates/test_quality_bar.py gates/test_hooks_parity.py -q (this turn, 96 passed, 1 xfailed in 1.20s, see Test evidence above)
## Acceptance verification
- test_pr_preflight.py regression fixed and green — checked: on-the-record/hooks/test_pr_preflight.py::test_hook_allows_legitimate_phase2_pr — result: pass
- targeted test set green including test_pr_preflight.py — checked: gates/test_human_comprehensibility.py::test_check_record_includes_citation_trailing_placement_rule — result: pass

## Test-tier note (issue #1518)

canonical: `ls .on-the-record/test-tiers.json` — no such file at repo root
in this session. No tier config exists, so the targeted subset above was
run explicitly per this task's own "run targeted tests" instruction rather
than a tiered `fast` command; a full-suite wall-clock measurement was not
taken since the task scoped this session to targeted tests only.

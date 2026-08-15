---
code_under_review:
  - gates/skip_eligibility.py
  - gates/test_skip_eligibility.py
  - gates/spawn_on_pr.py
  - tests/test_spawn_on_pr.py
  - docs/specs/enforcement-boundary.md
type: verification
breaking: false
verdict: all-present
# canonical: git log -1 --format=%H 22e162ed (run in this session) — 22e162ed44368c09989aa191664c7dd586d29a89 merged to main at 1425c881
loop_state: closed
---

# issue #745 — conformance-review phase 2: Item 3 three-axis skip-eligibility

## Summary of work

Checked the seven requirements listed in
docs/issue-745/reports/conformance-review/current-state.md ("What
phase 2 will check") against the actual code landed at commit
22e162ed44368c09989aa191664c7dd586d29a89, working from
gates/skip_eligibility.py, gates/spawn_on_pr.py,
gates/test_skip_eligibility.py, tests/test_spawn_on_pr.py, and
docs/specs/enforcement-boundary.md — not from the implementation
record's own narration.

## Verdicts

### Requirement 1 — Axis 1 (size): non-docs added+removed >= 50 trips R

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 1
verdict: Present
evidence: gates/skip_eligibility.py lines 31 and 68 — `NON_DOCS_LINE_THRESHOLD = 50`; `size_trip = non_docs >= NON_DOCS_LINE_THRESHOLD`. `non_docs_lines_changed` (lines 39-41) sums added+removed for rows whose path does not start with `docs/`.

### Requirement 2 — Axis 2 (reversibility): gates/*.py, on-the-record/hooks/*.sh/hooks.json, roles/*.json, migration path, or any deletion trips R

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 2
verdict: Present
evidence: gates/skip_eligibility.py lines 33-36 — `HARD_TO_REVERT_RE` covers all four path classes; `hard_to_revert_hit` (lines 44-52) checks the regex against every changed path first, then treats any entry in `deleted` as a hit regardless of path.

### Requirement 3 — Axis 3 (claim vocabulary): landing record trips claim_scan.CLAIM_RE

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 3
verdict: Present
evidence: gates/skip_eligibility.py line 29 imports `CLAIM_RE` from `claim_scan` unchanged (no second regex); `claim_vocabulary_hit` (lines 55-58) searches it against `record_text`. `classify_for_subject` (lines 113-120, 143) sources that text via `git show <ref>:docs/issue-<n>/reports/implementation.md`, i.e. the landing record.

### Requirement 4 — Skip-eligible (S) only when ALL three axes low-risk

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 4
verdict: Present
evidence: gates/skip_eligibility.py lines 71 and 80-81 — `required = size_trip or reversibility_trip or claim_trip`; `population` is `"R"` if `required` else `"S"`, `skip_eligible = not required`.

### Requirement 5 — Classification written to a ledger so population membership is reproducible from ledger + diff history alone

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 5
verdict: Present
evidence: gates/spawn_on_pr.py lines 144-147 — `_filter_execution_observation` calls `spawn.ledger_write({"event": "execution_observation_classification", **classification})`, where `classification` (from `classify_for_subject`) carries `subject`, `ref`, `population`, and all three per-axis fields (skip_eligibility.py lines 73-82 and 145-146).

### Requirement 6 — #476's fabrication_survival_rate guardrail machinery stays untouched

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 6
verdict: Present
evidence: derived:
```
$ git diff 1425c881~2..1425c881 --stat
```
(run in this session) shows only gates/skip_eligibility.py, gates/spawn_on_pr.py, gates/test_skip_eligibility.py, tests/test_spawn_on_pr.py, docs/specs/enforcement-boundary.md, and two proposal/record docs changed — no file under the `fabrication_survival_rate` guardrail's own path is in that diff.
derived:
```
$ grep -rn fabrication_survival_rate gates/
gates/skip_eligibility.py:16:(required). `#476`'s `fabrication_survival_rate` guardrail machinery is
```
(run in this session) — the only match is a docstring mention at gates/skip_eligibility.py line 16, not any guardrail-computation file.

### Requirement 7 — Test coverage for each axis's trip boundary, including exact-50 and deletion-regardless-of-path

spec_ref: docs/issue-745/reports/conformance-review/current-state.md#what-phase-2-will-check item 7
verdict: Present
evidence: gates/test_skip_eligibility.py lines 95-101, `test_size_exactly_at_threshold_trips` — rows summing to exactly 50 (`skip_eligibility.NON_DOCS_LINE_THRESHOLD`) assert `size_axis_trip` true and population `"R"`. gates/test_skip_eligibility.py lines 55-58, `test_any_deletion_hits_regardless_of_path` — a deleted path (`"src/harmless.py"`, outside the hard-to-revert path patterns) still returns a hit. Per-axis boundary tests also present for the hooks/roles/migrations path variants (lines 37-53) and the claim-vocabulary axis (lines 65-75).

derived:
```
$ python3 -m pytest gates/test_skip_eligibility.py tests/test_spawn_on_pr.py -q
...................................                                     [100%]
35 passed in 1.35s
```

## Why (rationale)

Per contract v3 s19's conformance-review role: a per-requirement
Present/Surface/Absent/Incorrect/Unverifiable verdict, checked against
the artifact and the approved spec
(docs/issue-745/proposals/item3-execution-observation-conditioning.md)
directly, not against the implementation record's own claims.

## Upstream basis

- docs/issue-745/proposals/conformance-review.md (this issue's own
  approved phase-1 proposal) — defines the seven-requirement checklist
  this record verifies against.
- docs/issue-745/reports/conformance-review/current-state.md — board
  condition and target-artifact/spec identification.
- Implementation commit 22e162ed44368c09989aa191664c7dd586d29a89 (see
  canonical tag in this record's frontmatter) — the artifact under
  review.

## What did not work

None — all seven requirements verified Present, no findings to route to
issue-745/implementation.

## Open findings

None.

## Resolution path

Not applicable — no open findings.

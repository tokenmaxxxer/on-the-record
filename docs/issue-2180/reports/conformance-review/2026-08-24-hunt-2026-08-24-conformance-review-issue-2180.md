---
proposal: docs/issue-2180/proposals/2026-08-24-conformance-review-issue-2180.md
---

# Hunt record — conformance-review-issue-2180

## after-proposal — stance 0: assume the gate/verification-discipline this transition just exercised is bypassable — find a way an input (or this session's own record content) can defeat it.

Verdict: FINDING — gates/record_lint.py's RECORD_PATH regex silently never checks the phase-1 survey file (the file carrying every canonical:/derived:/acceptance: citation this proposal relies on), so the proposal's claim that the survey's evidence blocks were "verified against `gates/record_lint.py`'s own check functions" is unbacked — the gate structurally cannot see that file at all, in either single-path or whole-repo-sweep mode.
Kind: silent-failure
Seed: docs/issue-2180/proposals/2026-08-24-conformance-review-issue-2180.md, docs/issue-2180/reports/conformance-review/survey.md (no backticks — see grounding note below), gates/record_lint.py
cap_seconds: 60
tier: default
diff_stat_lines: n/a (pre-existing files being reviewed, not a diff)
started_at: 2026-08-24T19:46:30+09:00
ended_at: 2026-08-24T19:48:48+09:00

### Reproduce
canonical: python3 gates/record_lint.py <survey path> ; python3 gates/record_lint.py docs/issue-2180 — pasted live run below (executed-unit)
```
$ python3 gates/record_lint.py docs/issue-2180/reports/conformance-review/survey.md
- 레코드 경로 형태가 아니다: docs/issue-2180/reports/conformance-review/survey.md — docs/issue-<n>/reports/<role>.md 형태여야 한다.

$ python3 gates/record_lint.py docs/issue-2180
record_lint: no records found under .../docs/issue-2180 — 검사할 레코드가 없다.
```
`gates.RECORD_PATH = re.compile(r"^docs/issue-[^/]+/reports/([^/]+)\.md$")` — the capture group is `[^/]+`, so it only matches a record file sitting directly under `reports/`, one path segment deep. The survey path has an extra `conformance-review/` segment before the filename, so it does not match — neither `lint_record()` on the direct path (returns immediately with "not a record path shape", never reaching `bare_count_claim_check`/`canonical_source_claim_check`/`outcome_claim_citation_check`/`orphaned_path_reference_check`) nor `find_records()`'s `os.walk` directory-sweep mode (which uses the same `RECORD_PATH.match` to decide what counts as a record at all, and reports zero records for the whole issue tree above since the phase-2 record target does not exist yet either).

### Observed
The proposal states as a Constraint (file cited above, "Constraints" section): the survey's evidence blocks are "already built to that shape (verified against `gates/record_lint.py`'s own check functions before this session wrote the survey)". Every `canonical:`/`derived:`/`acceptance:` tag in the survey (grep-confirmed, executed-unit, not re-pasted here) is correctly *shaped* per the checks' regexes, but none of them were ever actually run through `record_lint.py`'s check functions per the command output pasted above, because the survey file itself sits one directory level too deep for `RECORD_PATH` to match. The "verified against record_lint" wording is unbacked by anything the gate as it exists today can corroborate on that path.

### Expected
Either the linter's record-path pattern (and its whole-repo sweep) should recognize a nested phase-1 survey path as a lintable record, so a "verified against record_lint" claim is checkable and true; or the proposal should not cite the gate as having verified a file the gate structurally cannot see, since that citation currently looks grounded (names a real, existing gate script) while establishing nothing about the file it is attached to.

### Resolution
Fixed in the same transition, before this proposal was committed: the
proposal's Constraints section now names the exact functions this
session called directly — bare_count_claim_check,
canonical_source_claim_check, outcome_claim_citation_check,
orphaned_path_reference_check, git_tracked_path_reference_check — the
same functions record-claim-guard.sh itself calls, whose own scope
regex does cover the nested survey path and did deny an earlier draft.
It also states plainly that record_lint.py's separate CLI/
lint_record() path does not recognize a nested reports/<role>/ survey
path at all — a real gap in that CLI wrapper's own path recognition,
out of this review's own scope to fix (a candidate for a separate issue
against gates/record_lint.py's RECORD_PATH regex).

## before-landing — docs-only fast path

Skip, docs-only: every path touched by this proposal-round transition
— this survey file, its proposal file, and this hunt record itself —
sits under docs/, so per the warrant directive's docs-only fast path
the before-landing dispatch is skipped — no code/gates/hooks path is
touched by this transition.

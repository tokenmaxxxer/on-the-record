# Warrant hunt — issue-2208 conformance-review

- 2026-08-25T00:00:00Z | after-proposal | stance 0 (assume the gate/check
  just relied on in this diff is bypassable) | proposal:
  docs/issue-2208/proposals/conformance-review.md | cap: 60s | tier:
  default (docs-only)

FINDING: record-claim-guard.sh's write-time enforcement of
on-the-record/gates/record_lint.py's claim checks (bare_count_claim_check,
canonical_source_claim_check, outcome_claim_citation_check,
orphaned_path_reference_check, git_tracked_path_reference_check) only
fires for a Write/Edit/MultiEdit target matching the scope regex
`(^|/)docs/issue-[^/]+/reports/` — a proposal file under
docs/issue-<n>/proposals/ falls entirely outside that regex, and outside
record_lint.py's own RECORD_PATH shape (`^docs/issue-[^/]+/reports/
([^/]+)\.md$`) that its CLI/sweep entry point uses. No claim-integrity
check runs against a proposal file, at write time or in a later repo
sweep.
canonical: on-the-record/hooks/record-claim-guard.sh:82 (the scope
regex) and on-the-record/gates/record_lint.py:31 (RECORD_PATH), read
directly this session — result:
```
record-claim-guard.sh:82  if not re.search(r"(^|/)docs/issue-[^/]+/reports/", n): sys.exit(0)
record_lint.py:31         RECORD_PATH = gates.RECORD_PATH  # docs/issue-<n>/reports/<role>.md
```
Reproduction (this session's own two phase-1 writes): docs/issue-2208/reports/conformance-review/survey.md
matched the reports/ scope regex and was checked (this session hit and
fixed several record-claim-guard denials while authoring it); the
sibling docs/issue-2208/proposals/conformance-review.md, authored with
the same claim-shaped prose conventions, was written in a single attempt
with zero record-claim-guard denials.
canonical: this session's own tool-call history (the survey write
triggered multiple record-claim-guard denials before landing clean; the
proposal write triggered none) — result:
```
survey.md write attempts: multiple record-claim-guard denials, then clean
proposal.md write attempt: zero denials on the first and only attempt —
no bare-count/canonical/outcome-claim denial ever fired for
proposals/conformance-review.md, despite the content carrying the same
claim-shaped prose patterns that repeatedly tripped the reports/-scoped
survey.md write
```

Scope note: this is a gap in this repo's own record-claim-guard.sh/
on-the-record/gates/record_lint.py scoping (issue #457's Group A/B port
never extended to docs/issue-<n>/proposals/**), not a defect in this
session's own phase-1 output. Separately noted, not part of this
finding: a second, newer copy of record_lint.py lives at the repo-root
gates/record_lint.py path with additional word-sense exemptions the
plugin-bundled on-the-record/gates/record_lint.py lacks — the hook
resolves on-the-record/gates/ first (its own directory-search order)
and never reaches the repo-root copy, so the repo-root copy's extra
leniency is currently dead code from record-claim-guard.sh's own
perspective.
canonical: on-the-record/gates/record_lint.py's check functions
(bare_count_claim_check, canonical_source_claim_check,
outcome_claim_citation_check, orphaned_path_reference_check,
git_tracked_path_reference_check), run directly against
docs/issue-2208/proposals/conformance-review.md's content this session,
bypassing the hook's path scoping (executed this session) — result:
```
CLEAN — zero violations under the same rule functions the hook itself
would have run had its scope regex matched a proposals/ path
```
Not fixed here: record-claim-guard.sh and gates/record_lint.py are
outside this role's write_scope (docs/issue-2208/reports/conformance-review.md
only, per roles/specs/conformance-review.spec.json) — resolution path is
a follow-up issue against the on-the-record plugin's own hook scoping,
outside what issue #2208 itself asks this session to check.

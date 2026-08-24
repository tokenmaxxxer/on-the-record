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

## before-landing — stance 1: assume this change and another plugin's rule cancel each other out — find the pair

Verdict: FINDING — approval-gate.sh (which gated this session's Write of docs/issue-2208/reports/conformance-review.md) accepts an APPROVE comment with no round-scoping check, while contract-guard.sh's own explicit round-scoping rule (issue #577) would classify that exact same comment as a stale prior-round approval that must not authorize this round's phase-2 work — the two hooks disagree on whether the same signal authorizes the same act.
Kind: composition
Seed: docs/issue-2208/reports/conformance-review.md (NEW), docs/issue-2208/proposals/conformance-review.md (status proposed->approved)
cap_seconds: 60
tier: size:docs-only
diff_stat_lines: 333 (332 new + 1 changed)
started_at: 2026-08-25T00:30:00+09:00
ended_at: 2026-08-25T00:55:00+09:00

### Reproduce
```
git log --format='%H %ad %s' --date=iso-strict origin/main..HEAD
# -> 08a56a57... 2026-08-25T00:14:27+09:00 issue-2208: conformance-review phase-1 -- survey + proposal
#    (this branch's/PR's own first commit)

grep -n 'APPROVE issue-2208/conformance-review' -A2 docs/issue-2208/reports/conformance-review.md
# record cites: "posted 2026-08-24T15:11:40Z" (= before 2026-08-25T00:14:27+09:00 == 2026-08-24T15:14:27Z)

sed -n '236,247p' on-the-record/hooks/contract-guard.sh
# phase2 = any(... and (not first_commit_at or c.get("createdAt","") > first_commit_at) ...)
# comment "APPROVE issue-2208/conformance-review" createdAt=2026-08-24T15:11:40Z is NOT > first_commit_at=2026-08-24T15:14:27Z

grep -n 'createdAt' on-the-record/hooks/approval-gate.sh
# only hit is inside _delegation_valid() (delegation-citation path); the plain
# typed-comment match (_first_line_matches + login-in-approvers, lines ~255-270)
# has zero recency/round-scoping check
```

### Observed
approval-gate.sh let this session's Write of the phase-2 record proceed on the
strength of the "APPROVE issue-2208/conformance-review" comment (2026-08-24T15:11:40Z)
even though that comment predates this PR's own first commit
(08a56a57, 2026-08-24T15:14:27Z) — the record itself documents this ("already
existed... before this session's phase-1 commit landed"). contract-guard.sh's
round-scoping condition (`createdAt > first_commit_at`), built specifically
per its own header comment "a prior-round approval (older than the new
round's first commit) must not gate a new round's phase-1 proposal PR"
(issue #577), would evaluate `phase2=False` for this identical comment on
this identical PR at merge time — the exact same signal that already bought
the phase-2 write past approval-gate.sh is one contract-guard.sh's own
explicit anti-staleness logic is designed to reject.

### Expected
Either both hooks apply the same round-scoping rule to the same
"APPROVE issue-<n>/<role>" signal, or approval-gate.sh's header/behavior
should not claim parity with contract-guard.sh's phase-2 approval
determination while omitting the recency check contract-guard.sh treats as
load-bearing for exactly this scenario (a stale, pre-first-commit approval
comment reused for a new round).

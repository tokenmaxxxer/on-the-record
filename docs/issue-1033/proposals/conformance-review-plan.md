---
status: proposed
files:
  - docs/issue-1033/reports/conformance-review.md
---

## Request
Issue #1033 cites one requirement, R001: the credential guard
(`credential-record-guard.sh` / `credential-network-guard.sh`) is the
standing security invariant and must not be weakened by the
example-allowlist change. This conformance review's job is to verdict R001
against the merged implementation — commits d0855574 and 8e753c3f on main
(docs/issue-1033/reports/conformance-review/survey.md) — never to fix
anything; findings, if any, address back to the implementation role.

## Constraints
- Verdict is per-requirement (Present/Surface/Absent/Incorrect/
  Unverifiable), never a holistic code-quality judgment.
- Phase 2 (writing docs/issue-1033/reports/conformance-review.md) works
  from the artifact and the spec only, deliberately without the
  implementation role's stated intent — the implementation.md record is
  read only to locate the changed-file list, not to inherit its own
  self-assessment.
- Phase 2 opens only after a docs/specs/approvers.md account submits
  either a PR-review Approve (two-account mode) or an issue-comment whose
  body is exactly `APPROVE issue-1033/conformance-review` (single-account
  mode).

## Requirement list (phase-1 extraction)
Single requirement, no sampling needed (survey: issue body carries only
one requirement ID).

- **R001** — the guard is the standing security invariant and must not be
  weakened by the allowlist addition. Decomposed into the sub-checks a
  verdict will apply against the code, independent of the builder's
  narration:
  1. The allowlist is an exact-string set, never folded into or loosening
     any of the four shape regexes (`gh[oprs]_`, `github_pat_`, `sk-`,
     `AKIA`).
  2. A credential-shaped string that is NOT one of the sourced allowlist
     entries still triggers both guards (i.e., there is a passing test
     asserting a novel same-shape string still denies).
  3. Both guards share one allowlist source (no independent per-guard
     copy of the exception list).
  4. The allowlist entries are exact-string matches compared against the
     regex match span (`m.group(0)` membership), not prefix/substring
     matching.
  5. No unrelated loosening was introduced elsewhere in either guard's
     fail-closed behavior (trap/exit-code handling, scope checks) while
     making this change.

## Out of scope
- No new requirement IDs beyond R001 — issue #1033 names none other.
- No opinion on code style, naming, or architecture choices (module vs.
  sidecar file) — those are implementation-role judgment calls, not
  conformance criteria.

## How you'll know it worked
Phase 2 produces docs/issue-1033/reports/conformance-review.md carrying
one verdict line for R001 (and its five sub-checks folded into that
verdict's evidence), each backed by a `canonical:` citation to the actual
code read in this session, per the record-claim-citation directive.

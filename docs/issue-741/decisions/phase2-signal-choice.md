# Decision: content-based phase-2 signal for contract-guard.sh

Subject: issue-741

## Chosen signal

A PR only counts as phase-2-shaped for `contract-guard.sh`'s
Closes-attach decision when its own diff (`gh pr view --json files`)
touches at least one path matching `(^|/)(src|tests?)/`, OR matches the
acting role's own exact record file `docs/issue-<n>/reports/<role>.md` —
the same two conditions `approval-gate.sh:116-119` already checks, at the
same precision (an exact filename, not a directory-wide match). The path
list comes from widening the existing `gh pr view ... --json
body,number,commits` call to also request `files` — one more field on a
call already made, zero extra round trips.

The acting role is derived from `git rev-parse --abbrev-ref HEAD` parsed
against `^issue-(\d+)/([\w-]+)$`, the same lookup `pr-preflight.sh` and
`approval-gate.sh` already perform. If the branch doesn't parse, or its
issue number doesn't match the PR's own issue, the record-file half of
the check is skipped (treated as not matched) rather than falling back to
a broader pattern — failure narrows the match, it never widens it.

## Rejected — PR body phase declaration

A `phase: 2` or similar self-declared field in the PR body was rejected.
This is the plain self-report shape issue #476 already ruled
untrustworthy for exactly this class of decision: #476's H1 argument
(`docs/issue-476/proposals/discovery.md:94-100`) is that ground truth
must come from a source that "share[s] no state and no authorship" with
the thing being judged, not from "a self-report" the same actor controls.
A PR body is authored by the same session whose own compliance is in
question — trivially forgeable (accidentally or not) with no independent
check. `pr-preflight.sh` and `contract-guard.sh` already agree on this in
practice: neither derives `phase` from PR body content today; both derive
it from an independent `gh issue view` comments lookup.

## Rejected — proposal frontmatter write-set realization

Comparing the approved proposal's `files:` list against the PR's actual
diff was rejected on two grounds: (1) no existing code in this repo
parses a proposal's YAML `files:` list at all — `gates/gates.py`'s two
existing declared-vs-diff comparators (`writeset()` against `spec.md`'s
`- write: <glob>` lines, and `role_scope()` against `roles/<role>.json`'s
`write_scope` globs) both compare against a different, already-
machine-readable declaration, never a proposal's frontmatter; building a
new parser is a materially bigger, more fragile surface for the same
yes/no answer the simpler content check already gives. (2) it is
ambiguous which proposal file is authoritative once an issue accumulates
more than one round's proposals, and it would force `contract-guard.sh`
to locate and read a specific markdown file's frontmatter across repos it
may have no local checkout of (issue #443's `-R`/URL case) — the simpler
path-pattern check needs no such lookup, since `gh pr view --json files`
already returns paths directly.

## Forgeability judgment (the #476 line)

Could a session force a docs-only PR to look phase-2-shaped by adding a
throwaway file under `src/`/`tests?/`, or force a real code PR to look
phase-1-shaped by omitting them? The `src/`/`tests?/` direction is
already blocked by a deployed, independent gate: `approval-gate.sh`
denies any `Write/Edit/MultiEdit` to a `src/`/`tests?/` path from an
un-approved session — a phase-1 session cannot legally create such a path
before approval in the first place, so gaming this signal upward requires
first defeating a different, already-hardened gate.

The record-file direction needed a second pass after the after-proposal
warrant hunt (`docs/issue-741/reports/implementation/
2026-08-11-hunt-phase2-content-gate.md`) found the first draft matched
any direct-child filename under `docs/issue-<n>/reports/`, not just the
one exact filename `approval-gate.sh` itself restricts
(`docs/issue-<n>/reports/<role>.md`). That broadened match would have
reopened the hole: a phase-1 session can legally create an unrelated file
in that same directory today (a stray note, another role's record
filename), and a role-agnostic pattern would misread it as
phase-2-shaped if it shipped in a docs-only PR's diff. The shipped design
derives the acting role from the branch name and matches only that role's
exact filename, closing this — pinned as a permanent regression by
`test_unrelated_file_under_reports_dir_gets_no_closes` in
`test_contract_guard.py`.

The remaining case — a genuine phase-2 delivery touching none of `src/`,
`tests?/`, or its own record file — is not gaming so much as
non-delivery: the RECORD REQUIREMENT already mandates every phase-2
session commit its own exact record file before ending, so a real
delivery always trips the record-path check even in the degenerate
docs-only-deliverable case.

## Scope boundary — pr-preflight.sh unification, explicitly out

`pr-preflight.sh`'s own phase-2 signal (unscoped by time, unlike
`contract-guard.sh`) stays out of scope, per issue #653's ADR
(`docs/issue-653/proposals/2026-08-10-closes-trailer-preflight-hardening.md`
lines 60-70, 88-91): `pr-preflight.sh` only `deny()`s at create/edit time
— it never executes a merge and never writes `Closes` itself, so a wrong
verdict there cannot reproduce #741's actual failure (an issue closing
with no delivery). `contract-guard.sh` remains the sole authoritative
enforcement point. Unifying the two scripts' comment-matching logic
remains its own, already-identified gap
(`docs/issue-653/reports/architecture/survey.md` gap #1).

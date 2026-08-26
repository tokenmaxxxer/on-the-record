# Observer verification: record-kind matching (stage 5)

Issue #2241 (role-axis retirement) stage 5
(`docs/issue-2241/proposals/2026-08-25-stage-5-observer-record-kind.md`)
is the last of the five staged rewrites and the one the issue itself
calls out as the actual risk: `gates/merge_gate.py`'s
`required_verification_missing()` — the check a PR cannot merge without
passing — used to key directly off two hardcoded role names. That
hardcode is "exactly what jammed merges" in incident #2233 and fed the
#2238 runaway, which is why every other stage (lease, author identity,
write-scope, branch naming) had to land and prove stable first.

## What changed

`gates/spawn_on_pr.py`:

- `PR_TRIGGERED_ROLES` is now `PR_TRIGGERED_RECORD_KINDS` — same two
  values, `("execution-observation", "conformance-review")`. The
  narrowing itself (2 of the 10 `board_condition`-carrying roles that
  are mechanically presence-checkable) is unrelated to this stage and
  stays as-is.
- `applicable_roles()` is now `applicable_record_kinds()`. It scans a
  subject's board entries for a `kind:` frontmatter value in the
  required set, instead of testing whether a role-named file exists.

`gates/merge_gate.py`:

- `required_verification_missing()` delegates to
  `applicable_record_kinds()`, passing the subject's own
  `author:` (read off its `implementation` record) as
  `subject_author`.
- `_exempt_own_role` is renamed `_exempt_own_record_kind` — same
  circularity-breaking shape (an observer PR's own branch supplies
  the very record it would otherwise be blocked on lacking), now
  read as exempting a record-*kind*, not a role.

## Kind-field matching, with a filename fallback

Matching an entry against a required kind checks **either** signal,
not just one:

1. `kind: execution-observation` (or `conformance-review`) in the
   entry's own frontmatter, or
2. the entry's filename stem is `execution-observation.md` /
   `conformance-review.md`.

This is deliberately an OR, not a kind-only check with a narrow
fallback for absent fields. A repo-wide sweep at stage 1 found the
`kind:` field already in ad hoc use across 420+ pre-existing records
under 40+ spellings (`docs/specs/record-kind-vocabulary.md`) — a good
number of them carrying a `kind:` value that predates the closed
vocabulary entirely (e.g. a generic `kind: record`) rather than no
`kind:` line at all. A fallback that only triggers when the field is
*absent* misses every one of those: the field is present, just not one
of the two required values, so a kind-only check would report a
record as missing verification when a role-filename check would have
found it. The filename fallback is checked independently of what (if
anything) `kind:` says, so both eras of the corpus are read correctly
by the same function.

## Self-verification guard

Presence of the right `kind:` value is not sufficient — the record
also has to have been produced by someone other than the subject's own
author. A record-kind match whose `author:` equals the subject's own
`author:` (its `implementation` record's `author:` field) does not
count toward satisfying `required_verification_missing()`. This is the
mechanical enforcement of issue #2241's own non-goal: retiring the role
axis is not a reason to accept self-verification.

`subject_author` is looked up once, from the subject's own
`implementation` board entry; if that entry or its `author:` field is
absent (e.g. a subject predating stage 1, or a purely local call with
no board context), the guard is skipped rather than treating every
kind match as suspect — an unknown author is not evidence of
self-verification.

## What did not change

- `_exempt_own_record_kind`'s branch-derived exemption. It still reads
  the PR-under-evaluation's own branch suffix (`<subject>/<kind>`) and
  drops that one kind from `missing` if present — `gates/spawn_on_pr.py`
  is outside stage 4's write set and still checks out these two kinds'
  branches via `pipeline.checkout_issue_branch()`
  (`issue-<n>/<role>`, byte-identical to today), so the branch suffix
  is still a reliable proxy for which kind that PR itself supplies.
  This is also, not coincidentally, the same value the observer
  session's own `author:` field carries once its record lands — the
  branch suffix and the eventual `author:` value are the same string
  by construction for this pair.
- Which two kinds are required, or widening/narrowing the observer
  pair — a separate policy question, out of this stage's scope.
- Anything about branch naming (stage 4) or write-scope (stage 3).

## Rollback

Reverting `gates/merge_gate.py`/`gates/spawn_on_pr.py` to the
role-matching version is safe: every record written from stage 1
onward carries both `role:`/filename and `kind:`, so it evaluates
identically under either version. No subject's verification state is
stranded by a revert.

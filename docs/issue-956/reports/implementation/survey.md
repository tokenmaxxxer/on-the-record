# Current-state survey — issue #956

## Scope authorized

canonical: `gh issue view 956`, read live in this session.

Body explicitly authorizes target-project scope that #955's addendum (in
`docs/issue-566/reports/implementation.md`, re-delivery session) refused as unauthorized — "This
issue authorizes that scope explicitly." Ask: make requirement capture work by default in a
TARGET project repo where on-the-record is installed as a plugin, hooks-only (req#7 no-band-aid),
reusing the landed digest machinery as substrate.

## What exists today

canonical: `on-the-record/hooks/product-capture-stopgate.sh`, read live in this session (full
file, 211 lines).

- `on-the-record/hooks/product-capture-stopgate.sh` (#566, merged PR #575; extended #684): a `Stop`
  hook. Reads `transcript_path` off the Stop event, walks the transcript for `type=="user"` text,
  flags sentences against four EN+KO category regexes (requirements/priorities/philosophy/goals),
  and — for any category with a flagged sentence but no corresponding added line in
  `docs/issue-<n>/product/<cat>.md` (working diff or last commit) — emits an advisory
  `additionalContext` nudging the session to record it. It already runs off `pwd -P` (cwd, i.e.
  whatever repo the session is in), not a hardcoded on-the-record path — so the mechanism itself is
  not literally hardcoded to this repo.
- The gap (`product-capture-stopgate.sh:63-66`): `issue_n` is derived by regex-matching the
  **current branch** against `^issue-(\d+)/([\w-]+)$`. If the branch does not match, the hook exits
  0 silently — no bootstrap, no advisory, ever. That branch convention (`issue-<n>/<role>`) is
  on-the-record's own role-handoff convention (contract v3 s19); a target-project user working
  their own repo's ordinary branches (`main`, `feature/x`, etc.) will never match it, so the hook
  is permanently a no-op there. This is the literal band-aid req#7 flags: capture only works when
  the *host* repo happens to use on-the-record's own branch-naming scheme.

canonical: `gates/requirement_digest.py` and `on-the-record/hooks/requirement-digest-preflight.sh`,
both read live in full in this session.

- `gates/requirement_digest.py` + `on-the-record/hooks/requirement-digest-preflight.sh` (#930/#943):
  operate on `docs/specs/requirements.md` -> `docs/specs/requirement-digest.md`, repo-root paths,
  already fully repo-agnostic — no on-the-record-specific path or branch assumption anywhere in
  either file. This is the "landed digest machinery" the issue asks to reuse as substrate:
  condensing raw capture into a compact live-requirements digest, independent of which repo it
  runs in.

canonical: `harness/fixture-requirement-digest/scenario.py`, read live in this session.

- `harness/fixture-requirement-digest/scenario.py`: exercises `requirement_digest` mechanically
  against a seeded scratch repo (no live Claude session needed) — the pattern to mirror for the
  new target-repo capture scenario.

canonical: `docs/specs/requirements.md`, read live in this session.

- `docs/specs/requirements.md`: append-only registry, `## R<nnn>` blocks with
  `quote/source_issue/check/status`. Nothing today writes to this file automatically from
  conversation — entries are added by a role's own judgment. Out of scope for this issue: the ask
  is to fix the *capture* path (product-capture-stopgate.sh's four docs/product/<cat>.md
  categories), not to build a new autowriter for `requirements.md` itself.

## The one design decision this proposal must freeze

Where does capture write when the branch is NOT `issue-<n>/<role>` (i.e., an ordinary
target-project branch)? Two live options:

1. Fall back to a single fixed non-issue-scoped path, `docs/product/<cat>.md` (repo root, no
   issue segment) — the pre-#684 layout, appropriate because a target-project repo mostly does not
   run concurrent on-the-record role sessions against the same file the way #684's collision
   scenario worried about.
2. Leave the hook a no-op outside the `issue-<n>/<role>` pattern and require target-project users
   to adopt that branch convention.

Option 2 is exactly the band-aid the issue's title names ("must work in TARGET project repos, not
only on-the-record itself") — rejected. Option 1 is the proposal's choice; recorded with its
rejected alternative in the proposal's `## Rationale`.

## Scout-directive skip record

Skipped. Reason: this is internal hook/git-plumbing engineering with a single narrow fallback-path
decision already dictated by the issue's own explicit ask ("reuse the landed digest machinery...
make its capture path repo-agnostic and default-on") and the existing #566/#684 precedent this
proposal extends verbatim in shape — there is no product-facing category with external
best-in-class exemplars to compare against for "where should a git hook write a fallback file
path." Per the scout directive's two mandatory skip conditions, this falls under "the spec leaves
no design decision open" in the narrow sense that the only decision (fallback path scheme) is
already constrained by the existing landed pattern it must stay consistent with, not by any
external field to survey.

## Write set this proposal will freeze

- `on-the-record/hooks/product-capture-stopgate.sh` — repo-agnostic fallback path when branch
  doesn't match `issue-<n>/<role>`.
- `on-the-record/hooks/test_product_capture_stopgate.py` — new test(s) for the fallback path and
  the empty-state guard.
- `harness/fixture-target/scenario.py` (new fixture, mirroring `fixture-requirement-digest`'s
  no-live-session pattern) — asserts capture into a non-on-the-record target repo with no explicit
  skill call, and the empty-state guard (no stated requirements -> no digest/doc writes).

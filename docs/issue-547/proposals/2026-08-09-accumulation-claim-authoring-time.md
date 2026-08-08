---
status: proposed
files:
  - on-the-record/hooks/accumulation-claim-guard.sh
  - on-the-record/hooks/test_accumulation_claim_guard.py
  - gates/accumulation.py
  - gates/test_accumulation.py
---

## Request

Issue #547: `accumulation-claim-guard.sh` only checks for a filled
`## Accumulation` section the first time phase 2 edits an
accumulation-shaped `.py` file — after the proposal is already approved
and the write set frozen. Move the check earlier: require the section
at proposal-authoring time, when the proposal's own `files:` write set
already includes an accumulation-shaped target, so the cost lands at
the cheap point (writing the proposal) instead of the expensive one
(mid-build, per #533's two failed-no-commit attempts).

## Constraints

- Reuse the existing shape definitions (shape 1: >= 3 inline
  `subprocess`/`gh`-style calls in one `.py` file; shape 5:
  `roles/*.json`-pattern files) — no new, broader accumulation
  detector; #419's finding that a general structural-similarity
  detector floods this repo with false positives still holds.
- No hardcoded file list beyond what the two shapes already name.
- Keep one definition of "these two shapes" in one place; don't fork
  the shape logic into a second copy.
- Field-presence only (contract §14): the check verifies
  `## Accumulation` exists and is non-empty, never whether its content
  is an accurate prediction.

## Rationale

**Chosen: extend `accumulation-claim-guard.sh` with a second branch**
that fires when the write is a `.md` file under
`docs/issue-<n>/proposals/`, reading the write's own `files:`
frontmatter list and checking each listed path against the same two
shape functions the guard already uses for `.py` writes, then requiring
`## Accumulation` in the proposal body being written (not a separately
committed proposal file, so it catches the write in progress).

**Rejected: a new standalone `proposal-shape-gate.sh`.** It would need
its own `hooks.json` registration and would either duplicate the shape
constants and detection functions that already live in
`accumulation-claim-guard.sh` (two copies to keep in lockstep, on top of
the existing lockstep-with-`gates/accumulation.py` the current guard's
header already documents), or force factoring shared shell logic into a
library file, a pattern no other hook in this repo uses. One hook
already owns "does this touch an accumulation shape, and is the field
filled" end-to-end for `.py` writes; splitting the same question across
two hook files for the `.md` case buys no behavioral difference and
adds a second file to keep in sync every time the shape definitions
change.

**Rejected: enforce only in CI / `gates/accumulation.py`, not the
interactive hook.** Still lands the cost at PR-review time rather than
proposal-write time — the exact "cost lands at the most expensive
point" defect the issue is about, just moved from phase-2-first-edit to
CI instead of to authoring time.

## What will be done

- `gates/accumulation.py`: add `_touches_shape_1_by_path(work, rel)` /
  reuse `_touches_shape_5` against a plain path list (no git diff
  needed) so the same two shape checks work from either a `git diff`
  (existing phase-2 caller) or a static `files:` list (new
  authoring-time caller). Add a `check_accumulation_claim_for_files(work,
  files, body)` entry point that shape-checks a list of paths directly.
- `on-the-record/hooks/accumulation-claim-guard.sh`: add a branch that
  fires when `tool_input.file_path` matches
  `docs/issue-<n>/proposals/*.md` (any `tool_name` in
  `Write|Edit|MultiEdit`, matching the existing hook registration). For
  `Write`, the tool's `content` is the full resulting file and is used
  directly. For `Edit`/`MultiEdit`, the existing `.py`-branch pattern of
  scanning only the write's own `new_string` fragment is *not* reused
  here: a fragment-only scan misses a `files:` list edited incrementally
  (an `Edit` that appends a path to an already-open list without
  repeating the `files:` key parses as a bare list, not a mapping, and
  the branch would see no `files:` key at all — a warrant-hunt finding
  against an earlier draft of this design, recorded at
  `docs/reports/2026-08-09-hunt-accumulation-claim-authoring-time.md`).
  Instead, for `Edit`/`MultiEdit` the branch reads the proposal file's
  *current on-disk content*, applies the edit's `old_string`/`new_string`
  (or each `edits[]` entry in order) the same way the tool itself would,
  and parses `files:` and `## Accumulation` from that reconstructed
  full-file result — never from the fragment alone. It then applies
  shape 1 (content-based, checked against each listed path's *current*
  on-disk state — see Out of scope for what this can't see) and shape 5
  (path-regex, needs no content) to that list, and — if either shape is
  touched — requires `## Accumulation` to be present and non-empty in
  the reconstructed body. Denies (exit 2) with a message naming which
  shape and which listed path triggered it, mirroring the existing
  phase-2 denial message.
- `gates/test_accumulation.py`: unit tests for the new
  `check_accumulation_claim_for_files` — shape-5 path list with/without
  the section; shape-1 existing-file-over-threshold path list
  with/without the section; a files list touching neither shape passes
  regardless of body.
- `on-the-record/hooks/test_accumulation_claim_guard.py`: tests for the
  new `.md`/`files:` branch — proposal write naming `roles/x.json`
  without `## Accumulation` denied; same write with the section filled
  allowed; a proposal naming only unrelated files never blocked; a
  non-proposal `.md` write (e.g. a report) still ignored, matching
  current behavior; an incremental `Edit` that appends `roles/x.json`
  to an already-open `files:` list without repeating the `files:` key
  is still caught (regression test for the warrant-hunt finding above).

## Out of scope

- Detecting a *brand-new* file that will only reach the shape-1
  threshold as a *result* of this change (no call sites exist yet to
  count) — the check only sees the current on-disk state of listed
  paths, same limitation the existing phase-2 diff-based check already
  has for genuinely new files. This is the "empty state" the issue's
  acceptance criterion asks to name: authoring-time detection cannot
  fully reuse the guard's shape definition here because that definition
  is inherently content-based, and no content exists yet for a file
  that doesn't exist yet; the approximation is "check only paths already
  present in the tree."
- Any change to the phase-2 `.py`-write branch's existing behavior —
  it keeps running as today's safety net for cases the authoring-time
  check couldn't see (the brand-new-file case above, or a proposal
  whose `files:` list changes mid-build).
- Any change to shape definitions themselves (thresholds, patterns) —
  out of scope per issue #547's own framing ("pointing to the spec
  condition, no hardcoded file list beyond the existing gate's own
  shape definition").
- Retrofitting already-approved proposals (#533/#534/#540 already
  landed).

## How you'll know it worked

- `python3 gates/test_accumulation.py` and
  `python3 on-the-record/hooks/test_accumulation_claim_guard.py` (or the
  project's combined `python3 -m pytest` entry point) green in a clean
  worktree.
- New unit test: writing a proposal `.md` whose `files:` includes
  `roles/x.json` (or an existing over-threshold `.py` path) with no
  `## Accumulation` section is refused (exit 2) at write time, before
  any phase-2 code write happens.
- A proposal `files:` list touching neither shape, or one with the
  section filled, is never blocked.

## Accumulation

This proposal itself edits `gates/accumulation.py`, which already has
>= 3 inline `subprocess.run` call sites (`_touches_shape_1` fires on its
own implementation) — so this section is required and is being filled
here, one live instance of the exact rule this issue is adding earlier
enforcement for.

If this style of dual-purpose guard/checker file (bash mirror +
`gates/*.py` canonical implementation, kept in lockstep by hand) grows a
third instance beyond `accumulation-claim-guard.sh`/`accumulation.py`
and `call-shape-guard.sh`/its own counterpart, the manual lockstep
comment convention (as seen in this guard's header) stops scaling — a
shared test asserting the two files' shape constants stay equal would
be the next accumulation point to address, not attempted here since
only two such pairs exist today.

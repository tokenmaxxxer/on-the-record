# Survey — issue #547

## Current state

`gates/accumulation.py::check_accumulation_claim(work, body)` is the
source of truth for the two accumulation shapes (issue #424):

- shape 1: a `.py` file with >= `_SHAPE_1_THRESHOLD` (3) inline
  `subprocess.run/check_output/check_call/Popen` call sites
  (`_touches_shape_1`, line 75).
- shape 5: any changed path matching `^roles/[^/]+\.json$`
  (`_touches_shape_5`, line 94).

Its session-side mirror, `on-the-record/hooks/accumulation-claim-guard.sh`,
is wired in `on-the-record/hooks/hooks.json` (line 45) as a
`PreToolUse: Write|Edit|MultiEdit` hook. It only inspects the tool call
when `tool_input.file_path` ends in `.py` (guard script, "if not
isinstance(p, str) or not p or not p.endswith('.py'): sys.exit(0)"). A
`.md` write — including a proposal file itself — never reaches the
shape checks at all; the hook returns immediately.

Consequence, confirmed by the issue body and by `git log` on #533
(`67f12af`, `d89c5f5`): a proposal can be approved with no
`## Accumulation` section, and the gate only fires the first time phase
2 edits an accumulation-shaped `.py` file — after the proposal's write
set is already frozen and phase 2 is already underway. Two of #533's
early commits were guard-triggered rewrites, i.e. the cost the issue
describes.

There is no `proposal-shape-gate.sh` file in this repository (the
`<proposal-shape-directive>` in the session's system prompt is a plugin
convention layered on top of `on-the-record`, not code living here) —
so the fix has to live inside `on-the-record`'s own hook, not a file
that doesn't exist in this tree.

## Write surface for this issue

- `on-the-record/hooks/accumulation-claim-guard.sh` — the only file that
  currently decides when the `## Accumulation` requirement is checked
  and against what tool call. This is the natural place to add an
  authoring-time check, since it already owns both shape definitions
  (kept in lockstep with `gates/accumulation.py` per that guard's own
  header comment) and the field-presence check
  (`_has_filled_accumulation`).
- `gates/accumulation.py` — the canonical Python-side implementation.
  Extending its shape-detection to accept a `files:` list (not just a
  git diff) so both the guard and a potential CLI/test caller share one
  definition, rather than duplicating shape logic a third time.
- `gates/test_accumulation.py` — existing unit tests; new tests for
  proposal-authoring-time detection belong here, following the existing
  temp-git-repo harness pattern already in this file.
- `on-the-record/hooks/test_accumulation_claim_guard.py` — mirrors the
  guard's bash/python behavior; likely needs a new test class for the
  `.md`-write / `files:` frontmatter path.

## Unknowns the proposal must resolve

1. **What triggers the authoring-time check.** The guard currently
   matches on `file_path.endswith(".py")`. A proposal write is a `.md`
   write under `docs/issue-<n>/proposals/`. The check needs a second
   branch keyed on that path shape, reading the write's own frontmatter
   `files:` list (the write set, per `docs/proposals/*` and
   `docs/issue-<n>/proposals/*` convention already used by
   `record-claim-guard.sh` and this repo's proposal format) instead of
   `git diff`.
2. **How shape 1 is detected pre-code.** `_touches_shape_1` currently
   counts subprocess calls in the *changed file's new content* or the
   *existing tracked tree*. At proposal-authoring time, the listed
   `files:` targets usually do not have new content yet (the proposal
   only names paths) — so the only signal available is: does the listed
   path already exist in the tree with >= threshold calls (an edit to
   an already-accumulating file), or does it match a path convention
   scout/architecture surveys have already flagged as accumulation-prone
   (e.g. it already exists and crosses the threshold). This is the
   "state nothing maintains" gap that Out of scope must own explicitly:
   a proposal creating a *brand-new* file that will only reach the
   threshold *after* this change cannot be shape-1-detected from a path
   list alone, because there is no content to inspect yet. The
   acceptance criterion's "empty state" bullet asks for exactly this:
   state why detection can't fully reuse the guard's shape definition
   here, and name the approximation (existing on-disk content of listed
   paths only; new-file-reaching-threshold is not detectable at
   authoring time and is explicitly out of scope, same as the phase-2
   guard already can't see future edits either).
3. **Shape 5 is fully reusable as-is** — `roles/*.json` is a path-shape
   regex, requiring no content, so it applies identically to a `files:`
   list.
4. **Failure/refusal mechanics.** The existing guard fails closed on
   git errors and denies (`exit 2`) with a stderr message when the
   shape is touched and the field is missing/absent. The new
   authoring-time branch should mirror that: deny the proposal *write
   itself* pointing back at the same two shapes, so the person writing
   the proposal fixes it before it's ever approved — the entire point
   of the issue.

## Alternatives visible from this survey

- **A: extend `accumulation-claim-guard.sh` in place** (adds a
  `.md`-under-`docs/*/proposals/`-path branch) — reuses the existing
  wiring in `hooks.json`, the existing shape constants, and the existing
  `_has_filled_accumulation` regex. No new hook registration needed.
- **B: a new standalone `proposal-shape-gate.sh`-style hook** — cleaner
  separation of concerns (one hook per shape rule) but requires a new
  `hooks.json` entry, duplicates the shape-detection logic that already
  lives in the accumulation guard (or requires factoring it into a
  shared shell library, which no other hook here does), and splits one
  concept ("accumulation claim requirement") across two files for no
  behavioral gain.
- **C: enforce only in `gates/accumulation.py`/CI, not the interactive
  hook** — misses the point of the issue: the whole defect is that
  phase-1 authoring has no live gate, and CI-only enforcement still
  lands the cost late (at PR time, not at proposal-write time).

A and B are both viable; A is the survey's leaning since it keeps one
definition of "these two shapes" in one file, matching this repo's
existing pattern of guard scripts each owning one rule end-to-end.

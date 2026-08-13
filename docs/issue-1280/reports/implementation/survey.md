# Current-state survey — issue #1280

## Write surfaces

- `on-the-record/monitors/poll-heartbeat.sh`, the #1245 attachment gate
  (around line 71): `[ ! -f "$(pwd -P)/docs/specs/approvers.md" ]` ->
  `echo ...; exit 0`. This exits the whole Monitor process (not just one
  tick), before the alive-marker touch and before the `while true` tick
  loop. Session-bound + non-rearmable per the file's own "Hard boundary"
  comment: once this process exits, nothing in this session re-arms it.
- Same file, the alive marker touch: `$(pwd -P)/.orchestrate-monitor-alive/alive`
  (inside the target repo). This is the #1245 "no registration artifacts
  in non-board repos" boundary the issue asks to preserve while
  relocating the marker itself.
- `on-the-record/hooks/directive.sh`, `OTR_MN_DIR="$(pwd -P)/.orchestrate-monitor-alive"`
  — the #947 notice logic's read side. Must track wherever the marker
  moves to, or the notice logic silently goes blind (never fires, or
  worse, always fires).
- `spawn.py`, `_board_wide_sweep_all()` — already per-repo board gated for
  roster targets (issue #1276): a roster entry whose `work` repo lacks
  `docs/specs/approvers.md` gets one skip line and is excluded from the
  sweep. But `root` (the arm-root) is added to the sweep targets
  unconditionally — the function's own docstring states arm-root is
  "never skipped" because CLI-side validation (#1275) was assumed to have
  already guaranteed it is a board. That assumption breaks once
  poll-heartbeat.sh stops exiting on a non-board root: the arm-root sweep
  (closure_sweep/spawn_coverage) would then run `gh issue list` etc.
  against a non-board arm-root every tick — needs the same per-repo board
  check roster targets already get, but must also stay perfectly silent
  (no skip line at all) for the "non-board root + empty roster"
  empty-state case, since acceptance requires zero per-tick output there.
- `tests/test_spawn.py`,
  `test_board_wide_sweep_all_empty_roster_sweeps_arm_root_only` — asserts
  today's behavior: an arbitrary tempdir (not a board — no
  `docs/specs/approvers.md`) passed as `root` with an empty roster still
  gets the sweep function invoked on it once. This encodes the "CLI
  already validated" assumption as a test fixture accident (the tempdir
  was never meant to model a non-board root, just "some root"), not a
  deliberate non-board-root case. This test needs correcting so its
  `root` is an actual board (matching what the CLI gate always guaranteed
  before this issue); issue #1280's new non-board-root+empty-roster case
  gets its own new test asserting the opposite result (nothing swept, no
  output).

## Existing conventions to reuse

- `_repo_identity()` / the roster-sweep's per-repo-prefixed line shape in
  `_board_wide_sweep_all()` is the established shape for multi-repo sweep
  output; reuse it rather than inventing a new line shape for the
  excluded-root case (though the excluded-root case itself must stay
  silent, per acceptance).
- `docs/issue-1275/proposals/monitor-arm-root-validation.md` and
  `docs/issue-1245/proposals/2026-08-13-monitor-attachment-board-gate.md`
  are the two prior proposals this issue's gate demotion sits directly on
  top of — both currently document a hard `exit` on gate failure, which
  this issue narrows to "the git-repo check (#1275) still exits; the
  board-registration check (#1245) demotes to sweep-exclusion."
- `on-the-record/hooks/directive.sh`'s `GREETED_MARKER` shows the
  established pattern for a per-workspace marker rooted under a repo's
  own cwd, but nothing yet under `~/.claude/tokenmaxxxer/` is keyed by
  *which* repo a session is in — the relocated alive marker is the first
  thing there that needs that keying (multiple concurrent CLI sessions in
  different repos must not collide on one shared `alive` file, or a live
  session in repo A would falsely "prove" a monitor alive for a later
  session in repo B — the same collision class issue #947's own hunt
  findings already flagged for `session_id`, mirrored here for repo
  identity). No existing helper hashes an arbitrary filesystem path in
  this codebase; `directive.sh` already hashes `session_id` via
  `hashlib.sha256(...).hexdigest()[:24]` — the same primitive, applied to
  `pwd -P` instead, is the natural fit and keeps both scripts computing
  the identical key independently (no shared state file needed to agree
  on it).

## Unknowns / design decisions this proposal must freeze

1. The alive-marker path format under `~/.claude/tokenmaxxxer/` (must be
   computable independently and identically by both `poll-heartbeat.sh`
   and `directive.sh`, since they are different processes/hook
   invocations that never share state directly).
2. Whether the excluded-root case in `_board_wide_sweep_all` prints
   anything (acceptance says no per-tick output for the empty-roster
   case; the answer is "never print for the excluded root," full stop —
   the simplest option and it satisfies acceptance in both the empty- and
   non-empty-roster non-board-root cases alike).

## Skip condition

Scouting (best-in-class product research) does not apply: this is a
same-repo defect/behavior-correction change entirely internal to this
plugin's own Monitor/hook wiring, with no external product surface or
prior-art category to compare against — narrowing an existing gate's
severity and relocating a marker file. No design decision here benefits
from comparing external tools.

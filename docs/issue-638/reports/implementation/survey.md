# Current-state survey — issue #638

## What was checked

`grep -rln "proposal-shape-gate.sh\|survey-order-gate.sh" .` (excluding
`.git/`) across the repo. Hits:

- `docs/issue-600/reports/implementation.md` (lines 73, 83) — the origin
  reference: describes hitting `proposal-shape-gate.sh`'s seven-section
  check and `survey-order-gate.sh`'s ordering check while doing #600's own
  build.
- `docs/issue-623/reports/execution-observation.md` (lines 39, 61, 130,
  156) — #623's drive already flagged this as open finding 2: the two
  names are not found under the packaged `on-the-record/hooks/` tree,
  routed to a fresh remediation issue (this one).
- `docs/issue-319`, `docs/issue-245`, `docs/issue-547`, `docs/issue-517`,
  `docs/issue-363`, `docs/issue-373`, `docs/issue-419` survey/proposal
  files — checked individually; each occurrence is that file's own
  survey quoting the standing `<proposal-shape-directive>` /
  `<survey-order-directive>` boilerplate text (the same injected
  system-reminder every phase-1 session sees), not a claim about where
  the `.sh` files live. Not stale references — no correction needed
  there.

## Where the two names actually live

- `on-the-record/hooks/hooks.json` — the plugin's full `PreToolUse`
  hook registration list (`Write|Edit|MultiEdit` matcher block: 
  `record-claim-guard.sh`, `role-spec-reference-guard.sh`,
  `call-shape-guard.sh`, `accumulation-claim-guard.sh`,
  `approval-gate.sh`). Neither `proposal-shape-gate.sh` nor
  `survey-order-gate.sh` appears anywhere in this file.
- `ls on-the-record/hooks/` — 20 real `.sh`/`.py` files, none named
  `proposal-shape-gate.sh` or `survey-order-gate.sh`.
- `git log --all --oneline -- '*proposal-shape-gate.sh' '*survey-order-gate.sh'`
  — empty. These two filenames have never existed anywhere in this
  repo's history, under any path, at any commit.
- `on-the-record/hooks/directive.sh` (the plugin's own
  `UserPromptSubmit` injector) — 126 lines, read in full. It injects the
  *orchestrator*-session directive only, and explicitly exits early
  (`[ -z "${CLAUDE_ROLE:-}" ] || exit 0`) whenever `CLAUDE_ROLE` is set —
  i.e. it never fires anything into a role session at all. It contains
  no mention of "proposal-shape", "survey-order", or "seven-section"
  anywhere.
- `docs/specs/enforcement-boundary.md` — the authoritative row-per-
  mechanism table that `gates/test_boundary.py` enforces completeness
  of. It lists every `gates/*.py` module and every
  `on-the-record/hooks/*.sh` script that exists in the repo. Neither
  name appears, and none should be added: the boundary table's own
  completeness check is derived from what's on disk (`gates/*.py`,
  `on-the-record/hooks/*.sh`, `.github/workflows/*.yml`); adding a row
  for a nonexistent file would be a fabricated row, not a real one.

## Conclusion (answers the issue's three-way question)

Not repo-root tooling (no such file anywhere under the repo, `gates/`
included), not a rename (no prior git history to rename from), and not
a packaging gap in `on-the-record/hooks/` (`hooks.json` never listed
them, so there is no shipped-then-dropped hook to restore).

They are a **different, external layer**: role sessions spawned by this
project's own harness receive `UserPromptSubmit`-injected directives
(`<proposal-shape-directive>`, `<survey-order-directive>`, etc. — the
same block visible verbatim in this very session) from a source outside
`on-the-record/hooks/directive.sh`, which this survey confirmed never
fires into a role session. Those directive blocks describe
gate scripts (with these exact two names) that mechanically enforce the
directive at write time — but those scripts, if they exist at all,
live in the external harness that spawns role sessions, not in this
repo's packaged plugin tree. #600's implementation record — written
from inside a live role session — described hitting real, live gate
behavior; it was accurate about what happened, just silent about which
layer produced it, and #623's drive then read that silence as "missing
from the package," which is the stale part.

## Write set this implies

Correcting the reference is confined to `docs/issue-600/reports/implementation.md`
(the origin claim) and `docs/issue-623/reports/execution-observation.md`
(the finding built on it) — both prose-only edits, no code, no
`docs/specs/enforcement-boundary.md` row (nothing to add a row for).

## Skip conditions

Scout directive: not invoked as a full sweep — this is a repo-internal
documentation correction with no product-facing or external-field
question to research; the survey above (grep + hooks.json + git log +
full read of directive.sh) is the complete field for this fix.
